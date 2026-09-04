# Security Policy

Codex Engineering Kit modifies local Codex/plugin or skill state, can execute bounded lifecycle hooks, and can inspect project repositories through verification workflows. File ownership, executable trust, local state, secrets, and evidence handling are therefore explicit product boundaries.

## Supported versions

Security fixes target the latest release and the current `main` branch. Pre-release feature branches, including v0.2 alpha work, may change rapidly and must not be treated as stable security contracts without the corresponding release evidence.

## Reporting a vulnerability

Use GitHub private vulnerability reporting / security advisories when available. If private reporting is unavailable, open only a minimal public issue asking for a private contact channel.

Do **not** publish exploit details, credentials, private keys, sensitive project data, authentication/session material, private transcripts, or a working secret in a public issue.

A useful private report includes the affected version/commit, environment, affected component, minimal synthetic reproduction, security impact, required user interaction, and a safe proof of concept.

## Security boundaries

### Hooks are guardrails, not a sandbox

v0.2 native hooks can provide bounded lifecycle evidence, state/compaction handling, and narrow PreToolUse deny/allow decisions. They are not an operating-system sandbox, a complete policy engine, or a guarantee that arbitrary unsafe behavior cannot occur.

Hook configuration and executable code that is not managed by CEK remains a user trust/review boundary. A one-off trust bypass used for an isolated acceptance experiment would prove only that the tested loading/execution path worked under that bypass; it would **not** prove the normal trust UX.

The primary plugin manifest continues to omit an explicit `hooks` override while RISK-001 is unresolved. Runtime compatibility status is tracked in `docs/release/compatibility-matrix.md`.

### Python runtime requirement

The shipped v0.2 hook dispatcher and runtime-dependent local-state features require Python 3.11+ to be available. Missing Python must be treated as a feature/runtime limitation rather than silently reported as successful hook execution.

### Toolkit-owned vs user-owned files

The PowerShell installer records toolkit-owned skill directories and deterministic tree hashes in `codex-engineering-kit.manifest.json`.

- unowned/conflicting targets are refused by default;
- `-Force` backs up a conflicting target before replacement;
- uninstall removes a skill only when its current hash still matches the installed manifest;
- modified installed skills are preserved instead of silently deleted.

Native plugin installation and the PowerShell skill-installer ownership model are separate delivery surfaces.

### Public repository vs local private state

The public repository must never contain:

- API keys, access tokens, private keys, or real `.env` secrets;
- project/provider credentials;
- raw private session transcripts;
- generated authentication/session material;
- user-local executable, cache, home, or `CODEX_HOME` paths in committed evidence;
- private continuous-learning observations/candidates.

Runtime evidence commits only bounded summaries, repository-relative references, and hashes where appropriate. Raw operator artifacts remain local.

### Bounded `.codex-kit` state

Runtime state under `.codex-kit` is designed to be local, ignored, bounded by schemas, and sensitivity-filtered before shared evidence is produced. State/checkpoint files are not a general transcript store and should not contain raw prompts, credentials, or unbounded tool output.

### Trusted skills vs learned candidates

Continuous learning produces `pending_review` candidates only. Candidates are not automatically installed, promoted, or executed. Learned shell content is never an automatic execution source.

### Custom-agent instructions are not isolation

Read-only/custom-agent instructions constrain intended behavior but are not an operating-system sandbox. Repository/tool permissions and user review remain authoritative boundaries.

### Deterministic evidence vs model judgment

When a condition can be verified through code, exit status, schema checks, tests, hashes, or file/state contracts, deterministic evidence takes priority over model judgment. Missing runtime evidence must not be promoted to PASS.

### External MCP providers

MCP templates contain only secret-free requirements and login metadata. Provider authentication remains local and should use least privilege. A failed or unauthenticated optional MCP provider must not weaken unrelated CEK checks.

## Release evidence boundary

The v0.2 release contract does not claim blanket security, feature parity, measured context efficiency, or blanket cross-platform Codex runtime compatibility. Exact claim and compatibility scopes are recorded in:

- `docs/release/claim-evidence-matrix.md`;
- `docs/release/compatibility-matrix.md`;
- `docs/release/v0.2-rc-checklist.md`.

## Out of scope by design

CEK does not intentionally:

- store remote telemetry by default;
- upload session transcripts;
- execute learned candidates automatically;
- embed provider credentials in templates;
- treat hook guardrails as a security sandbox;
- infer one runtime's behavior from another runtime's evidence.

A change that adds any of these behaviors requires an explicit security design review and corresponding evidence contracts.
