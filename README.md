# Codex Engineering Kit

> Evidence-bound engineering workflows for OpenAI Codex: native plugin packaging, focused skills and subagents, lifecycle guardrails, verification, evals, state/compaction, and release contracts.

**Status:** v0.2 alpha · evidence-bound release-candidate work · independent community project

Codex Engineering Kit (CEK) is an independent engineering toolkit for Codex. It turns planning, architecture, debugging, review, testing, security, performance work, and release readiness into explicit, inspectable contracts.

CEK is **not an official OpenAI or Anthropic project**. No endorsement is implied. Runtime claims are intentionally scoped to the exact evidence recorded in this repository.

## Release evidence first

v0.2 separates four kinds of statements:

| State | Meaning |
| --- | --- |
| **IMPLEMENTED** | Deterministic implementation/repository evidence exists. |
| **VERIFIED** | Exact runtime evidence supports the stated wording for the named runtime scope. |
| **LIMITED** | The implementation exists, but an unresolved runtime, measurement, or compatibility boundary prevents a broader claim. |
| **PLANNED** | Outside the current implemented boundary. |

Source-of-truth release documents:

- [`docs/release/compatibility-matrix.md`](docs/release/compatibility-matrix.md) — per-surface Codex CLI 0.147.0 / Desktop 0.152.0 status;
- [`docs/release/claim-evidence-matrix.md`](docs/release/claim-evidence-matrix.md) — allowed public wording and evidence for each v0.2 claim;
- [`docs/release/v0.2-rc-checklist.md`](docs/release/v0.2-rc-checklist.md) — release-candidate gates and blockers;
- [`docs/benchmark.md`](docs/benchmark.md) — fixed benchmark protocol and reporting boundary;
- [`docs/install.md`](docs/install.md) — managed lifecycle and ownership contract;
- [`SECURITY.md`](SECURITY.md) — trust, secret, hook, and local-state boundaries.

## Architecture and roadmap

- [`docs/architecture.md`](docs/architecture.md) — current implemented architecture vs approved v1 target;
- [`ROADMAP.md`](ROADMAP.md) — evidence-gated v0.2/v1 workstreams.

## What v0.2 contains

| Capability | Evidence-bound status |
| --- | --- |
| Native `.codex-plugin` packaging + repo-local marketplace | Runtime-verified on Codex CLI 0.147.0 and 0.153.0; Desktop 0.152.0 remains separately tracked. |
| 8 plugin-native skills | Packaged with deterministic content contracts; direct CLI 0.153.0 skill discovery remains `NOT_RUN`. |
| Native hooks through default `hooks/hooks.json` discovery | Runtime-verified on CLI 0.153.0; historical CLI 0.147.0 SessionEnd and Desktop 0.152.0 remain separate limitations. |
| Explicit manifest `hooks` override | Runtime-verified only on CLI 0.153.0; historical CLI 0.147.0 and Desktop 0.152.0 remain blocked. |
| 8 project-local native agent definitions | `reviewer` and `explorer` have CLI 0.153.0 lifecycle evidence; the other definitions have deterministic contracts only. |
| 9 parent-context role contracts | Implemented as orchestration references; they are not autonomous agents. |
| Bounded state + compaction continuation | Runtime-verified on CLI 0.147.0; Desktop 0.152.0 remains separately tracked. |
| Verification engine + deterministic eval tooling | Implemented and exercised by repository CI/contracts. |
| Manual Git-worktree conflict-stop/cleanup acceptance | Implemented; this is not a claim about Codex-managed Desktop worktrees. |
| Backend/frontend domain pattern skills | Implemented as optional, narrow evidence packs. |
| A/B/C context benchmark | Frozen authenticated campaign completed: 34 PASS / 11 retained FAIL; no superiority or statistical-significance claim. |
| Three-OS repository CI | Deterministic contracts run on Ubuntu, Windows, and macOS; this is not blanket Codex runtime compatibility. |

## Eight active skills

```text
orchestrator
continuous-learning
eval-harness
verification-loop
software-architecture
concurrency-performance
backend-patterns
frontend-patterns
```

The domain packs are optional in routing terms: they are loaded when backend or frontend implementation/review evidence calls for them rather than being treated as universal guidance.

The canonical shipped-asset inventory is `release_contracts/assets.json`. Skill `agents/openai.yaml` files are interface metadata, not agent definitions.

