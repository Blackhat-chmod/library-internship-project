import os
import sqlite3
import uuid
from pathlib import Path
from typing import Literal, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from reservation_tool_demo import reserve_book
from week7_part_c_graph import (
    ActionResult,
    build_catalog_subgraph,
    choose_route,
    chitchat_node,
    planner_node,
    replan_node,
    retry_node,
    route_after_action,
    router_node,
)


AI_SERVICE_DIR = Path(__file__).resolve().parent
CHECKPOINT_DB = AI_SERVICE_DIR / "week7_checkpoints.sqlite"

RUNTIME_USER_TOKEN_ENV = "WEEK7_USER_TOKEN"
RUNTIME_IDEMPOTENCY_KEY_ENV = "WEEK7_IDEMPOTENCY_KEY"


class PartDState(TypedDict):
    user_message: str
    route: str
    answer: str
    status: str

    plan: list[str]
    book_id: int | None

    action_result: ActionResult
    action_status_code: int | None

    retry_count: int
    replan_count: int

    approval_required: bool
    approval_granted: bool | None
    approval_message: str


def route_after_planner(
    state: PartDState,
) -> str:
    if state["book_id"] is None:
        return "end"

    return "approval"


def normalize_approval(
    decision,
) -> bool:
    """
    Accept boolean, text, or dictionary resume values
    while keeping approval explicit.
    """

    if isinstance(decision, bool):
        return decision

    if isinstance(decision, dict):
        value = decision.get(
            "approved",
            decision.get("approve"),
        )

        if isinstance(value, bool):
            return value

        if value is not None:
            decision = value

    if isinstance(decision, str):
        normalized = decision.strip().lower()

        return normalized in {
            "yes",
            "y",
            "approve",
            "approved",
            "true",
        }

    return False


def approval_node(
    state: PartDState,
) -> dict:
    """
    Pause immediately before the reservation write.

    The human sees the exact tool name and exact
    arguments that will be executed.

    No JWT, API key, or idempotency key is included
    in the interrupt payload or graph state.
    """

    book_id = state["book_id"]

    if book_id is None:
        return {
            "approval_required": False,
            "approval_granted": False,
            "approval_message": (
                "Approval was not requested because "
                "there is no valid book ID."
            ),
            "answer": (
                "Please provide a valid book ID "
                "before approving a reservation."
            ),
            "status": "approval_not_required",
        }

    decision = interrupt(
        {
            "type": "tool_approval",
            "tool_name": "reserve_book",
            "arguments": {
                "book_id": book_id,
            },
            "question": (
                f"Approve reserve_book"
                f"(book_id={book_id})?"
            ),
            "message": (
                "This action writes reservation data "
                "and requires explicit human approval."
            ),
        }
    )

    approved = normalize_approval(
        decision
    )

    if approved:
        return {
            "approval_required": True,
            "approval_granted": True,
            "approval_message": (
                f"Human approved reserve_book"
                f"(book_id={book_id})."
            ),
            "status": "approval_granted",
        }

    return {
        "approval_required": True,
        "approval_granted": False,
        "approval_message": (
            f"Human denied reserve_book"
            f"(book_id={book_id})."
        ),
        "answer": (
            f"Reservation of Book {book_id} "
            f"was cancelled because approval "
            f"was not granted."
        ),
        "status": "approval_denied",
    }


def route_after_approval(
    state: PartDState,
) -> str:
    if state["approval_granted"] is True:
        return "execute"

    return "end"


def build_runtime_tool_config() -> RunnableConfig:
    """
    Build an ephemeral tool-only configuration.

    Credentials come from the process environment,
    not LangGraph state or checkpoint configuration.

    This config is created only inside the write node
    and is passed directly to the reservation tool.
    It is never returned from the node.
    """

    user_token = os.environ.get(
        RUNTIME_USER_TOKEN_ENV,
        "",
    ).strip()

    idempotency_key = os.environ.get(
        RUNTIME_IDEMPOTENCY_KEY_ENV,
        "",
    ).strip()

    configurable = {}

    if user_token:
        configurable["user_token"] = user_token

    if idempotency_key:
        configurable["idempotency_key"] = (
            idempotency_key
        )

    return {
        "configurable": configurable
    }


