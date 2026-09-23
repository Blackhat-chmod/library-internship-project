import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rag_pipeline import (
    retrieve,
    build_prompt,
    generate_answer
)


load_dotenv()

app = FastAPI(
    title="Library AI Service",
    description="FastAPI AI service for the Library Internship Project",
    version="1.2.0"
)


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_NAME = "openai/gpt-4o-mini"


class SummaryRequest(BaseModel):
    text: str = Field(
        min_length=10,
        description="Text that should be summarized"
    )

    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0
    )

    max_tokens: int = Field(
        default=150,
        ge=20,
        le=500
    )


class SummaryResponse(BaseModel):
    summary: str
    key_points: list[str]
    model: str


class GenreRequest(BaseModel):
    title: str = Field(
        min_length=1,
        description="Book title"
    )

    description: str = Field(
        min_length=5,
        description="Short description of the book"
    )


class GenreResponse(BaseModel):
    title: str
    suggested_genre: str


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        description="Question to ask the library knowledge assistant"
    )


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


def parse_llm_response(content: str) -> dict:
    try:
        parsed = json.loads(content)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LLM returned malformed JSON.",
                "raw_response": content
            }
        )

    summary = parsed.get("summary")
    key_points = parsed.get("key_points")

    if not isinstance(summary, str):
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LLM response is missing a valid summary.",
                "raw_response": content
            }
        )

    if not isinstance(key_points, list):
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LLM response is missing valid key_points.",
                "raw_response": content
            }
        )

    return {
        "summary": summary,
        "key_points": [
            str(point)
            for point in key_points
        ]
    }


def build_source_labels(
    metadatas: list[dict]
) -> list[str]:

    sources = []

    for metadata in metadatas:
        source = metadata.get(
            "source",
            "unknown-source"
        )

        title = metadata.get(
            "title",
            "Unknown Title"
        )

        author = metadata.get(
            "author",
            "Unknown Author"
        )

        label = (
            f"{title} — {author} ({source})"
        )

        if label not in sources:
            sources.append(label)

    return sources


@app.get("/")
def root():
    return {
        "message": "Library AI Service is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "library-ai-service",
        "version": "1.2.0"
    }


@app.post(
    "/summarize",
    response_model=SummaryResponse
)
async def summarize_text(
    request: SummaryRequest
):
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="OPENROUTER_API_KEY is missing."
        )

    system_prompt = """
You are a helpful library assistant.

Summarize the user's text clearly and accurately.

Return ONLY valid JSON in this exact format:

{
  "summary": "short summary",
  "key_points": [
    "point 1",
    "point 2"
  ]
}

Do not include markdown.
Do not include explanations outside the JSON.
"""

    user_prompt = f"""
Summarize the following text:

{request.text}
"""

    payload = {
        "model": MODEL_NAME,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "LLM request failed.",
                    "provider_status": response.status_code
                }
            )

        data = response.json()

        try:
            content = (
                data["choices"][0]["message"]["content"]
            )

        except (
            KeyError,
            IndexError,
            TypeError
        ):
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "LLM provider returned an unexpected response structure."
                }
            )

        parsed = parse_llm_response(content)

        return SummaryResponse(
            summary=parsed["summary"],
            key_points=parsed["key_points"],
            model=MODEL_NAME
        )

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach LLM provider: {error}"
        )


@app.post(
    "/ask",
    response_model=AskResponse
)
async def ask_question(
    request: AskRequest
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        chunks, metadatas = retrieve(
            question,
            k=3
        )

        if not chunks:
            return AskResponse(
                answer="I don't have that information.",
                sources=[]
            )

        prompt = build_prompt(
            question,
            chunks
        )

        answer = await generate_answer(
            prompt
        )

        clean_answer = answer.strip()

        if (
            "i don't have that information"
            in clean_answer.lower()
        ):
            return AskResponse(
                answer="I don't have that information.",
                sources=[]
            )

        sources = build_source_labels(
            metadatas
        )

        return AskResponse(
            answer=clean_answer,
            sources=sources
        )

    except httpx.RequestError as error:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Could not reach the LLM provider.",
                "error": str(error)
            }
        )

    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LLM provider returned an error.",
                "provider_status": error.response.status_code
            }
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "The RAG request could not be completed.",
                "error": str(error)
            }
        )


@app.get("/test-malformed-response")
def test_malformed_response():
    fake_llm_response = """
This is not valid JSON.

Summary: FastAPI is useful.
Key points:
- Validation
- Documentation
"""

    return parse_llm_response(
        fake_llm_response
    )


@app.post(
    "/genre",
    response_model=GenreResponse
)
def suggest_genre(
    request: GenreRequest
):
    content = (
        request.title +
        " " +
        request.description
    ).lower()

    if any(
        word in content
        for word in [
            "computer",
            "programming",
            "software",
            "technology",
            "coding",
            "python"
        ]
    ):
        genre = "Technology"

    elif any(
        word in content
        for word in [
            "murder",
            "detective",
            "crime",
            "mystery"
        ]
    ):
        genre = "Mystery"

    elif any(
        word in content
        for word in [
            "space",
            "future",
            "robot",
            "alien"
        ]
    ):
        genre = "Science Fiction"

    elif any(
        word in content
        for word in [
            "love",
            "relationship",
            "romance"
        ]
    ):
        genre = "Romance"

    else:
        genre = "General"

    return GenreResponse(
        title=request.title,
        suggested_genre=genre
    )