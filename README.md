# Library Internship Project

This repository contains the Library Management project developed during the internship.

The project includes:

- ASP.NET Core Web API backend
- Angular frontend
- SQL Server database
- JWT authentication and authorization
- FastAPI AI service
- LLM integration
- Embeddings and semantic search
- Chroma vector database
- Manual Retrieval-Augmented Generation (RAG)
- Git feature branch and pull request workflow

---

# Backend

The backend is built using ASP.NET Core Web API.

Main backend features include:

- Book management
- User registration
- User login
- Password hashing
- JWT authentication
- Role-based authorization
- SQL Server integration
- Swagger API documentation

## Authentication

Users can register and log in through the authentication API.

After successful login, the API generates a JWT token containing user information and role claims.

Protected endpoints require a valid JWT token.

### Authorization Rules

- GET book endpoints are public
- POST book endpoint requires authentication
- PUT book endpoint requires authentication
- DELETE book endpoint requires the Admin role

Normal users receive `403 Forbidden` when attempting Admin-only operations.

---

# Angular Frontend

The Angular frontend provides the user interface for the Library Management system.

Features include:

- Book list
- Add book form
- Login page
- JWT authentication
- AuthService
- HTTP authentication interceptor
- Route guard
- Logout functionality
- Role-based interface controls

The JWT token is stored in `localStorage`.

The HTTP interceptor automatically attaches the JWT token to authenticated API requests.

The route guard prevents unauthenticated users from opening protected routes.

## Role-Based UI

Admin users can see Delete controls.

Normal users cannot see Delete controls.

---

# FastAPI AI Service

The AI service is located in:

```text
ai-service/
```

The service is built using FastAPI and provides AI functionality for the Library Internship Project.

Main endpoints include:

```text
GET /
GET /health
POST /summarize
POST /ask
POST /genre
GET /test-malformed-response
```

FastAPI Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# Week 4 — Authentication and AI Service

Week 4 introduced JWT authentication, Angular authentication integration, FastAPI, LLM APIs, prompt engineering, and Git workflow practice.

## Week 4 Backend Work

The ASP.NET Core backend was extended with:

- User registration
- User login
- Secure password hashing
- JWT token generation
- JWT validation
- Role claims
- Authentication middleware
- Role-based authorization

Books API authorization rules:

```text
GET     Public
POST    Authenticated users
PUT     Authenticated users
DELETE  Admin only
```

A normal user receives:

```text
403 Forbidden
```

when attempting an Admin-only Delete operation.

Admin users can successfully perform Delete operations.

## Week 4 Angular Authentication

The Angular frontend was extended with:

- Login page
- AuthService
- JWT storage
- HTTP interceptor
- Route guard
- Logout
- Role-based interface controls

The JWT token is stored in:

```text
localStorage
```

The HTTP interceptor automatically attaches the JWT token to authenticated requests.

The route guard prevents unauthenticated access to protected pages.

Admin-only controls are hidden from normal users.

## Week 4 FastAPI Work

The FastAPI service introduced AI functionality into the project.

The LLM provider is accessed through OpenRouter.

The configured model is:

```text
openai/gpt-4o-mini
```

### Health Endpoint

```text
GET /health
```

This verifies that the AI service is running.

### Summarization Endpoint

```text
POST /summarize
```

The endpoint accepts text and generates:

- A summary
- Key points
- Model information

The service validates structured LLM responses and handles malformed JSON.

### Genre Endpoint

```text
POST /genre
```

This endpoint suggests a genre based on the supplied book title and description.

### Malformed Response Test

```text
GET /test-malformed-response
```

This endpoint is used to test handling of invalid LLM output.

---

# Week 4 Git Workflow

Week 4 included Git workflow practice using:

- Feature branches
- Pull requests
- Merge conflict resolution
- Branch protection
- Pull request review
- Conventional commit messages

A deliberate merge conflict was created and resolved using practice branches.

The Week 4 release tag is:

```text
v0.4-week4
```

---

# Week 5 — Embeddings, Vector Database and Manual RAG

Week 5 extends the Library Internship Project with semantic search and Retrieval-Augmented Generation (RAG).

The goal was to manually understand and implement the main stages of a RAG pipeline.

## Week 5 Features

The following features were implemented:

- Text embeddings
- Cosine similarity
- Local Sentence Transformer model
- Chroma vector database
- Manual RAG pipeline
- Document chunking
- Chunk overlap
- Semantic retrieval
- Context construction
- Grounded LLM generation
- Source attribution
- FastAPI `/ask` endpoint
- Real ASP.NET Core catalog integration
- Out-of-catalog question handling
- RAG evaluation
- Git revert practice

---

# Embeddings

Embeddings convert text into numerical vectors.

These vectors can be used to compare the semantic meaning of text.

The embedding demo is located in:

```text
ai-service/embed_demo.py
```

The project uses:

```text
sentence-transformers/all-MiniLM-L6-v2
```

The model generates:

```text
384-dimensional embeddings
```

## Cosine Similarity

Cosine similarity was used to compare embedding vectors.

Testing included:

- Similar sentences
- Unrelated sentences
- Sentences with similar words but opposite meaning

