import logging
import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from langchain_chroma import Chroma
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv()


OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

LLM_MODEL = "openrouter/free"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class LocalSentenceTransformerEmbeddings(
    Embeddings
):
    def __init__(self):
        self.model = SentenceTransformer(
            EMBEDDING_MODEL
        )

    def embed_documents(
        self,
        texts: list[str]
    ) -> list[list[float]]:
        return self.model.encode(
            texts
        ).tolist()

    def embed_query(
        self,
        text: str
    ) -> list[float]:
        return self.model.encode(
            text
        ).tolist()


def print_results(
    title: str,
    documents: list[Document]
):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    if not documents:
        print("No documents retrieved.")
        return

    for index, document in enumerate(
        documents,
        start=1
    ):
        source = document.metadata.get(
            "source",
            "Unknown"
        )

        print()
        print(
            f"Result {index}"
        )
        print(
            f"Source: {source}"
        )
        print(
            document.page_content
        )


def main():
    if not OPENROUTER_API_KEY:
        print(
            "OPENROUTER_API_KEY is missing."
        )
        return

    logging.basicConfig(
        level=logging.INFO
    )

    logging.getLogger(
        "langchain.retrievers.multi_query"
    ).setLevel(
        logging.INFO
    )

    logging.getLogger(
        "langchain_classic.retrievers.multi_query"
    ).setLevel(
        logging.INFO
    )

    print(
        "Loading local embedding model..."
    )

    embeddings = (
        LocalSentenceTransformerEmbeddings()
    )

    raw_book_texts = [
        {
            "source": "Python Essentials",
            "text": """
Python Essentials is designed for beginners
who want to learn programming.

The book introduces Python syntax, variables,
conditions, loops, functions and collections.

It also explains software development basics,
problem solving and how programmers build
small applications using Python.

The later chapters introduce object-oriented
programming and practical coding exercises.
"""
        },
        {
            "source": "React Essentials",
            "text": """
React Essentials focuses on modern frontend
and web development.

The book explains components, props, state,
events and reusable user interface design.

It also introduces client-side routing,
API integration and building interactive
web applications with React.

The book is useful for developers interested
in JavaScript-based frontend development.
"""
        },
        {
            "source": "Mystery House",
            "text": """
Mystery House is a detective novel.

A detective investigates a mysterious murder
inside an isolated house.

The investigation involves hidden evidence,
unreliable witnesses and several possible
suspects.

The story focuses on crime, mystery,
investigation and suspense.
"""
        },
        {
            "source": "Journey Beyond Earth",
            "text": """
Journey Beyond Earth is a science-fiction
story set in the future.

A crew of astronauts travels through deep
space while working with intelligent robots.

The story includes future technology,
space exploration, artificial intelligence
and encounters with unknown worlds.

It is aimed at readers who enjoy futuristic
science-fiction adventures.
"""
        },
        {
            "source": "Database Fundamentals",
            "text": """
Database Fundamentals introduces relational
database concepts.

It explains tables, rows, primary keys,
foreign keys and relationships.

Readers learn SQL queries, database design,
normalization and how applications store
structured information.

The book is useful for students learning
backend development and data management.
"""
        }
    ]

    print(
        "Splitting documents with "
        "RecursiveCharacterTextSplitter..."
    )

    splitter = (
        RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=40,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )
    )

    all_chunks = []

    for book in raw_book_texts:
        chunks = splitter.create_documents(
            texts=[
                book["text"]
            ],
            metadatas=[
                {
                    "source":
                        book["source"]
                }
            ]
        )

        all_chunks.extend(
            chunks
        )

    print(
        "Total chunks created:",
        len(all_chunks)
    )

    print()
    print(
        "Creating Chroma vector store..."
    )

    vectorstore = Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        collection_name=(
            "week6_advanced_retrieval"
        )
    )

    base_retriever = (
        vectorstore.as_retriever(
            search_kwargs={
                "k": 3
            }
        )
    )

    model = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=(
            "https://openrouter.ai/api/v1"
        ),
        temperature=0.2
    )

    multi_query_retriever = (
        MultiQueryRetriever.from_llm(
            retriever=base_retriever,
            llm=model
        )
    )

    test_questions = [
        (
            "Which book can help me "
            "learn coding?"
        ),
        (
            "I want to build modern "
            "web interfaces. What should "
            "I read?"
        ),
        (
            "Which book contains a "
            "detective investigation?"
        ),
        (
            "Do you have something about "
            "space and future technology?"
        ),
        (
            "Which book teaches how "
            "structured application data "
            "is stored?"
        )
    ]

    for question_number, question in enumerate(
        test_questions,
        start=1
    ):
        print()
        print()
        print("#" * 70)
        print(
            f"QUESTION {question_number}"
        )
        print("#" * 70)
        print(question)

        plain_results = (
            base_retriever.invoke(
                question
            )
        )

        print_results(
            "PLAIN RETRIEVER RESULTS",
            plain_results
        )

        print()
        print(
            "Running MultiQueryRetriever..."
        )

        multi_results = (
            multi_query_retriever.invoke(
                question
            )
        )

        print_results(
            "MULTI-QUERY RETRIEVER RESULTS",
            multi_results
        )

    print()
    print()
    print("=" * 70)
    print(
        "ADVANCED RETRIEVAL DEMO COMPLETE"
    )
    print("=" * 70)

    print()
    print(
        "Compare the plain and multi-query "
        "results above."
    )

    print(
        "Look for questions where generated "
        "alternative queries improved recall "
        "or introduced irrelevant results."
    )


if __name__ == "__main__":
    main()