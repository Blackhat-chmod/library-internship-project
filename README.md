Yes. Replace your entire `README.md` with the version below. I’ve kept your existing Week 4 and Week 5 documentation structure and extended it with the completed Week 6 work, rather than replacing the earlier material. :chatgpt-content-reference{index="0"} :chatgpt-content-reference{index="1"}

```markdown
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
- LangChain and LCEL
- Advanced retrieval
- Conversation memory
- LLM tool calling
- Resilient .NET to AI service integration
- End-to-end AI response streaming
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
- Book availability endpoint
- Typed AI service client
- Retry and circuit breaker policies
- AI streaming proxy

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
- AI Assistant page
- Live AI response streaming
- Streaming cancellation
- Source display

The JWT token is stored in `localStorage`.

The HTTP interceptor automatically attaches the JWT token to authenticated Angular HTTP requests.

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
POST /ask/stream
POST /genre
GET /test-malformed-response
```

FastAPI Swagger documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

# Week 4 - Authentication and AI Service

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

The configured model during the original Week 4 work was:

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

# Week 5 - Embeddings, Vector Database and Manual RAG

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
  ->
Embedding model
  ->
Vector
  ->
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

During testing, books retrieved from the database included:

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

The Week 5 manual RAG configuration uses:

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
    ->
ASP.NET Core GET /api/Books
    ->
Python corpus_fetch.py
    ->
library_corpus.json
    ->
SentenceTransformer embeddings
    ->
Chroma vector database
    ->
Semantic retrieval
    ->
FastAPI /ask
    ->
OpenRouter LLM
    ->
Grounded answer + sources
```

During Week 5 the integration is primarily:

```text
.NET API -> Python AI service
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
    "Advanced C# - Hajra Ali (book_5.json)"
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

## Test 4 - Out-of-Catalog Question

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
Advanced C# - Hajra Ali (book_5.json)
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

The incorrect commit was then undone using:

```text
git revert
```

The history preserved both the original commit and the revert commit.

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

# Week 5 Important AI Service Files

```text
ai-service/
|-- chroma_demo.py
|-- corpus_fetch.py
|-- embed_demo.py
|-- library_corpus.json
|-- main.py
|-- rag_demo.py
|-- rag_evaluation.md
|-- rag_pipeline.py
`-- requirements.txt
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
python -m uvicorn main:app --reload
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
Polly
IHttpClientFactory
```

## Frontend

```text
Angular
TypeScript
HTML
CSS
RxJS
Native Fetch API
ReadableStream
AbortController
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
LangChain
LCEL
```

## AI Models

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

LLM access is provided through OpenRouter.

Some Week 6 demonstrations use OpenRouter's free routing/model options depending on provider availability.

---

# Git Workflow

The project follows a feature-branch workflow:

```text
main
  ->
feature branch
  ->
commit
  ->
push
  ->
pull request
  ->
review
  ->
merge
  ->
delete feature branch
```

Conventional commit messages are used.

Examples include:

```text
feat: add embedding and cosine similarity demo script

feat: add local Chroma vector database demo

feat: build manual RAG pipeline: chunk, embed, store, retrieve, generate

feat: add /ask endpoint wiring RAG pipeline into FastAPI service

feat: fetch real book catalog for RAG corpus

feat: connect real book corpus to Chroma RAG pipeline

feat: finalize grounded /ask endpoint with source labels
```

---

# Week 6 - LangChain, Tool Calling, Resilience and Streaming

Week 6 extends the Library Internship Project from a manually implemented RAG system into a more production-shaped AI integration.

The main Week 6 areas include:

- LangChain Expression Language (LCEL)
- Advanced document splitting
- Multi-query retrieval
- Structured output integration
- Session-scoped conversation memory
- LLM tool calling
- Book availability API integration
- Resilient .NET to FastAPI communication
- Retry and exponential backoff
- Timeout handling
- Circuit breaker
- Graceful service failure
- Server-Sent Events (SSE)
- End-to-end AI response streaming
- Angular native fetch streaming
- Streaming cancellation
- Interactive Git rebase

---

# Week 6 LangChain RAG

The existing Week 5 RAG concepts were rebuilt using LangChain.

The LCEL demonstration is located in:

```text
ai-service/lcel_rag_demo.py
```

The chain uses LangChain runnable components to connect the RAG stages.

The flow is:

```text
User question
    ->
Input validation
    ->
Retriever
    ->
Context construction
    ->
Prompt
    ->
LLM
    ->
Output parser
    ->
