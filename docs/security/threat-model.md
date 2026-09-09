# CEK Threat Model

This model covers the CEK v1 security workstream. It complements the repository [security policy](../../SECURITY.md) and does not claim operating-system containment.

## Scope and non-goals

The scope is CEK-authored instructions, hooks, local state, verification output, installers, learning candidates, MCP metadata, plugin metadata, and build provenance. Provider security, the Codex host, repository-authored commands, and operating-system isolation are external boundaries. Hooks are guardrails, not a sandbox.

## Protected assets

- user repositories and files outside CEK-owned paths;
- credentials, private prompts, transcripts, session identifiers, and machine-local paths;
- the integrity of CEK state, installed skills, learning candidates, and public evidence;
- the provenance and ownership identity represented by plugin and CI metadata.

## Trust boundaries

Repository text and tool output are untrusted data. Project commands run with the current Codex/user permissions. Hook payloads cross from the host into CEK state. Installer manifests cross from mutable local storage into deletion logic. Learning observations cross into persistent candidates. MCP authentication and external URLs cross into third-party systems.

## Threats and mitigations

### Prompt/instruction injection

Untrusted repository text, tool output, or learning observations can contain instructions intended to override the user or exfiltrate data. CEK treats these values as data, persists only bounded hook identity fields, emits only fixed text when restoring a compact checkpoint, and never auto-executes learned candidates. Hook persistence and learning tests are deterministic; semantic recognition of every adversarial instruction remains a residual host/model risk.

### Unsafe shell/tool guidance

Skills or repository scripts can cause commands to execute with the caller's permissions. CEK's process runner uses explicit argument vectors and `shell=False`; Windows batch launch is the documented narrow platform exception. Verification warns that project scripts are active code. Tests cover argument construction and exit behavior, but CEK cannot make arbitrary project commands safe.

### Destructive writes

Mutable manifest data, repository-controlled links, or unsafe instructions could select files outside CEK ownership. Installer conflicts are refused or backed up, uninstall requires a matching ownership hash, and manifest paths are constrained to the declared `skills/<name>` target beneath `CODEX_HOME`. Hook state rejects pre-existing link/reparse paths and uses an exclusively created temporary file before atomic replacement. Lifecycle tests use disposable paths. User-authorized tools and link-swap races remain external trust boundaries.

### Secrets and credentials

Secrets can enter through repositories, command output, hook payloads, learning observations, or copied evidence. Repository scans, bounded hook fields, verification-output redaction, learning rejection, and public-artifact tests cover configured patterns without recording matched values. Pattern detection is not a guarantee against unknown credential formats.

### Local-state leakage

Raw prompts, transcripts, command output, or incompatible state could be restored or shared. Versioned state rejects unknown schemas, reserved identity fields cannot be overwritten by payloads, hook records use allowlisted fields, and verification evidence is bounded and redacted. Every generated `.codex-kit` state directory remains local and ignored; local project paths may still appear in local-only reports.

### MCP/app permission boundaries

External providers can expose data or mutate remote state under their granted permissions. Shipped templates contain only provider, login/environment requirements, local-only scope, and guidance; credentials and grants remain outside the repository. Tests validate the template key set and secret-free declarations. Least privilege and each provider's runtime authorization remain operator responsibilities.

### Dependency provenance

Mutable CI references or unattributed copied code could change trusted execution. Workflow actions are pinned to full commit SHAs, and `LICENSE` plus `THIRD_PARTY_NOTICES.md` record licensing boundaries. Static tests verify these properties; upstream compromise and host runner integrity remain outside CEK.

### Install/update ownership

Install or update could overwrite user content, and uninstall could delete content not owned by CEK. The installer records tree hashes, refuses unowned conflicts by default, backs up forced replacements, and uninstall validates manifest identity, target shape, containment, and current hashes. Local administrators can still alter both installed files and their manifest.

### Learned-content promotion

Private or adversarial observations could become executable instructions. The learning script rejects configured sensitive values, emits non-executable JSON candidates, sets `promotion_status` to `pending_review`, and never installs candidates. Human review is still required before any later promotion.

### Plugin metadata and external URL trust

Typosquatted or mutable metadata can misrepresent publisher ownership or direct users to an untrusted site. Contract tests bind the declared URLs to HTTPS GitHub paths owned by `aydemir0`; marketplace metadata uses the repository-local plugin source and explicit install/authentication policy. Repository ownership and future external metadata changes require separate verification.

## Residual risks

CEK does not sandbox project commands, exhaustively recognize secrets or prompt injection, constrain provider-side permissions, or establish the security of the Codex host and CI runners. Time-of-check/time-of-use link swaps and administrator-modified local state remain local trust boundaries. These limits must not be converted into blanket security claims.

## Security verification

`tests/test_security_contract.py`, `tests/test_state_contract.py`, hook tests, installer/learning PowerShell tests, package-manager tests, repository content validation, and full unit regression provide deterministic evidence for the controls above. A passing test proves only its named contract at the tested revision.

## Reporting

Follow [SECURITY.md](../../SECURITY.md) and use private vulnerability reporting. Public reports and committed evidence must not contain exploit details, credentials, raw private state, or machine-local user paths.
