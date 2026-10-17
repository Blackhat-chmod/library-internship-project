import os
from typing import Any

from langsmith import Client, traceable


PROJECT_NAME = os.getenv(
    "LANGSMITH_PROJECT",
    "library-week7",
)


@traceable(
    name="search_catalog",
    run_type="tool",
)
def search_catalog(query: str) -> dict[str, Any]:
    """
    Deterministic tool simulation used only for
    Week 7 tracing evidence.
    """
    return {
        "query": query,
        "book_id": 16,
        "title": "Week 7 Alternative Book",
        "available": True,
    }


@traceable(
    name="approval_check",
    run_type="tool",
)
def approval_check(
    approved: bool,
) -> dict[str, Any]:
    return {
        "approved": approved,
    }


@traceable(
    name="reserve_book",
    run_type="tool",
)
def reserve_book(
    book_id: int,
    approved: bool,
) -> dict[str, Any]:
    if not approved:
        return {
            "status": "blocked",
            "reason": "approval_required",
        }

    return {
        "status": "reserved",
        "book_id": book_id,
    }


@traceable(
    name="week7-passing-agent-run",
    run_type="chain",
)
def passing_agent_run() -> dict[str, Any]:
    catalog = search_catalog(
        "Find an available library book"
    )

    approval = approval_check(
        True
    )

    reservation = reserve_book(
        book_id=catalog["book_id"],
        approved=approval["approved"],
    )

    if reservation["status"] != "reserved":
        raise RuntimeError(
            "Expected reservation to succeed."
        )

    return {
        "evaluation": "PASS",
        "scenario":
            "approved reservation",
        "book_id":
            reservation["book_id"],
        "trajectory": [
            "search_catalog",
            "approval_check",
            "reserve_book",
            "final",
        ],
    }


@traceable(
    name="week7-failing-agent-run",
    run_type="chain",
)
def failing_agent_run() -> dict[str, Any]:
    catalog = search_catalog(
        "Reserve an available library book"
    )

    approval = approval_check(
        False
    )

    reservation = reserve_book(
        book_id=catalog["book_id"],
        approved=approval["approved"],
    )

    if reservation["status"] != "reserved":
        raise RuntimeError(
            "Intentional Week 7 failing trace: "
            "reservation was rejected because "
            "human approval was false."
        )

    return {
        "evaluation": "PASS",
        "book_id":
            reservation["book_id"],
    }


def verify_configuration() -> None:
    if not os.getenv(
        "LANGSMITH_API_KEY"
    ):
        raise RuntimeError(
            "LANGSMITH_API_KEY is not set."
        )

    if (
        os.getenv(
            "LANGSMITH_TRACING",
            "",
        ).lower()
        != "true"
    ):
        raise RuntimeError(
            "LANGSMITH_TRACING must be true."
        )


def main() -> None:
    verify_configuration()

    print(
        f"LangSmith project: "
        f"{PROJECT_NAME}"
    )

    print()
    print(
        "Creating PASSING trace..."
    )

    passing_result = (
        passing_agent_run()
    )

    print(
        "PASSING TRACE RESULT:",
        passing_result["evaluation"],
    )

    print()
    print(
        "Creating intentional "
        "FAILING trace..."
    )

    try:
        failing_agent_run()

    except RuntimeError as exc:
        print(
            "FAILING TRACE RESULT: "
            "EXPECTED FAILURE"
        )
        print(
            "Reason:",
            str(exc),
        )

    client = Client()
    client.flush()

    print()
    print(
        "LangSmith traces flushed."
    )
    print(
        "Open project:",
        PROJECT_NAME,
    )


if __name__ == "__main__":
    main()