Answer
```

A custom input guard rejects questions shorter than three characters.

Example:

```text
Question: a
```

Result:

```text
Question too short to answer meaningfully.
```

The LCEL implementation was tested successfully with a normal programming question and the short-question guard.

---

# Advanced Retrieval

Week 6 introduces more advanced LangChain retrieval techniques.

The demonstration is located in:

```text
ai-service/advanced_retrieval_demo.py
```

The implementation uses:

```text
RecursiveCharacterTextSplitter
```

with:

```text
Chunk size: 300
Chunk overlap: 40
```

The base retriever returns the top relevant chunks.

Week 6 also introduces:

```text
MultiQueryRetriever
```

MultiQueryRetriever asks the LLM to generate alternate versions of the user's question.

The alternate queries are then used to retrieve additional potentially relevant documents.

Testing compared normal retrieval and MultiQueryRetriever across five questions.

The tests demonstrated an important trade-off:

```text
Multi-query retrieval can improve recall,
but broader queries can also reduce precision.
```

For example, alternate queries sometimes retrieved additional relevant context, but they could also introduce unrelated books.

---

# Session-Scoped Conversation Memory

Week 6 introduces conversation memory using LangChain message history.

The demonstration is located in:

```text
ai-service/structured_memory_demo.py
```

The implementation uses:

```text
RunnableWithMessageHistory
```

with an in-memory session store.

A conversation using the same session can understand follow-up questions.

Example:

```text
User:
Tell me about Journey Beyond Earth.

User:
What genre is it?
```

The second question can use the previous conversation context.

A fresh session asking only:

```text
What genre is it?
```

does not have the previous book context.

## Memory Limitation

The Week 6 implementation uses in-memory conversation storage.

This has an important limitation:

```text
Conversation history is lost when the AI service process restarts.
```

A production implementation would normally use persistent storage such as a database or distributed cache.

---

# Structured Output

Week 6 includes LangChain structured-output integration using Pydantic.

The structured model contains fields such as:

```text
answer
confidence
sources
```

The implementation uses:

```text
with_structured_output(...)
```

Live structured-output verification was limited by the available free OpenRouter provider/model behavior during testing.

The integration code is present, but some free provider responses either reached rate limits or returned output that did not satisfy the requested JSON schema.

This limitation is documented instead of treating an unsuccessful provider response as a successful structured-output test.

---

# Book Availability Tool Calling

Week 6 introduces LLM tool calling.

A new availability field was added to the Book model:

```text
IsAvailable
```

The database schema was updated through an Entity Framework Core migration.

The public availability endpoint is:

```text
GET /api/Books/{id}/availability
```

Example response:

```json
{
  "bookId": 5,
  "title": "Advanced C#",
  "isAvailable": false
}
```

The LangChain tool-calling demonstration is located in:

```text
ai-service/availability_tool_demo.py
```

The tool is:

```text
check_book_availability
```

The language model decides whether the availability tool is required.

## Tool-Calling Tests

Availability question:

```text
Is book 5 available right now?
```

Result:

```text
Tool call detected.
```

The tool called the live ASP.NET Core availability endpoint and returned the real book availability status.

The tool result was then passed back to the model to generate a natural-language answer.

A non-availability question was also tested:

```text
What genre is book 5?
```

Result:

```text
Correct: no availability tool call was made.
```

This demonstrates that the tool is used only when the question requires availability information.

---

# Resilient .NET to AI Service Integration

Week 6 introduces a typed .NET HTTP client for communication with the FastAPI AI service.

The main files include:

```text
Services/IAiServiceClient.cs
Services/AiServiceClient.cs
Controllers/AssistantController.cs
```

The .NET endpoint is:

```text
POST /api/Assistant/ask
```

The communication flow is:

```text
Angular / Swagger
    ->
ASP.NET Core
    ->
IAiServiceClient
    ->
AiServiceClient
    ->
FastAPI /ask
    ->
RAG / LLM
    ->
ASP.NET Core response
```

The HTTP client is created through:

```text
IHttpClientFactory
```

The implementation includes:

- Retry
- Exponential backoff
- Timeout
- Circuit breaker
- Graceful service-unavailable responses

---

# Retry and Exponential Backoff

When the FastAPI service is unavailable, the .NET client automatically retries.

The configured retry delays include:

```text
2 seconds
4 seconds
8 seconds
```

Testing with FastAPI deliberately stopped showed retry messages such as:

```text
AI retry 1 after 2 seconds.
AI retry 2 after 4 seconds.
AI retry 3 after 8 seconds.
```

This prevents temporary connection failures from immediately causing the request to fail.

---

# Circuit Breaker

Repeated AI-service failures cause the circuit breaker to open.

During testing, the application logged:

```text
AI circuit opened for 30 seconds.
```

While the circuit is open, additional calls fail quickly rather than repeatedly attempting to contact an unavailable AI service.

The controller handles the open circuit and returns a graceful response instead of crashing.

Example HTTP status:

```text
503 Service Unavailable
```

Example response:

```json
{
  "message": "The AI assistant is temporarily unavailable. Please try again shortly."
}
```

This demonstrates resilient behavior when the Python AI service is offline.

---

# End-to-End AI Streaming

Week 6 adds real end-to-end streaming.

The completed streaming path is:

```text
OpenRouter LLM
    ->
