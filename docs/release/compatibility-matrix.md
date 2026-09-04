# v0.2 Compatibility Matrix

This matrix is the human-readable projection of `release_contracts/compatibility.json`. `PASS` is scoped to the named runtime and cited evidence only. `BLOCKED` means the required exact-runtime acceptance could not be executed; it is not converted to PASS by CI or by evidence from another runtime.

| Surface ID | Codex CLI 0.147.0 | Desktop 0.152.0 | Evidence / limitation |
| --- | --- | --- | --- |
| `plugin-discovery` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plugin-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `marketplace-install-list` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plugin-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `skill-discovery` | BLOCKED | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI: No committed 0.147.0 artifact directly proves this surface and the exact runtime is unavailable for a fresh Plan F check.<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `default-hooks` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `explicit-hooks` | BLOCKED | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI: RISK-001 explicit manifest hook override could not be launched because the exact CLI 0.147.0 binary is unavailable.<br>Desktop: RISK-001 explicit manifest hook override could not be launched because Desktop 0.152.0 is unavailable. |
| `hook-lifecycle` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `pretool-deny-allow` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `native-subagent` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `compaction-state` | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `session-end` | BLOCKED | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI: Historical graceful SessionEnd execution exists, but the 0.147.0 timeout-budget discrepancy cannot be rerun in this harness.<br>Desktop: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `interactive-plugin-discovery` | BLOCKED | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI: No exact-runtime interactive surface is available in the Plan F execution harness.<br>Desktop: Desktop 0.152.0 interactive UI is unavailable in the Plan F execution harness. |
| `desktop-parent-wait` | NOT_RUN | BLOCKED | `docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI: Desktop-specific surface; deliberately not applicable to the CLI baseline.<br>Desktop: Bounded Desktop reviewer rerun is unavailable; prior parent-wait observation remains unclassified. |

## Open compatibility risks

### RISK-001 — explicit manifest hooks override

`explicit-hooks` is BLOCKED on both declared baselines. The primary `.codex-plugin/plugin.json` therefore continues to omit an explicit `hooks` field. RISK-001 remains open until a disposable explicit-manifest variant passes on both Codex CLI 0.147.0 and Desktop 0.152.0.

### RISK-002 — runtime skew

Codex CLI 0.147.0 has bounded PASS evidence for several surfaces; Desktop 0.152.0 is BLOCKED in the current Plan F execution harness. No evidence from one baseline is promoted to the other. RISK-002 remains open.

### SessionEnd discrepancy

Historical CLI 0.147.0 runs observed graceful SessionEnd behavior, but the timeout-budget discrepancy cannot be rerun with the exact baseline in this harness. `session-end` remains BLOCKED rather than being promoted from historical execution alone.

### Desktop parent-wait observation

`desktop-parent-wait` remains BLOCKED for Desktop 0.152.0. The bounded reviewer rerun is unavailable here, so the prior observation remains unclassified and no root cause is asserted.

## Compatibility claim boundary

The repository does not claim blanket cross-platform Codex runtime compatibility or a fully verified 0.147.0–0.152.0 window. Deterministic repository CI across Ubuntu, Windows, and macOS is a separate claim from runtime compatibility.