Here, plugin-native identifies the packaged skill class. Direct skill discovery on Codex CLI 0.153.0 remains `NOT_RUN`; file presence and packaging are not promoted to runtime-discovery evidence.

## Native Codex plugin structure

```text
codex-engineering-kit/
├── .codex-plugin/plugin.json       # native plugin manifest
├── .agents/plugins/marketplace.json# repo-local development marketplace
├── .codex/agents/                  # project-local custom subagents
├── hooks/hooks.json                # default native hook discovery
├── hooks/scripts/                  # bounded Python hook dispatcher
├── runtime/                        # versioned bounded local-state helpers
├── skills/                         # eight shipped skills
├── workflows/                      # explicit engineering workflows
├── benchmarks/                     # fixed benchmark protocol/reporting
├── release_contracts/              # machine-readable claim/compatibility data
├── scripts/                        # installer/verification/acceptance helpers
├── tests/                          # deterministic repository contracts
└── docs/                           # architecture, evidence, release matrices
```

## Requirements

- Git;
- OpenAI Codex for runtime/plugin use;
- **Python 3.11+ for v0.2 hook/runtime-dependent features and repository validation**;
- PowerShell 7+ only for the PowerShell installer/update/uninstall and related Windows-oriented helper flows.

The repository's deterministic CI covers Ubuntu, Windows, and macOS contracts. That CI coverage must not be read as proof that every Codex runtime feature behaves identically on every OS.

## Managed install, verification, update, and uninstall

Clone the repository:

```text
git clone https://github.com/aydemir0/codex-engineering-kit.git
cd codex-engineering-kit
```

The supported managed onboarding path requires Python 3.11+ and exactly Codex CLI 0.153.0. Run it from the repository root and provide the project that should receive the shipped project-local reviewer:

```text
python scripts/cek_lifecycle.py install --project <project-root>
python scripts/cek_lifecycle.py verify --project <project-root>
```

The install command registers the repository-local marketplace when needed, installs the native plugin into the selected `CODEX_HOME`, verifies the cached `.codex-plugin/plugin.json`, eight plugin-native skills, and `hooks/hooks.json`, and provisions `.codex/agents/reviewer.toml` into the project. It writes two ownership manifests: `$CODEX_HOME/codex-engineering-kit.install.json` for the managed plugin and `<project>/.codex/codex-engineering-kit.install.json` for the managed reviewer.

The reviewer is a Codex-native **project-local** agent. It is not a plugin-native custom agent. Plugin-native custom agents are unsupported/deferred on Codex CLI 0.153.0 because plugin installation does not register custom agent roles there.

Update, verify again, and uninstall with the same project and `CODEX_HOME`:

```text
python scripts/cek_lifecycle.py update --project <project-root>
python scripts/cek_lifecycle.py verify --project <project-root>
python scripts/cek_lifecycle.py uninstall --project <project-root>
python scripts/cek_lifecycle.py verify-clean --project <project-root>
```

The lifecycle refuses a pre-existing reviewer, a marketplace name bound to another checkout, modified managed content, an unsupported CLI version, and incomplete ownership state. Update replaces only hash-matched CEK-owned content. Uninstall delegates plugin/cache removal to Codex, removes a marketplace only when this lifecycle added it, removes the project-local reviewer only when its ownership hash still matches, and preserves unrelated or modified user files. The managed path does not copy `auth.json`, credentials, normal-profile configuration, or user-private skills.

The native plugin cache contains packaged skills and hooks; installation does not by itself prove interactive skill discovery. Runtime hook and reviewer claims remain scoped by the [compatibility matrix](docs/release/compatibility-matrix.md).

### Existing PowerShell skill installer

The toolkit-owned skill installer remains available:

```powershell
pwsh -NoProfile -File scripts/install.ps1 -DryRun
pwsh -NoProfile -File scripts/install.ps1
```

Its ownership model uses deterministic hashes, refuses unsafe overwrite by default, and backs up forced replacements. This installer is a separate delivery path from the native plugin acceptance surface.

The PowerShell installer owns six core skills; the optional domain packs are plugin-only.

## Native hooks and trust boundary

v0.2 ships `hooks/hooks.json` and bounded hook handlers for lifecycle evidence, state/compaction, and narrow PreToolUse deny/allow guardrails.

The primary plugin manifest intentionally **does not** add an explicit `hooks` field while RISK-001 remains unresolved. Plan F tests an explicit override only in a disposable copy. See the [compatibility matrix](docs/release/compatibility-matrix.md).