FastAPI
    ->
.NET streaming proxy
    ->
Angular
    ->
Live answer in browser
```

The FastAPI streaming endpoint is:

```text
POST /ask/stream
```

The .NET streaming proxy is:

```text
POST /api/assistant/ask/stream
```

---

# FastAPI Streaming

The streaming helper is located in:

```text
ai-service/streaming_rag.py
```

The OpenRouter request uses:

```json
{
  "stream": true
}
```

This means the system receives real model-generated chunks instead of waiting for the entire answer before returning it.

FastAPI returns the stream using:

```text
text/event-stream
```

The SSE events include:

```text
token
sources
done
error
```

Example:

```text
data: {"type": "token", "content": "Advanced"}

data: {"type": "token", "content": " C#"}

data: {"type": "sources", "sources": [...]}

data: {"type": "done", "completed": true}
```

Direct FastAPI streaming was verified using:

```cmd
curl.exe -N
```

The individual model chunks appeared progressively in the terminal.

---

# .NET Streaming Proxy

The .NET streaming controller is:

```text
Controllers/AssistantStreamController.cs
```

The proxy calls FastAPI using:

```text
HttpCompletionOption.ResponseHeadersRead
```

This allows the .NET application to begin processing the response before the entire FastAPI response has completed.

The proxy forwards:

```text
Content-Type: text/event-stream
```

and disables unnecessary buffering.

A key operation is:

```text
Response.Body.FlushAsync(...)
```

This explicitly flushes complete SSE events to the downstream client.

Authenticated streaming through the .NET proxy was verified using curl.

The response included:

```text
HTTP/1.1 200 OK
Content-Type: text/event-stream
Transfer-Encoding: chunked
X-Accel-Buffering: no
```

and token events arrived progressively.

---

# FlushAsync Experiment

As part of Week 6 testing, the explicit:

```text
FlushAsync()
```

operation was temporarily removed from the .NET streaming proxy.

The streaming path was tested without it and then the explicit flush logic was restored.

Local development servers and browsers can sometimes flush buffered data automatically, so the visible difference can vary between environments.

The final implementation keeps:

```text
Response.Body.FlushAsync(...)
```

because explicit flushing provides more reliable immediate delivery of SSE events.

---

# Angular Streaming Chat UI

A new Angular AI Assistant interface was added.

The main files are:

```text
frontend/library-angular/src/app/assistant-chat/
|-- assistant-chat.ts
|-- assistant-chat.html
`-- assistant-chat.css
```

The route is:

```text
/assistant
```

The page is protected using the existing Angular authentication guard.

The interface provides:

- Question input
- Ask AI button
- Live streamed answer
- Streaming indicator
- Stop button
- Clear button
- Source display
- Error display

---

# Angular Native Fetch Streaming

Angular uses the browser's native:

```text
fetch()
```

API for streaming.

The response stream is read using:

```text
response.body.getReader()
```

and decoded progressively using:

```text
TextDecoder
```

Because native `fetch()` does not pass through the Angular HTTP interceptor, the JWT token is manually added:

```text
Authorization: Bearer <JWT>
```

The UI appends each incoming token to the current answer so users can see the answer being generated in real time.

---

# Angular Streaming Change Detection

During initial testing, tokens were reaching the browser but the Angular interface was not repainting after every chunk.

The accumulated answer became visible only after another UI event occurred.

This was resolved by triggering Angular change detection after streamed events.

The final result displays the answer progressively while the stream is active.

---

# Streaming Cancellation

The Angular streaming interface supports cancellation using:

```text
AbortController
```

When the user presses:

```text
Stop
```

the active fetch request is cancelled.

The interface displays:

```text
Streaming was cancelled.
```

The cancellation flow was successfully tested.

---

# Week 6 End-to-End Streaming Flow

The final streaming architecture is:

