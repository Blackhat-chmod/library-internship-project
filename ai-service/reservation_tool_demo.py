import uuid
from typing import Any

import requests
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field


LIBRARY_API_BASE_URL = "http://localhost:5087"


class ReserveArgs(BaseModel):
    book_id: int = Field(
        gt=0,
        description="Positive ID of the book to reserve.",
    )


@tool(args_schema=ReserveArgs)
def reserve_book(
    book_id: int,
    config: RunnableConfig,
) -> dict[str, Any]:
    """
    Reserve a specific library book for the currently
    authenticated user.

    Use this tool only when the user explicitly asks to
    reserve a book.

    Authentication is taken from runtime configuration.
    Never request, accept, or store a user ID or JWT in
    the tool arguments or graph state.
    """

    configurable = config.get("configurable", {})

    user_token = configurable.get("user_token")

    if not user_token:
        return {
            "ok": False,
            "status": 401,
            "message": "Authentication token is missing.",
        }

    idempotency_key = configurable.get(
        "idempotency_key"
    )

    if not idempotency_key:
        idempotency_key = str(uuid.uuid4())

    url = (
        f"{LIBRARY_API_BASE_URL}"
        f"/api/books/{book_id}/reserve"
    )

    headers = {
        "Authorization": f"Bearer {user_token}",
        "Idempotency-Key": idempotency_key,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            timeout=10,
        )
    except requests.RequestException as error:
        return {
            "ok": False,
            "status": 503,
            "message": (
                "Could not reach the Library API."
            ),
            "error": str(error),
        }

    try:
        data = response.json()
    except ValueError:
        data = {
            "message": response.text
            or "No response body."
        }

    if response.status_code == 200:
        return {
            "ok": True,
            "status": 200,
            "reservation": data,
            "idempotency_key": idempotency_key,
        }

    if response.status_code == 404:
        return {
            "ok": False,
            "status": 404,
            "message": data.get(
                "message",
                "Book not found.",
            ),
            "idempotency_key": idempotency_key,
        }

    if response.status_code == 409:
        return {
            "ok": False,
            "status": 409,
            "message": data.get(
                "message",
                "Reservation conflict.",
            ),
            "idempotency_key": idempotency_key,
        }

    if response.status_code in (401, 403):
        return {
            "ok": False,
            "status": response.status_code,
            "message": (
                "Authentication or authorization failed."
            ),
            "idempotency_key": idempotency_key,
        }

    return {
        "ok": False,
        "status": response.status_code,
        "message": data.get(
            "message",
            "Reservation request failed.",
        ),
        "idempotency_key": idempotency_key,
    }


def main() -> None:
    print("=" * 70)
    print("WEEK 7 - SECURE RESERVATION TOOL")
    print("=" * 70)

    print()
    print("ReserveArgs validation:")
    print("book_id must be greater than 0.")

    print()
    print("Security design:")
    print(
        "- JWT is read from "
        'config["configurable"]["user_token"].'
    )
    print("- JWT is NOT part of ReserveArgs.")
    print("- JWT is NOT stored in graph state.")
    print("- User ID is NOT accepted from the model.")
    print(
        "- Idempotency-Key protects repeated "
        "write requests."
    )


if __name__ == "__main__":
    main()