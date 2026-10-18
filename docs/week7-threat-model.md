
# Week 7 - Security Threat Model

## 1. System Overview

The Library Internship Project integrates an Angular frontend, ASP.NET Core API, FastAPI AI service, LangGraph agent, library tools, and SQL Server database.

The agent can process user requests and interact with library information and reservation-related operations.

## 2. Assets to Protect

- User accounts and JWT tokens
- Library and reservation records
- Agent execution state and checkpoints
- API keys and service credentials
- Approval decisions
- Agent run history

## 3. Trust Boundaries

1. Browser to ASP.NET Core API
2. ASP.NET Core API to FastAPI
3. LangGraph agent to library tools
4. Library API to SQL Server
5. User approval interface to protected actions

## 4. Threats and Mitigations

| Threat | Risk | Mitigation |
|---|---|---|
| Prompt injection | Malicious text influences agent behavior | Restrict tool access and validate actions |
| Unauthorized access | User accesses another user's agent run | JWT authentication and ownership checks |
| Unauthorized reservation | Agent performs a sensitive action without consent | Human approval before execution |
| Malicious tool arguments | Invalid or dangerous parameters reach APIs | Schema and argument validation |
| Excessive requests | Service overload or resource exhaustion | Rate limiting and execution limits |
| Credential exposure | Attackers obtain service secrets | Environment-based secrets and credential rotation |
| Replay or duplicate action | Reservation action executes more than once | Approval-state validation and idempotency safeguards |
| External service failure | Agent workflow becomes unavailable | Timeouts, retries, and graceful error handling |
| Sensitive information leakage | Agent reveals protected user information | Authorization checks and restricted tool responses |

## 5. Human-in-the-Loop Security

Sensitive agent actions should require explicit user approval.

The approval mechanism should verify:

- The authenticated user's identity
- Ownership of the agent run
- The pending action and its parameters
- The current approval state

Approval should not allow unrelated users to execute another user's actions.

## 6. Testing and Evidence

Week 7 security testing includes:

- Ownership and authorization tests
- Tool argument validation tests
- Prompt-injection and red-team scenarios
- Rate-limiting checks
- Approval workflow tests

Related documents:

- `week7-red-team-report.md`
- `week7-tool-risk-table.md`
- `week7-eval-report.md`

## 7. Residual Risks and Limitations

- The live FastAPI-to-.NET approval integration encountered a timeout and was not fully verified end-to-end.
- LLM outputs remain untrusted and require application-level validation.
- External LLM availability and rate limits can interrupt workflows.
- Production deployment requires additional monitoring, secret management, and security review.
- A previously exposed service credential requires rotation before production use.

## 8. Conclusion

Week 7 introduces multiple security controls around AI-agent execution. Automated testing provides evidence for individual safeguards, but production readiness and full live approval integration remain unverified.
