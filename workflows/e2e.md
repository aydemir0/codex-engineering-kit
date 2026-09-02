# E2E Workflow

## Entry conditions
A critical user journey or integration flow requires end-to-end validation.

## Evidence required
Target journey, supported environment, setup/seed requirements, external dependencies, and expected observable outcomes.

## Procedure
1. Route to `e2e-runner`.
2. Prefer existing E2E tooling and stable selectors/contracts.
3. Isolate test data and deterministic setup.
4. Assert outcomes rather than screenshots alone.
5. Capture artifacts only when they help diagnose a failure.

## Failure handling
Separate environment/tooling failure from product failure. Do not count a skipped journey as passed.

## Verification
Run the target journey, relevant surrounding E2E suite, and lower-level tests for any code fix introduced by E2E findings.

## Output contract
Report journeys, environment, commands, assertions, artifacts, failures, rerun instructions, and readiness.
