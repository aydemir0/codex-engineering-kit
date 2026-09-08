# Codex CLI 0.153.0 — v1 Representative Workflow Evidence

## Scope

- Runtime: `codex-cli 0.153.0`
- Runtime-tested CEK commit: `2ef05613fd26d8543ac03e365f1b0e29900fe0d2`
- Fixture: `representative-workflow-v1`
- Host family: Windows
- Result: PASS

This record is limited to the exact CLI runtime, CEK commit, and disposable
workflow described here. It does not establish Codex Desktop compatibility or
blanket cross-platform behavior.

## Supported v1 boundary

| Surface | Provisioning | Result |
| --- | --- | --- |
| CEK skills | Plugin-native | PASS |
| CEK hooks | Plugin-native | PASS |
| CEK reviewer | Codex-native project-local role copied from `.codex/agents/reviewer.toml` | PASS |
| Plugin-declared custom agent roles | Unsupported on CLI 0.153.0; deferred and not a v1 claim | NOT_SUPPORTED |

Plugin installation on Codex CLI 0.153.0 does not register custom agent roles.
The representative workflow therefore provisioned CEK's shipped reviewer TOML
into the disposable project's `.codex/agents/reviewer.toml`. No maintainer-local
agent or skill was required.

## Disposable setup

- Materialized the exact runtime-tested commit from a Git archive into a fresh
  temporary candidate directory.
- Copied the checked-in representative fixture into a fresh Git repository.
- Provisioned only the shipped project-local reviewer and verified its SHA-256
  matched the source asset.
- Installed CEK from the fresh local marketplace snapshot and verified the
  plugin-native orchestrator skill and hook manifest were present.
- Verified the plugin snapshot did not contain the removed
  `agents/reviewer.md` assumption.
- Verified the hooks tree was unchanged from the trusted CLI 0.153.0 baseline.
- Imported exactly eight CEK hook trust hashes and trusted only the disposable
  project. No hook-trust bypass was used.
- Copied authentication only from a previously verified disposable source. A
  minimal no-tool probe returned exactly `AUTH_OK` with exit code 0 and no 401.

## Representative workflow

The run explicitly invoked `$codex-engineering-kit:orchestrator` and required
the following ordered stages. Its final response was constrained by a JSON
schema and returned `READY`.

| Stage | Result | Evidence |
| --- | --- | --- |
| classify | PASS | Structured result classified the task as a bounded bug fix. |
| plan | PASS | Structured result contained a bounded seven-item plan. |
| red | PASS | `py -3 -B -m unittest discover -s tests -v` exited 1 with two tests and the expected `ValueError not raised` failure. |
| implement | PASS | One line in `src/calculator.py` changed from returning infinity to raising `ValueError("division by zero")`. |
| green | PASS | The same complete test command exited 0 with two tests passing. |
| review | PASS | The project-local reviewer ran once in a distinct subagent and reported no material findings. |
| verify | PASS | `$codex-engineering-kit:verification-loop` was explicitly required; the parent reran the complete tests and inspected the final diff/status. |

The sanitized schema-version-1 workflow record contained exactly the required
stage order and passed:

```text
python scripts/acceptance/workflow_evidence.py validate --record <sanitized-record>
PASS: representative workflow evidence validated
```

## Reviewer lifecycle evidence

The full workflow's plugin-native hooks recorded:

- exactly one `SubagentStart`;
- exactly one `SubagentStop`;
- matching child identity across start and stop;
- `agentType = reviewer` on both events;
- one allowed `collaborationlist_agents` PreToolUse/PostToolUse pair;
- one successful `collaborationspawn_agent` PreToolUse/PostToolUse pair;
- three allowed `collaborationwait_agent` PreToolUse/PostToolUse pairs.

The full workflow also recorded one `SessionStart`, one `SessionEnd`, and 19
matched PreToolUse/PostToolUse events. Parent self-review was not accepted as
review evidence. A separate minimal reviewer smoke also recorded exactly one
reviewer-typed child start/stop with matching identity.

## Independent verification

After the Codex run completed, an external verifier ran:

```text
python -B -m unittest discover -s tests -v
```

Result: exit code 0; two tests passed.

Independent Git checks confirmed:

- the sole tracked fixture change was `src/calculator.py`;
- fixture tests, task text, README, and `.codex/agents/reviewer.toml` were
  unchanged;
- `git diff --check` passed;
- no fixture commit was created.

The required repository regressions then passed with these exact commands and
counts:

| Command | Result |
| --- | --- |
| `python -B -m unittest tests.test_workflow_evidence -v` | PASS — 9 tests |
| `python -B -m unittest tests.test_representative_fixture -v` | PASS — 1 test |
| `python -B -m unittest tests.test_agent_contract -v` | PASS — 11 tests |
| `python -B -m unittest tests.test_hook_contract -v` | PASS — 7 tests |
| `python -B -m unittest tests.test_hook_dispatch -v` | PASS — 10 tests |
| `python -B -m unittest tests.test_verification_engine -v` | PASS — 19 tests |
| `python -B -m unittest tests.test_plugin_contract -v` | PASS — 5 tests |
| `python -B -m unittest tests.test_plugin_compatibility -v` | PASS — 8 tests |

The six required WS3 suites account for 57 passing tests; the two plugin
compatibility suites add 13, for 70 passing tests total. The content validator
and repository `git diff --check` also passed.

## Cleanup and claim limits

The copied disposable `auth.json` was deleted, then the complete disposable
campaign root was removed. No disposable runtime state was committed.

This evidence does not claim plugin-native custom-agent support, Codex Desktop
compatibility, production-grade status, full security, ECC feature parity,
OpenAI endorsement, OpenAI verification, or measured efficiency.

This document is an evidence-only change after the runtime-tested commit. The
closure gate must verify that its commit contains no runtime-affecting diff from
`2ef05613fd26d8543ac03e365f1b0e29900fe0d2`.
