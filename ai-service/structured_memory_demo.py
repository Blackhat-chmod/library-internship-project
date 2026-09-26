import os
from typing import Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MEMORY_MODEL = "openrouter/free"

STRUCTURED_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "openrouter/free"
]


class BookAnswer(BaseModel):
    answer: str = Field(
        description="The answer to the user's question"
    )

    confidence: str = Field(
        description="high, medium, or low"
    )

    sources: list[str] = Field(
        description="Book titles the answer was drawn from"
    )


session_store: Dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(
    session_id: str
) -> InMemoryChatMessageHistory:

    if session_id not in session_store:
        session_store[session_id] = (
            InMemoryChatMessageHistory()
        )

    return session_store[session_id]


def create_memory_model():
    return ChatOpenAI(
        model=MEMORY_MODEL,
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2
    )


def run_structured_output():
    print()
    print("=" * 70)
    print("STRUCTURED OUTPUT TEST")
    print("=" * 70)

    question = (
        "Which book should I read "
        "for frontend development?"
    )

    structured_prompt = (
        ChatPromptTemplate.from_template(
            """
You are a library assistant.

Available books:

1. Python Essentials
   Genre: Technology
   Description:
   Beginner-friendly Python programming book.

2. React Essentials
   Genre: Web Development
   Description:
   Modern frontend and React development book.

3. Mystery House
   Genre: Mystery
   Description:
   Detective investigation and murder mystery.

4. Journey Beyond Earth
   Genre: Science Fiction
   Description:
   Space travel, robots and future technology.

Question:
{question}

Return a structured answer containing:

answer
confidence
sources

Confidence must be:
high
medium
or low

Sources must contain only book titles
from the available list.
"""
        )
    )

    for model_name in STRUCTURED_MODELS:
        print()
        print(
            "Trying structured model:",
            model_name
        )

        try:
            structured_base_model = ChatOpenAI(
                model=model_name,
                api_key=OPENROUTER_API_KEY,
                base_url=(
                    "https://openrouter.ai/api/v1"
                ),
                temperature=0
            )

            structured_model = (
                structured_base_model
                .with_structured_output(
                    BookAnswer,
                    method="json_schema"
                )
            )

            structured_chain = (
                structured_prompt
                | structured_model
            )

            result = structured_chain.invoke(
                {
                    "question": question
                }
            )

            print()
            print("Answer:")
            print(result.answer)

            print()
            print("Confidence:")
            print(result.confidence)

            print()
            print("Sources:")
            print(result.sources)

            print()
            print(
                "Structured output succeeded."
            )

            return True

        except Exception as error:
            print()
            print(
                "Structured model failed:"
            )
            print(
                type(error).__name__
            )
            print(str(error))

            print()
            print(
                "Trying next available model..."
            )

    print()
    print(
        "Structured output could not be "
        "completed because the free provider "
        "is temporarily unavailable or does "
        "not support the requested schema."
    )

    print(
        "The program will continue without "
        "crashing."
    )

    return False


def main():
    if not OPENROUTER_API_KEY:
        print(
            "OPENROUTER_API_KEY is missing."
        )
        return

    model = create_memory_model()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a library assistant.

Use the conversation history to understand
follow-up questions.

When the user asks about a specific book,
remember that book for later follow-up questions.

Available books:

1. Python Essentials
   Genre: Technology
   Description:
   Beginner-friendly Python programming book.

2. React Essentials
   Genre: Web Development
   Description:
   Modern frontend and React development book.

3. Mystery House
   Genre: Mystery
   Description:
   Detective investigation and murder mystery.

4. Journey Beyond Earth
   Genre: Science Fiction
   Description:
   Space travel, robots and future technology.

Do not invent books that are not listed here.
"""
            ),
            MessagesPlaceholder(
                variable_name="history"
            ),
            (
                "human",
                "{question}"
            )
        ]
    )

    basic_chain = (
        prompt
        | model
        | StrOutputParser()
    )

    chain_with_memory = (
        RunnableWithMessageHistory(
            basic_chain,
            get_session_history,
            input_messages_key="question",
            history_messages_key="history"
        )
    )

    print()
    print("=" * 70)
    print("MEMORY TEST - SAME SESSION")
    print("=" * 70)

    session_id = "user-42"

    first_question = (
        "Tell me about Journey Beyond Earth."
    )

    print()
    print("Question 1:")
    print(first_question)

    try:
        first_answer = (
            chain_with_memory.invoke(
                {
                    "question":
                        first_question
                },
                config={
                    "configurable": {
                        "session_id":
                            session_id
                    }
                }
            )
        )

        print()
        print("Answer 1:")
        print(first_answer)

    except Exception as error:
        print()
        print(
            "Memory request failed:"
        )
        print(
            type(error).__name__
        )
        print(str(error))

        print()
        print(
            "The free model provider may be "
            "temporarily unavailable."
        )

        return

    follow_up_question = (
        "What genre is it?"
    )

    print()
    print("Question 2:")
    print(follow_up_question)

    try:
        follow_up_answer = (
            chain_with_memory.invoke(
                {
                    "question":
                        follow_up_question
                },
                config={
                    "configurable": {
                        "session_id":
                            session_id
                    }
                }
            )
        )

        print()
        print("Answer 2:")
        print(follow_up_answer)

    except Exception as error:
        print()
        print(
            "Follow-up memory request failed:"
        )
        print(
            type(error).__name__
        )
        print(str(error))

    print()
    print("=" * 70)
    print("MEMORY TEST - NEW SESSION")
    print("=" * 70)

    fresh_session_id = "user-99"

    print()
    print("Question:")
    print(follow_up_question)

    try:
        fresh_answer = (
            chain_with_memory.invoke(
                {
                    "question":
                        follow_up_question
                },
                config={
                    "configurable": {
                        "session_id":
                            fresh_session_id
                    }
                }
            )
        )

        print()
        print("Fresh session answer:")
        print(fresh_answer)

    except Exception as error:
        print()
        print(
            "Fresh-session request failed:"
        )
        print(
            type(error).__name__
        )
        print(str(error))

    run_structured_output()

    print()
    print("=" * 70)
    print("PART C DEMO COMPLETE")
    print("=" * 70)

    print()
    print(
        "Note: session memory is stored only "
        "in RAM and is lost when the Python "
        "or FastAPI process restarts."
    )


if __name__ == "__main__":
    main()