# Representative Workflow Demo

This short demo replays the bounded workflow already accepted in WS3. It does
not require a new feature or reinterpret the existing runtime evidence.

## What it demonstrates

The fixture at `tests/fixtures/representative-workflow` asks for one change:
`divide(a, b)` must preserve normal division and raise exactly
`ValueError("division by zero")` when `b == 0`.

The demo combines a disposable local RED/GREEN reproduction with a clearly
labeled replay of the retained authenticated orchestration record. The latter
shows classification, planning, a distinct project-local reviewer, and final
evidence validation without pretending a new authenticated run occurred.

## Five-minute path

1. Read `tests/fixtures/representative-workflow/task.md` and confirm the allowed
   implementation boundary is only `src/calculator.py`.
2. From the repository root in PowerShell, create and enter a unique disposable
   copy so the canonical fixture remains unchanged:

   ```powershell
   $DemoRoot = Join-Path ([IO.Path]::GetTempPath()) ("cek-workflow-demo-" + [Guid]::NewGuid())
   Copy-Item -LiteralPath tests\fixtures\representative-workflow -Destination $DemoRoot -Recurse
   Set-Location -LiteralPath $DemoRoot
   ```

3. In that disposable copy, run:

   ```text
   python -B -m unittest discover -s tests -p "test_*.py" -v
   ```

   The checked-in starting fixture produces RED because division by zero
   returns infinity instead of raising the required exception.
4. Replace only the zero-divisor branch in `src/calculator.py` with:

   ```python
   raise ValueError("division by zero")
   ```

5. Run the same test command again. Both tests produce GREEN, including preserved
   normal division behavior.
6. Return to the repository and inspect
   `docs/research/evidence/codex-v1-representative-workflow.md`. Replay this
   retained, authenticated record excerpt:

   ```text
   Invocation: $codex-engineering-kit:orchestrator
   Ordered stages: classify -> plan -> red -> implement -> green -> review -> verify
   Structured result: READY
   Reviewer: one distinct project-local reviewer
   Lifecycle: matching reviewer SubagentStart -> SubagentStop child identity

   python scripts/acceptance/workflow_evidence.py validate --record <sanitized-record>
   PASS: representative workflow evidence validated
   ```

   The evidence document binds each stage to artifacts, records the exact
   one-line implementation boundary, and explains why parent self-review or
   reviewer-like prose was not accepted. The `<sanitized-record>` placeholder
   denotes the retained campaign input described by the evidence; it is not a
   promise that private raw runtime material is committed.
7. Delete only the unique `$DemoRoot` created in step 2 when finished. No
   authentication or normal-profile state is copied into it.

## Honest demo boundary

Steps 1-5 reproduce the deterministic code path locally. Step 6 presents the
retained authenticated CLI 0.153.0 orchestration and reviewer evidence rather
than pretending a new authenticated subagent run occurred. The single fixture
demonstrates the workflow mechanics; it does not prove universal task quality
or compatibility.
