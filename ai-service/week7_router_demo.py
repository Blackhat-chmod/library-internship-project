import os
import time
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


AI_SERVICE_DIR = Path(__file__).resolve().parent
ENV_FILE = AI_SERVICE_DIR / ".env"

load_dotenv(ENV_FILE)


RouteName = Literal[
    "catalog",
    "action",
    "chitchat",
]


class RouteDecision(BaseModel):
    route: RouteName
    reason: str


ROUTER_PROMPT = """
You are the routing component of a library assistant.

Classify every user message into exactly one of these routes:

1. catalog
Use catalog for read-only questions about library books, authors,
categories, recommendations, descriptions, availability, or whether
a particular book is good, interesting, suitable, or worth reading.

2. action
Use action only when the user is asking the library system to perform
or change something, such as reserving a book, cancelling a
reservation, or making another change to library data.

3. chitchat
Use chitchat for greetings, thanks, casual conversation, and messages
that do not require library catalog information or a library action.

Important routing rules:
- A request to recommend, describe, compare, or evaluate a book is
  catalog, even if the wording is conversational.
- A question asking whether a book is available is catalog.
- Merely mentioning a book does not make the request an action.
- Use action only when the user wants the system to perform a change.
- Greetings and general conversation are chitchat.
- Follow the supplied structured-output schema exactly.
- Never return only a route word as plain text.
- Always return both the route and a short reason through the
  structured-output schema.
""".strip()


MODEL_NAME = "nvidia/nemotron-3.5-lightning:free"

ROUTER_TIMEOUT_SECONDS = 6
TEST_DELAY_SECONDS = 4


ACTION_PHRASES = (
    "reserve",
    "reservation",
    "cancel my reservation",
    "cancel the reservation",
    "make a reservation",
    "book this",
    "borrow this",
)

CATALOG_PHRASES = (
    "book",
    "author",
    "wrote",
    "written by",
    "catalog",
    "recommend",
    "recommendation",
    "available",
    "availability",
    "describe",
    "description",
    "compare",
    "worth reading",
    "good to read",
    "good book",
)

CHITCHAT_PHRASES = (
    "hello",
    "hi",
    "hey",
    "good morning",
    "good afternoon",
    "good evening",
    "thanks",
    "thank you",
    "how are you",
    "what can you do",
    "have a nice day",
)


def build_router():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. "
            "Keep the key in ai-service/.env."
        )

    model = ChatOpenAI(
        model=MODEL_NAME,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0,
        timeout=ROUTER_TIMEOUT_SECONDS,
        max_retries=0,
    )

    return model.with_structured_output(RouteDecision)


def fallback_route_message(
    message: str,
    failure_reason: str,
) -> RouteDecision:
    normalized = " ".join(
        message.lower().strip().split()
    )

    if any(
        phrase in normalized
        for phrase in ACTION_PHRASES
    ):
        return RouteDecision(
            route="action",
            reason=(
                "Deterministic fallback selected action "
                "after the remote router was unavailable."
            ),
        )

    if any(
        phrase in normalized
        for phrase in CATALOG_PHRASES
    ):
        return RouteDecision(
            route="catalog",
            reason=(
                "Deterministic fallback selected catalog "
                "after the remote router was unavailable."
            ),
        )

    if any(
        phrase in normalized
        for phrase in CHITCHAT_PHRASES
    ):
        return RouteDecision(
            route="chitchat",
            reason=(
                "Deterministic fallback selected chitchat "
                "after the remote router was unavailable."
            ),
        )

    return RouteDecision(
        route="chitchat",
        reason=(
            "Deterministic safe fallback selected chitchat "
            "because the remote router was unavailable: "
            f"{type(failure_reason).__name__}."
        ),
    )


def route_message(message: str) -> RouteDecision:
    try:
        router = build_router()

        decision = router.invoke(
            [
                SystemMessage(content=ROUTER_PROMPT),
                HumanMessage(content=message),
            ]
        )

        return decision

    except Exception as exc:
        return fallback_route_message(
            message=message,
            failure_reason=str(exc),
        )


TEST_CASES = [
    (
        "Tell me about Advanced C#.",
        "catalog",
    ),
    (
        "Who wrote Angular API Book?",
        "catalog",
    ),
    (
        "Recommend a book from the catalog.",
        "catalog",
    ),
    (
        "Is Angular Auth Test available?",
        "catalog",
    ),
    (
        "Is Dune any good?",
        "catalog",
    ),
    (
        "Reserve book 5 for me.",
        "action",
    ),
    (
        "Please make a reservation for book 9.",
        "action",
    ),
    (
        "Reserve book 15 for me.",
        "action",
    ),
    (
        "Cancel my reservation.",
        "action",
    ),
    (
        "Please reserve this book for me.",
        "action",
    ),
    (
        "Hello, how are you?",
        "chitchat",
    ),
    (
        "Thanks for your help.",
        "chitchat",
    ),
    (
        "Good morning!",
        "chitchat",
    ),
    (
        "What can you do?",
        "chitchat",
    ),
    (
        "Have a nice day.",
        "chitchat",
    ),
]


def main() -> None:
    print("=" * 70)
    print("WEEK 7 - STRUCTURED ROUTER")
    print(f"MODEL: {MODEL_NAME}")
    print(
        f"REMOTE TIMEOUT: "
        f"{ROUTER_TIMEOUT_SECONDS}s"
    )
    print("=" * 70)

    correct = 0
    misses = []

    for index, (message, expected) in enumerate(
        TEST_CASES,
        start=1,
    ):
        try:
            decision = route_message(message)

            actual = decision.route
            passed = actual == expected

            if passed:
                correct += 1
            else:
                misses.append(
                    {
                        "message": message,
                        "expected": expected,
                        "actual": actual,
                        "reason": decision.reason,
                    }
                )

            print()
            print(f"TEST {index:02d}")
            print(f"USER:     {message}")
            print(f"EXPECTED: {expected}")
            print(f"ACTUAL:   {actual}")
            print(
                f"RESULT:   "
                f"{'PASS' if passed else 'MISS'}"
            )
            print(f"REASON:   {decision.reason}")

        except Exception as exc:
            misses.append(
                {
                    "message": message,
                    "expected": expected,
                    "actual": "ERROR",
                    "reason": str(exc),
                }
            )

            print()
            print(f"TEST {index:02d}")
            print(f"USER:     {message}")
            print(f"EXPECTED: {expected}")
            print("ACTUAL:   ERROR")
            print("RESULT:   MISS")
            print(f"ERROR:    {exc}")

        if index < len(TEST_CASES):
            time.sleep(TEST_DELAY_SECONDS)

    total = len(TEST_CASES)
    accuracy = (correct / total) * 100

    print()
    print("=" * 70)
    print("ROUTER EVALUATION")
    print("=" * 70)
    print(f"CORRECT:  {correct}/{total}")
    print(f"ACCURACY: {accuracy:.1f}%")
    print(f"MISSES:   {len(misses)}")

    if misses:
        print()
        print("MISS INSPECTION")

        for miss in misses:
            print("-" * 70)
            print(f"USER:     {miss['message']}")
            print(f"EXPECTED: {miss['expected']}")
            print(f"ACTUAL:   {miss['actual']}")
            print(f"REASON:   {miss['reason']}")
    else:
        print()
        print(
            "All 15 handwritten routing "
            "tests passed."
        )


if __name__ == "__main__":
    main()