import asyncio
import json
import multiprocessing
import os
import queue
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from typing import Any

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Request,
)
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite import SqliteSaver

from week7_part_d_hitl import (
    CHECKPOINT_DB,
    build_part_d_graph,
    clear_runtime_credentials,
    create_initial_state,
    make_config,
    resume_with_decision,
    set_runtime_credentials,
)


router = APIRouter(
    prefix="/agent",
    tags=["Week 7 Agent"],
)


SERVICE_KEY_ENV = "WEEK7_SERVICE_KEY"

MAX_RUN_SECONDS = 30.0
MAX_GRAPH_STEPS = 12
PROCESS_STOP_GRACE_SECONDS = 1.0

_process_context = multiprocessing.get_context("spawn")

_active_processes: dict[str, multiprocessing.Process] = {}
_active_processes_lock = threading.Lock()

_cancelled_threads: set[str] = set()
_cancelled_threads_lock = threading.Lock()


def _sse(
    event_name: str,
    payload: dict[str, Any],
) -> str:
    return (
        f"event: {event_name}\n"
        f"data: {json.dumps(payload)}\n\n"
    )


def _require_service_key(
    supplied_key: str | None,
) -> None:
    expected_key = os.getenv(
        SERVICE_KEY_ENV,
        "",
    ).strip()

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Agent service key is not configured.",
        )

    if not supplied_key:
        raise HTTPException(
            status_code=401,
            detail="X-Service-Key is required.",
        )

    if supplied_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid X-Service-Key.",
        )


def _extract_forwarded_token(
    authorization: str | None,
) -> str:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail=(
                "Forwarded user authorization "
                "is required."
            ),
        )

    prefix = "Bearer "

    if not authorization.startswith(prefix):
        raise HTTPException(
            status_code=401,
            detail=(
                "Forwarded authorization must "
                "use Bearer authentication."
            ),
        )

    token = authorization[
        len(prefix):
    ].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Forwarded user token is empty.",
        )

    return token


def _validate_thread_id(
    raw_thread_id: Any,
) -> str:
    if not isinstance(
        raw_thread_id,
        str,
    ):
        raise HTTPException(
            status_code=400,
            detail="threadId is required.",
        )

    clean_thread_id = raw_thread_id.strip()

    if not clean_thread_id:
        raise HTTPException(
            status_code=400,
            detail="threadId is required.",
        )

    if len(clean_thread_id) > 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid threadId.",
        )

    try:
        parsed_thread_id = uuid.UUID(
            clean_thread_id
        )

    except (ValueError, AttributeError) as error:
        raise HTTPException(
            status_code=400,
            detail="threadId must be a valid UUID.",
        ) from error

    return str(parsed_thread_id)


@contextmanager
def _open_graph():
    connection = sqlite3.connect(
        CHECKPOINT_DB,
        check_same_thread=False,
        timeout=10.0,
    )

    checkpointer = SqliteSaver(
        connection
    )

    graph = build_part_d_graph(
        checkpointer
    )

    try:
        yield graph

    finally:
        connection.close()


def _is_cancelled(
    thread_id: str,
) -> bool:
    with _cancelled_threads_lock:
        return (
            thread_id
            in _cancelled_threads
        )


def _mark_cancelled(
    thread_id: str,
) -> None:
    with _cancelled_threads_lock:
        _cancelled_threads.add(
            thread_id
        )


def _clear_cancelled(
    thread_id: str,
) -> None:
    with _cancelled_threads_lock:
        _cancelled_threads.discard(
            thread_id
        )


def _register_process(
    thread_id: str,
    process: multiprocessing.Process,
) -> None:
    with _active_processes_lock:
        _active_processes[
            thread_id
        ] = process


def _unregister_process(
    thread_id: str,
    process: multiprocessing.Process,
) -> None:
    with _active_processes_lock:
        current = _active_processes.get(
            thread_id
        )

        if current is process:
            _active_processes.pop(
                thread_id,
                None,
            )


def _get_active_process(
    thread_id: str,
) -> multiprocessing.Process | None:
    with _active_processes_lock:
        process = _active_processes.get(
            thread_id
        )

        if (
            process is not None
            and process.is_alive()
        ):
            return process

        return None


def _terminate_process(
    process: multiprocessing.Process,
) -> None:
    if not process.is_alive():
        return

    process.terminate()
    process.join(
        timeout=PROCESS_STOP_GRACE_SECONDS
    )

    if process.is_alive():
        process.kill()
        process.join(
            timeout=PROCESS_STOP_GRACE_SECONDS
        )


