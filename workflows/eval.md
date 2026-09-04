# Eval Workflow

## Entry conditions
A change needs explicit capability, regression, or pressure evaluation beyond ordinary tests.

## Evidence required
Expected behavior, baseline/protected behavior, measurable success criteria, available deterministic graders, and the number of attempts actually executed.

## Procedure
1. Use `eval-harness` before implementation for new capability definitions when practical.
2. Prefer deterministic graders.
3. Run the Plan D offline campaign when its cases apply:

   ```text
   python -m evals.cli offline --cases evals/cases --fixtures evals/fixtures/offline --json
   ```

4. Store runtime eval artifacts under `.codex-kit/evals/`.
5. For authenticated pressure acceptance, use `scripts/acceptance/codex_pressure.py` only with an explicitly selected Codex binary. The helper must discover read-only sandbox support before any pressure case is invoked.
6. Execute the required real attempts before reporting repeated-success metrics.
7. Separate capability failures, regressions, pressure failures, and unavailable evidence.

Authenticated Codex pressure execution is operator-assisted and intentionally excluded from deterministic CI. See `docs/evals.md` for the structured pressure schema, artifact contract, and attempt-accounting rules.

## Failure handling
Do not fabricate `pass@k`, `pass^k`, baseline results, attempts, or model-grader certainty. Mark unavailable evidence as `PARTIAL`. A deterministic grader failure remains a real failure in evidence.

## Verification
Re-run deterministic graders and any required model/human review; preserve actual run evidence. Offline CI evidence is separate from authenticated Codex acceptance evidence.

## Output contract
Report eval definition, graders, actual attempt count, capability results, regression results, pressure results when applicable, legitimate reliability metrics, blockers, and `PASS`/`FAIL`/`PARTIAL`.
