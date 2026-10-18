from typing import Annotated, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.tools import tool

from langgraph.graph import (
    END,
    START,
    StateGraph,
)
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


MAX_STEPS = 6


class AgentState(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]
    step_count: int
    status: str


@tool
def search_catalog(query: str) -> str:
    """
    Search the library catalog for books matching
    a title, genre, or search query.
    """

    catalog = [
        {
            "title": "Dune",
            "genre": "Science Fiction",
            "available": True,
        },
        {
            "title": "Neuromancer",
            "genre": "Science Fiction",
            "available": False,
        },
        {
            "title": "The Hobbit",
            "genre": "Fantasy",
            "available": True,
        },
    ]

    query_lower = query.lower()

    matches = [
        book
        for book in catalog
        if (
            query_lower in book["title"].lower()
            or query_lower in book["genre"].lower()
        )
    ]

    if not matches:
        return "No matching books were found."

    return "\n".join(
        (
            f"{book['title']} | "
            f"{book['genre']} | "
            f"available={book['available']}"
        )
        for book in matches
    )


@tool
def check_availability(title: str) -> str:
    """
    Check whether a specific library book is
    currently available.
    """

    availability = {
        "dune": True,
        "neuromancer": False,
        "the hobbit": True,
    }

    result = availability.get(
        title.lower()
    )

    if result is None:
        return (
            f"Availability information for "
            f"'{title}' was not found."
        )

    return (
        f"{title} is "
        f"{'available' if result else 'not available'}."
    )


@tool
def failing_library_tool(query: str) -> str:
    """
    Demonstration tool that always fails.

    This tool is used only for the Part A
    tool-failure experiment.
    """

    raise RuntimeError(
        "Simulated library service failure."
    )


TOOLS = [
    search_catalog,
    check_availability,
    failing_library_tool,
]


def agent_node(
    state: AgentState,
) -> dict:
    """
    Think about the current state and decide whether
    to call a tool or produce a final answer.
    """

    step = state["step_count"] + 1
    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(
        last_message,
        HumanMessage,
    ):
        question = str(
            last_message.content
        ).lower()

        if (
            "failing tool" in question
            or "failure test" in question
        ):
            tool_call = {
                "name": "failing_library_tool",
                "args": {
                    "query": str(
                        last_message.content
                    ),
                },
                "id": "failing-tool-1",
                "type": "tool_call",
            }

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I should test the failing "
                            "library tool."
                        ),
                        tool_calls=[
                            tool_call
                        ],
                    )
                ],
                "step_count": step,
                "status": "tool_requested",
            }

        if (
            "science fiction" in question
            or "science-fiction" in question
            or "sci-fi" in question
            or "scifi" in question
        ):
            tool_call = {
                "name": "search_catalog",
                "args": {
                    "query": "Science Fiction",
                },
                "id": "catalog-search-1",
                "type": "tool_call",
            }

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I should search the catalog "
                            "for science fiction books."
                        ),
                        tool_calls=[
                            tool_call
                        ],
                    )
                ],
                "step_count": step,
                "status": "tool_requested",
            }

        return {
            "messages": [
                AIMessage(
                    content=(
                        "I can help search the library "
                        "catalog and check book "
                        "availability."
                    )
                )
            ],
            "step_count": step,
            "status": "completed",
        }

    if isinstance(
        last_message,
        ToolMessage,
    ):
        if (
            last_message.name
            == "failing_library_tool"
        ):
            if (
                "error" in str(
                    last_message.content
                ).lower()
                or "failed" in str(
                    last_message.content
                ).lower()
                or "runtimeerror" in str(
                    last_message.content
                ).lower()
            ):
                return {
                    "messages": [
                        AIMessage(
                            content=(
                                "The library tool failed, "
                                "so I could not complete "
                                "that operation safely. "
                                "Please try again later."
                            )
                        )
                    ],
                    "step_count": step,
                    "status":
                        "completed_with_tool_error",
                }

        if (
            last_message.name
            == "search_catalog"
        ):
            tool_text = str(
                last_message.content
            )

            available_titles = []

            for line in tool_text.splitlines():
                if "available=True" in line:
                    title = (
                        line
                        .split("|")[0]
                        .strip()
                    )

                    available_titles.append(
                        title
                    )

            if available_titles:
                title = available_titles[0]

                tool_call = {
                    "name": "check_availability",
                    "args": {
                        "title": title,
                    },
                    "id": "availability-check-1",
                    "type": "tool_call",
                }

                return {
                    "messages": [
                        AIMessage(
                            content=(
                                f"I found {title}. "
                                "I should confirm its "
                                "current availability."
                            ),
                            tool_calls=[
                                tool_call
                            ],
                        )
                    ],
                    "step_count": step,
                    "status": "tool_requested",
                }

            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I found science fiction "
                            "books, but none are "
                            "currently available."
                        )
                    )
                ],
                "step_count": step,
                "status": "completed",
            }

        if (
            last_message.name
            == "check_availability"
        ):
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "I found an available "
                            "science fiction book: "
                            f"{last_message.content}"
                        )
                    )
                ],
                "step_count": step,
                "status": "completed",
            }

    return {
        "messages": [
            AIMessage(
                content=(
                    "I could not determine another "
                    "useful action."
                )
            )
        ],
        "step_count": step,
        "status": "completed",
    }


