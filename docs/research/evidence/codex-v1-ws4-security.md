# CEK v1 WS4 Security Closure Evidence

Date: 2026-09-09  
Baseline: `e449cc754088efddc070f54f97887d7f834b2171`  
Implementation revision: `eacc3d077211a83d3d31eecee90a7e071db990b5`

## Assessment

WS4 covers only prompt injection, shell/tool safety, destructive writes, secrets, state leakage, MCP/app permissions, provenance, install/update ownership, learning promotion, and plugin metadata/URLs. The implementation revision satisfies the deterministic gates below. This assessment does not claim that hooks are a sandbox, that secret recognition is exhaustive, or that Codex Desktop has the same behavior as Codex CLI 0.153.

## Threat and contract inventory

| Surface | Root cause found at baseline | Deterministic contract at implementation revision | Residual boundary |
| --- | --- | --- | --- |
| Prompt injection | Compact-checkpoint output interpolated workspace-writable fields. | Restart text is fixed; tests inject adversarial checkpoint values and prove they are absent. | Semantic prompt-injection recognition remains a host/model concern. |
| Shell/tool safety | Windows batch execution did not safely support executable paths with spaces and accepted command metacharacters. | Batch paths are quoted for `COMSPEC`; unsafe arguments are rejected before execution; `shell=False` remains the process boundary. | Repository-authored commands still run with current user permissions. |
| Destructive writes | Mutable uninstall-manifest paths could authorize traversal or the `skills/.` root; repository-controlled hook links could redirect state writes outside the workspace. | Manifest identity, exact `skills/<name>` shape, containment, and current tree hash are required before deletion. Hook state rejects pre-existing link/reparse paths and uses exclusively created temporary files. | Time-of-check/time-of-use link swaps and local administrator changes remain outside the contract. |
| Secrets | Verification, pressure, and learning outputs did not share sufficient redaction/rejection coverage. | Tests cover credential-shaped values, private-key blocks, bearer forms, machine-local paths, and session identifiers without recording the samples in this document. | Pattern matching cannot recognize every secret format. |
| State leakage | State payloads could replace reserved schema/kind identity; generated verification state lacked an explicit ignore rule. | Reserved fields are authoritative; hook state is allowlisted; verification output is bounded/redacted; `.codex-kit/verification/` is ignored. | Explicit export or force-adding ignored local artifacts can still disclose local data. |
| MCP/app permissions | Template checks did not prove missing required environment failed or that supplied credentials stayed out of generated state. | Disposable tests require declared environment, prove supplied credentials are not persisted, and keep template scope local-only. | Provider grants and remote authorization behavior remain external. |
| Provenance | CI and licensing boundaries needed one deterministic contract. | Tests require full 40-character action pins and the MIT/third-party notice boundary. | Upstream and runner compromise are outside CEK. |
| Install/update ownership | Existing manifest entries were not all revalidated before authorizing updates; forced-backup execution also collided with PowerShell's read-only `$HOME`. | Strict name/path/hash/duplicate validation, conflict refusal, idempotence, and forced-backup content are tested on disposable homes. | A local administrator can alter both content and ownership records. |
| Learning promotion | Sensitive category and alternate bearer/path encodings could reach pending candidates. | Sensitive title/category/evidence inputs are rejected; emitted candidates remain non-executable JSON with `pending_review`. | Human review is mandatory before later promotion. |
| Plugin metadata/URLs | URL checks did not bind the first GitHub owner segment exactly. | HTTPS, GitHub host, exact `aydemir0` owner, repository-local marketplace source, and explicit policy are tested. | Future external metadata and account ownership require separate verification. |

The complete model, protected assets, trust boundaries, and non-goals are recorded in [the WS4 threat model](../../security/threat-model.md).

## TDD evidence

Each applicable change began with a focused failing assertion and was then made green at the shared trust boundary. Observed RED cases included reserved state-field override, adversarial checkpoint interpolation, traversal/dot uninstall targets, invalid update-manifest identity, sensitive learning/verification output, serialized session identifiers, fine-grained GitHub tokens, unsafe batch arguments, spaced batch paths, repository-controlled state links, and missing generated-state ignore coverage. The corresponding focused tests passed after the minimal fixes; no new dependency or generalized security framework was added.

## Fresh verification

The following checks passed on implementation revision `eacc3d077211a83d3d31eecee90a7e071db990b5`:

- `python -B -m unittest discover -s tests -p 'test_*.py'`: 197 tests, PASS.
- `./tests/Test-Install.ps1`: PASS.
- `./tests/Test-Learning.ps1`: PASS; one safe candidate emitted and eight sensitive or unsupported candidates rejected.
- `./tests/Test-Mcp.ps1`: PASS.
- `./tests/Test-Verify.ps1`: PASS.
- `python -B tests/validate_content.py`: PASS.
- `python -B -m compileall -q runtime verification scripts/acceptance tests`: PASS.
- `git diff --check`: PASS.

Expected failure text printed by negative-path fixtures does not represent a suite failure; the unittest process completed with `OK`.

## Support boundary

The Codex CLI 0.153 boundary is unchanged: CEK skills and hooks are plugin-native; the reviewer is a CEK-shipped, Codex-native project-local role provisioned from `.codex/agents/reviewer.toml`. Plugin installation does not register custom agent roles on CLI 0.153. No Codex Desktop behavior is inferred.

## Closure gate

WS4 may be marked CLOSED only when this evidence-only change also passes content/security contracts and an independent security reviewer finds no critical/high issue and no concrete unmitigated medium blocker within the frozen scope. WS5, WS6, WS7, install UX, publishing, release, and broader host/provider security remain outside this workstream.
