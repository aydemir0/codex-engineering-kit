# Roadmap

Codex Engineering Kit prioritizes evidence and bounded compatibility over expanding claims. v1.0.0 is the current release candidate; release readiness depends on the exact-candidate gate rather than the version label alone.

## v0.1 — Engineering foundation

The original foundation established repository-first architecture guidance, verification/eval workflows, review-gated learning, PowerShell installer ownership rules, secret-free MCP metadata, and deterministic content/behavior contracts.

## v0.2 — Historical native integration campaign

Implemented or evidence-tracked slices:

- **native plugin + marketplace** — `.codex-plugin/plugin.json` and repo-local marketplace integration;
- **runtime + hooks** — native `hooks/hooks.json`, bounded dispatcher behavior, and explicit-manifest compatibility experiment tooling;
- **custom subagents + state/compaction** — project-local agents, versioned bounded state, compaction continuation, and corruption recovery;
- **verification + evals** — verification engine, deterministic eval graders, authenticated-pressure helper, and evidence-oriented readiness semantics;
- **manual worktree + domain packs + benchmark protocol** — deterministic Git-worktree acceptance, backend/frontend pattern skills, and fixed A/B/C context benchmark protocol;
- **release evidence + compatibility** — machine-readable claims/compatibility data, human-readable matrices, public-claim boundaries, and RC gates.

The historical v0.2 campaign established the architecture and earlier runtime evidence. Its checklist remains a historical snapshot, not the current v1 release decision.

Historical and current compatibility limitations remain explicit:

- Desktop bundled Codex 0.152.0 Plan F acceptance is blocked in the current execution harness;
- RISK-001 explicit manifest hooks override is not proven on both declared baselines;
- RISK-002 runtime skew remains open;
- CLI 0.147.0 SessionEnd timeout-budget classification remains unresolved;
- the prior Desktop parent-wait observation remains unclassified;
- no CLI result is promoted to Codex Desktop behavior.

## v1.0 — OpenAI-ready Codex-native engineering system

v1.0 is an evidence-gated program, not a catalog-size target. The approved architecture and execution program are:

- [`docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`](docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md)
- [`docs/superpowers/plans/2026-09-05-v1-openai-ready-master.md`](docs/superpowers/plans/2026-09-05-v1-openai-ready-master.md)

The workstreams were executed in this order:

1. truth surface reconciliation;
2. runtime closure;
3. core workflow hardening;
4. security hardening;
5. skill/agent stocktake;
6. authenticated 45-run benchmark;
7. clean-install UX;
8. OpenAI-ready presentation;
9. exact-SHA/provenance v1.0 release gate.

WS1 through WS8 are closed. WS9 remains the exact-SHA release gate. A workstream is complete only when its tests/evidence pass; v1.0.0 is not release-ready merely because the roadmap item exists.

The authenticated benchmark is complete with 45 authenticated runs: A 15/15 PASS, B 15/15 PASS, C 4/15 PASS, and 34 PASS / 11 retained FAIL, comprising 9 missing-lifecycle failures and 2 quality-contract failures. The failures were not retried or replaced. These measurements do not support an efficiency, context-reduction, latency, quality-superiority, statistical-significance, or benchmark-leadership claim.

## Next release-readiness work

- execute the exact Desktop 0.152.0 compatibility campaign in a suitable operator environment;
- execute explicit-manifest hook acceptance on both declared baselines;
- rerun and classify the SessionEnd timeout behavior;
- rerun the bounded Desktop parent-wait case without assigning a root cause in advance;
- reconcile release metadata/public surfaces;
- obtain fresh exact-candidate CI and close only the proven release gate;
- publish a release only after the RC checklist permits it.

## Future work

- additional benchmark campaigns only under a separately frozen methodology;
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
