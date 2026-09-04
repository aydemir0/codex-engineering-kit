# Plan E Context Benchmark

This document defines the deterministic context-efficiency benchmark contract. It does not report a real benchmark result.

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

## Deterministic CI boundary

CI validates the worktree acceptance harness, domain skills, benchmark protocol/report contracts, repository content rules, and offline benchmark protocol. It does not launch authenticated benchmark execution, Codex sessions, browsers, or network benchmark processes.
