# Week 7 Tool Risk Table

## Purpose

This document classifies the Library AI agent tools by risk level and defines when human approval and retries are allowed.

Human approval is required before write, cost-bearing, or irreversible actions. Read-only operations do not require approval because they do not modify library or user data.

| Tool | Operation | Read / Write | Human Approval | Idempotent | Retryable | Reason |
|---|---|---|---|---|---|---|
| `search_catalog` | Searches the library catalog using a user query. | Read | No | Yes | Yes | It only retrieves catalog information and does not modify data. |
| `check_availability` | Checks whether a named book is currently available. | Read | No | Yes | Yes | It is a read-only availability lookup with no persistent side effect. |
| `check_book_availability` | Checks current availability for a specific book ID. | Read | No | Yes | Yes | It reads availability information and does not change library state. |
| `reserve_book` | Creates a reservation for the authenticated user. | Write | Yes | Yes, when the same `Idempotency-Key` is reused | Yes, only for transient failures and with the same idempotency key | It changes persistent reservation data, so the exact tool name and arguments must be approved before execution. |
| `failing_library_tool` | Deliberately raises an error for the Part A failure experiment. | Test-only | No | N/A | No in production | This is an artificial demonstration tool and is not a production library operation. |

## Approval Policy

Read-only tools do not require human approval because they cannot create, update, or delete persistent library data.

`reserve_book` requires approval because it performs a write. Before execution, the Part D LangGraph workflow pauses with `interrupt()` and shows the human the exact action:

- Tool: `reserve_book`
- Arguments: the exact `book_id`

Approval is therefore bound to the specific action the user sees. Approval for one book does not authorize a different reservation.

If a reservation conflict causes the graph to propose another book, the alternative is not automatically reserved. A different write would require a new approval.

## Retry Policy

Read-only operations may be retried after transient failures because repeating a read does not create duplicate writes.

`reserve_book` may be retried only for transient failures such as HTTP 408, 429, 500, 502, 503, or 504, and the same `Idempotency-Key` must be reused. The backend idempotency protection makes the retry safe against duplicate reservation creation.

HTTP 409 conflicts are not blindly retried. They trigger the re-plan path.

HTTP 401 or 403 authentication/authorization failures stop the action and are not retried.

A human rejection also stops the write and must never be automatically retried.

## Security Notes

The authenticated user's JWT is never placed in graph state.

For the persistent Part D workflow, secrets are also excluded from checkpointed LangGraph configuration. The reservation write node obtains the JWT from ephemeral process runtime configuration and passes it directly to the reservation tool.

The SQLite checkpoint database was inspected after an authenticated approved action. Neither the JWT nor the OpenRouter API key was present in the checkpoint file.