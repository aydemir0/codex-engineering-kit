# Code Review Workflow

## Entry conditions
A diff, commit, branch, or pull request is available for review.

## Evidence required
Actual diff, surrounding interfaces, tests, repository instructions, and changed configuration/schema where applicable.

## Procedure
1. Route to `code-reviewer`.
2. Understand intended behavior before judging implementation.
3. Review correctness and regression risk before style.
4. Escalate changed trust boundaries to `security-reviewer`.
5. Verify high-confidence findings with code/tests when practical.

## Failure handling
If the diff or required context is incomplete, mark affected findings as conditional rather than inventing certainty.

## Verification
Run targeted checks for blocking findings and inspect the final diff after fixes.

## Output contract
List findings by severity with evidence and impact, then blockers, non-blocking suggestions, verification performed, and readiness.
