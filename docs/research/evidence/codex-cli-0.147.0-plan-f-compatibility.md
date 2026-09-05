# Codex CLI 0.147.0 Plan F Compatibility Evidence

Date: 2026-09-05
Platform: ChatGPT execution harness, Linux x86_64; target Codex baseline unavailable in this harness
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit: `88096382e4b5a467930ed72d23eccb2e0ae72fa0`
Plugin version: `0.2.0-alpha.1`
Exact runtime version: not observed in this Plan F campaign; `CEK_CODEX_0147` was unset and no `codex` executable was available

## Provenance for reused 0.147.0 evidence

The Plan F harness could not launch a new 0.147.0 session, so prior runtime evidence is reused only where the current shipped bytes or the relevant code path remain bound to that evidence:

- `.codex-plugin/plugin.json` is blob-identical to the plugin acceptance commit (`e16de71f1628c9ff78c33a1de5f34b8d3155f2e6`).
- `.agents/plugins/marketplace.json` is blob-identical to the plugin acceptance commit (`4128761cbc15a03810941e657e63dc1eb08e94cd`).
- `hooks/hooks.json` is blob-identical to the original hook acceptance commit (`aa350bc47ec668a0de662bfd694605c612944d3a`).
- The current `PreToolUse` allow/acceptance-deny implementation is unchanged from the original hook acceptance code path.
- The later Plan C state/subagent acceptance ran the same current dispatcher blob (`8bec1da4cc715a0b59853dd0332c37f13d19838f`) and the same current `runtime/state.py` blob (`d59bf5aa02a347b0f62cf70425853a5617f43089`).
- Plan C also exercised the current `.codex/config.toml` and `explorer.toml` configuration used for the native-subagent lifecycle.

These provenance checks do not convert blocked Plan F surfaces into new runtime measurements; they only bound reuse of already committed 0.147.0 evidence.

## Results

- Default-hook result: **PASS from existing committed 0.147.0 evidence**, not rerun in this harness. `docs/research/evidence/codex-cli-0.147.0-hook-acceptance.md` directly records default `hooks/hooks.json` discovery and hook execution.
- Explicit-manifest result: **BLOCKED**. The Plan F disposable `"hooks": "./hooks/hooks.json"` variant could not be launched on the exact 0.147.0 runtime because that binary is unavailable in this execution harness.
- Plugin/marketplace discovery result: **PASS from existing committed 0.147.0 evidence** in `docs/research/evidence/codex-cli-0.147.0-plugin-acceptance.md`.
- Skill discovery result: **BLOCKED**. No committed 0.147.0 artifact directly proves the Plan F skill-discovery surface, and the exact runtime is unavailable for a fresh check.
- Hook lifecycle result: **PASS from bounded combined existing 0.147.0 evidence plus byte/code-path provenance**. The unchanged original hook paths cover SessionStart/PreToolUse/PostToolUse behavior, while the later Plan C state/subagent acceptance runs the current dispatcher bytes and records SubagentStart/SubagentStop, PreCompact/PostCompact, compact restart, and graceful SessionEnd.
- PreToolUse allow/deny result: **PASS from existing committed 0.147.0 hook evidence**.
- Subagent result: **PASS from `codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`**, whose dispatcher/config/explorer bytes remain current.
- Compaction result: **PASS from `codex-cli-0.147.0-plan-c-state-subagent-acceptance.md`**, which exercised the current dispatcher and state-runtime bytes.
- SessionEnd result or limitation: **BLOCKED for the Plan F timeout-budget classification**. Historical evidence records graceful SessionEnd execution, but the known 0.147.0 timeout discrepancy remains open and cannot be rerun here.
- Interactive discovery result: **BLOCKED**. No exact-runtime interactive surface can be exercised in this harness.
- Desktop wait result: not applicable to the CLI baseline.

## Raw artifact integrity

No new runtime artifact was produced because the campaign was blocked before runtime launch. Historical raw-artifact hashes remain in the previously committed acceptance records; they are not duplicated here.

## Blockers and limitations

- `CEK_CODEX_0147` was not set in the execution harness.
- No `codex` executable is available in the execution harness.
- Current official platform documentation is not treated as retroactive proof for Codex CLI 0.147.0.
- RISK-001 remains open because explicit manifest hook override was not executed on this baseline in Plan F.
- The SessionEnd timeout-budget discrepancy remains open.

## Bounded conclusion

Plan F may reuse the existing committed 0.147.0 acceptance evidence only for surfaces it directly proves. This campaign adds no new 0.147.0 runtime PASS. Explicit manifest hooks, Plan F skill discovery, SessionEnd timeout classification, and interactive discovery remain blocked until the exact baseline can be exercised.
