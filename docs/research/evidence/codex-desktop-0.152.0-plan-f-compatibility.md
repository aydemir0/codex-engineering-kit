# Codex Desktop 0.152.0 Plan F Compatibility Evidence

Date: 2026-09-05
Platform: ChatGPT execution harness, Linux x86_64; Codex Desktop runtime unavailable in this harness
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit: `88096382e4b5a467930ed72d23eccb2e0ae72fa0`
Plugin version: `0.2.0-alpha.1`
Exact runtime version: not observed; `CEK_CODEX_DESKTOP_0152` was unset and no Desktop-bundled Codex runtime is available in this execution harness

## Results

- Default-hook result: **BLOCKED**.
- Explicit-manifest result: **BLOCKED**.
- Plugin/marketplace/skill discovery result: **BLOCKED**.
- Hook lifecycle result: **BLOCKED**.
- PreToolUse allow/deny result: **BLOCKED**.
- Subagent result: **BLOCKED**.
- Compaction result: **BLOCKED**.
- SessionEnd result or limitation: **BLOCKED**.
- Interactive discovery result: **BLOCKED**.
- Desktop wait result: **BLOCKED**. The prior parent-wait observation remains unclassified because the bounded reviewer acceptance cannot be rerun in this harness.

Every result above is blocked for the same bounded reason: the exact Desktop-bundled 0.152.0 runtime and its interactive UI are unavailable to this execution environment. No CLI result is copied into the Desktop baseline.

## Raw artifact integrity

No Desktop runtime was launched and no raw artifact was produced. There is therefore no new raw artifact hash for this campaign.

## Blockers and limitations

- `CEK_CODEX_DESKTOP_0152` was not set in the execution harness.
- Codex Desktop and its bundled 0.152.0 runtime are unavailable in this execution harness.
- Current official platform documentation is not treated as proof of Desktop 0.152.0 behavior.
- RISK-001 remains open because explicit manifest hook override is not proven on Desktop 0.152.0.
- RISK-002 remains open because Desktop behavior cannot be assumed from CLI 0.147.0 evidence.
- The prior Desktop reviewer parent-wait observation remains an observation, not a CEK hook failure or a proven Codex engine defect.

## Bounded conclusion

No Desktop 0.152.0 compatibility PASS is promoted by this Plan F campaign. The release surface must represent Desktop 0.152.0 as blocked/unverified until an operator can execute the exact bundled runtime and record sanitized evidence.
