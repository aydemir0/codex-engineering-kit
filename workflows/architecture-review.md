# Architecture Review Workflow

## Entry conditions
A proposed change alters module/service boundaries, state/data ownership, transactions, APIs/events, deployment units, or major scalability/failure behavior.

## Evidence required
Relevant repository structure, schemas, interfaces, critical paths, tests, deployment topology, observed constraints, and rollback mechanisms.

## Procedure
1. Route to `architect`.
2. Map current ownership/dependencies and the invariant being protected.
3. Separate measured problems from assumptions.
4. Compare the smallest sound options, including keeping the boundary in-process.
5. Define migration, compatibility, rollback, and verification before adoption.

## Failure handling
If evidence is unavailable, provide only a conditional preliminary direction. Reject unsupported rewrites or service decomposition.

## Verification
Use architecture skill completion gates plus relevant tests, migration validation, failure-path checks, security review, and performance evidence.

## Output contract
Render the architecture recommendation contract and decision status with prerequisites and unresolved risk.
