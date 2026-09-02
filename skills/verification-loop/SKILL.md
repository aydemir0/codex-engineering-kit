---
name: verification-loop
description: Runs evidence-based release and PR readiness checks using repository-native commands.
---

# Verification Loop

Use after significant implementation, refactoring, build fixes, security-sensitive changes, and before a PR or release decision.

## Principle

Verification is evidence, not confidence. A gate is `PASS` only when its command actually ran successfully. Missing or intentionally skipped gates are `SKIPPED`, never implicit success.

## Discover before running

Inspect repository instructions and project configuration first. Prefer project-native commands from package scripts, task runners, CI files, Makefiles, pyproject configuration, or equivalent sources. Do not hard-code npm when the repository uses another toolchain.

## Default gate order

1. build
2. typecheck
3. lint
4. tests
5. security checks
6. diff review
7. readiness decision

A repository may define a different required order. Stop early only when continuing would be misleading or destructive; otherwise collect enough evidence to explain all blockers.

## Security checks

Use repository-supported scanners when available. Also inspect changed trust boundaries, secrets handling, privileged operations, uploads, external fetches, and dependency/config changes. Never print secret values into the report.

## Diff review

Review the actual diff for unintended changes, missing tests, compatibility breaks, debug output, generated artifacts, and unrelated refactors.

## Required output

### Commands executed
List each command exactly as run and its exit status.

### Evidence
Summarize bounded relevant output, test counts, and files/configuration inspected.

### Blocking failures
List failures that prevent readiness. Use `None` only when there are no blockers.

### Warnings
List skipped optional gates, non-blocking warnings, and environmental limits.

### Readiness
Return exactly one state:

- `READY` — all required gates ran and passed.
- `NOT READY` — at least one required gate failed or a blocking issue remains.
- `PARTIAL` — required evidence could not be obtained; explain what remains unverified.

Never convert `PARTIAL` into `READY` based on model judgment alone.