def _interrupt_payload(
    snapshot,
) -> dict[str, Any] | None:
    tasks = getattr(
        snapshot,
        "tasks",
        (),
    )

    for task in tasks:
        interrupts = getattr(
            task,
            "interrupts",
            (),
        )

        for interrupt_item in interrupts:
            value = getattr(
                interrupt_item,
                "value",
                None,
            )

            if isinstance(
                value,
                dict,
            ):
                return value

    return None


def _snapshot_values(
    graph,
    thread_id: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any] | None,
]:
    config = make_config(
        thread_id
    )

    snapshot = graph.get_state(
        config
    )

    values = dict(
        snapshot.values or {}
    )

    interrupt_payload = (
        _interrupt_payload(
            snapshot
        )
    )

    return (
        values,
        interrupt_payload,
    )


def _safe_worker_values(
    values: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": str(
            values.get(
                "status",
                "",
            )
        ),
        "answer": str(
            values.get(
                "answer",
                "",
            )
        ),
        "action_result": str(
            values.get(
                "action_result",
                "",
            )
        ),
    }


def _status_payload(
    graph,
    thread_id: str,
) -> dict[str, Any]:
    values, interrupt_payload = (
        _snapshot_values(
            graph,
            thread_id,
        )
    )

    active_process = _get_active_process(
        thread_id
    )

    if (
        not values
        and active_process is None
        and not _is_cancelled(thread_id)
    ):
        raise HTTPException(
            status_code=404,
            detail="Agent thread not found.",
        )

    if _is_cancelled(
        thread_id
    ):
        status = "cancelled"

    elif active_process is not None:
        status = "running"

    elif interrupt_payload is not None:
        status = "pending_approval"

    else:
        status = str(
            values.get(
                "status",
                "unknown",
            )
        )

    pending_approval = None

    if interrupt_payload is not None:
        tool_name = str(
            interrupt_payload.get(
                "tool_name",
                "",
            )
        )

        arguments = (
            interrupt_payload.get(
                "arguments",
                {},
            )
        )

        pending_approval = {
            "calls": [
                {
                    "name": tool_name,
                    "args": arguments,
                }
            ]
        }

    return {
        "threadId": thread_id,
        "status": status,
        "answer": str(
            values.get(
                "answer",
                "",
            )
        ),
        "pendingApproval": pending_approval,
    }


def _start_worker(
    thread_id: str,
    message: str,
    user_token: str,
    result_queue,
) -> None:
    try:
        with _open_graph() as graph:
            config = make_config(
                thread_id
            )

            try:
                set_runtime_credentials(
                    user_token=user_token,
                )

                graph.invoke(
                    create_initial_state(
                        message
                    ),
                    config={
                        **config,
                        "recursion_limit":
                            MAX_GRAPH_STEPS,
                    },
                )

            finally:
                clear_runtime_credentials()

            values, interrupt_payload = (
                _snapshot_values(
                    graph,
                    thread_id,
                )
            )

            result_queue.put(
                {
                    "ok": True,
                    "values":
                        _safe_worker_values(
                            values
                        ),
                    "interrupt":
                        interrupt_payload,
                }
            )

    except BaseException as error:
        try:
            clear_runtime_credentials()
        except Exception:
            pass

        result_queue.put(
            {
                "ok": False,
                "error": str(error),
            }
        )


def _resume_worker(
    thread_id: str,
    approved: bool,
    user_token: str,
    idempotency_key: str,
    result_queue,
) -> None:
    try:
        with _open_graph() as graph:
            values, interrupt_payload = (
                _snapshot_values(
                    graph,
                    thread_id,
                )
            )

            if not values:
                result_queue.put(
                    {
                        "ok": True,
                        "notFound": True,
                    }
                )
                return

            if interrupt_payload is None:
                result_queue.put(
                    {
                        "ok": True,
                        "alreadyResolved": True,
                        "values":
                            _safe_worker_values(
                                values
                            ),
                    }
                )
                return

            config = make_config(
                thread_id
            )

            try:
                set_runtime_credentials(
                    user_token=user_token,
                    idempotency_key=
                        idempotency_key,
                )

                resume_with_decision(
                    graph,
                    config,
                    approved,
                )

            finally:
                clear_runtime_credentials()

            new_values, new_interrupt = (
                _snapshot_values(
                    graph,
                    thread_id,
                )
            )

            result_queue.put(
                {
                    "ok": True,
                    "values":
                        _safe_worker_values(
                            new_values
                        ),
                    "interrupt":
                        new_interrupt,
                }
            )

    except BaseException as error:
        try:
            clear_runtime_credentials()
        except Exception:
            pass

        result_queue.put(
            {
                "ok": False,
                "error": str(error),
            }
        )


