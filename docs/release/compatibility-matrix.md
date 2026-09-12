# v1 Compatibility Matrix

This matrix is the human-readable projection of `release_contracts/compatibility.json`. `PASS` is scoped to the named runtime and cited evidence only. Evidence is never promoted across runtimes.

Runtime boundaries retained by the contract:

- Codex CLI 0.147.0 — historical compatibility evidence
- Codex CLI 0.153.0 — fresh v1 runtime-closure evidence
- Codex Desktop 0.152.0 — separately tracked and currently blocked where noted

| Surface ID | Codex CLI 0.147.0 | Codex CLI 0.153.0 | Codex Desktop 0.152.0 | Evidence / limitation |
| --- | --- | --- | --- | --- |
| `plugin-discovery` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plugin-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `marketplace-install-list` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plugin-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `skill-discovery` | BLOCKED | NOT_RUN | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.147.0: No committed 0.147.0 artifact directly proves this surface and the exact runtime is unavailable for a fresh Plan F check.<br>CLI 0.153.0: Direct CLI 0.153.0 runtime observation of project skill discovery was not established.<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `default-hooks` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `explicit-hooks` | BLOCKED | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.147.0: RISK-001 explicit manifest hook override could not be launched because the exact CLI 0.147.0 binary is unavailable.<br>Desktop 0.152.0: RISK-001 explicit manifest hook override could not be launched because Desktop 0.152.0 is unavailable. |
| `hook-lifecycle` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `pretool-deny-allow` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `native-subagent` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-v1-representative-workflow.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.153.0: Project-local `explorer` and `reviewer` lifecycle evidence passed. The other six definitions are contract-only. Plugin installation does not register custom agent roles on CLI 0.153.0.<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness; no Desktop behavior is inferred. |
| `compaction-state` | PASS | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.153.0: Manual PreCompact/PostCompact, schema-v1 checkpoint, resumed continuation, and unsupported-schema recovery passed; SessionStart source=compact was not observed in the manual resume path.<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `session-end` | BLOCKED | PASS | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.147.0: Historical graceful SessionEnd execution exists, but the 0.147.0 timeout-budget discrepancy cannot be rerun in this harness.<br>Desktop 0.152.0: Exact Desktop 0.152.0 runtime is unavailable in the Plan F execution harness. |
| `interactive-plugin-discovery` | BLOCKED | NOT_RUN | BLOCKED | `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.147.0: No exact-runtime interactive surface is available in the Plan F execution harness.<br>CLI 0.153.0: No separate interactive plugin-discovery acceptance was classified on CLI 0.153.0.<br>Desktop 0.152.0: Desktop 0.152.0 interactive UI is unavailable in the Plan F execution harness. |
| `managed-install-lifecycle` | NOT_RUN | PASS | BLOCKED | `docs/research/evidence/codex-v1-ws7-clean-install.md`<br>`docs/research/evidence/codex-v1-ws7-clean-install.json`<br>`docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.147.0: The v1 managed lifecycle intentionally requires CLI 0.153.0.<br>CLI 0.153.0: Project-local reviewer provisioning is separate from plugin-native custom-agent registration; interactive skill discovery is not claimed.<br>Desktop 0.152.0: CLI evidence is not promoted to Desktop behavior. |
| `desktop-parent-wait` | NOT_RUN | NOT_RUN | BLOCKED | `docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md`<br>CLI 0.147.0: Desktop-specific surface; deliberately not applicable to the CLI baseline.<br>CLI 0.153.0: Desktop-specific surface; not applicable to the CLI 0.153.0 baseline.<br>Desktop 0.152.0: Bounded Desktop reviewer rerun is unavailable; prior parent-wait observation remains unclassified. |

## Open compatibility risks

### RISK-001 -- explicit manifest hooks override

Status: CLOSED (v1 scoped)

The v1 public support claim for explicit manifest hooks is Codex CLI 0.153.0 only. The `explicit-hooks` surface is PASS at that runtime boundary.

Support on historical Codex CLI 0.147.0 and Codex Desktop 0.152.0 is not claimed for this v1 explicit-hook support surface; both tracked results remain BLOCKED.

This scoped closure does not convert either BLOCKED result to PASS, does not establish Codex Desktop support, and does not promote CLI 0.153.0 evidence to another runtime.

The shipped primary `.codex-plugin/plugin.json` continues to omit an explicit `hooks` override and relies on default `hooks/hooks.json` discovery.

### RISK-002 — runtime skew

Fresh Codex CLI 0.153.0 results are not promoted to historical CLI 0.147.0 or Codex Desktop 0.152.0. Each runtime retains its own surface classification.

### SessionEnd boundary

`session-end` is BLOCKED on historical CLI 0.147.0, PASS on fresh CLI 0.153.0 with graceful and timeout behavior tested separately, and BLOCKED on Codex Desktop 0.152.0.

### Desktop parent-wait

`desktop-parent-wait` remains BLOCKED for Codex Desktop 0.152.0. CLI evidence is not used to classify this Desktop-only surface.

## Compatibility claim boundary

The repository does not claim blanket cross-platform Codex runtime compatibility. Codex CLI 0.153.0 has fresh scoped v1 evidence; CLI 0.147.0 is retained as historical evidence; Codex Desktop 0.152.0 remains separately blocked/unverified where shown.
