---
name: eval-harness
description: Defines capability and regression evals for agentic engineering changes with deterministic graders preferred.
---

# Eval Harness

Use when an engineering change needs explicit success criteria beyond ordinary unit tests, especially for agent behavior, workflow reliability, generated artifacts, or repeated model execution.

## Executable Plan D modes

Run the deterministic offline campaign with:

```text
python -m evals.cli offline --cases evals/cases --fixtures evals/fixtures/offline --json
```

Run authenticated Codex pressure acceptance only as an operator-assisted path:

```text
python scripts/acceptance/codex_pressure.py --codex PATH --repo PATH --cases evals/cases --output .codex-kit/evals/authenticated/latest.json
```

Authenticated pressure execution requires read-only sandbox support discovered from `codex exec --help` and is intentionally excluded from deterministic CI. See `docs/evals.md` for the stable pressure-response schema, attempt accounting, artifact handling, and reliability rules.

## Eval types

### Capability eval
Proves a new behavior can be achieved.

Required fields:
- task
- preconditions
- success criteria
- grader
- expected evidence

### Regression eval
Proves previously working behavior remains intact.

Required fields:
- baseline reference
- protected behavior
- grader
- pass/fail evidence

### Pressure eval
Tests bounded safe behavior under unsupported, destructive, verification-skipping, secret-handling, or unbounded-concurrency pressure. Plan D pressure candidates are graded deterministically from structured JSON.

## Grader priority

1. **Deterministic/code-based** — tests, exit codes, schema checks, exact file/content contracts.
2. **Model-assisted** — structured rubric for open-ended quality where deterministic checks are insufficient.
3. **Human review required** — security, UX judgment, irreversible operations, or high-impact ambiguity.

Never use a model grader when the result can be checked deterministically.

## Storage

Project-local eval artifacts belong under `.codex-kit/evals/`. Plan D uses:

```text
.codex-kit/evals/
├── offline/latest.json
└── authenticated/<campaign>.json
```

Do not store secrets, private transcripts, raw authenticated stdout/stderr, or credentials in committed eval evidence.

## Workflow

1. Define evals before implementation when behavior is new.
2. Record the baseline for regression-sensitive work.
3. Implement using normal repository workflow.
4. Run deterministic graders first.
5. Run model/human graders only when required.
6. Record attempt count and actual outcomes.
7. Report regressions separately from capability failures.
8. Keep unavailable evidence explicit as `PARTIAL`; never fabricate an attempt or grade.

## Reliability metrics

`pass@k` means at least one success within `k` independent attempts. `pass^k` means all `k` attempts succeed. Only report these metrics when the required number of real attempts was executed. A single run cannot justify a multi-run reliability claim.

## Output contract

Report:
- eval definition
- grader type per criterion
- attempts actually executed
- capability results
- regression results
- pressure results when applicable
- reliability metrics, if legitimately measured
- blocking failures
- final status: `PASS`, `FAIL`, or `PARTIAL`
