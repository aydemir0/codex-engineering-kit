# CEK Context Benchmark

This document defines the deterministic context benchmark contract and the authenticated v1 collection method. Results remain separate from methodology.

## Fixed configurations

- A = naive always-loaded engineering instructions
- B = progressive-disclosure skill routing
- C = native isolated subagent delegation

The fixed repository task set contains five cases pinned to fixture commit `1dbf382b6e838ca351c6fb8818a64aa793176198`. Prompts and invariants are fixed before authenticated execution. One complete campaign is:

`5 tasks × 3 configurations × 3 repeats = 45 runs`

All 45 runs in one campaign must use the same model, reasoning setting, and Codex runtime version. Missing, duplicate, or runtime-mismatched tuples make the campaign incomplete.

## Evidence and aggregation

Token evidence source precedence is runtime/API measured, then structured export exported, then tokenizer estimated. If none is available, the source is `unavailable`. Sources remain separately labeled; measured, exported, and estimated values are never merged into an unlabeled aggregate.

Numeric reporting uses median and range (minimum and maximum) with sample size for each case/configuration/metric/source group. Three repeats support descriptive reporting only: there is no statistical significance claim from three repeats.

Task PASS/FAIL outcomes remain task outcomes. The report generator does not produce pass@k, pass^k, reliability, security, performance, or efficiency claims beyond the collected evidence.

## Synthetic fixtures are not evidence

`benchmarks/fixtures/results/complete-synthetic.json` and `incomplete-synthetic.json` exist only to test completeness and aggregation logic. Synthetic data and the report generator alone do not earn a `lean` claim. They must never be cited as measured benchmark evidence.

Actual authenticated collection is a later operator campaign outside deterministic CI. Until a real complete 45-run campaign is collected under the fixed model/reasoning/runtime controls, the project does not promote a measured `lean` or context-efficiency result.

## Authenticated v1 methodology

The five fixed tasks are `backend-design`, `concurrency-pressure`, `frontend-review`, `node-small-bug`, and `repository-review`. Each case points to a fixture pinned at commit `1dbf382b6e838ca351c6fb8818a64aa793176198` and carries deterministic evidence-check groups. The runner rejects a fixture that differs from that pin.

The three modes change only the declared context strategy:

- A injects all eight shipped `SKILL.md` contracts into every task prompt.
- B injects only the case's `requiredSkill`; `node-small-bug` receives no skill contract.
- C injects no skill contract, provisions the shipped project-local `explorer` definition, registers the disposable collaboration session with one `list_agents` call, and requires the spawn call to use `agent_type = explorer`, `fork_turns = none`, and a separate task name. Default-agent fallback is invalid. The shipped CEK plugin-native hooks must record exactly one `SubagentStart` and one `SubagentStop` with the same non-empty child and session identities and `agentType = explorer`. A CLI JSONL `wait` pair or model prose is insufficient.

Every attempt uses the same case prompt, response JSON schema, explicit model and reasoning setting, Codex CLI binary/version, read-only sandbox, automatic review for non-interactive safe-command approvals, disabled app loading, explicitly enabled CEK plugin-native lifecycle hooks whose exact source bytes are included in the methodology hash and whose handler hashes are persistently trusted in the disposable config, exact-path trust only for the current disposable fixture, excluded plugin/native skill instructions, enabled `skip_host_skill_discovery`, ignored repository rules, a fresh benchmark-only `CODEX_HOME/config.toml`, a disposable Windows user-profile environment, scrubbed inherited parent `CODEX_*` control-plane variables, and session storage confined to that disposable `CODEX_HOME`. Each fresh fixture copy is initialized as its own Git repository so Codex can resolve its project-local `.codex/agents/explorer.toml`. The runner does not pass `--ignore-user-config`, because that would discard the disposable config's required plugin and hook-trust state; no normal user config is copied. Hooks are evidence instrumentation, not a sandbox. CLI 0.153.0 cannot start an isolated subagent from an ephemeral parent session, so `--ephemeral` is intentionally omitted and the disposable runtime is deleted after evidence capture. Mode A/B disable multi-agent; mode C enables it. Prompts are sent through UTF-8 stdin. Attempts execute sequentially in deterministic case/configuration/repeat order against a fresh fixture copy.

On Windows, CLI 0.153.0 may still parse host `.agents` descriptors using the OS account home even when the disposable profile environment and `skip_host_skill_discovery` are set. A preflight `debug prompt-input` probe therefore additionally requires those host skill names, paths, and the skills instruction block to be absent from the model-visible prompt before authenticated execution proceeds.

Before authenticated execution, the candidate and fixture pins are verified in the source worktree and a detached sparse capsule is created at the same candidate SHA. The authenticated runner receives only the five fixture trees, fixed case/configuration files, eight required `SKILL.md` files, the project-local explorer contract, and the minimum local runner modules. Repository files outside that allowlist are not materialized in the capsule.

The v1 campaign configuration is:

```text
runtime: Codex CLI 0.153.0
model: gpt-5.6-terra
reasoning: medium
timeout: 180 seconds per attempt
repetitions: 3
```

The model identity is fixed by the explicit CLI argument; runtime version is captured from `codex --version`. A nonzero exit, timeout, malformed JSONL, absent completion/final response, missing C subagent lifecycle, or failed deterministic evidence checks produces a retained `FAIL` row. A failed C attempt remains a valid accounted failure even when execution stopped before a subagent lifecycle appeared; only a passing C attempt must carry the structured lifecycle evidence.

## Metrics and raw-data boundary

Per attempt, the runner records:

- CLI-reported input, cached-input, and output token counts from `turn.completed.usage` as `measured`; absent telemetry is `unavailable`, never estimated from text length;
- wall-clock process duration from a monotonic clock as `measured`;
- completed tool-call event count;
- deterministic evidence-check outcome;
- C subagent lifecycle outcome;
- hashes of the raw capture and final response.

Parent-only and child-only token counts remain `unavailable` unless the runtime exposes them separately. Aggregate reporting never merges `measured` and `unavailable` evidence.

Raw JSONL/stderr captures remain under ignored local `.codex-kit/benchmarks/` storage. The publishable dataset contains measurements, classifications, and hashes only; it excludes prompts, responses, stdout/stderr, session identifiers, auth data, and machine-local paths.

## Timeout and retry policy

Each planned tuple receives exactly one attempt. Failed and timed-out attempts remain failures. There are no selective retries and no replacement rows. If the smoke proves a harness defect, the defect is fixed before methodology freeze. If a whole-campaign infrastructure defect is proven after counted collection begins, that campaign is invalidated and retained by hash; the entire 45-run campaign restarts under a new campaign ID.

The one-attempt smoke uses `node-small-bug/C/1`, writes a separate non-counted artifact, and cannot be promoted into campaign data. This exercises the most complex mode and must prove a real explorer hook lifecycle. The campaign candidate is frozen only after smoke passes and the runner, cases, configurations, skills, explorer definition, hook manifest, and hook dispatcher are committed. The runner records a platform-stable methodology SHA-256 over normalized UTF-8/LF content with stable source labels; the validator independently recomputes it and rejects candidate drift.

## Deterministic CI boundary

CI validates the worktree acceptance harness, domain skills, benchmark protocol/report contracts, repository content rules, and offline benchmark protocol. It does not launch authenticated benchmark execution, Codex sessions, browsers, or network benchmark processes.
