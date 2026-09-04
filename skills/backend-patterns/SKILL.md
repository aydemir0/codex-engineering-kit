---
name: backend-patterns
description: Reviews backend APIs, data boundaries, transactions, retries, queues, caching, and service ownership using repository evidence.
---

# Backend Patterns

Use this skill for backend changes where API or service ownership, persistence, transactions, idempotency, authentication/authorization boundaries, queues/events, caching, retry behavior, or backend observability materially affects correctness. Do not treat framework-specific boilerplate as universal architecture.

## Entry conditions

Use only when the task has a real backend boundary to inspect or change. Keep the scope narrow: API/service contracts, data ownership, transaction and failure semantics, asynchronous delivery, cache behavior, or operational signals. If the request is primarily system-wide decomposition, use the architecture skill instead and invoke this skill only for the backend slice that needs concrete evidence.

## Repository evidence

Inspect repository and runtime evidence before recommending a pattern. Read the smallest relevant set of repository instructions, service/module layout, framework/runtime configuration, route or RPC definitions, schemas and migrations, persistence adapters, queue/event definitions, cache configuration, authentication and authorization policy, tests, deployment configuration, and existing logs/metrics/traces.

Identify the concrete owner for each mutable data set and each externally visible contract. Record assumptions separately from observations. Do not infer a framework capability, database isolation level, delivery guarantee, retry policy, or cache topology that is not shown by repository or runtime evidence.

Do not recommend a service split without an ownership or scaling boundary.

## Data and transaction boundaries

Map write authority, consistency requirements, transaction scope, isolation assumptions, uniqueness constraints, migrations, and rollback behavior before changing persistence. Prefer the smallest transaction that preserves the invariant; do not widen transactions merely for convenience.

For multi-resource operations, identify which guarantees are atomic and which are compensating. Treat schema evolution as a compatibility problem across readers, writers, deployments, and rollback. Verify migration ordering, backward compatibility, data backfill strategy, lock/availability impact, and recovery path when material.

Treat retries, idempotency, and transaction boundaries as one failure model.

For every retriable write, define the idempotency key or deduplication boundary, storage lifetime, replay semantics, and behavior after partial success. Do not assume a database transaction makes external side effects atomic.

## API and service contracts

For each API, RPC, event, or service boundary, identify ownership, caller expectations, validation, authentication, authorization, compatibility, timeouts, error semantics, and versioning. Keep business invariants behind one authoritative boundary rather than duplicating policy across handlers.

Prefer explicit request/response or event contracts over framework magic when the boundary crosses modules, processes, or teams. Validate untrusted input at the trust boundary and preserve domain validation at the authoritative write path. Distinguish authentication from authorization and state what resource/action is being authorized.

Do not introduce a network boundary solely because code is large or because a framework template suggests a service layer. A split requires evidence such as independent ownership, deployment, scaling, isolation, or fault-containment needs.

## Failure, retry, and idempotency

Model timeouts, transient errors, permanent errors, duplicate delivery, out-of-order delivery, partial completion, and replay. Retry only operations proven safe to repeat or protected by an idempotency/deduplication mechanism. Bound retry count and backoff, and define the terminal path.

For queues and events, inspect producer acknowledgement, consumer acknowledgement, visibility/lease behavior, delivery guarantees, ordering guarantees, poison-message handling, dead-letter behavior, replay tooling, and observability. State where deduplication lives and what happens when processing succeeds but acknowledgement fails.

For caches, define source of truth, key scope, invalidation/expiry strategy, stampede behavior, stale-read tolerance, and failure fallback. A cache is not a correctness boundary unless the repository explicitly makes it one.

Do not claim a query or cache change is faster without measurement.

## Security boundaries

Identify trust boundaries, credential handling, secrets flow, authentication, authorization, tenant isolation, object-level access control, input validation, serialization/deserialization risks, and sensitive-data exposure. Verify authorization at the authoritative resource boundary rather than relying on UI or routing assumptions.

Do not log secrets, raw credentials, session material, or unnecessary sensitive payloads. For background jobs and events, confirm that the worker identity and authorization model are explicit rather than inherited accidentally from the initiating request.

## Observability

Require signals that explain backend behavior without storing raw sensitive content: bounded structured logs, metrics, traces or correlation identifiers where supported, queue depth/age, retry and dead-letter counts, error rates, latency distributions, saturation indicators, and migration outcomes as applicable.

Tie each proposed signal to an operational question. Avoid adding telemetry that cannot drive a diagnosis, alert, capacity decision, or verification gate. Performance claims require load, benchmark, query-plan, runtime, or production evidence appropriate to the claim.

## Verification

Choose verification from the actual change surface: unit tests for invariants, integration tests for persistence and transactions, contract tests for external boundaries, authorization tests, migration tests, failure/retry/idempotency tests, queue replay tests, cache invalidation tests, and load or benchmark tests when making capacity or latency claims.

Exercise rollback or downgrade behavior when schema, deployment ordering, or irreversible side effects make it material. Verify unhappy paths and partial failure, not only the successful request. Preserve existing repository commands and CI contracts rather than inventing replacement tooling.

## Output contract

Return a concise evidence-bound review with:

1. observed backend boundary and repository evidence;
2. data owner, transaction boundary, and consistency invariant;
3. API/event contract and authn/authz boundary;
4. failure, retry, idempotency, queue, and cache behavior that materially applies;
5. observability and rollback requirements;
6. executable verification gates;
7. unresolved assumptions or missing evidence;
8. final decision: `Adopt`, `Reject`, `Experiment`, or `Needs evidence`.
