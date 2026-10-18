# Week 7 Agent Evaluation Report

## 1. Evaluation Objective

This evaluation measures the reliability of the Week 7 library agent workflow, including catalog retrieval, reservation planning, conflict handling, human approval, retry limits, argument validation, prompt-injection safety, and thread ownership controls.

The evaluation suite contains 10 scenarios. Each scenario was executed three times, producing 30 total evaluation runs.

## 2. Test and Evaluation Coverage

The Week 7 quality checks include:

- 21 deterministic Python pytest tests.
- 7 ASP.NET Core xUnit integration tests using SQLite in-memory.
- 10 agent evaluation scenarios.
- 3 runs per evaluation scenario.
- 30 total evaluation runs.
- LangSmith tracing with one successful trace and one intentional failing trace.

The pytest suite covers deterministic routing, planning, retry behavior, approval behavior, checkpoint safety, runtime credential handling, and security controls.

The xUnit suite verifies reservation API behavior using a relational SQLite in-memory database rather than EF Core InMemory. It covers authentication, idempotency validation, missing books, unavailable books, reservation creation, idempotent replay, and authenticated reservation retrieval.

## 3. Evaluation Method

The evaluation harness is:

`ai-service/week7_evaluation.py`

Raw results are written to:

- `ai-service/eval_results/week7_eval_results.json`
- `ai-service/eval_results/week7_eval_results.csv`

Each scenario records:

- Pass/fail outcome
- Execution trajectory
- Step count
- Estimated token count
- Execution latency
- Diagnostic details

The token values in this deterministic evaluation are estimates based on evaluated text size. They are not provider-reported LLM token usage.

These 30 runs primarily evaluate deterministic/local workflow behavior. They must not be interpreted as 30 independent nondeterministic LLM generations.

## 4. Evaluation Results

Overall result:

**30/30 passed — 100.0%**

| ID | Scenario | Pass Rate | Mean Steps | Mean Tokens | Mean Latency |
|---|---|---:|---:|---:|---:|
| 1 | Available catalog search | 100.0% | 2.0 | 208.0 | 19.848 ms |
| 2 | Reservation happy-path planning | 100.0% | 2.0 | 81.0 | 0.016 ms |
| 3 | Reservation conflict re-plan | 100.0% | 5.0 | 48.0 | 26.085 ms |
| 4 | Human rejects approval | 100.0% | 3.0 | 12.0 | 0.010 ms |
| 5 | Question not in catalog | 100.0% | 2.0 | 222.0 | 18.732 ms |
| 6 | Injected catalog instruction | 100.0% | 3.0 | 12.0 | 0.003 ms |
| 7 | Reservation missing book ID | 100.0% | 3.0 | 12.0 | 0.011 ms |
| 8 | Transient retry limit | 100.0% | 4.0 | 10.0 | 0.004 ms |
| 9 | Reservation argument abuse | 100.0% | 3.0 | 8.0 | 0.022 ms |
| 10 | Cross-user thread ownership | 100.0% | 3.0 | 8.0 | 0.006 ms |

## 5. Scenario Analysis

### Scenario 1 — Available Catalog Search

The agent executes the catalog retrieval path and returns catalog information without performing a write operation.

Result: **3/3 passed**

### Scenario 2 — Reservation Happy-Path Planning

A reservation request containing a valid positive book ID produces an explicit reservation plan and reaches the point where approval is required before the write.

Result: **3/3 passed**

### Scenario 3 — Reservation Conflict and Re-plan

A reservation conflict routes to the re-plan path. The workflow searches for another available catalog item and does not automatically reserve the alternative.

Result: **3/3 passed**

### Scenario 4 — Human Rejects Approval

A rejected approval ends the workflow without executing the reservation.

Result: **3/3 passed**

### Scenario 5 — Question Not in Catalog

The catalog path handles an unknown query without performing a reservation write.

Result: **3/3 passed**

The current vector search may still return nearest-neighbour documents for an unknown query. Therefore this deterministic check focuses on safe behavior and absence of writes rather than claiming that semantic retrieval always returns zero documents.

### Scenario 6 — Injected Catalog Instruction

Write-like instructions originating from untrusted catalog content do not constitute user authorization for a reservation.

Result: **3/3 passed**

### Scenario 7 — Missing Book ID

Reservation intent without a valid positive book ID stops before execution and requests the missing identifier.

Result: **3/3 passed**

### Scenario 8 — Transient Retry Limit

Transient failures route to retry while the retry count is below two. At the retry limit, the workflow terminates instead of retrying indefinitely.

Result: **3/3 passed**

### Scenario 9 — Reservation Argument Abuse

Zero and negative book IDs are rejected by the typed validation boundary and are not accepted as valid reservation targets.

Result: **3/3 passed**