def secure_action_executor_node(
    state: PartDState,
) -> dict:
    """
    Execute reserve_book only after approval.

    The checkpointed LangGraph config is deliberately
    NOT passed to the tool. A fresh ephemeral config is
    built from process environment variables instead.

    Therefore the JWT can authenticate the HTTP request
    without entering graph state, checkpoint metadata,
    or the SQLite checkpoint database.
    """

    book_id = state["book_id"]

    if book_id is None:
        return {
            "action_result": "failed",
            "action_status_code": None,
            "answer": (
                "A valid book ID is required."
            ),
            "status": "action_failed",
        }

    if state["approval_granted"] is not True:
        return {
            "action_result": "failed",
            "action_status_code": None,
            "answer": (
                "The reservation was not executed "
                "because human approval is required."
            ),
            "status": "approval_required",
        }

    tool_config = build_runtime_tool_config()

    result = reserve_book.invoke(
        {
            "book_id": book_id,
        },
        config=tool_config,
    )

    status_code = result.get(
        "status"
    )

    if result.get("ok") is True:
        return {
            "action_result": "success",
            "action_status_code": status_code,
            "answer": (
                f"Book {book_id} was "
                "reserved successfully."
            ),
            "status": "action_success",
        }

    if status_code == 409:
        return {
            "action_result": "conflict",
            "action_status_code": 409,
            "answer": result.get(
                "message",
                "Reservation conflict.",
            ),
            "status": "action_conflict",
        }

    if status_code in (401, 403):
        return {
            "action_result": "auth_failure",
            "action_status_code": status_code,
            "answer": (
                "Authentication or authorization "
                "failed. The action was stopped."
            ),
            "status": "action_auth_failure",
        }

    if status_code in (
        408,
        429,
        500,
        502,
        503,
        504,
    ):
        return {
            "action_result": "transient_failure",
            "action_status_code": status_code,
            "answer": (
                "The Library API is "
                "temporarily unavailable."
            ),
            "status": "action_transient_failure",
        }

    return {
        "action_result": "failed",
        "action_status_code": status_code,
        "answer": result.get(
            "message",
            "Reservation failed.",
        ),
        "status": "action_failed",
    }


def build_part_d_graph(
    checkpointer: SqliteSaver,
):
    """
    Build the Part D graph with SQLite persistence,
    exact-action human approval, and secret-safe
    runtime authentication.
    """

    builder = StateGraph(
        PartDState
    )

    catalog_subgraph = (
        build_catalog_subgraph()
    )

    builder.add_node(
        "router",
        router_node,
    )

    builder.add_node(
        "catalog",
        catalog_subgraph,
    )

    builder.add_node(
        "planner",
        planner_node,
    )

    builder.add_node(
        "approval",
        approval_node,
    )

    builder.add_node(
        "action_executor",
        secure_action_executor_node,
    )

    builder.add_node(
        "replan",
        replan_node,
    )

    builder.add_node(
        "retry",
        retry_node,
    )

    builder.add_node(
        "chitchat",
        chitchat_node,
    )

    builder.add_edge(
        START,
        "router",
    )

    builder.add_conditional_edges(
        "router",
        choose_route,
        {
            "catalog": "catalog",
            "action": "planner",
            "chitchat": "chitchat",
        },
    )

    builder.add_edge(
        "catalog",
        END,
    )

    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "approval": "approval",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "execute": "action_executor",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "action_executor",
        route_after_action,
        {
            "replan": "replan",
            "retry": "retry",
            "end": END,
        },
    )

    builder.add_edge(
        "replan",
        END,
    )

    builder.add_edge(
        "retry",
        "action_executor",
    )

    builder.add_edge(
        "chitchat",
        END,
    )

    return builder.compile(
        checkpointer=checkpointer
    )


def create_initial_state(
    message: str,
) -> PartDState:
    return {
        "user_message": message,
        "route": "",
        "answer": "",
        "status": "started",
        "plan": [],
        "book_id": None,
        "action_result": "not_run",
        "action_status_code": None,
        "retry_count": 0,
        "replan_count": 0,
        "approval_required": False,
        "approval_granted": None,
        "approval_message": "",
    }


def make_config(
    thread_id: str,
) -> RunnableConfig:
    """
    Create checkpoint-safe LangGraph configuration.

    Only thread identity is stored here.

    JWTs, API keys, and idempotency keys must never
    be placed in checkpointed LangGraph config.
    """

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def set_runtime_credentials(
    user_token: str,
    idempotency_key: str | None = None,
) -> None:
    """
    Set credentials in process memory for the current
    Python process.

    These values are not inserted into graph state or
    LangGraph checkpoint configuration.
    """

    if user_token:
        os.environ[
            RUNTIME_USER_TOKEN_ENV
        ] = user_token

    if idempotency_key:
        os.environ[
            RUNTIME_IDEMPOTENCY_KEY_ENV
        ] = idempotency_key
    else:
        os.environ.pop(
            RUNTIME_IDEMPOTENCY_KEY_ENV,
            None,
        )


def clear_runtime_credentials() -> None:
    """
    Remove runtime write credentials from this process.
    """

    os.environ.pop(
        RUNTIME_USER_TOKEN_ENV,
        None,
    )

    os.environ.pop(
        RUNTIME_IDEMPOTENCY_KEY_ENV,
        None,
    )


def print_state_summary(
    result,
) -> None:
    print()
    print("-" * 70)

    if "__interrupt__" in result:
        print("STATUS:  INTERRUPTED")
        print(
            "The graph is waiting for "
            "human approval."
        )

        for item in result["__interrupt__"]:
            print(
                f"INTERRUPT: {item.value}"
            )

        return

    print(
        f"ROUTE:    {result.get('route')}"
    )
    print(
        f"STATUS:   {result.get('status')}"
    )
    print(
        f"BOOK ID:  {result.get('book_id')}"
    )
    print(
        "APPROVED: "
        f"{result.get('approval_granted')}"
    )
    print(
        "RETRIES:  "
        f"{result.get('retry_count')}"
    )
    print(
        "REPLANS:  "
        f"{result.get('replan_count')}"
    )
    print(
        f"ANSWER:   {result.get('answer')}"
    )


