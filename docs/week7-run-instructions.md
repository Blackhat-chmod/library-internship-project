
# Week 7 - Run Instructions and Verification

## 1. Project Components

The Library Internship Project contains three main applications:

- ASP.NET Core Web API backend
- Angular frontend
- FastAPI AI service with LangGraph agent functionality

The backend uses SQL Server for library data. The AI service uses OpenRouter for LLM integration.

## 2. Prerequisites

Install and configure:

- .NET 10 SDK
- Node.js 22 and npm
- Python 3.13
- SQL Server
- Git

These versions match the Week 7 CI environment. Other compatible versions may work but have not been verified here.

## 3. Repository Setup

Clone the repository:

    git clone https://github.com/Blackhat-chmod/library-internship-project.git

Open the project:

    cd library-internship-project

Keep API keys, JWT secrets, and service credentials out of Git.

## 4. ASP.NET Core Backend

Backend location:

    backend/LibraryApi/LibraryApi/

The backend requires a valid SQL Server connection string and the application's authentication configuration.

From the backend directory:

    dotnet restore
    dotnet build
    dotnet run

The local development configuration previously used:

    https://localhost:7272

The actual URL may differ depending on launch settings.

## 5. FastAPI AI Service

AI service location:

    ai-service/

From the AI service directory:

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt

Configure the required environment variables locally, including:

    OPENROUTER_API_KEY

Use the project's existing environment configuration for backend URLs and service authentication. Do not commit the .env file.

Start FastAPI:

    python -m uvicorn main:app --reload

FastAPI Swagger is normally available at:

    http://127.0.0.1:8000/docs

## 6. Angular Frontend

Frontend location:

    frontend/library-angular/

From the frontend directory:

    npm ci
    npm start

Open the local URL displayed by Angular.

Sign in using an authorized test account.

## 7. Week 7 Agent Features

Week 7 adds:

- LangGraph agent execution
- Tool routing
- Agent state and checkpoint management
- Reservation-related actions
- Human approval workflow
- Agent run history and timeline
- Ownership checks and rate limiting

Some features are implemented and covered by automated tests but have not been verified through a complete live browser-to-backend-to-AI-service workflow.

## 8. Automated Verification

### Python Tests

From the ai-service directory:

    python -m pytest tests/test_week7_agent.py -v

Previously verified: 21 tests passing.

### .NET Tests

Run the project's .NET test suite using the solution or test project configured in the repository.

Previously verified: 10 tests passing.

### Angular Build

From frontend/library-angular:

    npm run build

Previously verified: build passing.

### GitHub Actions

Workflow:

    .github/workflows/ci.yml

The pipeline contains:

1. .NET build and tests
2. Angular build
3. Python tests

Pull Request #25 passed the CI checks and was merged.

Pull Request #26 demonstrated a deliberately failing Python test and was closed without merging.

## 9. Known Limitations

- Live FastAPI-to-.NET agent integration encountered an approximately 60-second timeout.
- The complete live human-approval flow remains unverified.
- External LLM rate limits and availability may affect agent responses.
- Local development requires three application processes.
- Production deployment and monitoring have not been completed.
- Previously exposed service credentials must be rotated before production use.

## 10. Security Notes

- Never commit API keys or JWT secrets.
- Use authorized test accounts only.
- Do not expose local development endpoints publicly.
- Verify ownership before accessing agent runs.
- Require approval before executing sensitive actions.
- Treat LLM-generated content and tool arguments as untrusted.

See:

- docs/week7-threat-model.md
- docs/week7-red-team-report.md
- docs/week7-tool-risk-table.md

## 11. Final Release Checklist

- [x] Week 7 agent implementation
- [x] Agent security and ownership tests
- [x] Python test suite verified
- [x] .NET test suite verified
- [x] Angular build verified
- [x] Three-job GitHub Actions CI
- [x] Passing CI pull request
- [x] Deliberately failing CI pull request
- [x] Interactive rebase practice
- [x] Git bisect practice
- [x] README Week 7 documentation
- [x] Threat model
- [ ] Documentation committed and merged
- [ ] Final release tag created
- [ ] Exposed credential rotated
- [ ] Live agent approval integration verified

## 12. Release

Planned annotated Git tag:

    v0.7-week7

Create this tag only after the documentation pull request is merged and final checks are complete.
