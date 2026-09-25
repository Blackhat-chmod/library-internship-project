import os
import warnings

import requests
import urllib3
from dotenv import load_dotenv

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI


load_dotenv()


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

MODEL_NAME = "openrouter/free"

BOOK_API_BASE_URL = (
    "https://localhost:7272/api/Books"
)


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

warnings.filterwarnings(
    "ignore",
    category=urllib3.exceptions.InsecureRequestWarning
)


@tool
def check_book_availability(
    book_id: int
) -> str:
    """
    Check whether a specific library book is
    currently available to borrow.

    Use this tool ONLY when the user asks about
    current availability, borrowing status,
    whether a book is available, or whether a
    book is currently borrowed.

    Do NOT use this tool for genre, author,
    title, summary, category, recommendation,
    or general information questions.
    """

    url = (
        f"{BOOK_API_BASE_URL}/"
        f"{book_id}/availability"
    )

    try:
        response = requests.get(
            url,
            timeout=10,
            verify=False
        )

        if response.status_code == 404:
            return (
                f"Book {book_id} was not found."
            )

        if response.status_code != 200:
            return (
                "Could not check book availability "
                "right now."
            )

        data = response.json()

        title = data.get(
            "title",
            f"Book {book_id}"
        )

        is_available = data.get(
            "isAvailable",
            False
        )

        if is_available:
            return (
                f"{title} is currently available "
                "to borrow."
            )

        return (
            f"{title} is currently borrowed "
            "and is not available."
        )

    except requests.RequestException as error:
        return (
            "Could not reach the Library API. "
            f"Error: {error}"
        )


def create_model():
    return ChatOpenAI(
        model=MODEL_NAME,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0
    )


def main():
    if not OPENROUTER_API_KEY:
        print(
            "OPENROUTER_API_KEY is missing."
        )
        return

    model = create_model()

    model_with_tools = model.bind_tools(
        [
            check_book_availability
        ]
    )

    system_message = SystemMessage(
        content="""
You are a library assistant.

You have exactly one tool:
check_book_availability.

STRICT TOOL RULES:

Call check_book_availability ONLY when the user
is asking about:

- whether a book is available
- whether a book can currently be borrowed
- whether a book is currently borrowed
- the current availability status of a book

DO NOT call the availability tool when the user
asks about:

- genre
- category
- author
- title
- description
- summary
- recommendations
- general book information

If a question does not require current
availability information, answer normally
without calling the tool.

Examples:

User:
"Is book 5 available?"
Action:
CALL check_book_availability.

User:
"Can I borrow book 5 right now?"
Action:
CALL check_book_availability.

User:
"What genre is book 5?"
Action:
DO NOT call the tool.

User:
"Who wrote book 5?"
Action:
DO NOT call the tool.
"""
    )

    print()
    print("=" * 70)
    print("TEST 1 - SHOULD CALL TOOL")
    print("=" * 70)

    availability_question = (
        "Is book 5 available right now?"
    )

    print()
    print("Question:")
    print(availability_question)

    messages = [
        system_message,
        HumanMessage(
            content=availability_question
        )
    ]

    response = model_with_tools.invoke(
        messages
    )

    if response.tool_calls:
        print()
        print("Tool call detected.")

        messages.append(
            response
        )

        for call in response.tool_calls:
            print()
            print(
                "Tool name:",
                call["name"]
            )

            print(
                "Tool arguments:",
                call["args"]
            )

            result = (
                check_book_availability.invoke(
                    call["args"]
                )
            )

            print(
                "Tool result:",
                result
            )

            messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=call["id"]
                )
            )

        final_response = (
            model_with_tools.invoke(
                messages
            )
        )

        print()
        print(
            "Natural-language answer:"
        )
        print(
            final_response.content
        )

        test_1_passed = True

    else:
        print()
        print(
            "ERROR: Expected an availability "
            "tool call, but none was made."
        )

        print()
        print(
            "Model answer:",
            response.content
        )

        test_1_passed = False

    print()
    print("=" * 70)
    print("TEST 2 - SHOULD NOT CALL TOOL")
    print("=" * 70)

    genre_question = (
        "What genre is book 5?"
    )

    print()
    print("Question:")
    print(genre_question)

    second_response = (
        model_with_tools.invoke(
            [
                system_message,
                HumanMessage(
                    content=genre_question
                )
            ]
        )
    )

    if second_response.tool_calls:
        print()
        print(
            "ERROR: Unexpected availability "
            "tool call detected."
        )

        for call in second_response.tool_calls:
            print(
                "Unexpected tool:",
                call["name"]
            )

            print(
                "Arguments:",
                call["args"]
            )

        test_2_passed = False

    else:
        print()
        print(
            "Correct: no availability "
            "tool call was made."
        )

        print()
        print(
            "Model answer:"
        )

        print(
            second_response.content
        )

        test_2_passed = True

    print()
    print("=" * 70)
    print("FINAL TEST RESULT")
    print("=" * 70)

    print()
    print(
        "Availability question:",
        "PASS"
        if test_1_passed
        else "FAIL"
    )

    print(
        "Genre question:",
        "PASS"
        if test_2_passed
        else "FAIL"
    )

    if (
        test_1_passed
        and test_2_passed
    ):
        print()
        print(
            "PART D TOOL-CALLING "
            "BEHAVIOR PASSED."
        )

    else:
        print()
        print(
            "PART D needs another "
            "tool-selection adjustment."
        )


if __name__ == "__main__":
    main()