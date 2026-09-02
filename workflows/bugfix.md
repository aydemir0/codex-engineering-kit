# Bugfix Workflow

## Entry conditions
A reproducible defect, failing test, error report, or concrete incorrect behavior exists.

## Evidence required
Exact symptom, reproduction steps/command, relevant logs, implementation path, tests, and recent related changes.

## Procedure
1. Route through the relevant debugging/build role.
2. Reproduce the defect before editing when practical.
3. Form one causal hypothesis at a time.
4. Add a regression test that fails for the intended reason.
5. Implement the minimal root-cause fix.
6. Refactor only after green.

## Failure handling
If reproduction is impossible, state the missing evidence and avoid speculative production changes. If the fix exposes architectural risk, escalate instead of broadening silently.

## Verification
Run the regression test, surrounding suite, and required verification gates.

## Output contract
Report reproduction, root cause, fix, regression evidence, side effects, and readiness state.
