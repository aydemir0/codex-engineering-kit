# Feature Workflow

## Entry conditions
Approved feature outcome and repository access are available.

## Evidence required
Repository instructions, existing flow, interfaces, tests, schemas, and deployment constraints relevant to the feature.

## Procedure
1. Route through `planner`; add `architect` only if boundaries/ownership change.
2. Define acceptance criteria and a failing test/eval for new behavior.
3. Implement the smallest vertical slice.
4. Keep migrations and compatibility reversible.
5. Update docs only for verified changed behavior.

## Failure handling
Stop on unclear ownership, destructive migration risk, repeated verification failure, or requirements contradiction; return the blocker with evidence.

## Verification
Run targeted tests, then required build/type/lint/test/security/diff gates through the verification workflow.

## Output contract
Summarize files changed, behavior delivered, tests/evals run, migration/rollback notes, warnings, and `READY`/`NOT READY`/`PARTIAL`.
