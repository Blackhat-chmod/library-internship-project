# Library Internship Project

This repository contains the Library Management project developed during the AI Software Development Internship.

The project began in Week 2 with an ASP.NET Core Web API and Angular frontend. In Week 3 it will be extended with SQL Server, Entity Framework Core, live Angular API integration, Git/GitHub workflow, and a standalone AI/Python script.

## Tech Stack

### Backend
- C#
- ASP.NET Core Web API
- Swagger
- Entity Framework Core
- SQL Server

### Frontend
- Angular
- TypeScript
- Reactive Forms
- Angular Router
- HttpClient

### AI Track
- Python
- Virtual Environment
- LLM API

### Tools
- Visual Studio
- Visual Studio Code
- Git
- GitHub
- Postman

## Project Structure

library-internship-project/
- backend/LibraryApi
- frontend/library-angular
- sql
- docs
- ai-scripts

## Backend Architecture

Controller -> Service -> Repository -> Data Store

## Run Backend

Open the ASP.NET Core project inside:

backend/LibraryApi

Run it using Visual Studio.

Swagger can then be used to test the API.

## Run Frontend

Open a terminal inside:

frontend/library-angular

Install dependencies if required:

npm install

Run:

ng serve

Open:

http://localhost:4200

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/Books | Get all books |
| GET | /api/Books/{id} | Get book by ID |
| POST | /api/Books | Add a book |
| PUT | /api/Books/{id} | Update a book |
| DELETE | /api/Books/{id} | Delete a book |

## Week 3 Goals

- Design relational database structure
- Configure SQL Server
- Add Entity Framework Core
- Replace in-memory storage with database storage
- Connect Angular to the live API
- Add loading and error handling
- Practice feature branches and Pull Requests
- Build the first standalone Python AI script