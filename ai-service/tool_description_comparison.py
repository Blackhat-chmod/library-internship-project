from langchain_core.tools import tool


@tool
def reserve_book_vague(book_id: int) -> str:
    """
    Reserve a book.
    """
    return f"Would reserve book {book_id}."


@tool
def reserve_book_precise(book_id: int) -> str:
    """
    Reserve a library book only when the user
    explicitly asks to reserve that specific book.

    This is a write action that changes library data.

    Do NOT use this tool when the user only asks:
    - whether a book is available
    - for book information
    - for recommendations
    - about an author or category

    The user must clearly request a reservation.
    """
    return f"Would reserve book {book_id}."


def main() -> None:
    print("=" * 70)
    print("WEEK 7 - TOOL DESCRIPTION COMPARISON")
    print("=" * 70)

    print()
    print("VAGUE TOOL DESCRIPTION:")
    print(reserve_book_vague.description)

    print()
    print("PRECISE TOOL DESCRIPTION:")
    print(reserve_book_precise.description)

    print()
    print("COMPARISON:")
    print(
        "The vague description only states what the "
        "tool does."
    )
    print(
        "The precise description also states when the "
        "tool is allowed and when it must not be used."
    )
    print(
        "For a write tool, the precise description is "
        "safer because it reduces accidental tool calls."
    )
    print(
        "The final reserve_book tool therefore uses an "
        "explicit-reservation-only description."
    )


if __name__ == "__main__":
    main()