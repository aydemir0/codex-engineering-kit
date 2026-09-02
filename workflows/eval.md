# Eval Workflow

## Entry conditions
A change needs explicit capability or regression evaluation beyond ordinary tests.

## Evidence required
Expected behavior, baseline/protected behavior, measurable success criteria, and available deterministic graders.

## Procedure
1. Use `eval-harness` before implementation for new capability definitions when practical.
2. Prefer deterministic graders.
3. Store project evals under `.codex-kit/evals/`.
4. Execute the required attempts before reporting repeated-success metrics.
5. Separate capability failures from regressions.

## Failure handling
Do not fabricate `pass@k`, baseline results, or model-grader certainty. Mark unavailable evidence as partial.

## Verification
Re-run deterministic graders and any required model/human review; preserve actual run evidence.

## Output contract
Report eval definition, graders, attempt count, capability results, regression results, legitimate reliability metrics, blockers, and `PASS`/`FAIL`/`PARTIAL`.