This demonstrated both the usefulness and limitations of semantic embeddings.

---

# Local Embedding Model

The original task referenced OpenAI embeddings.

A local and free Sentence Transformer model was used instead:

```text
sentence-transformers/all-MiniLM-L6-v2
```

This avoids paid embedding API usage while preserving the same semantic search and RAG concepts.

The basic flow is:

```text
Text
↓
Embedding model
↓
Vector
↓
Semantic comparison
```

---

# Chroma Vector Database

Chroma is used as the local vector database.

The Chroma demonstration is located in:

```text
ai-service/chroma_demo.py
```

The demo includes:

- Adding documents
- Vector storage
- Semantic search
- Metadata
- Metadata filtering

The real RAG pipeline stores metadata including:

- Book ID
- Title
- Author
- Source
- Chunk number

---

# Real Library Corpus

The RAG system uses real data from the existing ASP.NET Core backend.

The public Books API endpoint is:

```text
GET /api/Books
```

The Python corpus-fetching script is:

```text
ai-service/corpus_fetch.py
```

During testing, four real books were retrieved from the database:

- Advanced C#
- Persistent Library Book
- Angular API Book
- Angular Auth Test

The processed corpus is stored in:

```text
ai-service/library_corpus.json
```

Each book is transformed into a RAG-ready text document containing available information such as:

- Title
- Author
- Category
- Description

Where category information is unavailable, the record remains uncategorized instead of inventing data.

---

# Manual RAG Pipeline

The manual RAG implementation is located in:

```text
ai-service/rag_pipeline.py
```

The pipeline performs the following stages:

1. Load documents
2. Split documents into chunks
3. Generate embeddings
4. Store embeddings in Chroma
5. Embed the user's question
6. Retrieve semantically relevant chunks
7. Build the context prompt
8. Send the grounded prompt to the LLM
9. Generate the final answer
10. Return source information

## Chunking

The default chunking configuration is:

```text
Chunk size: 500
Overlap: 50
```

The pipeline validates chunk settings so invalid values such as:

```text
chunk_size = 0
```

cannot be used accidentally.

---

# Week 5 RAG Data Flow

The completed Week 5 data flow is:

```text
SQL Server
    ↓
ASP.NET Core GET /api/Books
    ↓
Python corpus_fetch.py
    ↓
library_corpus.json
    ↓
SentenceTransformer embeddings
    ↓
Chroma vector database
    ↓
Semantic retrieval
    ↓
FastAPI /ask
    ↓
OpenRouter LLM
    ↓
Grounded answer + sources
```

During Week 5 the integration is primarily:

```text
.NET API → Python AI service
```

The Angular frontend does not directly call the AI service during this stage.

---

# FastAPI `/ask` Endpoint

The AI service provides the RAG endpoint:

```text
POST /ask
```

Example request:

```json
{
  "question": "Who wrote Advanced C#?"
}
```

The question is embedded and used to retrieve relevant documents from Chroma.

The retrieved context is then supplied to the LLM.

Example response:

```json
{
  "answer": "Hajra Ali wrote Advanced C#.",
  "sources": [
    "Advanced C# — Hajra Ali (book_5.json)"
  ]
}
```

The exact number of sources can vary depending on the retrieved documents.

---

# Grounding Behaviour

The RAG prompt instructs the LLM to use only the supplied library context.

The LLM is instructed:

```text
Do not use outside knowledge.
Do not guess.
```

If the answer is not available in the context, the service responds with:

```text
I don't have that information.
```

and returns:

```json
{
  "sources": []
}
```

This helps prevent unsupported answers.

---

# Week 5 RAG Testing

The completed RAG pipeline was tested through FastAPI Swagger.

## Test 1

Question:

```text
Who wrote Advanced C#?
```

Correct result:

```text
Hajra Ali
```

Source information was returned from the real library corpus.

## Test 2

Question:

```text
What books are available in the library?
```

The service returned books from the real catalog.

## Test 3

Question:

```text
Who wrote Angular API Book?
```

Correct result:

```text
Hajra Ali
```

with source attribution.

## Test 4 — Out-of-Catalog Question

Question:

```text
What is the capital of Japan?
```

Since this information is not present in the library corpus, the system correctly returned:

```text
I don't have that information.
```

with:

```json
{
  "sources": []
}
```

This confirms the grounding behavior.

---

# RAG Evaluation

Week 5 RAG evaluation is documented in:

```text
ai-service/rag_evaluation.md
```

The evaluation checks:

- Whether the correct document was retrieved
- Whether the generated answer was correct
- Whether grounding was preserved

It also distinguishes between:

- Retrieval failure
- Generation failure

A retrieval failure means the correct information was not retrieved.

A generation failure means relevant information was retrieved but the final answer was still incorrect.

---

# Source Attribution

The final `/ask` endpoint returns human-readable source labels.

Example:

```text
Advanced C# — Hajra Ali (book_5.json)
```

Source labels contain:

- Book title
- Author
- Internal source identifier

Out-of-catalog refusals return an empty source list.

---

# Git Revert Practice

Week 5 included a dedicated Git revert exercise.

The practice branch was:

