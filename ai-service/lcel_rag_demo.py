import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    RunnableLambda,
    RunnablePassthrough,
)
from langchain_openai import ChatOpenAI


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

LLM_MODEL = "openrouter/free"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class LocalSentenceTransformerEmbeddings(Embeddings):
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


def guard_short_questions(
    inputs: dict
) -> dict:
    question = inputs.get(
        "question",
        ""
    ).strip()

    if len(question) < 3:
        raise ValueError(
            "Question too short to answer meaningfully."
        )

    return inputs


def format_docs(
    docs: list[Document]
) -> str:
    return "\n\n".join(
        document.page_content
        for document in docs
    )


def main():
    if not OPENROUTER_API_KEY:
        print(
            "OPENROUTER_API_KEY is missing."
        )
        return

    print("Loading local embedding model...")

    embeddings = (
        LocalSentenceTransformerEmbeddings()
    )

    documents = [
        Document(
            page_content=(
                "Python Essentials is a beginner-friendly "
                "book about Python programming, coding, "
                "software development and programming basics."
            ),
            metadata={
                "title": "Python Essentials"
            }
        ),
        Document(
            page_content=(
                "React Essentials is a web development "
                "book covering React, frontend development "
                "and modern user interfaces."
            ),
            metadata={
                "title": "React Essentials"
            }
        ),
        Document(
            page_content=(
                "Mystery House is a detective story about "
                "a crime investigation and a mysterious murder."
            ),
            metadata={
                "title": "Mystery House"
            }
        ),
        Document(
            page_content=(
                "Journey Beyond Earth is a science-fiction "
                "story involving space travel, robots "
                "and future technology."
            ),
            metadata={
                "title": "Journey Beyond Earth"
            }
        )
    ]

    print("Creating LangChain Chroma vector store...")

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="week6_lcel_demo"
    )

    retriever = vectorstore.as_retriever(
        search_kwargs={
            "k": 2
        }
    )

    model = ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url=(
            "https://openrouter.ai/api/v1"
        ),
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a library assistant.

Answer the question using ONLY the library
context provided below.

If the answer is not present in the context,
say:

"The available library information is not sufficient."

Context:
{context}

Question:
{question}
"""
    )

    retrieval_chain = (
        {
            "context":
                RunnableLambda(
                    lambda inputs:
                    inputs["question"]
                )
                | retriever
                | RunnableLambda(
                    format_docs
                ),
            "question":
                RunnableLambda(
                    lambda inputs:
                    inputs["question"]
                )
        }
    )

    chain = (
        RunnableLambda(
            guard_short_questions
        )
        | retrieval_chain
        | prompt
        | model
        | StrOutputParser()
    )

    question = (
        "Which book should I read "
        "to learn programming?"
    )

    print()
    print("Question:")
    print(question)

    print()
    print("Running LCEL chain...")

    answer = chain.invoke({
        "question": question
    })

    print()
    print("Answer:")
    print(answer)

    print()
    print("Testing input guard...")

    try:
        chain.invoke({
            "question": "a"
        })

    except ValueError as error:
        print(
            "Guard worked:",
            error
        )


if __name__ == "__main__":
    main()