Hooks are guardrails, not a sandbox or a substitute for Codex trust/review controls. Python availability is required for the shipped Python hook dispatcher. See [SECURITY.md](SECURITY.md).

## Native subagents and bounded state

Project-local agent definitions live in `.codex/agents/`. On CLI 0.153.0, distinct project-local lifecycle evidence exists for the shipped `reviewer` and `explorer`; the remaining definitions are contract-validated but not individually runtime-smoked.

Plugin installation does not register custom agent roles on Codex CLI 0.153.0. Plugin-native custom agents are unsupported/deferred at that boundary; project-local provisioning is a separate mechanism. No Desktop behavior is inferred.

`.codex-kit` runtime state is local/ignored and uses bounded schemas. Read-only agent instructions are policy guidance, not an operating-system sandbox.

## Verification and evals

CEK prefers deterministic evidence when it can be obtained: exit codes, schema checks, tests, repository contracts, and file/state invariants take priority over model confidence.

Verification tooling discovers project-native gates where supported and reports missing evidence as missing/partial rather than converting it to success. The eval layer separates capability and regression checks and prefers deterministic graders before model-assisted judgment.

## Manual worktree acceptance

The repository includes deterministic acceptance for manual Git-worktree creation, isolated writes, conflict-stop behavior, cleanup, and residual-worktree checks.

This is deliberately narrow: it does **not** establish Codex Desktop-managed worktree behavior.

## Context benchmark protocol

The repository defines a fixed 45-run A/B/C protocol:

- A — naive always-loaded;
- B — progressive disclosure;
- C — isolated subagent.

The frozen campaign contains 45 authenticated runs with A 15/15 PASS, B 15/15 PASS, C 4/15 PASS, and 34 PASS / 11 retained FAIL overall. There was no retry or replacement of failed counted attempts. These descriptive measurements do not establish statistical significance, general efficiency, context reduction, latency advantage, quality superiority, or benchmark leadership. The unauthorized connector startup warning observed on CLI 0.153.0 remains documented; no connector isolation claim is inferred. See [`docs/research/evidence/codex-v1-ws6-benchmark.md`](docs/research/evidence/codex-v1-ws6-benchmark.md).

## Continuous learning

Continuous learning remains review-gated:

```text
completed work
  -> evidence extraction
  -> candidate normalization
  -> sensitive-data rejection
  -> deduplication
  -> confidence + scope
  -> pending_review
  -> human approval
```

Candidates are not automatically installed, promoted, or executed. Learned shell content is never an automatic execution source.

## MCP integrations

Secret-free metadata templates remain available for GitHub, Supabase, Vercel, Railway, and Cloudflare. Provider authentication remains local; generated templates do not contain credentials.

## Compatibility boundary

Tracked runtime baselines are:

- Codex CLI 0.147.0;
- Codex CLI 0.153.0;
- Codex Desktop bundled CLI 0.152.0.

CLI 0.153.0 has the current v1 bounded evidence. CLI 0.147.0 retains historical limitations, including SessionEnd classification and explicit-hook coverage. The Desktop 0.152.0 acceptance campaign remains blocked in the current execution harness and no CLI result is inferred as Desktop behavior.

Therefore v0.2 does not claim a fully verified compatibility window. Use the [compatibility matrix](docs/release/compatibility-matrix.md) for the exact surface-by-surface state.

## Development

Core deterministic checks include:

```text
python -m unittest tests.test_release_contract -v
python -m unittest tests.test_plugin_compatibility -v
python tests/validate_content.py
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Additional Plan D/E suites cover verification, evals, worktrees, domain packs, benchmark contracts, plugin/hook behavior, installer lifecycle, learning, and MCP configuration.

## Attribution

Codex Engineering Kit is an independent implementation. Some high-level workflow and agent-organization ideas were inspired by the MIT-licensed Everything Claude Code project by Affaan Mustafa. CEK's native Codex plugin, hook, subagent, state, verification, and release-contract implementation is maintained here and does not represent Claude-specific APIs as Codex behavior.

See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). No endorsement by OpenAI, Anthropic, or upstream project authors is implied.

## Contributing

Changes to the plugin manifest, native hooks, state schemas, custom agents, active skill surface, verification semantics, release evidence model, or installer ownership rules are architectural changes and should include corresponding deterministic contracts and bounded evidence.

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT License. See [`LICENSE`](LICENSE).
