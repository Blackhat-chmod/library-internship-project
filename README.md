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