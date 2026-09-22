import os

import chromadb
import httpx
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()


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

    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def embed_text(
    text: str
) -> list[float]:

    vector = embedding_model.encode(text)

    return vector.tolist()


def add_document(
    text: str,
    source: str
) -> None:

    chunks = chunk_text(text)

    embeddings = [
        embed_text(chunk)
        for chunk in chunks
    ]

    ids = [
        f"{source}-{index}"
        for index in range(len(chunks))
    ]

    metadatas = [
        {
            "source": source,
            "chunk": index
        }
        for index in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )


def load_demo_documents() -> None:

    if collection.count() > 0:
        return

    documents = [
        (
            """
            The Aurora Library contains a science fiction collection
            focused on space exploration, robotics, and future technology.
            One popular book follows a crew travelling through a wormhole
            to find a new home for humanity.
            """,
            "science_fiction.txt"
        ),

        (
            """
            The library's fantasy collection includes stories about
            magic, dragons, ancient kingdoms, and young heroes.
            One story follows a young wizard studying at a magical school.
            """,
            "fantasy.txt"
        ),

        (
            """
            The technology section contains books about Python,
            software engineering, web development, databases,
            and artificial intelligence.
            """,
            "technology.txt"
        )
    ]

    for text, source in documents:
        add_document(
            text,
            source
        )


def retrieve(
    question: str,
    k: int = 3
):

    query_embedding = embed_text(
        question
    )

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=k
    )

    documents = (
        results["documents"][0]
        if results["documents"]
        else []
    )

    metadatas = (
        results["metadatas"][0]
        if results["metadatas"]
        else []
    )

    return documents, metadatas


def build_prompt(
    question: str,
    chunks: list[str]
) -> str:

    context = "\n\n".join(
        chunks
    )

    return f"""
Answer the question using ONLY the context below.

If the answer is not contained in the context, say:

"I don't have that information."

Do not use outside knowledge.

Context:

{context}

Question:

{question}
"""


async def generate_answer(
    prompt: str
) -> str:

    if not OPENROUTER_API_KEY:
        return (
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
        timeout=30
    ) as client:

        response = await client.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload
        )

    response.raise_for_status()

    data = response.json()

    return (
        data["choices"][0]
        ["message"]["content"]
    )


load_demo_documents()