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
- [`SECURITY.md`](SECURITY.md) — trust, secret, hook, and local-state boundaries.

## Architecture and roadmap

- [`docs/architecture.md`](docs/architecture.md) — current implemented architecture vs approved v1 target;
- [`ROADMAP.md`](ROADMAP.md) — evidence-gated v0.2/v1 workstreams.

## What v0.2 contains

| Capability | Evidence-bound status |
| --- | --- |
| Native `.codex-plugin` packaging + repo-local marketplace | Runtime-verified on Codex CLI 0.147.0; Desktop 0.152.0 remains separately tracked. |
| Eight shipped skills | Implemented with deterministic content contracts. |
| Native hooks through default `hooks/hooks.json` discovery | Scoped CLI 0.147.0 evidence; SessionEnd and Desktop 0.152.0 remain limitations. |
| Explicit manifest `hooks` override | Experimental/disposable helper exists; runtime acceptance is still blocked on both declared baselines. |
| Project-local Codex-native subagents | Runtime-verified on CLI 0.147.0; Desktop 0.152.0 remains separately tracked. |
| Bounded state + compaction continuation | Runtime-verified on CLI 0.147.0; Desktop 0.152.0 remains separately tracked. |
| Verification engine + deterministic eval tooling | Implemented and exercised by repository CI/contracts. |
| Manual Git-worktree conflict-stop/cleanup acceptance | Implemented; this is not a claim about Codex-managed Desktop worktrees. |
| Backend/frontend domain pattern skills | Implemented as optional, narrow evidence packs. |
| A/B/C context benchmark protocol | Fixed 45-run protocol/report engine implemented; no measured efficiency or lean result is claimed. |
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

## Native plugin quick start

Clone the repository:

```text
git clone https://github.com/aydemir0/codex-engineering-kit.git
cd codex-engineering-kit
```

The Codex CLI 0.147.0 acceptance record proves this repo-local marketplace/install boundary:

```text
codex plugin marketplace add <repo-root> --json
codex plugin marketplace list --json
codex plugin list --available --json
codex plugin add codex-engineering-kit@codex-engineering-kit-dev --json
codex plugin list --json
```

That evidence is scoped to Codex CLI 0.147.0. Before treating another runtime as supported, check the [compatibility matrix](docs/release/compatibility-matrix.md).

### Existing PowerShell skill installer

The toolkit-owned skill installer remains available:

```powershell
pwsh -NoProfile -File scripts/install.ps1 -DryRun
pwsh -NoProfile -File scripts/install.ps1
```

Its ownership model uses deterministic hashes, refuses unsafe overwrite by default, and backs up forced replacements. This installer is a separate delivery path from the native plugin acceptance surface.

## Native hooks and trust boundary

v0.2 ships `hooks/hooks.json` and bounded hook handlers for lifecycle evidence, state/compaction, and narrow PreToolUse deny/allow guardrails.

The primary plugin manifest intentionally **does not** add an explicit `hooks` field while RISK-001 remains unresolved. Plan F tests an explicit override only in a disposable copy. See the [compatibility matrix](docs/release/compatibility-matrix.md).

Hooks are guardrails, not a sandbox or a substitute for Codex trust/review controls. Python availability is required for the shipped Python hook dispatcher. See [SECURITY.md](SECURITY.md).

## Native subagents and bounded state

Project-local agent definitions live in `.codex/agents/`. CLI 0.147.0 evidence covers a real custom-agent lifecycle and bounded state/compaction continuation.

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

The protocol, fixtures, validator, and report engine are implemented. The authenticated 45-run campaign has not been completed, so CEK does not claim measured token savings, measured context efficiency, or a lean/leaner performance result. See [`docs/benchmark.md`](docs/benchmark.md).

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

Declared Plan F baselines are:

- Codex CLI 0.147.0;
- Codex Desktop bundled CLI 0.152.0.

The first baseline has bounded PASS evidence for selected surfaces. The Desktop 0.152.0 acceptance campaign is blocked in the current execution harness, and explicit manifest hooks are blocked on both baselines. SessionEnd timeout classification and the prior Desktop parent-wait observation also remain unresolved.

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
