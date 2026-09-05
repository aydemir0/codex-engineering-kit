# Roadmap

Codex Engineering Kit prioritizes evidence and bounded compatibility over expanding claims. The v0.2 branch is an evidence-bound alpha/release-candidate workstream, not a completed public release.

## v0.1 — Engineering foundation

The original foundation established repository-first architecture guidance, verification/eval workflows, review-gated learning, PowerShell installer ownership rules, secret-free MCP metadata, and deterministic content/behavior contracts.

## v0.2 — Native Codex engineering kit + release evidence

Implemented or evidence-tracked slices:

- **native plugin + marketplace** — `.codex-plugin/plugin.json` and repo-local marketplace integration;
- **runtime + hooks** — native `hooks/hooks.json`, bounded dispatcher behavior, and explicit-manifest compatibility experiment tooling;
- **custom subagents + state/compaction** — project-local agents, versioned bounded state, compaction continuation, and corruption recovery;
- **verification + evals** — verification engine, deterministic eval graders, authenticated-pressure helper, and evidence-oriented readiness semantics;
- **manual worktree + domain packs + benchmark protocol** — deterministic Git-worktree acceptance, backend/frontend pattern skills, and fixed A/B/C context benchmark protocol;
- **release evidence + compatibility** — machine-readable claims/compatibility data, human-readable matrices, public-claim boundaries, and RC gates.

Current v0.2 limitations remain explicit:

- Desktop bundled Codex 0.152.0 Plan F acceptance is blocked in the current execution harness;
- RISK-001 explicit manifest hooks override is not proven on both declared baselines;
- RISK-002 runtime skew remains open;
- CLI 0.147.0 SessionEnd timeout-budget classification remains unresolved;
- the prior Desktop parent-wait observation remains unclassified;
- the real authenticated 45-run benchmark campaign has not been completed, so no measured context-efficiency result is claimed.

## v1.0 — OpenAI-ready Codex-native engineering system

v1.0 is an evidence-gated program, not a catalog-size target. The approved architecture and execution program are:

- [`docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`](docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md)
- [`docs/superpowers/plans/2026-09-05-v1-openai-ready-master.md`](docs/superpowers/plans/2026-09-05-v1-openai-ready-master.md)

The workstreams close in this order:

1. truth surface reconciliation;
2. runtime closure;
3. core workflow hardening;
4. security hardening;
5. skill/agent stocktake;
6. authenticated 45-run benchmark;
7. clean-install UX;
8. OpenAI-ready presentation;
9. exact-SHA/provenance v1.0 release gate.

A workstream is complete only when its tests/evidence pass. v1.0 is not release-ready merely because the roadmap item exists.

## Next release-readiness work

- execute the exact Desktop 0.152.0 compatibility campaign in a suitable operator environment;
- execute explicit-manifest hook acceptance on both declared baselines;
- rerun and classify the SessionEnd timeout behavior;
- rerun the bounded Desktop parent-wait case without assigning a root cause in advance;
- complete release metadata/public-surface audit;
- obtain fresh exact-head Plan F CI and close only the proven implementation gate;
- publish a release only after the RC checklist permits it.

## Future work

- real authenticated context benchmark campaign and evidence-backed performance reporting;
- broader version-by-version Codex compatibility coverage;
- Linux/macOS installer parity where the installer ownership contract can be preserved and tested;
- richer verification adapters for additional project ecosystems;
- signed/reproducible release artifacts;
- broader MCP setup validation without embedding credentials;
- public release packaging/distribution after release evidence is complete.

## Non-goals unless the architecture changes

The project does not prioritize:

- a large marketplace of overlapping always-loaded skills;
- representing another coding agent's lifecycle API as Codex behavior;
- remote telemetry by default;
- silent promotion of learned session output;
- autonomous destructive changes to user repositories;
- storing integration credentials in repository configuration;
- claiming runtime compatibility or performance results that were not actually measured.