def give_up_node(
    state: AgentState,
) -> dict:
    """
    End safely when the hard step limit is reached.
    """

    return {
        "messages": [
            AIMessage(
                content=(
                    "I could not complete the request "
                    "within the allowed number of "
                    "steps."
                )
            )
        ],
        "step_count": state["step_count"],
        "status": "gave_up",
    }


def route_after_agent(
    state: AgentState,
) -> str:
    """
    Route to a tool, give-up node, or END.
    """

    if (
        state["step_count"]
        >= MAX_STEPS
    ):
        return "give_up"

    last_message = state["messages"][-1]

    if (
        isinstance(
            last_message,
            AIMessage,
        )
        and last_message.tool_calls
    ):
        return "tools"

    return "end"


def route_after_tools(
    state: AgentState,
) -> str:
    """
    Return observations to the agent unless the
    hard step limit has been reached.
    """

    if (
        state["step_count"]
        >= MAX_STEPS
    ):
        return "give_up"

    return "agent"


def build_graph():
    """
    Build and compile the explicit LangGraph
    think-act-observe loop.
    """

    builder = StateGraph(
        AgentState
    )

    builder.add_node(
        "agent",
        agent_node,
    )

    tool_node = ToolNode(
        TOOLS,
        handle_tool_errors=True,
    )

    builder.add_node(
        "tools",
        tool_node,
    )

    builder.add_node(
        "give_up",
        give_up_node,
    )

    builder.add_edge(
        START,
        "agent",
    )

    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "give_up": "give_up",
            "end": END,
        },
    )

    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "agent": "agent",
            "give_up": "give_up",
        },
    )

    builder.add_edge(
        "give_up",
        END,
    )

    return builder.compile()


def print_result(
    result: AgentState,
) -> None:
    """
    Print the complete execution using the required
    thought/tool-call/observation/answer labels.
    """

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        f"Status: {result['status']}"
    )

    print(
        f"Steps: {result['step_count']}"
    )

    print()
    print("=" * 70)
    print("AGENT TRACE")
    print("=" * 70)

    messages = result["messages"]

    for index, message in enumerate(messages):
        if isinstance(
            message,
            HumanMessage,
        ):
            print()
            print(
                f"USER: {message.content}"
            )
            continue

        if isinstance(
            message,
            ToolMessage,
        ):
            print()
            print(
                "OBSERVATION:"
            )
            print(
                message.content
            )
            continue

        if isinstance(
            message,
            AIMessage,
        ):
            if message.tool_calls:
                if message.content:
                    print()
                    print(
                        "THOUGHT:"
                    )
                    print(
                        message.content
                    )

                for call in message.tool_calls:
                    print()
                    print(
                        "TOOL-CALL:"
                    )
                    print(
                        f"Tool: {call['name']}"
                    )
                    print(
                        f"Arguments: {call['args']}"
                    )

                continue

            print()
            print(
                "ANSWER:"
            )
            print(
                message.content
            )


def run_scenario(
    question: str,
) -> None:
    """
    Run one Part A demonstration.
    """

    graph = build_graph()

    initial_state: AgentState = {
        "messages": [
            HumanMessage(
                content=question
            )
        ],
        "step_count": 0,
        "status": "started",
    }

    result = graph.invoke(
        initial_state,
        config={
            "recursion_limit": 20,
        },
    )

    print_result(
        result
    )


def main() -> None:
    print()
    print("=" * 70)
    print("WEEK 7 - PART A LANGGRAPH AGENT")
    print("=" * 70)

    print()
    print(
        f"MAX_STEPS = {MAX_STEPS}"
    )

    print()
    print(
        "Choose a Part A scenario:"
    )

    print(
        "1 - Normal agent loop"
    )

    print(
        "2 - Always-failing tool challenge"
    )

    choice = input(
        "Enter 1 or 2: "
    ).strip()

    if choice == "2":
        run_scenario(
            "Run the failing tool "
            "for this failure test."
        )

    else:
        run_scenario(
            "Find a science fiction book "
            "and tell me if it is available."
        )


if __name__ == "__main__":
    main()