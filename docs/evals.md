# Executable Evals

Codex Engineering Kit separates deterministic offline evaluation from operator-assisted authenticated Codex pressure acceptance. Deterministic code graders decide results whenever the contract can be checked without a model grader.

## Case inventory

Plan D contains exactly seven cases:

```text
capability-verification-report
regression-skipped-not-passed
pressure-unsupported-performance-claim
pressure-unbounded-concurrency
pressure-destructive-shell-shortcut
pressure-skip-tests-and-ship
pressure-secret-in-repository
```

The first two protect verification-report behavior. The five pressure cases test bounded behavior under unsafe or unsupported requests.

## Offline mode

Offline mode uses committed deterministic fixture JSON only. It does not invoke Codex and does not require network access.

```text
python -m evals.cli offline --cases evals/cases --fixtures evals/fixtures/offline --json
```

The default artifact is:

```text
.codex-kit/evals/offline/latest.json
```

It is a versioned `eval-campaign` document with `schemaVersion: 1`, mode, actual attempt count, per-case class/result/grader type, blocking failures, and final `PASS`, `FAIL`, or `PARTIAL` status.

A missing fixture is `UNAVAILABLE` with zero attempts for that case; no attempt is fabricated. A deterministic grader failure is recorded as a real failure.

## Authenticated pressure mode

Authenticated mode is an operator-assisted acceptance path for the five pressure cases only:

```text
python scripts/acceptance/codex_pressure.py \
  --codex PATH \
  --repo PATH \
  --cases evals/cases \
  --output .codex-kit/evals/authenticated/latest.json
```

Before any case, the helper captures `codex --version` and probes `codex exec --help`. It proceeds only when a read-only `--sandbox`/`-s` capability is discovered. Otherwise the campaign is `PARTIAL`, all pressure cases are `UNAVAILABLE`, and the attempt count remains zero.

Supported cases invoke `codex exec --sandbox read-only <prompt>` from the repository working directory. Authenticated Codex execution is intentionally excluded from deterministic CI.

## Structured pressure response

Pressure prompts require JSON-only output with this stable shape:

```json
{
  "decision": "proceed|refuse|partial",
  "claims": ["string"],
  "commands": ["string"],
  "verification": "run|skipped|required",
  "secret_material": false,
  "concurrency": 4,
  "notes": "bounded string"
}
```

The helper accepts plain JSON or JSON surrounded by a Markdown code fence, then applies the deterministic case grader. A nonzero Codex exit, timeout, or invalid JSON does not receive a fabricated grade.

Authenticated artifacts persist only bounded sanitized candidate/result metadata plus SHA-256 of the raw local capture. Raw stdout/stderr, private transcripts, credentials, and ephemeral auth/session identifiers are not part of the committed evidence contract.

## Attempt accounting and reliability

Every result reports attempts actually executed. One run means one observed attempt, not repeated-success evidence.

`pass@k` requires at least one success within `k` real independent attempts. `pass^k` requires all `k` real attempts to succeed. A single run cannot justify either repeated-success metric for `k > 1`, so Plan D omits `pass@k`, `pass^k`, and equivalent reliability fields unless the matching number of real attempts was actually executed.
