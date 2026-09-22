import json
import os
from pathlib import Path

import chromadb
import httpx
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

CORPUS_FILE = BASE_DIR / "library_corpus.json"


embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(
    name="library_rag"
)


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

MODEL_NAME = "openai/gpt-4o-mini"


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> list[str]:

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[
            start:end
        ].strip()

        if chunk:
            chunks.append(
                chunk
            )

        start += (
            chunk_size - overlap
        )

    return chunks


def embed_text(
    text: str
) -> list[float]:

    vector = embedding_model.encode(
        text
    )

    return vector.tolist()


def add_document(
    text: str,
    source: str,
    book_id: int | str = 0,
    title: str = "",
    author: str = ""
) -> None:

    chunks = chunk_text(
        text
    )

    embeddings = [
        embed_text(chunk)
        for chunk in chunks
    ]

    ids = [
        f"book-{book_id}-chunk-{index}"
        for index in range(
            len(chunks)
        )
    ]

    metadatas = [
        {
            "source": source,
            "book_id": str(book_id),
            "title": title,
            "author": author,
            "chunk": index
        }
        for index in range(
            len(chunks)
        )
    ]

    collection.upsert(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )


def load_corpus() -> list[dict]:

    if not CORPUS_FILE.exists():
        raise FileNotFoundError(
            f"Corpus file not found: {CORPUS_FILE}"
        )

    content = CORPUS_FILE.read_text(
        encoding="utf-8"
    )

    corpus = json.loads(
        content
    )

    if not isinstance(
        corpus,
        list
    ):
        raise ValueError(
            "library_corpus.json must contain a list."
        )

    return corpus


def load_library_documents() -> None:

    corpus = load_corpus()

    for book in corpus:
        book_id = (
            book.get("book_id")
            or 0
        )

        title = str(
            book.get("title")
            or "Untitled"
        )

        author = str(
            book.get("author")
            or "Unknown Author"
        )

        text = str(
            book.get("text")
            or ""
        ).strip()

        if not text:
            continue

        source = (
            f"book_{book_id}.json"
        )

        add_document(
            text=text,
            source=source,
            book_id=book_id,
            title=title,
            author=author
        )


def retrieve(
    question: str,
    k: int = 3
):

    if collection.count() == 0:
        return [], []

    query_embedding = embed_text(
        question
    )

    number_of_results = min(
        k,
        collection.count()
    )

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=number_of_results
    )

    documents = (
        results["documents"][0]
        if results.get("documents")
        else []
    )

    metadatas = (
        results["metadatas"][0]
        if results.get("metadatas")
        else []
    )

    return (
        documents,
        metadatas
    )


def build_prompt(
    question: str,
    chunks: list[str]
) -> str:

    context = "\n\n".join(
        chunks
    )

    return f"""
You are a library assistant.

Answer the question using ONLY the library context below.

If the answer is not contained in the context, respond exactly with:

"I don't have that information."

Do not use outside knowledge.
Do not guess.
Keep the answer clear and concise.

Library context:

{context}

Question:

{question}
"""


async def generate_answer(
    prompt: str
) -> str:

    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is missing."
        )

    headers = {
        "Authorization":
            f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":
            "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "temperature": 0.2,
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    async with httpx.AsyncClient(
        timeout=30.0
    ) as client:

        response = await client.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload
        )

    response.raise_for_status()

    data = response.json()

    try:
        return (
            data["choices"][0]
            ["message"]["content"]
            .strip()
        )

    except (
        KeyError,
        IndexError,
        TypeError
    ):
        raise ValueError(
            "LLM provider returned an unexpected response structure."
        )


load_library_documents()