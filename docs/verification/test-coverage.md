# Verification test-family coverage

The verifier's top-level `passed` status is **not** a full test-coverage certificate.
It certifies the recorded, candidate-bound commands only. Individual test IDs,
subprocess sandboxing, and external services remain outside this contract.

## Detection and status rules

- **Node only:** Execute each discovered package script without appending
  script arguments. `testFamilies: [{family:"node", status:...}]` records the
  result of the discovered `test`/`tests` script. If no test script is
  configured, the overall result is `partial` even when build/lint passed.
- **Python only:** Inspect Python test files using AST, without importing them.
  If pytest-style free test functions/classes or pytest configuration is found,
  prefer `python -m pytest` when available. pytest is expected to collect
  standard unittest TestCase tests as well; a `delegated-to-pytest` entry
  indicates selection, **not** proof of each individual test's execution.
  If pytest is unavailable and a unittest suite is identified, run unittest
  but record the pytest family as `unavailable` and overall `partial`.
  If only pytest-style tests exist without pytest, no passing gate is claimed.
  A unittest run collecting **zero tests** also becomes `unavailable`.
  Unreadable or syntactically invalid candidate test files prevent a full GREEN.
  For unittest, CEK runs conventional discovery under `tests/` and explicitly
  runs importable root test files as a separate step. Nested directories
  under `tests/` require package markers for unittest discovery. Candidate
  files outside the supported layout leave the report `partial` when the
  attempted checks pass.
- **Node + Python markers in the same project root.** Run the Node preset and
  the discovered Python tests, even if the Node tests fail. Python steps get a
  `-python` suffix in the report and publish their own test families. Both
  families must pass for an overall `passed`. A failed suite produces
  `failed`, while a missing test gate or required test runner produces
  `partial` when the attempted checks pass. The report retains
  `projectType: "node"` and the selected Node package manager. Run separate
  verification commands for independently configured project roots. The
  mixed mode runs Python tests only and uses the invoking Python interpreter.
- **Generic/unsupported:** `partial`.

Python test commands use a fresh temporary bytecode cache path and disable
bytecode writes. Existing project bytecode caches are preserved. This keeps
an old timestamp-based cache from substituting stale Python code for the
candidate being verified.

A standard unittest summary that reports every test as skipped leaves that
family `unavailable`, even if the test command exits zero. A pytest family
requires a summary reporting at least one passing test. If output settings
such as `-qq` suppress the summary, the family remains `unavailable` even
when the subprocess exits zero. Use an output configuration that emits the
terminal summary to attest those tests.

The `steps` array retains exact attempted commands, exit codes and bounded
evidence; the additive `testFamilies` array enumerates detected families
and their gate statuses. `skipped`, `unavailable` or `not-run` tests
prevent overall `passed`. A normal failing command is still `failed`.

## CI usage (PowerShell)

```powershell
python -B -m verification.cli --project . --json --require-complete
```

Exit codes: `0` when `passed`; `1` when `failed`; `2` when
`partial` with `--require-complete`. Without the flag, `partial`
continues to exit `0` for older consumers; **do not use that default
as a CI success gate**.

## Boundaries

AST classification is conservative, not exhaustive: dynamically registered
tests, nonstandard test naming, custom collection hooks, skipped/xfail tests,
and nested monorepos may require additional manual verification. Availability
of pytest is checked in the **invoking Python interpreter**, not guaranteed
to match a project's virtualenv. A package `test` script returning zero
does not prove it ran a nonzero number of individual cases. The report
does not claim percentage or statement coverage.

These changes are post-beta: the frozen published `v1.1.0-beta.1` tag does
**not** receive these changes. The artifact remains bound to candidate-file
manifest/digest checks; no model run or benchmark inference is added.