def _read_worker_result(
    result_queue,
) -> dict[str, Any]:
    try:
        return result_queue.get(
            timeout=1.0
        )

    except queue.Empty:
        return {
            "ok": False,
            "error": (
                "Agent worker ended without "
                "returning a result."
            ),
        }


async def _monitor_worker(
    request: Request,
    thread_id: str,
    process: multiprocessing.Process,
    result_queue,
) -> dict[str, Any]:
    started_at = time.monotonic()

    try:
        while True:
            try:
                outcome = result_queue.get_nowait()

            except queue.Empty:
                outcome = None

            if outcome is not None:
                process.join(
                    timeout=PROCESS_STOP_GRACE_SECONDS
                )

                if process.is_alive():
                    _terminate_process(
                        process
                    )

                return outcome

            if await request.is_disconnected():
                _mark_cancelled(
                    thread_id
                )

                _terminate_process(
                    process
                )

                return {
                    "cancelled": True,
                    "disconnected": True,
                }

            if _is_cancelled(
                thread_id
            ):
                _terminate_process(
                    process
                )

                return {
                    "cancelled": True,
                }

            elapsed = (
                time.monotonic()
                - started_at
            )

            if elapsed >= MAX_RUN_SECONDS:
                _terminate_process(
                    process
                )

                return {
                    "timedOut": True,
                    "elapsedSeconds":
                        round(elapsed, 3),
                }

            if not process.is_alive():
                process.join(
                    timeout=PROCESS_STOP_GRACE_SECONDS
                )

                return await asyncio.to_thread(
                    _read_worker_result,
                    result_queue,
                )

            await asyncio.sleep(
                0.05
            )

    finally:
        _unregister_process(
            thread_id,
            process,
        )

        try:
            result_queue.close()
        except Exception:
            pass


async def _execute_start(
    request: Request,
    thread_id: str,
    message: str,
    user_token: str,
) -> dict[str, Any]:
    result_queue = (
        _process_context.Queue()
    )

    process = _process_context.Process(
        target=_start_worker,
        args=(
            thread_id,
            message,
            user_token,
            result_queue,
        ),
        daemon=True,
    )

    _register_process(
        thread_id,
        process,
    )

    try:
        process.start()

    except Exception:
        _unregister_process(
            thread_id,
            process,
        )

        try:
            result_queue.close()
        except Exception:
            pass

        raise

    return await _monitor_worker(
        request,
        thread_id,
        process,
        result_queue,
    )


async def _execute_resume(
    request: Request,
    thread_id: str,
    approved: bool,
    user_token: str,
    idempotency_key: str,
) -> dict[str, Any]:
    existing_process = (
        _get_active_process(
            thread_id
        )
    )

    if existing_process is not None:
        return {
            "ok": False,
            "error": (
                "Agent thread is already running."
            ),
        }

    result_queue = (
        _process_context.Queue()
    )

    process = _process_context.Process(
        target=_resume_worker,
        args=(
            thread_id,
            approved,
            user_token,
            idempotency_key,
            result_queue,
        ),
        daemon=True,
    )

    _register_process(
        thread_id,
        process,
    )

    try:
        process.start()

    except Exception:
        _unregister_process(
            thread_id,
            process,
        )

        try:
            result_queue.close()
        except Exception:
            pass

        raise

    return await _monitor_worker(
        request,
        thread_id,
        process,
        result_queue,
    )


async def _read_json_body(
    request: Request,
) -> dict[str, Any]:
    try:
        body = await request.json()

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON request body.",
        ) from error

    if not isinstance(
        body,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Request body must be "
                "a JSON object."
            ),
        )

    return body


