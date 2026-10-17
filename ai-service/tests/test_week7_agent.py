import os
import sys
from pathlib import Path

import pytest


AI_SERVICE_DIR = Path(__file__).resolve().parents[1]

if str(AI_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICE_DIR))


from week7_part_c_graph import (
    chitchat_node,
    extract_book_id,
    planner_node,
    retry_node,
    route_after_action,
    route_after_planner as part_c_route_after_planner,
)

from week7_part_d_hitl import (
    build_runtime_tool_config,
    clear_runtime_credentials,
    create_initial_state,
    make_config,
    normalize_approval,
    route_after_approval,
    route_after_planner as part_d_route_after_planner,
    set_runtime_credentials,
)

from week7_red_team import (
    MAX_AGENT_STEPS,
    MAX_TOOL_CALLS,
    SafeBookId,
    argument_is_rejected,
    test_argument_abuse as run_argument_abuse_attack,
    test_cross_user_access as run_cross_user_attack,
    test_direct_override as run_direct_override_attack,
    test_indirect_injection as run_indirect_injection_attack,
    test_resource_exhaustion as run_resource_exhaustion_attack,
    test_secret_extraction as run_secret_extraction_attack,
    test_thread_hijack as run_thread_hijack_attack,
    thread_owner_can_access,
)


def make_action_state(
    action_result: str,
    retry_count: int = 0,
) -> dict:
    return {
        "user_message": "reserve book 15",
        "route": "action",
        "answer": "",
        "status": "started",
        "plan": [],
        "book_id": 15,
        "action_result": action_result,
        "action_status_code": None,
        "retry_count": retry_count,
        "replan_count": 0,
    }


def test_extract_book_id_returns_positive_id():
    assert extract_book_id(
        "Please reserve book 15."
    ) == 15


def test_extract_book_id_rejects_zero():
    assert extract_book_id(
        "Please reserve book 0."
    ) is None


def test_extract_book_id_returns_none_when_missing():
    assert extract_book_id(
        "Please reserve this book."
    ) is None


def test_planner_missing_book_id_does_not_write():
    state = make_action_state(
        "not_run"
    )
    state["user_message"] = (
        "Please reserve a book for me."
    )

    result = planner_node(state)

    assert result["book_id"] is None
    assert result["status"] == (
        "plan_needs_book_id"
    )
    assert "provide the book ID" in (
        result["answer"]
    )


def test_part_c_planner_routes_valid_id_to_execute():
    state = make_action_state(
        "not_run"
    )

    assert (
        part_c_route_after_planner(state)
        == "execute"
    )


def test_part_c_planner_routes_missing_id_to_end():
    state = make_action_state(
        "not_run"
    )
    state["book_id"] = None

    assert (
        part_c_route_after_planner(state)
        == "end"
    )


def test_conflict_routes_to_replan():
    state = make_action_state(
        "conflict"
    )

    assert route_after_action(
        state
    ) == "replan"


def test_transient_failure_routes_to_retry_below_limit():
    state = make_action_state(
        "transient_failure",
        retry_count=1,
    )

    assert route_after_action(
        state
    ) == "retry"


def test_transient_failure_stops_at_retry_limit():
    state = make_action_state(
        "transient_failure",
        retry_count=2,
    )

    assert route_after_action(
        state
    ) == "end"


def test_retry_node_increments_retry_count(
    monkeypatch,
):
    state = make_action_state(
        "transient_failure",
        retry_count=0,
    )

    monkeypatch.setattr(
        "week7_part_c_graph.time.sleep",
        lambda _: None,
    )

    result = retry_node(state)

    assert result["retry_count"] == 1
    assert result["status"] == "retrying"


def test_chitchat_hello_response():
    state = make_action_state(
        "not_run"
    )
    state["user_message"] = "Hello"

    result = chitchat_node(state)

    assert result["status"] == (
        "chitchat_complete"
    )
    assert "Hello" in result["answer"]


def test_normalize_approval_accepts_supported_values():
    assert normalize_approval(True) is True
    assert normalize_approval("yes") is True
    assert normalize_approval(
        {"approved": True}
    ) is True


def test_normalize_approval_rejects_denial_values():
    assert normalize_approval(False) is False
    assert normalize_approval("no") is False
    assert normalize_approval(
        {"approved": False}
    ) is False


def test_part_d_routes_write_through_approval():
    state = create_initial_state(
        "reserve book 15"
    )
    state["book_id"] = 15

    assert (
        part_d_route_after_planner(state)
        == "approval"
    )


def test_rejected_approval_routes_to_end():
    state = create_initial_state(
        "reserve book 15"
    )
    state["book_id"] = 15
    state["approval_granted"] = False

    assert route_after_approval(
        state
    ) == "end"


def test_checkpoint_config_contains_only_thread_id():
    config = make_config(
        "week7-test-thread"
    )

    assert config == {
        "configurable": {
            "thread_id": "week7-test-thread"
        }
    }

    serialized = str(config).lower()

    assert "token" not in serialized
    assert "api_key" not in serialized
    assert "idempotency" not in serialized


def test_runtime_credentials_are_ephemeral(
    monkeypatch,
):
    monkeypatch.delenv(
        "WEEK7_USER_TOKEN",
        raising=False,
    )
    monkeypatch.delenv(
        "WEEK7_IDEMPOTENCY_KEY",
        raising=False,
    )

    set_runtime_credentials(
        "test-user-token",
        "test-idempotency-key",
    )

    config = build_runtime_tool_config()

    assert (
        config["configurable"]["user_token"]
        == "test-user-token"
    )
    assert (
        config["configurable"][
            "idempotency_key"
        ]
        == "test-idempotency-key"
    )

    clear_runtime_credentials()

    assert (
        os.environ.get("WEEK7_USER_TOKEN")
        is None
    )
    assert (
        os.environ.get(
            "WEEK7_IDEMPOTENCY_KEY"
        )
        is None
    )


def test_security_controls_block_all_seven_attacks():
    attacks = [
        run_indirect_injection_attack,
        run_direct_override_attack,
        run_cross_user_attack,
        run_secret_extraction_attack,
        run_argument_abuse_attack,
        run_resource_exhaustion_attack,
        run_thread_hijack_attack,
    ]

    results = [
        attack()
        for attack in attacks
    ]

    assert len(results) == 7
    assert all(
        result.blocked
        for result in results
    )


def test_book_id_schema_and_argument_guard():
    valid = SafeBookId(
        book_id=15
    )

    assert valid.book_id == 15

    assert argument_is_rejected(-1)
    assert argument_is_rejected(0)
    assert argument_is_rejected(
        999999999
    )
    assert argument_is_rejected(
        "4; DROP TABLE"
    )


def test_thread_ownership_prevents_hijacking():
    assert thread_owner_can_access(
        "user-a",
        "user-a",
    ) is True

    assert thread_owner_can_access(
        "user-b",
        "user-a",
    ) is False


def test_agent_resource_limits_are_bounded():
    assert MAX_AGENT_STEPS == 6
    assert MAX_TOOL_CALLS == 4
    assert MAX_TOOL_CALLS < MAX_AGENT_STEPS