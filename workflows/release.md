# Release Workflow

## Entry conditions
A branch/change set is intended for PR merge, deployment, or versioned release.

## Evidence required
Final diff, repository-native build/test commands, migration/deploy notes, security-sensitive changes, and rollback mechanism.

## Procedure
1. Freeze unrelated scope.
2. Run `verification-loop` through every required gate.
3. Review migrations, compatibility, secrets/configuration, and deployment ordering.
4. Confirm rollback trigger and mechanism.
5. Update release-facing documentation from verified behavior only.

## Failure handling
Any failed required gate or unresolved blocker yields `NOT READY`. Missing required evidence yields `PARTIAL`; do not release on model confidence alone.

## Verification
Build, typecheck, lint, tests, security checks, diff review, and project-specific release checks must be recorded with exit status/evidence.

## Output contract
Provide executed commands, blocking failures, warnings, migration/rollback notes, and final `READY`/`NOT READY`/`PARTIAL`.
