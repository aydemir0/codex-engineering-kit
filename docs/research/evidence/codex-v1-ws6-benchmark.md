# CEK v1 WS6 Authenticated Benchmark Evidence

Date: 2026-09-12

WS5 baseline: `78206e1a67800f21f059c7c699727fc3d40df9cf`

Measured candidate: `d245ed987f016ac116d478cfe747cb2580360258`

Branch: `feat/v1-core-workflow`

## Acceptance contract

WS6 requires five frozen repository tasks, three context modes, and three repetitions per task/mode: exactly 45 authenticated attempts. Each planned tuple receives one attempt. Failures, timeouts, and quota events remain failures; they are never silently replaced. Runtime/API telemetry is the only accepted token measurement source.

The modes are A always-loaded, B progressive disclosure, and C project-local isolated subagent. A passing C attempt requires CEK hook evidence containing matching `SubagentStart` and `SubagentStop` child identity with `agentType = explorer`. Parent `wait` events and model prose are not lifecycle evidence.

## Frozen runtime and provenance

- Fixture commit: `1dbf382b6e838ca351c6fb8818a64aa793176198`
- Candidate commit: `d245ed987f016ac116d478cfe747cb2580360258`
- Methodology SHA-256: `b2c7c83c62862c561d0d8adc361437726746763502bfbfdeb20139376a6c1738`
- Runtime: Codex CLI 0.153.0
- Model: `gpt-5.6-terra`
- Reasoning: `medium`
- Timeout: 180 seconds per attempt
- Retry policy: one attempt per tuple; no selective retry
- Execution: deterministic sequential case/configuration/repeat order
- Isolation: read-only sandbox, automatic approval review, apps and remote-plugin features disabled in the disposable config, CEK plugin-native lifecycle hooks enabled with exact-handler trust, exact-path trust for each disposable fixture, plugin skill instructions excluded, repository rules ignored, benchmark-only disposable config/profile/`CODEX_HOME`, and host skill instructions excluded from model-visible input. Hooks are not treated as a sandbox.

The authenticated capsule materialized only the five frozen fixture trees, five case files, three configuration files, eight required CEK `SKILL.md` files, the shipped project-local explorer definition, and the minimum benchmark runner modules. The counted candidate remained stable throughout the campaign.

## Non-counted smoke and invalidated lineage

The final non-counted smoke was `ws6-smoke-v29` at the same candidate and methodology hash. It passed quality checks and produced exactly one matching CEK-hook `SubagentStart`/`SubagentStop` pair with the same child and session identity and `agentType = explorer`. It is harness evidence only and is not included in the 45 measurements.

Campaign `ws6-cli01530-v1` is invalidated. It retained 45 attempts: 20 PASS and 25 quota-limit FAIL rows. It exposed a validator defect around failed C attempts; no row was replaced.

Campaign `ws6-cli01530-v2` is also **INVALIDATED**. It retained 45 attempts with 42 PASS / 3 FAIL, but independent review proved that its C lifecycle parser accepted parent `wait` events without a spawned child and that its methodology hash depended on checkout line endings. Its sanitized dataset and invalidation record remain committed; none of its measurements is used for the final comparison.

## Final measured campaign

Campaign `ws6-cli01530-v3` contains exactly 45 unique counted attempts in the frozen order: 15 per mode and three repetitions for every task/mode tuple. The observed outcome is 34 PASS / 11 FAIL.

| Mode | Attempts | PASS | FAIL | Input tokens median (range) | Output tokens median (range) | Duration median ms (range) | Tool calls median (range) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 15 | 15 | 0 | 60,134 (57,934-81,176) | 1,020 (503-1,408) | 43,748 (33,618-59,377) | 2 (2-3) |
| B | 15 | 15 | 0 | 43,264 (39,962-59,132) | 982 (520-1,446) | 45,681 (34,757-61,347) | 2 (2-3) |
| C | 15 | 4 | 11 | 54,973 (53,795-68,783) | 691 (437-904) | 74,207 (55,766-83,418) | 1 (1-2) |

All 45 input, cached-input, and output token fields have source `measured`. Parent-only and child-only token totals remain unavailable because CLI 0.153.0 did not expose that split.

Failure accounting is deterministic:

