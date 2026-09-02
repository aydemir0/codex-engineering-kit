# Codex Engineering Kit — Design Specification

## Goal

Build a public, production-oriented agentic software engineering toolkit for OpenAI Codex that adapts the strongest ideas from mature Claude Code workflows without pretending Claude-specific hooks, commands, or lifecycle APIs exist in Codex.

The toolkit must be useful as both a real development system and a portfolio-quality open-source project.

## Product Principles

1. **Codex-native, not a mechanical port.** Claude-specific concepts are re-modeled around Codex skills, project instructions, scripts, Git workflows, and explicit orchestration.
2. **Evidence before action.** Existing repositories are inspected before architecture, debugging, performance, or security recommendations are treated as implementation-ready.
3. **Lean context.** Keep the active skill catalog small. Prefer role references, workflows, and scripts over dozens of always-visible skills.
4. **Correctness before speed.** Verification gates, tests, type checks, security checks, and rollback discipline are first-class.
5. **Human approval for learned behavior.** Continuous learning may propose reusable patterns but must not silently promote arbitrary session output into trusted skills.
6. **Safe-by-default integrations.** Secrets never live in the repository. MCP configuration uses environment variables, login flows, and validation.
7. **Cross-platform direction.** Windows PowerShell is first-class for v1; architecture must not prevent later Linux/macOS support.
8. **Public-repo hygiene.** No user-specific secrets, local project data, credentials, or private learned content may be committed.

## High-Level Architecture

```text
codex-engineering-kit/
├── skills/
│   ├── orchestrator/
│   │   └── references/
│   │       ├── roles/
│   │       └── workflows/
│   ├── continuous-learning/
│   ├── eval-harness/
│   ├── verification-loop/
│   ├── software-architecture/
│   └── concurrency-performance/
├── rules/
├── contexts/
├── workflows/
├── scripts/
├── mcp/
├── templates/
├── tests/
├── docs/
├── THIRD_PARTY_NOTICES.md
└── README.md
```

## Skill Strategy

The toolkit will intentionally avoid one skill per engineering persona.

### Active core skills

- `orchestrator`
- `continuous-learning`
- `eval-harness`
- `verification-loop`
- `software-architecture`
- `concurrency-performance`

The `orchestrator` skill will route work to role-specific reference material instead of registering every role as a separate active skill.

### Role references

The orchestration layer will include references for:

- architect
- planner
- code reviewer
- security reviewer
- build error resolver
- E2E runner
- TDD guide
- refactor cleaner
- documentation updater

Role files define responsibilities, evidence requirements, boundaries, and completion criteria. They are not separate autonomous products and must not inflate Codex's skill-description budget unnecessarily.

## Workflow Layer

Reusable workflows will exist for:

- feature implementation
- bugfix/root-cause resolution
- build failure resolution
- architecture review
- code review
- security review
- refactoring
- E2E validation
- eval definition/check/report
- release verification
- learning extraction
- checkpoint creation

Each workflow must define entry conditions, evidence required, execution gates, verification, failure handling, and output contract.

## Verification Architecture

The default verification pipeline is:

```text
implementation
  → build
  → typecheck
  → lint
  → tests
  → security checks
  → diff review
  → release/readiness decision
```

The implementation must discover project-native commands where possible rather than hard-code `npm` for all repositories.

Verification reports must separate:

- command executed
- exit status
- evidence
- blocking failures
- warnings
- final readiness state

A change cannot be labeled ready when required gates have not run or failed.

## Eval-Driven Development

The toolkit will adapt capability and regression eval concepts into Codex-oriented project artifacts.

Project-local eval storage:

```text
.codex-kit/
└── evals/
    ├── <feature>.md
    ├── <feature>.log
    └── baseline.json
```

Supported grader categories:

1. deterministic/code-based
2. model-assisted
3. human review required

Deterministic graders are preferred whenever the success condition can be checked mechanically.

The system may track `pass@k` or repeated-success metrics where repeated model execution is genuinely useful, but it must not fabricate reliability metrics from a single run.

## Continuous Learning

Continuous learning is candidate-based, not auto-trusting.

```text
session/work result
  → pattern extraction
  → candidate normalization
  → deduplication
  → confidence/evidence assessment
  → human approval
  → learned pattern or promoted skill
```

