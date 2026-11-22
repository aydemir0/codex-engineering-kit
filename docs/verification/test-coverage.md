# Verification test-family coverage (post-beta proposal)

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
- **Node + Python markers:** Run the Node preset and explicitly record
  `tests-python: unavailable` / `{family:"python",status:"not-run"}`.
  No overall `passed` is permitted until another explicit verification
  checks Python. The first PR does not silently execute every language's
  build scripts in a mixed repository.
- **Generic/unsupported:** `partial`.

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

This proposal is post-beta: the frozen published `v1.1.0-beta.1` tag does
**not** receive these changes. The artifact remains bound to candidate-file
manifest/digest checks; no model run or benchmark inference is added.