- Nine C attempts failed with `missing-subagent-lifecycle`; they did not produce the required matching explorer hook pair.
- Two `frontend-review/C` attempts produced valid explorer lifecycle evidence but failed the frozen `quality-contract` ownership check.
- Six C attempts produced valid explorer lifecycle evidence in total; four also passed the quality contract.
- No failed counted attempt was retried or replaced.

## Reset boundary evidence

- Reset #1 was redeemed during the invalidated v2 campaign only after attempt 15 completed. The sanitized receipt binds it to attempt 15's capture hash.
- Reset #2 was redeemed during v3 only after the fixed attempt-30 boundary. The account operation was issued after attempt 31 had already completed because polling observed both rows together, so the evidence records both the authorized boundary capture and the observed attempt-31 capture. Immediately before redemption, the five-hour window was 99% used with 14 attempts still pending; immediately after, the five-hour and weekly windows both read 0%, and no credits remained.
- Both operations returned `reset`; no counted row was altered.

`benchmarks/results/ws6-reset-evidence.json` contains only sanitized hashes and campaign/attempt bindings. Account, credit, idempotency, credential, and session identifiers are not committed.

## Sanitization and raw-data boundary

The committed final dataset is `benchmarks/results/ws6-cli01530-v3.json`. Its normalized LF SHA-256 is `33761f665e5402d752e641cacbbfe1d5299835a3bd452a037acc7e9d6f5b3382`.

Deterministic scans found no absolute user path, username, `auth.json`, session/thread identifier, raw prompt, stdout/stderr field, private-skill path, API key, bearer credential, account identifier, credit identifier, or reset idempotency key in the committed dataset. The 105 raw files remain separate under ignored local benchmark storage. A manifest formed by sorting relative filenames, pairing each with its lowercase SHA-256 separated by a tab, and terminating every line with LF has SHA-256 `1a768d888ab6ba5a84ad41c821817968459291156c1f86de13ff9fc7a7779635`. No raw content is committed.

Codex CLI 0.153.0 still emitted account-level remote catalog and an unauthorized Cloudflare startup warning even with disposable `apps = false`, `remote_plugin = false`, and no configured MCP servers. The warning returned 401/AuthRequired. There is no evidence that a benchmark fixture, credential, or unintended file was sent to that connector; this campaign therefore records the warning without claiming complete connector-process isolation.

## Interpretation boundary

The complete measurements describe this frozen task set and runtime only. Three repetitions per cell are reported as medians and ranges, with no statistical significance claim. The large C failure count prevents a truthful C-mode quality or efficiency advantage claim. There is no benchmark-leadership, general quality-superiority, latency-advantage, or universal context-reduction claim.

This campaign did not test plugin skill discovery. It preserves WS5's `NOT_RUN` status for that separate surface, preserves the CLI 0.153 boundary that plugin installation does not register custom agent roles, and does not infer Codex Desktop behavior.

## Deterministic validation

- Authenticated campaign validator: complete, expected 45, observed 45, blockers empty.
- Raw evidence inventory: 105 files (45 stdout JSONL, 45 stderr captures, 15 C hook captures).
- Sanitized dataset scan: passed.
- `python -B -m unittest tests.test_benchmark_contract -v` — 16 tests passed.
- `python -B -m unittest discover -s tests -p 'test_*.py'` — 231 tests passed. Expected negative-fixture diagnostics were printed; the suite exited successfully.
- `pwsh -NoProfile -File tests/Test-Install.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Verify.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Learning.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Mcp.ps1` — passed.
- `python -B tests/validate_content.py` — passed.
- `python -B -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json` — 12 claims and 12 compatibility surfaces passed.
- `python -B -m benchmarks.cli validate --cases benchmarks/cases --configurations benchmarks/configurations` — fixed protocol passed with 45 planned attempts.
- `python -B -m compileall -q benchmarks scripts tests release_contracts` — passed.
- `git diff --check` — passed; line-ending conversion warnings were informational.
- Disposable v3 auth home, user profile, and plugin copy were removed after the campaign. Ignored raw evidence was retained.
- Independent final review — passed with no material findings. It reproduced the 45-run inventory, dataset/methodology/raw-manifest hashes, all four passing C hook lifecycles, reset timing and receipt binding, sanitization, and disposable-state cleanup.

## Closure assessment

**WS6 is CLOSED.** All 45 counted runs are retained, the sanitized dataset and frozen methodology validate deterministically, regressions pass, independent review passes, and disposable auth/runtime state is removed.