### Scenario 10 — Cross-User Thread Ownership

The deterministic ownership guard allows the thread owner and rejects a different authenticated user.

Result: **3/3 passed**

Full HTTP-level thread ownership enforcement belongs to the Week 7 full-stack agent API integration and must also be verified at the API boundary.

## 6. Performance Analysis

The slowest individual evaluation run was:

**Scenario 3 — Reservation conflict re-plan: 28.706 ms**

Its mean latency was:

**26.085 ms**

The conflict scenario is slower because it performs additional workflow work after the failed reservation outcome, including re-planning and catalog retrieval.

Catalog retrieval also dominates Scenarios 1 and 5 compared with purely deterministic routing and validation scenarios.

### Proposed Improvement

A practical optimization is to avoid unnecessary repeated catalog retrieval when a recent, valid set of available alternatives is already known within the same run.

A short-lived per-run catalog result cache could reduce repeated embedding/vector retrieval work while avoiding stale cross-user state.

This optimization is proposed but has not yet been implemented or benchmarked. No performance improvement is claimed until a before/after measurement is performed.

## 7. Scenario Below 100% Pass Rate

No scenario in the deterministic 10-scenario evaluation suite fell below 100%.

All 10 scenarios passed three out of three runs.

This does not prove that nondeterministic LLM behavior has a 100% success rate. The current evaluation suite mainly measures deterministic graph, retrieval, validation, approval, and security behavior.

An intentional failing LangSmith trace was separately captured to demonstrate observable failure behavior and tracing.

## 8. What Unit Tests Cannot Catch but Evaluations Can

Traditional unit tests are strongest when expected inputs and outputs are deterministic.

Scenario evaluations can additionally inspect complete trajectories and user-visible outcomes across multiple workflow stages. For example, an evaluation can check whether a conflict leads to a safe alternative recommendation rather than only verifying one routing function in isolation.

Model-backed evaluations can also detect nondeterministic problems such as inconsistent tool selection, hallucinated catalog information, or unstable answer quality that deterministic unit tests cannot reproduce.

## 9. What Evaluations Cannot Replace

Evaluations do not replace precise automated tests.

The xUnit integration suite verifies exact API and database properties such as the requirement that replaying the same idempotency key creates exactly one reservation.

Pytest precisely verifies retry boundaries, state transitions, secret-safe checkpoint configuration, argument validation, and security guards.

These deterministic assertions are more appropriate than subjective evaluation scoring for strict invariants.

## 10. LangSmith Tracing

LangSmith tracing was enabled with:

- `LANGSMITH_TRACING=true`
- `LANGSMITH_PROJECT=library-week7`
- `LANGSMITH_API_KEY` stored outside Git

The API key is not stored in the repository.

The trace evidence was generated by:

`ai-service/week7_langsmith_traces.py`

Two top-level traces were successfully uploaded to the `library-week7` LangSmith project.

### Passing Trace

Trace name:

`week7-passing-agent-run`

Observed result:

**Success — PASS**

The traced trajectory includes catalog lookup, approval checking, reservation execution, and final completion.

### Failing Trace

Trace name:

`week7-failing-agent-run`

Observed result:

**Error — intentional RuntimeError**

The failing trace represents a reservation attempt where human approval is false. The reservation tool blocks the write and the traced run intentionally raises an error so that failure behavior is visible in LangSmith.

This is an intentional controlled failure used for tracing evidence, not an unexpected production failure.

### LangSmith Evidence Result

**PASS — one successful trace and one failing trace were captured and verified in the `library-week7` project.**

## 11. Current Limitations

1. The 30-run evaluation is primarily deterministic/local and is not equivalent to 30 independent LLM generations.
2. Token counts in the deterministic evaluation are estimates rather than provider-reported LLM usage.
3. Semantic vector retrieval can return nearest-neighbour documents even when the query has no exact catalog answer.
4. HTTP-level AgentThread ownership enforcement must also be verified during the full-stack agent API integration.
5. The proposed catalog-retrieval performance optimization has not yet been implemented or benchmarked.
6. The LangSmith evidence demonstrates tracing of successful and failing tool/chain execution, but it is not evidence of 30 independent model-backed runs.

## 12. Conclusion

The current Week 7 quality suite completed successfully:

- **pytest: 21/21 passed**
- **xUnit: 7/7 passed**
- **Agent evaluation: 30/30 runs passed**
- **Evaluation pass rate: 100.0%**
- **LangSmith passing trace: verified**
- **LangSmith failing trace: verified**

The deterministic workflow demonstrates correct behavior for routing, approval, conflict re-planning, retry limits, input validation, security controls, reservation API behavior, and trace observability.

The remaining HTTP-level ownership and full-stack agent API requirements will be verified as part of the Week 7 full-stack integration work.