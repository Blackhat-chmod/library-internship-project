import json
from pathlib import Path

import httpx


BOOKS_API_URL = "https://localhost:7272/api/Books"

OUTPUT_FILE = Path("library_corpus.json")


def get_author_name(book: dict) -> str:
    author_entity = book.get("authorEntity")

    if isinstance(author_entity, dict):
        full_name = author_entity.get("fullName")

        if full_name:
            return str(full_name)

    author = book.get("author")

    if author:
        return str(author)

    return "Unknown Author"


def get_category_names(book: dict) -> list[str]:
    categories = book.get("categories")

    if isinstance(categories, list):
        names = []

        for category in categories:
            if isinstance(category, dict):
                name = category.get("categoryName")

                if name:
                    names.append(str(name))

        if names:
            return names

    category = book.get("category")

    if category:
        return [str(category)]

    return ["Uncategorized"]


def build_document(book: dict) -> dict:
    book_id = (
        book.get("bookId")
        or book.get("id")
        or 0
    )

    title = str(
        book.get("title")
        or "Untitled"
    )

    author = get_author_name(book)

    categories = get_category_names(book)

    description = str(
        book.get("description")
        or (
            f"{title} is a library book written by {author}. "
            f"It belongs to the following category or categories: "
            f"{', '.join(categories)}."
        )
    )

    text = (
        f"Title: {title}\n"
        f"Author: {author}\n"
        f"Categories: {', '.join(categories)}\n"
        f"Description: {description}"
    )

    return {
        "book_id": book_id,
        "title": title,
        "author": author,
        "categories": categories,
        "text": text
    }


def fetch_books() -> list[dict]:
    with httpx.Client(
        verify=False,
        timeout=30.0
    ) as client:
        response = client.get(
            BOOKS_API_URL
        )

    response.raise_for_status()

    books = response.json()

    if not isinstance(books, list):
        raise ValueError(
            "Expected the Books API to return a list."
        )

    return books


def main():
    print(
        f"Fetching books from: {BOOKS_API_URL}"
    )

    books = fetch_books()

    print(
        f"Books received: {len(books)}"
    )

    corpus = [
        build_document(book)
        for book in books
    ]

    OUTPUT_FILE.write_text(
        json.dumps(
            corpus,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print(
        f"Corpus saved to: {OUTPUT_FILE.resolve()}"
    )

    print(
        "\nCorpus preview:"
    )

    for document in corpus:
        print(
            "\n------------------------------"
        )

        print(
            document["text"]
        )


if __name__ == "__main__":
    main()