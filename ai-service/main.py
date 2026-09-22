from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(
    title="Library AI Service",
    description="Week 4 FastAPI service for the Library Internship Project",
    version="1.0.0"
)


class SummaryRequest(BaseModel):
    text: str = Field(
        min_length=10,
        description="Text that should be summarized"
    )


class SummaryResponse(BaseModel):
    original_length: int
    summary: str


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


@app.get("/")
def root():
    return {
        "message": "Library AI Service is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "library-ai-service"
    }


@app.post(
    "/summarize",
    response_model=SummaryResponse
)
def summarize_text(request: SummaryRequest):
    text = request.text.strip()

    sentences = [
        sentence.strip()
        for sentence in text.replace("!", ".").replace("?", ".").split(".")
        if sentence.strip()
    ]

    if len(sentences) <= 2:
        summary = text
    else:
        summary = ". ".join(sentences[:2]) + "."

    return SummaryResponse(
        original_length=len(text),
        summary=summary
    )


@app.post(
    "/genre",
    response_model=GenreResponse
)
def suggest_genre(request: GenreRequest):
    content = (
        request.title + " " + request.description
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