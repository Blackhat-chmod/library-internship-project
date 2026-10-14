import operator
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


MAX_STEPS = 6


class AgentState(TypedDict):
    messages: Annotated[
        list[BaseMessage],
        operator.add,
    ]
    step_count: int
    status: str


@tool
def search_catalog(query: str) -> str:
    """
    Search the library catalog for books matching a query.
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
    Check whether a library book is currently available.
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

    It is used to verify that a tool failure becomes
    an observation instead of crashing the graph.
    """

    raise RuntimeError(
        "Simulated library service failure."
    )


TOOLS = {
    "search_catalog": search_catalog,
    "check_availability": check_availability,
    "failing_library_tool": failing_library_tool,
}


def agent_node(
    state: AgentState,
) -> dict:
    """
    Decide the next action in the explicit agent loop.
    """

    step = state["step_count"] + 1
    messages = state["messages"]
    last_message = messages[-1]

    # First decision based on the user's request.
    if isinstance(
        last_message,
        HumanMessage,
    ):
        question = str(
            last_message.content
        ).lower()

        # Dedicated failing-tool challenge.
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
                        content="",
                        tool_calls=[
                            tool_call
                        ],
                    )
                ],
                "step_count": step,
                "status": "tool_requested",
            }

        # Normal science-fiction scenario.
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
                        content="",
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

    # Process observations returned by tools.
    if isinstance(
        last_message,
        ToolMessage,
    ):
        if (
            last_message.name
            == "failing_library_tool"
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
                "status": "completed_with_tool_error",
            }

        if (
            last_message.name
            == "search_catalog"
        ):
            tool_text = str(
                last_message.content
            )

            available_titles = []

            for line in (
                tool_text.splitlines()
            ):
                if (
                    "available=True"
                    in line
                ):
                    title = (
                        line
                        .split("|")[0]
                        .strip()
                    )

                    available_titles.append(
                        title
                    )

            if available_titles:
                title = (
                    available_titles[0]
                )

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
                            content="",
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
                            "I found science-fiction "
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
                            "science-fiction book: "
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
                    "I could not determine "
                    "another useful action."
                )
            )
        ],
        "step_count": step,
        "status": "completed",
    }


def tool_node(
    state: AgentState,
) -> dict:
    """
    Execute tool calls requested by the agent.

    Tool exceptions are converted into ToolMessages so
    the graph can observe and respond to the failure.
    """

    last_message = (
        state["messages"][-1]
    )

    if not isinstance(
        last_message,
        AIMessage,
    ):
        return {
            "messages": [],
            "step_count": state["step_count"],
            "status": "completed",
        }

    results = []

    for tool_call in (
        last_message.tool_calls
    ):
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]

        selected_tool = (
            TOOLS.get(tool_name)
        )

        if selected_tool is None:
            results.append(
                ToolMessage(
                    content=(
                        f"Unknown tool: {tool_name}"
                    ),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

            continue

        try:
            result = (
                selected_tool.invoke(
                    tool_args
                )
            )

            results.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

        except Exception as error:
            results.append(
                ToolMessage(
                    content=(
                        "Tool execution failed: "
                        f"{error}"
                    ),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            )

    return {
        "messages": results,
        "step_count": state["step_count"],
        "status": "tool_completed",
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
    Route after every agent decision.
    """

    if (
        state["step_count"]
        >= MAX_STEPS
    ):
        return "give_up"

    last_message = (
        state["messages"][-1]
    )

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
    Return tool observations to the agent unless
    the hard step limit has been reached.
    """

    if (
        state["step_count"]
        >= MAX_STEPS
    ):
        return "give_up"

    return "agent"


def build_graph():
    """
    Build and compile the explicit LangGraph loop.
    """

    builder = StateGraph(
        AgentState
    )

    builder.add_node(
        "agent",
        agent_node,
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
    Print the final state and complete message trace.
    """

    print(
        "\n=== FINAL RESULT ==="
    )

    print(
        f"Status: {result['status']}"
    )

    print(
        f"Steps: {result['step_count']}"
    )

    print(
        "\n=== MESSAGE TRACE ==="
    )

    for message in (
        result["messages"]
    ):
        print(
            f"{type(message).__name__}: "
            f"{message.content}"
        )

        if (
            isinstance(
                message,
                AIMessage,
            )
            and message.tool_calls
        ):
            print(
                "Tool calls:",
                message.tool_calls,
            )


def run_scenario(
    question: str,
) -> None:
    """
    Run one demonstration scenario.
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


if __name__ == "__main__":
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
            "Find me a science-fiction "
            "book that is available."
        )