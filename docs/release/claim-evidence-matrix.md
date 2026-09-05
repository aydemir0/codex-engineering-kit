# v0.2 Claim-to-Evidence Matrix

Public wording must be no broader than the `Allowed public wording` column. `VERIFIED` is always runtime-scoped; `IMPLEMENTED` is not a runtime-compatibility claim; `LIMITED` preserves the named unresolved boundary.

Declared runtime baselines: Codex CLI 0.147.0 and Codex Desktop 0.152.0.

| Claim ID | State | Allowed public wording | Evidence | Limitation / runtime scope |
| --- | --- | --- | --- | --- |
| `plugin-packaging` | VERIFIED | Native plugin packaging and repo-local marketplace integration are runtime-verified on Codex CLI 0.147.0; Desktop 0.152.0 remains separately tracked. | `.codex-plugin/plugin.json`<br>`.agents/plugins/marketplace.json`<br>`tests/test_plugin_contract.py`<br>`docs/research/evidence/codex-cli-0.147.0-plugin-acceptance.md` | Desktop 0.152.0 plugin discovery and install/list behavior remain blocked in the Plan F campaign.<br>Runtime scope: Codex CLI 0.147.0 |
| `skills-eight` | IMPLEMENTED | The repository ships eight skills with deterministic content contracts. | `tests/validate_content.py`<br>`skills/backend-patterns/SKILL.md`<br>`skills/frontend-patterns/SKILL.md` | — |
| `native-hooks-default` | LIMITED | Native hook handlers and default hook discovery have scoped Codex CLI 0.147.0 evidence; SessionEnd and Desktop 0.152.0 remain explicit limitations. | `hooks/hooks.json`<br>`tests/test_hook_contract.py`<br>`tests/test_hook_dispatch.py`<br>`docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md` | Default discovery and bounded lifecycle behavior have scoped CLI 0.147.0 evidence, but the SessionEnd timeout-budget discrepancy is unresolved and Desktop 0.152.0 is blocked.<br>Runtime scope: Codex CLI 0.147.0 |
| `native-subagents` | VERIFIED | Project-local Codex-native subagent lifecycle is runtime-verified on Codex CLI 0.147.0; Desktop 0.152.0 remains separately tracked. | `.codex/agents/reviewer.toml`<br>`tests/test_agent_contract.py`<br>`docs/research/evidence/codex-cli-0.147.0-native-reviewer-subagent-acceptance.md`<br>`docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md` | Desktop 0.152.0 native-subagent behavior remains blocked in the Plan F campaign.<br>Runtime scope: Codex CLI 0.147.0 |
| `state-compaction` | VERIFIED | Bounded state persistence and compaction continuation are runtime-verified on Codex CLI 0.147.0; Desktop 0.152.0 remains separately tracked. | `tests/test_hook_dispatch.py`<br>`runtime/state.py`<br>`docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-cli-0.147.0-plan-c-corruption-recovery-acceptance.md` | Desktop 0.152.0 compaction/state behavior remains blocked in the Plan F campaign.<br>Runtime scope: Codex CLI 0.147.0 |
| `verification-evals` | IMPLEMENTED | Verification and deterministic eval tooling are implemented and exercised in the repository CI matrix. | `tests/test_verification_engine.py`<br>`tests/test_eval_runner.py`<br>`.github/workflows/ci.yml`<br>`docs/research/evidence/codex-cli-0.147.0-plan-d-pressure-rerun-acceptance.md` | Runtime scope: Codex CLI 0.147.0 |
| `manual-worktrees` | IMPLEMENTED | Manual Git-worktree conflict-stop and cleanup invariants are covered by deterministic acceptance; this is not a claim about Codex-managed Desktop worktrees. | `tests/test_worktree_acceptance.py`<br>`docs/research/evidence/plan-e-manual-worktree-acceptance.md` | — |
| `domain-packs` | IMPLEMENTED | Optional backend and frontend pattern skills are implemented with narrow repository-evidence contracts. | `skills/backend-patterns/SKILL.md`<br>`skills/frontend-patterns/SKILL.md`<br>`tests/test_domain_skills.py` | — |
| `context-benchmark-protocol` | IMPLEMENTED | A fixed 45-run context benchmark protocol and report engine are implemented; no measured lean or context-efficiency result is claimed. | `benchmarks/model.py`<br>`benchmarks/report.py`<br>`tests/test_benchmark_contract.py`<br>`docs/benchmark.md` | — |
| `three-os-ci` | IMPLEMENTED | Deterministic repository contracts run across Ubuntu, Windows, and macOS; this does not establish blanket Codex runtime compatibility across those operating systems. | `.github/workflows/ci.yml` | — |
| `compatibility-window` | LIMITED | Compatibility is tracked separately for Codex CLI 0.147.0 and Desktop 0.152.0; unresolved or unavailable surfaces remain explicitly limited. | `docs/superpowers/specs/2026-09-05-v0.2-release-evidence-compatibility-design.md`<br>`docs/superpowers/plans/2026-09-03-codex-engineering-kit-v0.2-master.md`<br>`release_contracts/compatibility.json`<br>`docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md` | Desktop 0.152.0 required surfaces are blocked in the current execution harness; explicit manifest hooks are blocked on both baselines; SessionEnd and Desktop parent-wait remain unresolved.<br>Runtime scope: Codex CLI 0.147.0; Codex Desktop 0.152.0 |

## Benchmark boundary

`context-benchmark-protocol` links `docs/benchmark.md` and the deterministic benchmark/report contracts. The fixed 45-run A/B/C campaign definition and synthetic reporting fixtures are not measured context-efficiency evidence. No measured `lean`, `leaner`, token-savings, or efficiency result is claimed until a real authenticated campaign is completed.

## CI boundary

`three-os-ci` describes deterministic repository contracts on Ubuntu, Windows, and macOS. It does not establish blanket Codex runtime compatibility on those operating systems.

## Worktree boundary

`manual-worktrees` covers the repository's bounded manual Git-worktree acceptance invariants. It does not claim Codex-managed Desktop worktree behavior.
