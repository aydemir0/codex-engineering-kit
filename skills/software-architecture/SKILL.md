---
name: software-architecture
description: Designs and reviews production architecture from repository evidence with incremental migration and rollback discipline.
---

# Software Architecture

Use for system design, module/service boundaries, backend/frontend architecture, data ownership, API design, scalability, caching, queues, deployment architecture, technical debt, and architecture refactoring.

## Evidence first

For an existing repository, inspection is mandatory when access is available. A deadline or request to assume a conventional architecture does not replace evidence.

Inspect the smallest relevant set of:

1. repository-local instructions and architecture docs;
2. package/build/deploy configuration;
3. schemas, migrations, APIs, caches, queues, and external services;
4. relevant implementation and tests;
5. runtime units, trust boundaries, configuration/secrets, observability, and rollback mechanisms.

Map modules and dependency directions, state/data ownership, transaction boundaries, and representative critical paths. Do not fabricate missing infrastructure or ownership. If read-only inspection is prohibited or unavailable, provide only conditional preliminary direction and do not call it implementation-ready.

## Diagnose before designing

Distinguish symptoms from root causes. Evaluate coupling, cohesion, cycles, duplicated policy, misplaced business logic, consistency requirements, transactions, concurrency, idempotency, query/network count, cache invalidation, queue backpressure, hot paths, partial failure, timeout/retry behavior, ordering, overload, authentication/authorization, validation, isolation, secrets, abuse controls, logs/metrics/traces, deployment sequencing, feature flags, and rollback.

State the architectural invariant being protected before choosing a mechanism.

## Choose the smallest sound boundary

Default to a well-structured modular monolith. Create cohesive domain modules, stable interfaces, explicit state/data ownership, and enforceable dependency direction before adding network boundaries.

Recommend a microservice only when repository and operational evidence demonstrates a meaningful need for independent deployment, scaling, fault/security isolation, data ownership, or team autonomy and the organization can operate versioned contracts, tracing, retries, idempotency, schema evolution, and partial failures.

A large file, deadline, executive preference, or sunk cost is not sufficient evidence. Do not recommend a rewrite without proving incremental correction is inadequate. Prefer reversible vertical slices, strangler migrations, branch-by-abstraction, and compatibility layers with removal criteria.

## Boundary test

Before separating a module or service, answer:

| Question | Required evidence |
|---|---|
| What does it own? | State, data, invariants, write authority |
| Why is it separate? | Cohesion plus operational or organizational driver |
| How does it communicate? | Typed/versioned API or event contract |
| How does it fail? | Timeout, retry, idempotency, ordering, recovery |
| How is it changed safely? | Compatibility, migration, tests, deploy, rollback |

If ownership or failure semantics remain ambiguous, keep the boundary in-process and refine it first.

## Recommendation contract

For every significant recommendation, render these exact level-3 headings in order.

### Current architecture
Observed components, boundaries, dependency direction, and file-level evidence.

### Actual problem
Measurable behavior or engineering constraint; separate facts from assumptions.

### Root cause
The mechanism producing the problem.

### Proposed architecture
Modules, interfaces, state/data owners, transaction boundaries, and dependency rules.

### Why this architecture
Connect the design directly to evidence and invariants.

### Trade-offs
Complexity gained, complexity removed, alternatives rejected, and operating cost.

### Migration strategy
Small ordered slices, compatibility plan, data migration, deploy sequence, and removal criteria.

### Rollback strategy
Trigger, mechanism, data reconciliation, and recovery point.

### Testing strategy
Characterization/regression, contract, migration, integration, failure-injection, load, and end-to-end gates as applicable.

### Performance implications
Latency, throughput, query/network count, caching, capacity, and Big O on critical paths where material.

### Security implications
Trust boundaries, authn/authz, validation, secrets, isolation, and abuse controls.

### Decision status
Adopt, defer, reject, or experiment; list prerequisites and unresolved risks.

Make migration steps concrete enough to become issues or pull requests. Use Mermaid only when relationships, ownership, or multi-step failure/migration flows are materially clearer than prose or a compact table.

## Completion gate

Before presenting a decision, verify that it is grounded in inspected evidence, assigns every mutable state/schema to an owner, preserves intentional dependency direction, covers unhappy paths and concurrency, includes incremental migration and rollback, and names executable verification gates.