@router.post("/runs")
async def start_agent_run(
    request: Request,
    x_service_key: str | None = Header(
        default=None,
        alias="X-Service-Key",
    ),
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
):
    _require_service_key(
        x_service_key
    )

    user_token = (
        _extract_forwarded_token(
            authorization
        )
    )

    body = await _read_json_body(
        request
    )

    message = str(
        body.get(
            "message",
            body.get(
                "question",
                "",
            ),
        )
    ).strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message is required.",
        )

    if len(message) > 1000:
        raise HTTPException(
            status_code=400,
            detail=(
                "Message cannot exceed "
                "1000 characters."
            ),
        )

    thread_id = _validate_thread_id(
        body.get(
            "threadId"
        )
    )

    if _get_active_process(
        thread_id
    ) is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Agent thread is already running."
            ),
        )

    _clear_cancelled(
        thread_id
    )

    async def event_stream():
        yield _sse(
            "thread",
            {
                "threadId": thread_id,
            },
        )

        yield _sse(
            "step",
            {
                "kind": "tool_call",
                "name": "agent",
                "summary":
                    "Agent run started.",
            },
        )

        try:
            outcome = await _execute_start(
                request,
                thread_id,
                message,
                user_token,
            )

            if outcome.get(
                "disconnected"
            ):
                return

            if outcome.get(
                "cancelled"
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "run_cancelled",
                        "message":
                            "Agent run was cancelled.",
                        "retryable": False,
                    },
                )

                return

            if outcome.get(
                "timedOut"
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "run_timeout",
                        "message":
                            "Agent run exceeded "
                            "its time budget.",
                        "retryable": True,
                    },
                )

                return

            if not outcome.get(
                "ok",
                False,
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "agent_run_failed",
                        "message":
                            str(
                                outcome.get(
                                    "error",
                                    "Agent run failed.",
                                )
                            ),
                        "retryable": True,
                    },
                )

                return

            interrupt_payload = (
                outcome.get(
                    "interrupt"
                )
            )

            values = outcome.get(
                "values",
                {},
            )

            if interrupt_payload:
                yield _sse(
                    "step",
                    {
                        "kind":
                            "tool_call",
                        "name":
                            interrupt_payload.get(
                                "tool_name",
                                "unknown",
                            ),
                        "summary":
                            "Write action requires "
                            "human approval.",
                    },
                )

                yield _sse(
                    "approval_required",
                    {
                        "threadId":
                            thread_id,
                        "calls": [
                            {
                                "name":
                                    interrupt_payload.get(
                                        "tool_name",
                                        "",
                                    ),
                                "args":
                                    interrupt_payload.get(
                                        "arguments",
                                        {},
                                    ),
                            }
                        ],
                    },
                )

                return

            answer = str(
                values.get(
                    "answer",
                    "",
                )
            )

            if answer:
                yield _sse(
                    "token",
                    {
                        "text": answer
                    },
                )

            yield _sse(
                "final",
                {
                    "answer": answer,
                    "sources": [],
                },
            )

        except asyncio.CancelledError:
            _mark_cancelled(
                thread_id
            )

            process = (
                _get_active_process(
                    thread_id
                )
            )

            if process is not None:
                _terminate_process(
                    process
                )

            raise

        except Exception as error:
            process = (
                _get_active_process(
                    thread_id
                )
            )

            if process is not None:
                _terminate_process(
                    process
                )

            yield _sse(
                "error",
                {
                    "code":
                        "agent_run_failed",
                    "message":
                        str(error),
                    "retryable": True,
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":
                "no-cache",
            "Connection":
                "keep-alive",
            "X-Accel-Buffering":
                "no",
        },
    )


