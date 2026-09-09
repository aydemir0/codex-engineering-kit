# CEK v1 WS5 Skill/Agent Stocktake Evidence

Date: 2026-09-09  
Baseline: `eea6f836ca995e23787cc3fd0309fb22de3792de`  
Final implementation commit: `f3379f26ec0b8e2aa89adf9df13f3f43fc1bfb52`  
Branch: `feat/v1-core-workflow`

## Acceptance contract

WS5 requires a complete, deterministic inventory of shipped skills, project-local native agent definitions, and parent-context role contracts. Each asset must appear exactly once with its activation, output, mutation, overlap, and runtime-support boundary. Counts and public wording must distinguish those classes, plugin-installed custom agents must not be claimed on Codex CLI 0.153.0, and no asset may be added or removed without deterministic evidence.

## Root cause and RED evidence

The repository had no canonical asset inventory. Counts, cross-class relationships, runtime support, and delivery distinctions were maintained independently across documentation, tests, plugin metadata, and the PowerShell installer.

Before implementation:

- `python -B -m unittest tests.test_asset_stocktake -v` ran 11 tests and failed 10. The missing `release_contracts/assets.json`, stale contribution count, generalized agent wording, missing class-specific documentation, and absent CI gate caused the failures.
- After the first inventory pass, the installer regression output exposed a second delivery distinction: the plugin packages eight skills while the ownership-aware PowerShell installer intentionally names six core skills. `test_powershell_installer_subset_is_explicit` failed before that distinction was recorded.

## Deterministic inventory

`release_contracts/assets.json` contains 25 primary asset records:

| Asset class | Count | Support boundary |
| --- | ---: | --- |
| Plugin-native skills | 8 | Packaged through `.codex-plugin/plugin.json` and its `./skills/` declaration; CLI 0.153.0 skill discovery is `NOT_RUN`. |
| Project-local native agent definitions | 8 | Provisioned from `.codex/agents/*.toml`; not registered by plugin installation on CLI 0.153.0. |
| Parent-context role contracts | 9 | Loaded as orchestrator references; never evidence that a child agent ran. |

The inventory also records six intentional role-to-agent responsibility mappings, three parent-only roles (`doc-updater`, `planner`, `tdd-guide`), and two agent-only definitions (`docs-researcher`, `explorer`). Skill `agents/openai.yaml` files are interface metadata and are excluded from agent counts.

## Runtime and delivery boundary

- CEK packages eight plugin-native skill assets. Direct Codex CLI 0.153.0 skill discovery is `NOT_RUN`; packaging is not runtime-discovery evidence.
- Plugin installation does not register custom agent roles on Codex CLI 0.153.0. Plugin-native custom agents remain unsupported/deferred.
- Direct CLI 0.153.0 lifecycle evidence exists for the project-local `reviewer` and `explorer` definitions. The other six project-local definitions have deterministic repository contracts only and were not promoted to runtime-verified status.
- No Codex Desktop behavior is inferred.
- The separate PowerShell ownership installer names six core skills. `backend-patterns` and `frontend-patterns` are plugin-only optional domain packs; WS5 did not expand installer behavior.

## Duplicate, dead, stale, and conflicting asset assessment

- Exact SHA-256 comparison found no duplicate primary asset contents.
- Every parent-context role is routed by the orchestrator; there are no phantom routed roles.
- Every discovered skill, agent definition, and role contract is represented exactly once in the inventory.
- Cross-class name or responsibility overlap is recorded explicitly and is not treated as file duplication.
- No asset deletion was justified. Lack of individual runtime smoke for six agent definitions is recorded as `contract-only-project-local`, not misclassified as dead code.
- Stale six-skill contribution wording and generalized native-subagent wording were reconciled. Admission criteria now require a workflow gap, activation boundary, overlap analysis, context-cost rationale, tests/eval story, maintenance owner, and public-evidence impact.

## GREEN evidence

Fresh checks against the final implementation tree committed as `f3379f26ec0b8e2aa89adf9df13f3f43fc1bfb52`:

- `python -B -m unittest tests.test_asset_stocktake tests.test_architecture_contract tests.test_release_contract -v` — 36 tests passed.
- `python -B tests/validate_content.py` — passed.
- `python -B -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json` — 12 claims and 12 compatibility surfaces passed.
- `python -B -m unittest discover -s tests -p 'test_*.py'` — 209 tests passed after removing only generated `__pycache__` directories created by a prior compile check.
- `pwsh -NoProfile -File tests/Test-Install.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Verify.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Learning.ps1` — passed.
- `pwsh -NoProfile -File tests/Test-Mcp.ps1` — passed.
- `git diff --check` — passed; line-ending conversion warnings were informational.

The full Python suite prints expected error text from negative fixtures for incomplete lifecycle evidence and malformed repository SHA; the suite exits successfully.

## Change and hygiene boundary

WS5 adds the canonical inventory and its contract test, updates CI and stocktake-related documentation/release wording, and adjusts two older architecture assertions to the truthful class names. No skill, native agent definition, or parent-context role was added, removed, or renamed. Closed WS1-WS4 implementation surfaces were not reopened.

The pre-existing untracked `.serena/` directory is excluded from WS5 and remains untouched. No credential, private runtime transcript, disposable authentication state, absolute user path, or raw child-agent payload is included here. No push, merge, publish, tag, or release was performed.

## Closure gate

The independent reviewer found two material claim/evidence gaps: the reviewer lifecycle source was absent from the native-subagent claim, and plugin-native skill packaging was incorrectly described as CLI 0.153 runtime support. Both findings were reproduced with failing assertions and fixed before this document was committed. Exact final-boundary confirmation is required after the evidence commit; no closure is inferred from the draft review.
