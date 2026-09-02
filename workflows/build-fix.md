# Build Fix Workflow

## Entry conditions
A compiler, bundler, dependency, module-evaluation, packaging, or deployment-build command fails.

## Evidence required
Exact command, first relevant error, tool/runtime versions, package/lock configuration, and the import/configuration chain leading to failure.

## Procedure
1. Route to `build-error-resolver`.
2. Reproduce the failing command.
3. Minimize the causal path and form a falsifiable hypothesis.
4. Change the smallest relevant dependency/configuration/code path.
5. Re-run the original command before broader tests.
6. Review the diff for unrelated dependency churn.

## Failure handling
Do not delete lockfiles, blanket-upgrade dependencies, disable type checking, or suppress errors without causal evidence. Escalate incompatible runtime/library constraints explicitly.

## Verification
Original build command must pass, then run relevant tests/type checks and code review.

## Output contract
Report failing command, root cause, minimal fix, versions/files changed, verification evidence, and readiness.
