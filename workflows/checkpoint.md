# Checkpoint Workflow

## Entry conditions
A long-running engineering task needs a durable state handoff before context switch, compaction, or session end.

## Evidence required
Current branch/commit, completed work, current verification state, unresolved blockers, next executable step, and any migration/deploy constraints.

## Procedure
1. Record repository/branch and clean/dirty state.
2. Summarize completed behavior with file-level evidence.
3. Record commands/tests actually run and their results.
4. List unresolved risks and assumptions.
5. Name the next smallest executable step.
6. Keep secrets and private transcript content out of checkpoints.

## Failure handling
If repository state cannot be inspected, mark it unknown rather than guessing. Do not describe uncommitted work as safely persisted.

## Verification
Cross-check checkpoint claims against current diff/status and available test evidence.

## Output contract
Return branch/commit, completed scope, verification status, blockers, next step, and `SAFE TO HAND OFF` or `NEEDS ATTENTION`.