Candidate categories include:

- recurring error resolutions
- user corrections
- framework/library workarounds
- effective debugging techniques
- project-specific conventions

Candidates that are one-off, secret-bearing, stale, or insufficiently supported must be rejected.

Public toolkit code must never persist private session transcripts or project-specific secrets.

## Lifecycle Adaptation

Claude Code hook names such as `PreToolUse`, `PostToolUse`, `Stop`, and `SessionStart` will not be copied as if Codex exposes identical semantics.

For v1, lifecycle behavior is modeled through explicit scripts and workflows:

```text
codex-wrapper.ps1
  ├── preflight
  ├── optional context/checkpoint restore
  ├── launch Codex
  └── post-session candidate extraction / state persistence
```

Tool-level safety and quality remain enforced through workflow instructions, verification skills, repository instructions, and explicit scripts rather than fictional hook compatibility.

## Rules and Contexts

Rules are grouped by concern:

- engineering
- security
- testing
- Git workflow
- performance

Contexts provide lightweight operating modes such as:

- development
- review
- research

These are references/templates, not magic system-prompt injection unless Codex explicitly supports the mechanism used.

## MCP Strategy

The repository may include templates and setup scripts for integrations such as GitHub, Supabase, Vercel, Railway, and Cloudflare.

Requirements:

- no API keys or tokens committed
- placeholders must clearly identify required environment variables
- login-based flows preferred when available
- configuration scripts validate dependencies and missing secrets
- generated local config is ignored by Git
- MCP setup failures must not break unrelated toolkit features

## Installer and Update Model

Windows-first scripts:

- `install.ps1`
- `update.ps1`
- `uninstall.ps1`
- `verify.ps1`
- `learn-session.ps1`
- `codex-wrapper.ps1`

Installer requirements:

- idempotent
- refuses unsafe overwrite by default
- backs up replaced user-owned files when replacement is explicitly allowed
- installs toolkit-owned skills into the supported Codex skill directory
- reports exactly what changed
- provides dry-run mode
- never writes secrets

The public repository remains the source of truth; installed files are derived copies.

## Security Model

Security boundaries include:

- repository contents versus local private configuration
- toolkit-owned files versus user-owned files
- trusted shipped skills versus untrusted learned candidates
- deterministic verification versus model judgment
- external MCP servers versus local project data

The toolkit must not execute arbitrary learned shell content automatically.

Security-sensitive recommendations require explicit evidence and, where appropriate, human review.

## Attribution

The project may adapt ideas and MIT-licensed material from `WorldFlowAI/everything-claude-code` and other compatible sources.

Requirements:

- preserve required license notices
- document adapted sources in `THIRD_PARTY_NOTICES.md`
- avoid implying original authors endorse this project
- rewrite Claude-specific behavior where Codex semantics differ

## Portfolio Quality

The public repository must include:

- strong English README
- architecture overview
- quick start
- supported environments
- examples
- security model
- roadmap
- contribution guide
- attribution
- CI validation
- clean project structure

The README must describe the project as a Codex engineering toolkit, not as a renamed Claude Code repository.

## Initial Release Scope

### v0.1 must include

- orchestrator skill and role references
- verification-loop skill
- eval-harness skill
- continuous-learning candidate workflow
- software-architecture skill
- concurrency-performance skill
- PowerShell installer/update/uninstall
- safe project template with `AGENTS.md`
- core workflows
- tests for installer and content contracts
- public README and attribution

### Deferred beyond v0.1

- automatic cross-platform installer parity
- remote telemetry
- automatic skill publication
- autonomous modification of user repositories without approval
- large plugin marketplace compatibility layer

## Acceptance Criteria

The first public release is acceptable when:

1. A clean Windows machine with Codex installed can clone the repo and run the installer successfully.
2. Re-running the installer is safe and idempotent.
3. Core skills validate and can be listed by Codex.
4. The toolkit does not require Claude Code.
5. No secrets or user-specific local data are present in the repository.
6. Verification can run against a sample project and produce an evidence-based readiness result.
7. Continuous learning produces reviewable candidates rather than silently trusted skills.
8. CI validates repository structure and core script behavior.
9. Attribution is present and accurate.
10. README is sufficient for an external developer to understand, install, and evaluate the project without private context.
