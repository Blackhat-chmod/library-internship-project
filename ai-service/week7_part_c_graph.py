import time
from typing import Literal, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from rag_pipeline import retrieve
from reservation_tool_demo import reserve_book
from week7_router_demo import route_message


ActionResult = Literal[
    "not_run",
    "success",
    "conflict",
    "auth_failure",
    "transient_failure",
    "failed",
]


class WorkflowState(TypedDict):
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


class CatalogSubgraphState(TypedDict):
    user_message: str
    answer: str
    status: str


def router_node(
    state: WorkflowState,
) -> dict:
    decision = route_message(
        state["user_message"]
    )

    return {
        "route": decision.route,
        "status": "routed",
    }


def choose_route(
    state: WorkflowState,
) -> str:
    return state["route"]


def catalog_retrieval_node(
    state: CatalogSubgraphState,
) -> dict:
    """
    Reuse the Week 6 RAG retrieval pipeline
    inside a dedicated catalog subgraph.
    """

    documents, metadatas = retrieve(
        state["user_message"],
        k=3,
    )

    if not documents:
        return {
            "answer": (
                "I could not find relevant "
                "library catalog information."
            ),
            "status": "catalog_no_results",
        }

    results = []

    for document, metadata in zip(
        documents,
        metadatas,
    ):
        title = metadata.get(
            "title",
            "Unknown title",
        )

        author = metadata.get(
            "author",
            "Unknown author",
        )

        book_id = metadata.get(
            "book_id",
            "Unknown",
        )

        results.append(
            (
                f"Book ID {book_id}: "
                f"{title} by {author}\n"
                f"{document}"
            )
        )

    return {
        "answer": "\n\n".join(results),
        "status": "catalog_complete",
    }


def build_catalog_subgraph():
    """
    Compile the Week 6 catalog/RAG branch as
    a reusable LangGraph subgraph.
    """

    builder = StateGraph(
        CatalogSubgraphState
    )

    builder.add_node(
        "week6_rag",
        catalog_retrieval_node,
    )

    builder.add_edge(
        START,
        "week6_rag",
    )

    builder.add_edge(
        "week6_rag",
        END,
    )

    return builder.compile()


def extract_book_id(
    message: str,
) -> int | None:
    """
    Extract a positive integer book ID from
    a simple reservation request.
    """

    for token in message.split():
        cleaned = token.strip(
            ".,!?()[]{}"
        )

        if cleaned.isdigit():
            book_id = int(cleaned)

            if book_id > 0:
                return book_id

    return None


def planner_node(
    state: WorkflowState,
) -> dict:
    """
    Write an explicit ordered list of action
    steps into graph state before execution.
    """

    book_id = extract_book_id(
        state["user_message"]
    )

    if book_id is None:
        return {
            "plan": [
                (
                    "Identify that the reservation "
                    "request is missing a valid "
                    "positive book ID."
                ),
                (
                    "Ask the user to provide the "
                    "book ID before any write "
                    "operation is attempted."
                ),
            ],
            "book_id": None,
            "answer": (
                "Please provide the book ID "
                "you want to reserve."
            ),
            "status": "plan_needs_book_id",
        }

    return {
        "plan": [
            (
                f"Identify book {book_id} as the "
                "requested reservation target."
            ),
            (
                "Use the authenticated reservation "
                "tool without storing the JWT in "
                "graph state."
            ),
            (
                "Inspect the reservation result for "
                "success, conflict, authentication "
                "failure, or a transient failure."
            ),
            (
                "Finish on success, re-plan after "
                "a conflict, or retry a transient "
                "failure at most twice."
            ),
        ],
        "book_id": book_id,
        "action_result": "not_run",
        "action_status_code": None,
        "status": "planned",
    }


def route_after_planner(
    state: WorkflowState,
) -> str:
    if state["book_id"] is None:
        return "end"

    return "execute"


