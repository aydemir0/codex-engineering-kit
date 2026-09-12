# CEK v1 Evidence Index

This index maps the presentation layer to committed evidence. A document link
is not itself runtime proof; the linked record states the applicable revision,
runtime, deterministic checks, and remaining limitations.

| Workstream | Closed scope | Primary evidence | Deterministic contract |
| --- | --- | --- | --- |
| WS1 | Truth surface and bounded public wording | `docs/release/claim-evidence-matrix.md`; `docs/release/compatibility-matrix.md`; `release_contracts/claims.json`; `release_contracts/compatibility.json` | `tests/test_release_contract.py` |
| WS2 | Codex CLI 0.153.0 runtime closure | `docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md` | `tests/test_v1_runtime_contract.py` |
| WS3 | Representative RED-to-GREEN workflow and distinct reviewer | `docs/research/evidence/codex-v1-representative-workflow.md` | `tests/test_workflow_evidence.py`; `tests/fixtures/representative-workflow/` |
| WS4 | Security threat/contract scope | `docs/research/evidence/codex-v1-ws4-security.md`; `SECURITY.md` | `tests/test_security_contract.py`; `tests/test_state_contract.py` |
| WS5 | Skill, agent, and parent-context role stocktake | `docs/research/evidence/codex-v1-ws5-skill-agent-stocktake.md`; `release_contracts/assets.json` | `tests/test_asset_stocktake.py`; `tests/test_agent_contract.py` |
| WS6 | Frozen authenticated benchmark | `docs/research/evidence/codex-v1-ws6-benchmark.md`; `benchmarks/results/ws6-cli01530-v3.json` | `tests/test_benchmark_contract.py` |
| WS7 | Clean install, update, uninstall, ownership, and reviewer provisioning | `docs/research/evidence/codex-v1-ws7-clean-install.md`; `docs/research/evidence/codex-v1-ws7-clean-install.json` | `tests/test_clean_install_lifecycle.py`; `tests/test_clean_install_docs.py` |
| WS8 | Evidence-bound OpenAI/Codex presentation and reproducible demo | `docs/research/evidence/codex-v1-ws8-presentation.md`; `docs/presentation/openai-project-brief.md`; `docs/demo/representative-workflow.md` | `tests/test_presentation_contract.py` |

## Presentation claim map

| Material claim | Source of truth |
| --- | --- |
| Exact runtime and support boundaries | `docs/release/compatibility-matrix.md` and the WS2 runtime record |
| Plugin-native skill count and discovery limitation | `release_contracts/assets.json`, WS5 evidence, and `skills-eight` in `docs/release/claim-evidence-matrix.md` |
| Project-local reviewer/explorer lifecycle | WS2 and WS3 evidence plus `native-subagents` in the claim matrix |
| Hooks and state behavior | WS2 and WS4 evidence; `SECURITY.md` |
| 45-run totals and all 11 retained failures | `benchmarks/results/ws6-cli01530-v3.json` and WS6 evidence |
| Managed lifecycle and ownership safety | WS7 JSON/Markdown evidence and `managed-install-lifecycle` in the claim matrix |
| Independent community-project status | `README.md`, `.codex-plugin/plugin.json`, and `THIRD_PARTY_NOTICES.md` |

## Limits that must travel with the claims

- CLI 0.153.0 evidence is not Codex Desktop evidence.
- Direct CLI 0.153.0 skill discovery remains `NOT_RUN`.
- Plugin-native custom-agent registration is unsupported/deferred on CLI
  0.153.0; the evidenced reviewer and explorer are project-local.
- The other six shipped project-local agent definitions are contract-only.
- Hooks are not a sandbox.
- The WS6 unauthorized connector startup warning remains documented.
- The benchmark makes no general efficiency, context-reduction, latency,
  quality-superiority, statistical-significance, or leadership claim.
- CEK is independent and does not imply OpenAI endorsement or verification.