def print_checkpoint_state(
    graph,
    config: RunnableConfig,
) -> None:
    snapshot = graph.get_state(
        config
    )

    print()
    print("CHECKPOINT STATE")
    print("-" * 70)
    print(
        f"NEXT:   {snapshot.next}"
    )
    print(
        "STATUS: "
        f"{snapshot.values.get('status')}"
    )
    print(
        "BOOK ID: "
        f"{snapshot.values.get('book_id')}"
    )

    configurable = config.get(
        "configurable",
        {},
    )

    print(
        "THREAD: "
        f"{configurable.get('thread_id')}"
    )

    print(
        "JWT IN STATE: "
        f"{'user_token' in snapshot.values}"
    )

    checkpoint_config = (
        snapshot.config.get(
            "configurable",
            {},
        )
    )

    print(
        "JWT IN CHECKPOINT CONFIG: "
        f"{'user_token' in checkpoint_config}"
    )


def print_state_history(
    graph,
    config: RunnableConfig,
) -> None:
    print()
    print("STATE HISTORY")
    print("-" * 70)

    history = list(
        graph.get_state_history(
            config
        )
    )

    print(
        f"CHECKPOINTS: {len(history)}"
    )

    for index, snapshot in enumerate(
        history,
        start=1,
    ):
        status = snapshot.values.get(
            "status",
            "unknown",
        )

        next_nodes = snapshot.next

        print(
            f"{index}. status={status}, "
            f"next={next_nodes}"
        )


def run_safe_persistence_demo(
    graph,
) -> None:
    """
    Create persistent state without a write.
    """

    thread_id = (
        "week7-part-d-safe-"
        + uuid.uuid4().hex[:8]
    )

    config = make_config(
        thread_id
    )

    print()
    print("=" * 70)
    print(
        "PART D SAFE SQLITE "
        "PERSISTENCE DEMO"
    )
    print("=" * 70)
    print(
        f"THREAD ID: {thread_id}"
    )

    result = graph.invoke(
        create_initial_state(
            "Hello, how are you?"
        ),
        config=config,
    )

    print_state_summary(
        result
    )

    print_checkpoint_state(
        graph,
        config,
    )

    print_state_history(
        graph,
        config,
    )


def run_approval_pause_demo(
    graph,
) -> tuple[str, RunnableConfig]:
    """
    Demonstrate that the write request pauses before
    execution.

    No runtime credentials are required merely to
    reach the approval interrupt.
    """

    thread_id = (
        "week7-part-d-approval-"
        + uuid.uuid4().hex[:8]
    )

    config = make_config(
        thread_id
    )

    print()
    print("=" * 70)
    print(
        "PART D HUMAN APPROVAL "
        "INTERRUPT DEMO"
    )
    print("=" * 70)
    print(
        f"THREAD ID: {thread_id}"
    )

    result = graph.invoke(
        create_initial_state(
            "Reserve book 15 for me."
        ),
        config=config,
    )

    print_state_summary(
        result
    )

    print_checkpoint_state(
        graph,
        config,
    )

    print()
    print(
        "The reservation tool has NOT "
        "executed."
    )
    print(
        "Resume requires an explicit "
        "Command(resume=...) decision."
    )

    return thread_id, config


def resume_with_decision(
    graph,
    config: RunnableConfig,
    approved: bool,
):
    """
    Resume an interrupted thread.

    The graph config contains only checkpoint-safe
    information. Authentication is read independently
    by the secure write node from process memory.
    """

    decision = {
        "approved": approved
    }

    return graph.invoke(
        Command(
            resume=decision
        ),
        config=config,
    )


def open_checkpointer():
    """
    Open persistent SQLite checkpoint storage.
    """

    connection = sqlite3.connect(
        CHECKPOINT_DB,
        check_same_thread=False,
    )

    return (
        connection,
        SqliteSaver(connection),
    )


def main() -> None:
    print("=" * 70)
    print(
        "WEEK 7 - PART D SQLITE "
        "CHECKPOINT + HITL"
    )
    print("=" * 70)
    print(
        f"CHECKPOINT DB: {CHECKPOINT_DB}"
    )

    connection, checkpointer = (
        open_checkpointer()
    )

    try:
        graph = build_part_d_graph(
            checkpointer
        )

        run_safe_persistence_demo(
            graph
        )

        run_approval_pause_demo(
            graph
        )

        print()
        print("=" * 70)
        print("PART D DEMO COMPLETE")
        print("=" * 70)
        print(
            "SQLite persistence: enabled"
        )
        print(
            "Human approval interrupt: enabled"
        )
        print(
            "JWT checkpointed: no"
        )
        print(
            "Runtime authentication: "
            "process environment only"
        )
        print(
            "No reservation write was "
            "performed by this safe demo."
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()