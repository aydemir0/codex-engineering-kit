# Security Review Workflow

## Entry conditions
A change affects authentication, authorization, tenant/data isolation, secrets, uploads, external fetches, privileged operations, or sensitive data.

## Evidence required
Changed code, adjacent trust-boundary code, schemas/configuration, auth policy, tests, and deployment assumptions.

## Procedure
1. Route to `security-reviewer`.
2. Map actors, assets, trust boundaries, and privileged actions.
3. Verify server-side authorization and isolation where required.
4. Review validation, secret handling, abuse controls, and failure behavior.
5. Define regression checks and human review for residual high risk.

## Failure handling
Do not weaken controls to achieve green tests. If production testing would be destructive, use safe local/staging evidence and mark remaining uncertainty.

## Verification
Run security-relevant tests/scanners plus normal verification gates; manually inspect trust-boundary changes.

## Output contract
List findings with severity, attack/failure path, remediation, regression evidence, residual risk, and readiness.
