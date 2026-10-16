import os
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


MODEL_NAME = "nvidia/nemotron-3.5-lightning:free"


BASELINE_PROMPT = """
You are a router for a library assistant.

Choose exactly one route:

catalog:
Questions asking for factual catalog information such as
book availability, author, title, or book ID.

action:
Requests that ask the system to perform an action such as
reserving or cancelling a reservation.

chitchat:
Greetings, casual conversation, opinions, recommendations,
and general discussion.

Return the best route and a short reason.
"""


IMPROVED_PROMPT = """
You are a router for a library assistant.

Choose exactly one route:

catalog:
Any request primarily about books or the library catalog.
This includes factual questions, availability, authors,
titles, book IDs, recommendations, opinions about books,
and questions asking whether a book is good or worth
reading.

action:
Requests that ask the system to change something or perform
an operation, such as reserving a book or cancelling a
reservation.

chitchat:
Greetings, thanks, casual conversation, or general
discussion that is not primarily asking about a book or
library catalog information.

Important general rule:
If a message discusses or evaluates a specific book or asks
for a book recommendation, route it to catalog even when
the wording sounds conversational or asks for an opinion.

Return the best route and a short reason.
"""


def build_router(prompt: str):
    api_key = os.getenv(
        "OPENROUTER_API_KEY"
    )

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. "
            "Check ai-service/.env."
        )

    model = ChatOpenAI(
        model=MODEL_NAME,
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        temperature=0,
    )

    router = model.with_structured_output(
        RouteDecision
    )

    return router, prompt


def run_router(
    label: str,
    prompt: str,
    message: str,
) -> RouteDecision:
    router, system_prompt = build_router(
        prompt
    )

    decision = router.invoke(
        [
            SystemMessage(
                content=system_prompt
            ),
            HumanMessage(
                content=message
            ),
        ]
    )

    print()
    print("=" * 70)
    print(label)
    print("=" * 70)
    print(f"MESSAGE:  {message}")
    print("EXPECTED: catalog")
    print(f"ACTUAL:   {decision.route}")
    print(f"REASON:   {decision.reason}")

    if decision.route == "catalog":
        print("RESULT:   CORRECT")
    else:
        print("RESULT:   MISROUTE")

    return decision


def main() -> None:
    message = "Is Dune any good?"

    print(
        "WEEK 7 PART C - CHALLENGE 3"
    )
    print(
        "Router prompt improvement demonstration"
    )

    baseline = run_router(
        "BEFORE - BASELINE PROMPT",
        BASELINE_PROMPT,
        message,
    )

    improved = run_router(
        "AFTER - IMPROVED PROMPT",
        IMPROVED_PROMPT,
        message,
    )

    print()
    print("=" * 70)
    print("CHALLENGE 3 SUMMARY")
    print("=" * 70)

    print(
        f"Before improvement: {baseline.route}"
    )
    print(
        f"After improvement:  {improved.route}"
    )

    if (
        baseline.route != "catalog"
        and improved.route == "catalog"
    ):
        print("DEMONSTRATION: PASS")
        print(
            "The baseline prompt treated book "
            "opinions as chitchat."
        )
        print(
            "The improved prompt adds a general "
            "rule: book evaluations and "
            "recommendations belong to catalog."
        )
        print(
            "No special-case rule for Dune was "
            "added."
        )
    else:
        print(
            "DEMONSTRATION: REVIEW REQUIRED"
        )
        print(
            "The model did not produce the "
            "expected before/after contrast."
        )


if __name__ == "__main__":
    main()