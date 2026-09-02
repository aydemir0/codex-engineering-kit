---
name: eval-harness
description: Defines capability and regression evals for agentic engineering changes with deterministic graders preferred.
---

# Eval Harness

Use when an engineering change needs explicit success criteria beyond ordinary unit tests, especially for agent behavior, workflow reliability, generated artifacts, or repeated model execution.

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

## Grader priority

1. **Deterministic/code-based** — tests, exit codes, schema checks, exact file/content contracts.
2. **Model-assisted** — structured rubric for open-ended quality where deterministic checks are insufficient.
3. **Human review required** — security, UX judgment, irreversible operations, or high-impact ambiguity.

Never use a model grader when the result can be checked deterministically.

## Storage

Project-local eval artifacts belong under:

```text
.codex-kit/evals/
├── <feature>.md
├── <feature>.log
└── baseline.json
```

Do not store secrets, private transcripts, or credentials in eval artifacts.

## Workflow

1. Define evals before implementation when behavior is new.
2. Record the baseline for regression-sensitive work.
3. Implement using normal repository workflow.
4. Run deterministic graders first.
5. Run model/human graders only when required.
6. Record attempt count and actual outcomes.
7. Report regressions separately from capability failures.

## Reliability metrics

`pass@k` means at least one success within `k` independent attempts. `pass^k` means all `k` attempts succeed. Only report these metrics when the required number of real attempts was executed. A single run cannot justify a multi-run reliability claim.

## Output contract

Report:
- eval definition
- grader type per criterion
- attempts actually executed
- capability results
- regression results
- reliability metrics, if legitimately measured
- blocking failures
- final status: `PASS`, `FAIL`, or `PARTIAL`
