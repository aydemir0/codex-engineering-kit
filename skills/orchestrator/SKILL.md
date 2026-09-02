---
name: orchestrator
description: Routes production engineering work to focused role references and Codex-native workflows without inflating the active skill catalog.
---

# Engineering Orchestrator

Use this skill when a task spans planning, architecture, implementation, debugging, review, security, testing, refactoring, or documentation.

## Operating rule

For repository-scoped work, inspect repository-local instructions and the smallest relevant evidence set before selecting a role or proposing implementation-ready changes. Do not fabricate modules, infrastructure, tests, deployment behavior, ownership, or tool results.

Role references are operating contracts, not autonomous background agents. Use them to shape analysis and execution; never claim work happened in a separate agent unless the runtime actually performed it.

## Routing table

| Intent | Primary role | Required companion |
|---|---|---|
| feature planning | `planner` | `tdd-guide` before implementation |
| architecture change | `architect` | `planner` for migration sequencing |
| code review | `code-reviewer` | `security-reviewer` when trust boundaries change |
| security-sensitive change | `security-reviewer` | `code-reviewer` |
| build failure | `build-error-resolver` | `code-reviewer` after the fix |
| e2e validation | `e2e-runner` | `code-reviewer` for failures caused by product code |
| tdd workflow | `tdd-guide` | relevant implementation role |
| refactor | `refactor-cleaner` | `code-reviewer` |
| docs update | `doc-updater` | owner of changed behavior |

## Intent keywords

- **architecture**: boundaries, modules, services, data ownership, deployment, migration
- **plan**: implementation sequence, acceptance criteria, rollback, risk
- **review**: correctness, maintainability, regressions, API contracts
- **security**: authn/authz, secrets, isolation, validation, abuse controls
- **build**: compiler, bundler, dependency, runtime/module-evaluation failures
- **e2e**: browser/user-flow validation and regression evidence
- **tdd**: failing test first, minimal implementation, refactor after green
- **refactor**: dead code, duplication, oversized units, dependency cleanup
- **docs**: README, architecture docs, runbooks, changed behavior

## Selection procedure

1. Read repository-local instructions.
2. Identify the user-visible or operational outcome.
3. Inspect the relevant implementation, tests, schemas, and build/deploy configuration.
4. Select the smallest role set that covers the task.
5. Load only the selected role references and workflow.
6. Define acceptance and verification before editing.
7. Implement through repository-native commands.
8. Run required verification and report evidence.

## Escalation rules

- A build symptom with unclear cause starts with `build-error-resolver`, not architecture redesign.
- A local code smell does not justify a service boundary; use `architect` only when boundaries or ownership materially change.
- Security review is mandatory when authentication, authorization, secrets, tenancy, uploads, external fetches, or privileged operations change.
- Documentation is updated only for behavior, interfaces, setup, or operational facts that actually changed.

## Output contract

For non-trivial work, report:

1. selected roles and why;
2. evidence inspected;
3. decision or implementation summary;
4. tests/verification actually run;
5. blockers, warnings, and unresolved risks;
6. final status: `READY`, `NOT READY`, or `PARTIAL`.

Never label unexecuted verification as passed.
