# Security Policy

Codex Engineering Kit modifies local Codex skill directories and can inspect project repositories through its verification workflows. That makes file ownership, secrets, and trust boundaries part of the product design.

## Supported versions

Security fixes target the latest release and the current `main` branch. Pre-release feature branches may change rapidly and should not be treated as stable security contracts.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting / security advisory flow for this repository when available.

If private reporting is unavailable, open a minimal public issue asking for a private contact channel. **Do not include exploit details, credentials, private keys, sensitive project data, or a working secret in a public issue.**

A useful private report includes:

- affected version/commit;
- operating environment;
- affected script/skill/workflow;
- minimal reproduction steps;
- security impact;
- whether user interaction is required;
- a safe proof of concept using synthetic data.

## Security boundaries

### Toolkit-owned vs user-owned files

The installer records toolkit-owned skill directories and deterministic tree hashes in `codex-engineering-kit.manifest.json`.

- unowned/conflicting targets are refused by default;
- `-Force` backs up a conflicting target before replacement;
- uninstall removes a skill only when its current hash still matches the installed manifest;
- modified installed skills are preserved instead of silently deleted.

### Public repository vs local private state

The public repository must never contain:

- API keys, access tokens, or private keys;
- real `.env` secrets;
- project credentials;
- raw private session transcripts;
- generated authentication state;
- private continuous-learning observations/candidates.

Local working state should remain under ignored paths such as `.codex-kit/local/` and `.codex-kit/candidates/`.

### Trusted skills vs learned candidates

Continuous learning produces `pending_review` candidates only. Candidates are not automatically installed, promoted, or executed. Learned shell content is never an automatic execution source.

### Deterministic evidence vs model judgment

When a condition can be verified through code, exit status, schema checks, tests, or file contracts, deterministic evidence takes priority over model judgment. Missing evidence must not be reported as success.

### External MCP providers

MCP templates contain only secret-free requirements and login metadata. Provider authentication remains local and should use least privilege. A failed or unauthenticated optional MCP provider must not weaken unrelated toolkit safety checks.

## Out of scope by design

The v0.1 toolkit does not intentionally:

- store remote telemetry;
- upload session transcripts;
- execute learned candidates automatically;
- modify user repositories autonomously without an explicit workflow/action;
- embed provider credentials in templates.

A change that adds any of these behaviors requires an explicit security design review.
