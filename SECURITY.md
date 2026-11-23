# Security Policy

Codex Engineering Kit modifies local Codex/plugin or skill state, can execute bounded lifecycle hooks, and can inspect project repositories through verification workflows. File ownership, executable trust, local state, secrets, and evidence handling are therefore explicit product boundaries.

## Supported versions

Security fixes target the latest release and the current `main` branch.
[v1.1.0-beta.1](https://github.com/aydemir0/codex-engineering-kit/releases/tag/v1.1.0-beta.1)
is a public pre-release. Its security evidence applies to the documented
configuration and checks in the [beta release notes](docs/release/v1.1-beta.1.md).

## Reporting a vulnerability

Use GitHub private vulnerability reporting / security advisories when available. If private reporting is unavailable, open only a minimal public issue asking for a private contact channel.

Do **not** publish exploit details, credentials, private keys, sensitive project data, authentication/session material, private transcripts, or a working secret in a public issue.

A useful private report includes the affected version/commit, environment, affected component, minimal synthetic reproduction, security impact, required user interaction, and a safe proof of concept.

## Security boundaries

The repository-specific assets, trust boundaries, mitigations, and residual risks are detailed in the [CEK threat model](docs/security/threat-model.md).

### Hooks are guardrails, not a sandbox

v1.0.0 native hooks can provide bounded lifecycle evidence, state/compaction handling, and narrow PreToolUse deny/allow decisions. They are not an operating-system sandbox, a complete policy engine, or a guarantee that arbitrary unsafe behavior cannot occur.

Hook configuration and executable code that is not managed by CEK remains a user trust/review boundary. A one-off trust bypass used for an isolated acceptance experiment would prove only that the tested loading/execution path worked under that bypass; it would **not** prove the normal trust UX.

The primary plugin manifest omits an explicit `hooks` override. The scoped Codex CLI 0.153 hook result and the still-separate Desktop/runtime statuses are tracked in `docs/release/compatibility-matrix.md`.

### Python runtime requirement

The shipped v1.0.0 hook dispatcher and runtime-dependent local-state features require Python 3.11+ to be available. Missing Python must be treated as a feature/runtime limitation rather than silently reported as successful hook execution.

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

Release-contract validation also treats claim IDs, compatibility surface IDs and
evidence references as untrusted data for diagnostics. Invalid entries are
reported using bounded row positions and error categories, **not** the raw
value, so malformed metadata does not echo token-shaped values or private
paths into CI output. Validating intentionally provided local JSON paths is a
read-only operator-controlled CLI operation, not an authorization boundary
for arbitrary third-party requests.

The release CLI intentionally supports operator-selected local JSON files. That
path is **not derived from release JSON fields**, and the CLI does not run with
more privileges than its invoker. In CI, both approved release inputs are
bound to two static repository paths using `--ci-contract-files`:
unexpected operator-supplied paths and symlink/junction escapes fail
closed before content is read. Invalid inputs yield a fixed diagnostic without
echoing filenames or JSON content. This bounded input policy is not an
arbitrary-file sandbox; the non-CI CLI mode still permits an operator to
select any readable local JSON file explicitly.

### Bounded `.codex-kit` state

Runtime state under `.codex-kit` is designed to be local, ignored, bounded by schemas, and sensitivity-filtered before shared evidence is produced. State/checkpoint files are not a general transcript store and should not contain raw prompts, credentials, or unbounded tool output.

The production hook entrypoint treats JSON `cwd` as untrusted. Before any
state write, it requires an absolute workspace path, refuses traversal and
symlink/junction/reparse components, and binds the payload to the hook
process's actual working directory. A mismatch fails closed; the path from
JSON is replaced with the verified host workspace for subsequent operations.
Direct in-process `dispatch()` is an internal testable unit, **not** an
untrusted public entrypoint; external callers must use the validated hook
command. Runtime configurations where the host launches hooks in a different
working directory may now fail closed and require host integration fixes.
This check does not eliminate filesystem races or replace OS sandboxing.

### Trusted skills vs learned candidates

Continuous learning produces `pending_review` candidates only. Candidates are not automatically installed, promoted, or executed. Learned shell content is never an automatic execution source.

### Custom-agent instructions are not isolation

Read-only/custom-agent instructions constrain intended behavior but are not an operating-system sandbox. Repository/tool permissions and user review remain authoritative boundaries.

### Verifier executes project-defined code

Verification is **not** a passive security scanner. In supported projects it
runs configured build, test, lint and/or typecheck commands with the invoking
user's privileges. Project-controlled package scripts and test code are
executable inputs; do not verify an unfamiliar repository as a trusted user
or on a workstation with production credentials. For external beta testing,
use only the documented disposable fixture and isolated Codex profile.

On Windows, batch-backed commands use the operating system's system-directory
`cmd.exe`, rather than the caller's `COMSPEC` or search `PATH`. Batch
executable paths and arguments containing shell metacharacters are refused
rather than interpolated. This is bounded hardening, not a guarantee that
arbitrary project scripts are safe or a replacement for an OS sandbox.
Some legitimate paths with special characters may require relocation.

### Dependency update and scan coverage

Dependabot vulnerability alerts and Dependabot security-update PRs are
enabled for this repository. The `.github/dependabot.yml` configuration
requests reviewed weekly GitHub Actions version-update PRs; there is **no
automatic merge**. CI workflows continue to pin actions to full commit SHAs.

GitHub CodeQL default setup is configured, but CodeQL, GitHub Code Scanning,
and externally managed Semgrep Cloud checks are separate evidence surfaces.
A successful external PR check does not imply that GitHub has stored
code-scanning results or that a local scan has no findings. Dependency alerts
are not comprehensive for unmanifested or externally installed packages,
including the separately pinned Codex CLI.

### Frozen historical benchmark dependency

As of 22 November 2026, GitHub Dependabot reported **41 open alerts**
(5 critical, 11 high, 21 moderate, 4 low) that all resolve to the
`next: 15.0.0` declaration in the historical
`benchmarks/fixtures/frontend-review/package.json`. This is **not an
installed CEK runtime dependency**, but installing or running that benchmark
fixture exposes it to those advisories. Do **not** install, serve or deploy
the fixture on a trusted machine or with valuable credentials. External
beta testers should use only the published calculator fixture.

The benchmark fixture is pinned to a separate historical source commit.
Its original installable `package.json` has been retired from the active
fixture tree and archived as plain text at
`benchmarks/archive/frontend-review-v1/package.json.txt`. The archive is
verified against the historical Git blob, while `app/page.tsx` and all
frozen evidence remain unchanged. A CEK runner fail-closed guard rejects new
execution of this legacy fixture. Direct manual restoration or installation
outside the runner is not a supported activity. GitHub Dependabot alert counts
must be rechecked after GitHub processes the changed manifest surface; do not
assume that previous advisories have automatically disappeared.

Do not silently alter historical dependency versions without a separately
pinned fixture identity and new protocol. Previous vulnerability alerts have
**not** been dismissed or represented as resolved by the runner guard alone.

### Deterministic evidence vs model judgment

When a condition can be verified through code, exit status, schema checks, tests, hashes, or file/state contracts, deterministic evidence takes priority over model judgment. Missing runtime evidence must not be promoted to PASS.

### External MCP providers

MCP templates contain only secret-free requirements and login metadata. Provider authentication remains local and should use least privilege. A failed or unauthenticated optional MCP provider must not weaken unrelated CEK checks.

## Release evidence boundary

The v1.0 security contract does not claim blanket security, feature parity, measured context efficiency, or blanket cross-platform Codex runtime compatibility. Exact claim and compatibility scopes are recorded in:

- `docs/release/claim-evidence-matrix.md`;
- `docs/release/compatibility-matrix.md`;
- `docs/release/v1.0-readiness.md`.

### External Semgrep Cloud check

The beta PR had one external Semgrep Cloud check alongside its 12 GitHub
Actions jobs. Semgrep Cloud policies are externally managed. A checkout or
fork alone cannot reproduce that policy or its scan result.

## Out of scope by design

CEK does not intentionally:

- store remote telemetry by default;
- upload session transcripts;
- execute learned candidates automatically;
- embed provider credentials in templates;
- treat hook guardrails as a security sandbox;
- infer one runtime's behavior from another runtime's evidence.

A change that adds any of these behaviors requires an explicit security design review and corresponding evidence contracts.
