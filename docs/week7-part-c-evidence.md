# Week 7 Part C - Router, Planning, Re-planning and Retry Evidence

## Overview

Part C extends the Week 7 LangGraph agent with:

- Structured routing
- Catalog RAG subgraph
- Explicit planning
- Action execution
- Conflict re-planning
- Typed retry handling
- Authentication failure handling
- Retry limits and backoff
- Router prompt evaluation and improvement

---

## 1. Structured Router

The router uses structured output with a Pydantic model and a Literal route field.

Valid routes are:

- `catalog`
- `action`
- `chitchat`

The router therefore produces only valid route names.

### Router Evaluation

The router was tested against 15 handwritten messages:

- 5 catalog messages
- 5 action messages
- 5 chitchat messages

Final result:

```text
CORRECT: 15/15
ACCURACY: 100.0%
MISSES: 0
This confirms that the improved router prompt correctly handled all 15 evaluation messages.
2. Catalog RAG Subgraph
The Week 6 retrieval pipeline was reused inside a compiled LangGraph subgraph.
The main Part C graph contains the compiled catalog subgraph as its catalog node.
Test message:
Tell me about Advanced C#.

Observed result:
ROUTE: catalog
STATUS: catalog_complete

The retrieval result included:
Book ID 5: Advanced C# by Hajra Ali

This demonstrates reuse of the Week 6 RAG retrieval functionality inside the larger Week 7 graph.
3. Plan-Then-Execute Workflow
For an action request, the planner writes an explicit ordered list of steps into graph state before executing the reservation.
Example request:
Reserve book 15 for me.

The generated plan included:
1. Identify book 15 as the requested reservation target.
2. Use the authenticated reservation tool without storing the JWT in graph state.
3. Inspect the reservation result for success, conflict, authentication failure, or a transient failure.
4. Finish on success, re-plan after a conflict, or retry a transient failure at most twice.
The plan is stored as a list in graph state rather than being implicit in the execution code.
4. Challenge 1 - Conflict and Re-planning
Book 15 was deliberately used as an already-reserved target.
Observed result:
USER:    Reserve book 15 for me.
ROUTE:   action
STATUS:  replanned_with_alternative
BOOK ID: 15
HTTP:    409
RETRIES: 0
REPLANS: 1

The graph detected the HTTP 409 conflict and followed the re-plan edge instead of retrying the same write.
The re-planned steps were:
1. Record that book 15 returned a reservation conflict.
2. Search the library catalog for another explicitly available book.
3. Select Book 16, Week 7 Alternative Book, as an available alternative.
4. Offer the alternative to the user without reserving it automatically.
Observed final answer:
Book 15 cannot currently be reserved. I searched the catalog
and found another available option: Book 16,
Week 7 Alternative Book by Hajra Ali. I have not reserved
the alternative automatically.

This demonstrates:
User action request
        |
        v
Reservation attempt
        |
        v
HTTP 409 Conflict
        |
        v
Re-plan
        |
        v
Search catalog
        |
        v
Find another available book
        |
        v
Offer alternative to user

The alternative was not automatically reserved because that would perform a new write without user approval.
5. Authentication Failure
The action workflow was also tested using an expired authentication token.
Observed result:
STATUS: action_auth_failure
HTTP: 401
RETRIES: 0

The graph stopped immediately instead of retrying an authentication failure.
This demonstrates that authentication errors are treated differently from transient infrastructure failures.
6. Challenge 2 - Transient Failure Then Success
A controlled backend retry demonstration was added for testing the transient-failure workflow.
The backend returned HTTP 503 for the first two attempts and then allowed the third attempt to continue normally.
Observed output:
Transient failure: retry 1/2 after 1s backoff.
Transient failure: retry 2/2 after 2s backoff.

STATUS: action_success
HTTP: 200
RETRIES: 2
REPLANS: 0
ANSWER: Book 16 was reserved successfully.

This demonstrates:
Attempt 1 -> transient failure
Retry 1  -> transient failure
Retry 2  -> success

The retry counter correctly reached 2.
7. Challenge 2 - Retry Limit
A persistent transient-failure mode was also tested.
The backend returned HTTP 503 on every attempt.
Observed output:
Transient failure: retry 1/2 after 1s backoff.
Transient failure: retry 2/2 after 2s backoff.

STATUS: action_transient_failure
HTTP: 503
RETRIES: 2
RESULT: transient_failure
ANSWER: The Library API is temporarily unavailable.

The workflow therefore performed:
Attempt 1 -> HTTP 503
Retry 1
Attempt 2 -> HTTP 503
Retry 2
Attempt 3 -> HTTP 503
STOP

The third failure did not create another retry because the configured retry limit had already been reached.
The user received a clear final message:
The Library API is temporarily unavailable.

8. Why Retrying the Write Is Safe
Reservation retries reuse the same idempotency key.
This is important because a client may experience a timeout or transient failure even when the original write reached the server.
Without idempotency, retrying the write could create duplicate reservations.
With the Part B idempotency mechanism, repeated requests using the same idempotency key can safely replay the original result instead of creating a duplicate write.
The JWT remains in runtime configuration and is not stored in LangGraph state.
9. Typed Retry Decisions
The workflow distinguishes between different failure categories.
Conflict
HTTP 409
-> re-plan

Authentication / Authorization Failure
HTTP 401 / 403
-> stop

Transient Failure
Handled transient status codes include:
408
429
500
502
503
504

Behavior:
transient failure
-> retry with backoff
-> maximum 2 retries
-> stop after third failed attempt

Other failures terminate normally without incorrectly entering the retry loop.
10. Challenge 3 - Router Misroute
A realistic ambiguous message was tested:
Is Dune any good?

Expected route:
catalog

With the baseline prompt, the actual result was:
ACTUAL: chitchat
RESULT: MISROUTE

Reason returned by the model:
The user is asking for an opinion/recommendation about a book,
which falls under casual conversation and recommendations.

This demonstrated a realistic ambiguity between catalog questions and conversational opinion questions.
11. Challenge 3 - General Prompt Improvement
The router prompt was improved.
The fix did not special-case the message or the title "Dune".
Instead, the prompt introduced a general routing rule:
- Questions evaluating a specific book belong to catalog.
- Book recommendations belong to catalog.
- Opinions about books belong to catalog.
- chitchat is for casual discussion that is not primarily about a book or library catalog information.
The same message was tested again:
Is Dune any good?

Observed result:
EXPECTED: catalog
ACTUAL:   catalog
RESULT:   CORRECT

Challenge summary:
Before improvement: chitchat
After improvement:  catalog
DEMONSTRATION: PASS

The improvement generalizes to other book evaluation and recommendation questions rather than matching one specific test message.
12. Part C Result
Part C successfully demonstrates:
- Structured router output
- 15-message router evaluation
- 100% final router accuracy on the evaluation set
- Week 6 RAG reuse through a compiled subgraph
- Explicit plan stored in graph state
- Action execution
- HTTP 409 conflict detection
- Re-planning after conflict
- Alternative book search
- Authentication failure termination
- Typed transient-failure handling
- Backoff
- Maximum retry count
- Third-failure termination
- Idempotent write retries
- Realistic router misroute analysis
- Generalized router prompt improvement
Part C implementation and required challenge demonstrations are complete.