```text
User question
    ->
Angular AI Assistant
    ->
Native fetch + JWT
    ->
POST /api/assistant/ask/stream
    ->
ASP.NET Core streaming proxy
    ->
POST /ask/stream
    ->
FastAPI RAG retrieval
    ->
OpenRouter stream=true
    ->
SSE token events
    ->
.NET FlushAsync()
    ->
Angular ReadableStream
    ->
Live answer in browser
```

---

# Week 6 Git Workflow

Week 6 used the following main feature branches:

```text
feature/langchain-rag-chain
feature/availability-tool
feature/resilient-ai-client
feature/streaming-chat-ui
```

Each major feature was developed independently and merged through a pull request.

The Week 6 pull requests were:

```text
#20 LangChain RAG
#21 Book Availability Tool
#22 Resilient AI Client
#23 End-to-End Streaming
```

---

# Interactive Rebase Practice

Week 6 included interactive rebase practice.

A temporary branch was created:

```text
practice/interactive-rebase
```

Five deliberately small commits were created.

Interactive rebase was used to squash them into one clean commit:

```text
chore: complete interactive rebase practice
```

This demonstrated how several messy commits can be cleaned before creating a pull request.

---

# Interactive Rebase on a Real Feature Branch

Interactive rebase was also applied to the real:

```text
feature/langchain-rag-chain
```

branch before its pull request.

The original Part A, Part B and Part C commits were squashed into:

```text
feat: build advanced LangChain RAG chain with retrieval and memory
```

The rewritten branch was updated using:

```cmd
git push --force-with-lease
```

This demonstrates safe history rewriting on a feature branch without rebasing the shared `main` branch.

The streaming branch was also rebased onto the latest `main` before its final pull request so that the resilience and streaming changes could be combined cleanly.

---

# Week 6 Known Limitations

The current Week 6 implementation has the following known limitations:

1. Conversation memory is stored in memory and is lost when FastAPI restarts.

2. Live structured-output verification depends on the capabilities and availability of free OpenRouter models. During testing, some free providers were rate-limited or did not return the requested structured schema.

3. The local development setup uses separate FastAPI, ASP.NET Core and Angular processes.

4. The streaming implementation is designed for the internship development environment and has not yet been deployed behind a production reverse proxy.

5. Retrieval quality depends on the available library corpus. If relevant information is not present in the corpus, the assistant may correctly respond that it does not have the information.

---

# Week 6 Important Files

```text
ai-service/
|-- advanced_retrieval_demo.py
|-- availability_tool_demo.py
|-- lcel_rag_demo.py
|-- main.py
|-- streaming_rag.py
`-- structured_memory_demo.py

backend/LibraryApi/LibraryApi/
|-- Controllers/
|   |-- AssistantController.cs
|   `-- AssistantStreamController.cs
|-- Models/
|   |-- AiAskResponse.cs
|   `-- AskDto.cs
|-- Services/
|   |-- AiServiceClient.cs
|   `-- IAiServiceClient.cs
`-- Program.cs

frontend/library-angular/src/app/
`-- assistant-chat/
    |-- assistant-chat.ts
    |-- assistant-chat.html
    `-- assistant-chat.css
```

---

# Release Tags

Completed internship milestones are tagged in Git.

Existing tags include:

```text
v0.3-week3
v0.4-week4
v0.5-week5
```

After the final Week 6 documentation commit is complete, the Week 6 release is tagged as:

```text
v0.6-week6
```

---

# Current Project Status

At the end of Week 6, the project includes:

- ASP.NET Core Library API
- SQL Server persistence
- JWT authentication
- Role-based authorization
- Angular authentication
- Protected frontend routes
- FastAPI AI service
- OpenRouter LLM integration
- Local Sentence Transformer embeddings
- Chroma vector search
- Real catalog corpus generation
- Manual RAG pipeline
- Grounded `/ask` endpoint
- Source attribution
- LCEL-based RAG demonstrations
- Recursive document splitting
- Multi-query retrieval
- Session-scoped conversation memory
- Structured-output integration
- LLM tool calling
- Live book availability lookup
- Typed .NET AI service client
- Retry with exponential backoff
- Timeout handling
- Circuit breaker
- Graceful `503` responses
- FastAPI SSE streaming
- .NET streaming proxy
- Angular AI Assistant
- Live token-by-token rendering
- JWT-authenticated streaming
- Streaming cancellation
- Git revert practice
- Interactive rebase practice
- Interactive rebase on a real feature branch
- Feature branch and pull request workflow

Week 6 moves the project from a manually implemented RAG prototype toward a more resilient, interactive and production-shaped AI-enabled application.
```

