# CEK v1 WS6 Authenticated Benchmark Evidence — INVALIDATED CAMPAIGN

Date: 2026-09-11

WS5 baseline: `78206e1a67800f21f059c7c699727fc3d40df9cf`

Measured candidate: `08576e25da4ef0c78950abe335ea64b85edd8671`

Branch: `feat/v1-core-workflow`

## Acceptance contract

WS6 requires five frozen repository tasks, three context modes, and three repetitions per task/mode: exactly 45 authenticated attempts. Each planned tuple receives one attempt. Failures, timeouts, and quota events remain failures; they are never silently replaced. Runtime/API token telemetry is the only accepted token measurement source.

The modes are A always-loaded, B progressive disclosure, and C project-local isolated subagent. A passing C attempt requires CEK hook evidence containing matching `SubagentStart` and `SubagentStop` child identity with `agentType = explorer`. A `wait` tool pair and model prose are not lifecycle evidence.

## Frozen runtime and provenance

- Fixture commit: `1dbf382b6e838ca351c6fb8818a64aa793176198`
- Candidate commit: `08576e25da4ef0c78950abe335ea64b85edd8671`
- Methodology SHA-256: `7a1c00580ac07f3d23e7cfdeb596e8866ea569fb6e5e005c63ff42d13d0c60be`
- Runtime: Codex CLI 0.153.0
- Model: `gpt-5.6-terra`
- Reasoning: `medium`
- Timeout: 180 seconds per attempt
- Retry policy: one attempt per tuple; no selective retry
- Execution: deterministic sequential case/configuration/repeat order
- Isolation: read-only sandbox, automatic approval review, apps disabled, pre-vetted CEK plugin-native lifecycle hooks enabled with an explicit acceptance-only trust bypass, exact-path trust for each disposable fixture, plugin skill instructions excluded, repository rules ignored, benchmark-only disposable config/profile/`CODEX_HOME`, and host skill instructions excluded from model-visible input. This is not a hook sandbox or normal hook-trust UX claim.

The authenticated capsule materialized only the five frozen fixture trees, five case files, three configuration files, eight required CEK `SKILL.md` files, the shipped project-local explorer definition, and the minimum benchmark runner modules. The capsule contained 32 files and was clean at the candidate commit.

## Pre-counted smoke and campaign lineage

The former non-counted smoke `ws6-smoke-v9` is invalidated. It produced measured token telemetry and passed quality checks, but its `collab-wait-lifecycle` was only a parent `wait` pair with no child identity. It did not prove a real explorer subagent.

An earlier counted campaign, `ws6-cli01530-v1`, is invalidated and not interpreted as the final benchmark. It retained all 45 attempts: 20 PASS and 25 quota-limit FAIL rows. The campaign also exposed a validator defect that rejected a valid failed C attempt merely because execution ended before a child lifecycle could exist. The defect was reproduced RED, fixed so lifecycle remains mandatory for every passing C attempt, and the entire campaign was restarted under a new ID. The invalidated sanitized dataset SHA-256 is `6d202fde29f84398e2b53381f61f06f774246cc295147bc9d11070aad491e51e`; its 90-file local raw manifest SHA-256 is `824e0294e393e968ab621e2b0a9f6ebf7d66deae9742e7011193783da2b98528`.

## Invalidated measured campaign

Campaign `ws6-cli01530-v2` retains exactly 45 unique counted attempts with an observed outcome of 42 PASS / 3 FAIL, but it is **INVALIDATED** and is not WS6 closure evidence. Independent review proved that its C-mode lifecycle parser accepted parent `wait` events without a spawned child and that its methodology hash depended on checkout line endings. The retained dataset is bound to `benchmarks/results/ws6-cli01530-v2-invalidated.json`; no counted row was deleted or replaced.