```text
practice/git-revert
```

A deliberately incorrect change was committed:

```text
chunk_size = 0
```

The incorrect commit was:

```text
chore: add incorrect chunk size for revert practice
```

It was then undone using:

```text
git revert
```

The history preserved the original commit and the revert commit:

```text
Revert "chore: add incorrect chunk size for revert practice"
```

This demonstrates safe rollback without rewriting existing Git history.

---

# Week 5 Git Workflow

The main Week 5 project branches were:

```text
feature/rag-corpus-fetch
feature/rag-pipeline
feature/ai-ask-endpoint
```

## `feature/rag-corpus-fetch`

Responsibilities:

- Fetch books from the ASP.NET Core API
- Convert book records into RAG-ready documents
- Generate `library_corpus.json`

## `feature/rag-pipeline`

Responsibilities:

- Load the real corpus
- Generate local embeddings
- Store documents in Chroma
- Perform semantic retrieval
- Connect retrieval to the manual RAG pipeline

## `feature/ai-ask-endpoint`

Responsibilities:

- Finalize the FastAPI `/ask` endpoint
- Add human-readable source labels
- Handle out-of-catalog questions
- Improve provider error handling
- Verify grounded answers against the real catalog

---

# Important AI Service Files

The AI service contains:

```text
ai-service/
├── chroma_demo.py
├── corpus_fetch.py
├── embed_demo.py
├── library_corpus.json
├── main.py
├── rag_demo.py
├── rag_evaluation.md
├── rag_pipeline.py
└── requirements.txt
```

## `embed_demo.py`

Demonstrates:

- Embeddings
- Vector size
- Cosine similarity
- Semantic similarity

## `chroma_demo.py`

Demonstrates:

- Chroma
- Vector storage
- Semantic retrieval
- Metadata filtering

## `corpus_fetch.py`

Fetches the real catalog from:

```text
GET /api/Books
```

and creates the RAG corpus.

## `library_corpus.json`

Contains the processed real library catalog.

## `rag_pipeline.py`

Contains the manual RAG pipeline.

## `rag_demo.py`

Demonstrates the manual RAG flow.

## `rag_evaluation.md`

Contains retrieval and generation evaluation results.

## `main.py`

Contains FastAPI endpoints including:

```text
/health
/summarize
/ask
/genre
```

---

# Running the FastAPI AI Service

Go to:

```text
E:\library-internship-project\ai-service
```

Activate the virtual environment:

```cmd
.venv\Scripts\activate
```

Start FastAPI:

```cmd
uvicorn main:app --reload
```

Open Swagger:

```text
http://127.0.0.1:8000/docs
```

---

# Running the Corpus Fetch

First start the ASP.NET Core backend.

Then from the AI service directory run:

```cmd
python corpus_fetch.py
```

The script fetches data from:

```text
https://localhost:7272/api/Books
```

and generates:

```text
library_corpus.json
```

---

# Environment Configuration

Secrets are stored locally in:

```text
ai-service/.env
```

The `.env` file is ignored by Git.

The FastAPI LLM integration uses:

```text
OPENROUTER_API_KEY
```

API keys and secrets must not be committed to the repository.

---

# Technology Stack

## Backend

```text
ASP.NET Core Web API
C#
Entity Framework Core
SQL Server
JWT Authentication
Swagger
```

## Frontend

```text
Angular
TypeScript
HTML
CSS
RxJS
```

## AI Service

```text
Python
FastAPI
Sentence Transformers
Chroma
OpenRouter
HTTPX
Pydantic
```

## AI Models

LLM:

```text
openai/gpt-4o-mini
```

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

---

# Git Workflow

The project follows a feature-branch workflow:

```text
main
 ↓
feature branch
 ↓
commit
 ↓
push
 ↓
pull request
 ↓
review / branch protection
 ↓
merge
 ↓
delete feature branch
```

Conventional commit messages are used.

Examples include:

```text
feat: add embedding and cosine similarity demo script

feat: add local Chroma vector database demo

feat: build manual RAG pipeline: chunk, embed, store, retrieve, generate

docs: add manual RAG evaluation results for 5 test questions

feat: add /ask endpoint wiring RAG pipeline into FastAPI service

feat: fetch real book catalog for RAG corpus

feat: connect real book corpus to Chroma RAG pipeline

feat: finalize grounded /ask endpoint with source labels
```

---

# Release Tags

Completed internship milestones are tagged in Git.

Existing tags include:

```text
v0.3-week3
v0.4-week4
```

The Week 5 release tag is:

```text
v0.5-week5
```

---

# Current Project Status

At the end of Week 5, the project includes:

- ASP.NET Core Library API
- SQL Server persistence
- JWT authentication
- Role-based authorization
- Angular authentication
- Protected frontend routes
- FastAPI AI service
- OpenRouter LLM integration
- Local text embeddings
- Chroma vector search
- Real catalog corpus generation
- Manual RAG pipeline
- Grounded `/ask` endpoint
- Source attribution
- Out-of-catalog refusal behavior
- Git revert practice
- Feature branch and pull request workflow

Week 5 prepares the project for the next stage of AI integration and Week 6 development.