@router.post(
    "/runs/{thread_id}/resume"
)
async def resume_agent_run(
    thread_id: str,
    request: Request,
    x_service_key: str | None = Header(
        default=None,
        alias="X-Service-Key",
    ),
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    _require_service_key(
        x_service_key
    )

    user_token = (
        _extract_forwarded_token(
            authorization
        )
    )

    thread_id = _validate_thread_id(
        thread_id
    )

    body = await _read_json_body(
        request
    )

    approved = body.get(
        "approved"
    )

    if not isinstance(
        approved,
        bool,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "approved must be "
                "true or false."
            ),
        )

    clean_idempotency_key = (
        idempotency_key or
        f"agent-{thread_id}"
    ).strip()

    if (
        not clean_idempotency_key
        or len(
            clean_idempotency_key
        ) > 100
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid Idempotency-Key.",
        )

    async def event_stream():
        try:
            outcome = await _execute_resume(
                request,
                thread_id,
                approved,
                user_token,
                clean_idempotency_key,
            )

            if outcome.get(
                "disconnected"
            ):
                return

            if outcome.get(
                "notFound"
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "thread_not_found",
                        "message":
                            "Agent thread was "
                            "not found.",
                        "retryable": False,
                    },
                )

                return

            if outcome.get(
                "cancelled"
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "run_cancelled",
                        "message":
                            "Agent run was cancelled.",
                        "retryable": False,
                    },
                )

                return

            if outcome.get(
                "timedOut"
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "run_timeout",
                        "message":
                            "Agent run exceeded "
                            "its time budget.",
                        "retryable": True,
                    },
                )

                return

            if not outcome.get(
                "ok",
                False,
            ):
                yield _sse(
                    "error",
                    {
                        "code":
                            "agent_resume_failed",
                        "message":
                            str(
                                outcome.get(
                                    "error",
                                    "Agent resume failed.",
                                )
                            ),
                        "retryable": True,
                    },
                )

                return

            values = outcome.get(
                "values",
                {},
            )

            if outcome.get(
                "alreadyResolved"
            ):
                answer = str(
                    values.get(
                        "answer",
                        "",
                    )
                )

                yield _sse(
                    "final",
                    {
                        "answer": answer,
                        "sources": [],
                    },
                )

                return

            interrupt_payload = (
                outcome.get(
                    "interrupt"
                )
            )

            if interrupt_payload:
                yield _sse(
                    "approval_required",
                    {
                        "threadId":
                            thread_id,
                        "calls": [
                            {
                                "name":
                                    interrupt_payload.get(
                                        "tool_name",
                                        "",
                                    ),
                                "args":
                                    interrupt_payload.get(
                                        "arguments",
                                        {},
                                    ),
                            }
                        ],
                    },
                )

                return

            action_result = str(
                values.get(
                    "action_result",
                    "",
                )
            )

            if action_result:
                yield _sse(
                    "step",
                    {
                        "kind":
                            "tool_result",
                        "name":
                            "reserve_book",
                        "summary":
                            action_result,
                    },
                )

            answer = str(
                values.get(
                    "answer",
                    "",
                )
            )

            if answer:
                yield _sse(
                    "token",
                    {
                        "text": answer
                    },
                )

            yield _sse(
                "final",
                {
                    "answer": answer,
                    "sources": [],
                },
            )

        except asyncio.CancelledError:
            _mark_cancelled(
                thread_id
            )

            process = (
                _get_active_process(
                    thread_id
                )
            )

            if process is not None:
                _terminate_process(
                    process
                )

            raise

        except Exception as error:
            process = (
                _get_active_process(
                    thread_id
                )
            )

            if process is not None:
                _terminate_process(
                    process
                )

            yield _sse(
                "error",
                {
                    "code":
                        "agent_resume_failed",
                    "message":
                        str(error),
                    "retryable": True,
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":
                "no-cache",
            "Connection":
                "keep-alive",
            "X-Accel-Buffering":
                "no",
        },
    )


@router.get(
    "/runs/{thread_id}"
)
async def get_agent_run(
    thread_id: str,
    x_service_key: str | None = Header(
        default=None,
        alias="X-Service-Key",
    ),
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
):
    _require_service_key(
        x_service_key
    )

    _extract_forwarded_token(
        authorization
    )

    thread_id = _validate_thread_id(
        thread_id
    )

    try:
        with _open_graph() as graph:
            return _status_payload(
                graph,
                thread_id,
            )

    except sqlite3.OperationalError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Agent checkpoint store "
                "is temporarily busy."
            ),
        ) from error


@router.post(
    "/runs/{thread_id}/cancel"
)
async def cancel_agent_run(
    thread_id: str,
    x_service_key: str | None = Header(
        default=None,
        alias="X-Service-Key",
    ),
    authorization: str | None = Header(
        default=None,
        alias="Authorization",
    ),
):
    _require_service_key(
        x_service_key
    )

    _extract_forwarded_token(
        authorization
    )

    thread_id = _validate_thread_id(
        thread_id
    )

    process = _get_active_process(
        thread_id
    )

    if process is not None:
        _mark_cancelled(
            thread_id
        )

        _terminate_process(
            process
        )

        return {
            "threadId": thread_id,
            "status": "cancelled",
        }

    try:
        with _open_graph() as graph:
            values, _ = (
                _snapshot_values(
                    graph,
                    thread_id,
                )
            )

    except sqlite3.OperationalError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Agent checkpoint store "
                "is temporarily busy."
            ),
        ) from error

    if (
        not values
        and not _is_cancelled(
            thread_id
        )
    ):
        raise HTTPException(
            status_code=404,
            detail="Agent thread not found.",
        )

    _mark_cancelled(
        thread_id
    )

    return {
        "threadId": thread_id,
        "status": "cancelled",
    }