def action_executor_node(
    state: WorkflowState,
    config: RunnableConfig,
) -> dict:
    """
    Execute the secure reservation tool.

    Authentication stays in runtime config.
    JWT is never copied into graph state.
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

    result = reserve_book.invoke(
        {
            "book_id": book_id,
        },
        config=config,
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
                "Authentication or "
                "authorization failed. "
                "The action was stopped."
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


def route_after_action(
    state: WorkflowState,
) -> str:
    result = state["action_result"]

    if result == "conflict":
        return "replan"

    if result == "transient_failure":
        if state["retry_count"] < 2:
            return "retry"

        return "end"

    return "end"


def replan_node(
    state: WorkflowState,
) -> dict:
    """
    Re-plan safely after HTTP 409.

    Search the Week 6 catalog for another
    available candidate and offer it.

    The alternative is not automatically
    reserved because that would perform
    another write without user approval.
    """

    count = state["replan_count"] + 1
    requested_book_id = state["book_id"]

    documents, metadatas = retrieve(
        "available library books",
        k=5,
    )

    for document, metadata in zip(
        documents,
        metadatas,
    ):
        candidate_id = metadata.get(
            "book_id"
        )

        title = metadata.get(
            "title",
            "Unknown title",
        )

        author = metadata.get(
            "author",
            "Unknown author",
        )

        if candidate_id == requested_book_id:
            continue

        normalized_document = (
            document.lower()
        )

        explicitly_available = (
            "available: true"
            in normalized_document
            or
            "is available: true"
            in normalized_document
        )

        if explicitly_available:
            return {
                "replan_count": count,
                "plan": [
                    (
                        f"Record that book "
                        f"{requested_book_id} "
                        "returned a reservation "
                        "conflict."
                    ),
                    (
                        "Search the library catalog "
                        "for another explicitly "
                        "available book."
                    ),
                    (
                        f"Select Book {candidate_id}, "
                        f"{title}, as an available "
                        "alternative."
                    ),
                    (
                        "Offer the alternative to "
                        "the user without reserving "
                        "it automatically."
                    ),
                ],
                "answer": (
                    f"Book {requested_book_id} "
                    "cannot currently be reserved. "
                    "I searched the catalog and "
                    "found another available "
                    "option: "
                    f"Book {candidate_id}, "
                    f"{title} by {author}. "
                    "I have not reserved the "
                    "alternative automatically."
                ),
                "status": (
                    "replanned_with_alternative"
                ),
            }

    return {
        "replan_count": count,
        "plan": [
            (
                f"Record that book "
                f"{requested_book_id} returned "
                "a reservation conflict."
            ),
            (
                "Search the library catalog for "
                "another explicitly available "
                "book."
            ),
            (
                "Report that no suitable available "
                "alternative was found."
            ),
            (
                "Do not attempt another write "
                "without a new valid target."
            ),
        ],
        "answer": (
            f"Book {requested_book_id} cannot "
            "currently be reserved. I searched "
            "the catalog, but I could not find "
            "another available book to offer."
        ),
        "status": (
            "replanned_no_alternative"
        ),
    }


def retry_node(
    state: WorkflowState,
) -> dict:
    """
    Retry transient failures at most twice
    with a small increasing backoff.
    """

    count = state["retry_count"] + 1
    backoff_seconds = count

    print(
        f"Transient failure: retry "
        f"{count}/2 after "
        f"{backoff_seconds}s backoff."
    )

    time.sleep(
        backoff_seconds
    )

    return {
        "retry_count": count,
        "status": "retrying",
    }


def chitchat_node(
    state: WorkflowState,
) -> dict:
    message = state[
        "user_message"
    ].lower()

    if "hello" in message:
        answer = (
            "Hello! How can I help you today?"
        )
    elif "thank" in message:
        answer = "You're welcome!"
    else:
        answer = (
            "I'm here to help with the "
            "library system."
        )

    return {
        "answer": answer,
        "status": "chitchat_complete",
    }


def build_graph():
    builder = StateGraph(
        WorkflowState
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
        "action_executor",
        action_executor_node,
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

    return builder.compile()


def run_test(
    graph,
    message: str,
    config: RunnableConfig | None = None,
) -> None:
    initial_state: WorkflowState = {
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
    }

    result = graph.invoke(
        initial_state,
        config=config or {},
    )

    print()
    print("-" * 70)
    print(f"USER:    {message}")
    print(f"ROUTE:   {result['route']}")
    print(f"STATUS:  {result['status']}")

    if result["plan"]:
        print("PLAN:")

        for index, step in enumerate(
            result["plan"],
            start=1,
        ):
            print(
                f"  {index}. {step}"
            )

    print(
        f"BOOK ID: {result['book_id']}"
    )

    print(
        "HTTP:    "
        f"{result['action_status_code']}"
    )

    print(
        f"RETRIES: {result['retry_count']}"
    )

    print(
        f"REPLANS: {result['replan_count']}"
    )

    print(
        f"ANSWER:  {result['answer']}"
    )


def main() -> None:
    print("=" * 70)
    print(
        "WEEK 7 - PART C SECURE ACTION GRAPH"
    )
    print("=" * 70)

    graph = build_graph()

    print()
    print(
        "Safe tests only: no JWT is supplied "
        "by this demo."
    )

    run_test(
        graph,
        "Tell me about Advanced C#.",
    )

    run_test(
        graph,
        "Please make a reservation.",
    )

    run_test(
        graph,
        "Hello, how are you?",
    )


if __name__ == "__main__":
    main()