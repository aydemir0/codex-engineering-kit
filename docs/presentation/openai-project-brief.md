# Codex Engineering Kit: OpenAI Project Brief

Codex Engineering Kit (CEK) is an independent, evidence-bound engineering
workflow for OpenAI Codex. It makes task routing, test-first implementation,
independent review, verification, runtime acceptance, and release claims
inspectable instead of asking reviewers to trust model prose.

CEK is not an OpenAI product, certification, or endorsement. The current
evidence is deliberately scoped to the named repository revisions and
runtimes.

## Why it matters

Agentic engineering can produce convincing explanations before it produces a
reproducible result. CEK reverses that priority: deterministic failures,
tests, lifecycle events, bounded state, and machine-checkable evidence are the
primary record. Missing evidence remains `LIMITED`, `NOT_RUN`, or unsupported;
it is not promoted to success.

The product focus is a small number of connected engineering workflows, not a
large feature count. The central path is:

```text
task -> orchestrator -> classify -> plan -> RED -> implementation -> GREEN -> real reviewer subagent -> verify -> hooks/state/evidence -> sanitized machine-checkable record -> release claim/evidence contract
```

The orchestrator chooses the smallest relevant skill, parent-context contract,
or project-local subagent. Deterministic tests establish RED and GREEN. A real
reviewer must execute in a distinct child context; parent self-review and model
prose do not satisfy that gate. Hooks and bounded state record lifecycle and
verification evidence. Release contracts then limit public wording to what the
record supports.

## Verified capability surface

| Surface | Evidence-bound statement | Important boundary |
| --- | --- | --- |
| Truth and release contracts | Claims and compatibility states have machine-readable and human-readable contract validation. | `IMPLEMENTED`, `VERIFIED`, `LIMITED`, and `NOT_RUN` are not interchangeable. |
| Codex-native packaging | Plugin packaging, install/list behavior, and native hooks have scoped Codex CLI 0.153.0 runtime evidence. | Direct CLI 0.153.0 skill discovery remains `NOT_RUN`. |
| Engineering workflow | A representative task completed deterministic RED, minimal implementation, GREEN, distinct project-local reviewer lifecycle, and final verification. | Parent self-review is invalid; this is one bounded fixture, not universal workflow proof. |
| Security contract | Prompt-injection handling, tool/destructive-write boundaries, secrets, state, MCP permissions, provenance, ownership, learning promotion, and metadata have deterministic repository evidence. | Hooks are guardrails, not a sandbox; secret recognition is not claimed exhaustive. |
| Asset stocktake | Eight plugin-native skills, eight project-local native agent definitions, and nine parent-context role contracts are inventoried separately. | Only reviewer and explorer have direct CLI 0.153.0 lifecycle evidence; the other six agents are contract-only. |
| Authenticated benchmark | The frozen five-task, three-mode, three-repetition campaign accounts for every planned attempt. | Results describe only that task set/runtime and support no general superiority claim. |
| Managed lifecycle | Clean install, verification, ownership-aware update, uninstall, reviewer provisioning, sentinel preservation, verify-clean, and reinstall passed in a disposable CLI 0.153.0 environment. | The reviewer is project-local; lifecycle evidence is not promoted to Desktop or other CLI versions. |

Full claim-to-source mapping is in the [evidence index](evidence-index.md).

## Benchmark, without the missing rows hidden

WS6 contains exactly 45 authenticated runs with one counted attempt per frozen
tuple:

- A: 15/15 PASS (always-loaded)
- B: 15/15 PASS (progressive disclosure)
- C: 4/15 PASS (isolated subagent)
- Total: 34 PASS / 11 retained FAIL
- 9 missing-lifecycle failures
- 2 quality-contract failures

There was no retry or replacement of a failed counted attempt. The dataset
supports no efficiency or superiority claim: no general context-reduction,
latency, quality, statistical-significance, or benchmark-leadership conclusion
is made. Mode C's failures are part of the result and show why lifecycle events
and quality contracts must be checked rather than inferred.

## Runtime and trust boundaries

- The current v1 runtime conclusions are scoped to Codex CLI 0.153.0.
- CEK packages eight plugin-native skills, but direct skill discovery on that
  runtime remains `NOT_RUN`.
- Plugin-native hooks are supported within the documented CLI 0.153.0 boundary;
  hooks are guardrails, not a sandbox.
- The reviewer and explorer with runtime evidence are project-local Codex
  agents. Plugin installation does not register custom agent roles on CLI
  0.153.0.
- A project-local reviewer can be provisioned by the managed lifecycle.
  Plugin-native custom agents remain unsupported/deferred on CLI 0.153.0.
- No Codex Desktop behavior is inferred from CLI evidence.
- The unauthorized connector startup warning observed during WS6 remains a
  documented limitation. The campaign found no evidence that fixture content,
  credentials, or unintended files were transmitted to that connector, but it
  does not claim complete connector-process isolation.
- CEK makes no claim of complete security or universal production readiness.
  Host sandboxing, trust controls, provider permissions, and human approval
  remain separate security boundaries.

## Reproducible review path

1. Run the [representative workflow demo](../demo/representative-workflow.md)
   to reproduce its deterministic RED and GREEN and inspect the retained
   reviewer lifecycle evidence.
2. Read the [evidence index](evidence-index.md) to follow each material claim to
   a deterministic test, runtime record, dataset, or explicit limitation.
3. Run the repository content and release-contract validators before reusing
   any wording as a public claim.

This brief is a presentation of existing evidence. It does not add product
functionality, publish a release, or broaden any compatibility claim.