| Mode | Attempts | PASS | FAIL | Input tokens median (range) | Output tokens median (range) | Duration median ms (range) | Tool calls median (range) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 15 | 15 | 0 | 57,244 (57,000-77,351) | 984 (522-1,476) | 38,706 (25,382-50,345) | 2 (2-3) |
| B | 15 | 15 | 0 | 40,737 (37,689-54,743) | 1,039 (462-1,461) | 39,447 (25,606-46,129) | 2 (2-3) |
| C | 15 | 12 | 3 | 38,178 (37,777-51,348) | 703 (429-834) | 62,033 (46,893-71,812) | 1 (1-2) |

All 45 input, cached-input, and output token fields have source `measured`. Parent-only and child-only token totals remain unavailable because CLI 0.153.0 did not expose that split.

The three retained failures are `frontend-review/C` repetitions 1-3. Each had measured telemetry but failed deterministic quality check 2: the final response did not include the required client/server ownership evidence. None of the v2 C rows has acceptable child lifecycle evidence, so v2 is not interpreted as a valid mode comparison.

## Reset boundary evidence

- Reset #1 was redeemed only after attempt 15 completed. The account operation returned `reset`; no counted attempt was altered. The sanitized receipt in `benchmarks/results/ws6-reset-evidence.json` binds the operation to attempt 15's capture hash and the raw tool-result hash.
- Reset #2 was not redeemed during v2 and remains available. It may be redeemed only after attempt 30 of the restarted frozen campaign and only if needed.

## Sanitization and raw-data boundary

The committed dataset is `benchmarks/results/ws6-cli01530-v2.json`. Its normalized LF SHA-256 is `d9a5d97381cc25fc80b33a8a3063af21aaa91bd6842efa74c6a4f37e9ce658c3`.

Deterministic scans found no absolute user path, username, `auth.json`, session/thread identifier, raw prompt, stdout/stderr field, private-skill path, API key, token, or bearer-credential pattern in the committed dataset. Raw JSONL and stderr remain separate under ignored local benchmark storage. The final campaign has 90 raw files; its filename/hash manifest SHA-256 is `8ee165499fdfca018ff93f5ec8fb3802b666b013f73ad98d1f6f71d0684a2154`. No raw content is committed.

## Interpretation boundary

The v2 numbers are retained historical measurements from an invalidated methodology and are not interpreted as comparative results. There is no efficiency, context-reduction, latency, quality, or benchmark-leadership claim, and no statistical significance claim.

This campaign did not test plugin skill discovery. It does not change WS5's `NOT_RUN` status for that separate surface and does not infer Codex Desktop behavior.

## Deterministic validation

- The former v2 authenticated validation is superseded and must not be used as closure evidence; the corrected validator rejects its non-reproducible methodology hash.
- `python -B -m benchmarks.cli report --runs .codex-kit/benchmarks/ws6-campaign-v2.json --cases benchmarks/cases --configurations benchmarks/configurations --json` — complete, expected 45, observed 45, blockers empty.
- `python -B -m unittest tests.test_context_benchmark_runner tests.test_benchmark_contract -v` — 26 tests passed.
- `python -B -m unittest discover -s tests -p 'test_*.py'` — 223 tests passed. Expected negative-fixture diagnostics were printed; the suite exited successfully.
- `pwsh -NoProfile -File tests/Test-Install.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Verify.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Learning.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Mcp.ps1` — passed.
- `python -B tests/validate_content.py` — passed.
- `python -B -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json` — 12 claims and 12 compatibility surfaces passed.
- `python -B -m benchmarks.cli validate --cases benchmarks/cases --configurations benchmarks/configurations` — fixed protocol passed with 45 planned attempts.

## Closure assessment

**WS6 is NOT CLOSED.** A restarted campaign requires a fresh non-counted smoke with real hook `SubagentStart`/`SubagentStop` explorer evidence, followed by all 45 counted attempts under the corrected platform-stable methodology, deterministic validation, regressions, sanitization, independent review, and disposable auth/runtime cleanup.
