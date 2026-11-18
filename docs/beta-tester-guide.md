# CEK v1.1.0-beta.1 — External tester guide

This is an **exploratory public-beta usability test**, not a benchmark or a claim of general reliability. We are seeking the first **3–5 independent Windows developers** to check whether the published artifact is understandable, installable and usable.

## Fixed release and environment

- **Source to test:** GitHub [`v1.1.0-beta.1` pre-release](https://github.com/aydemir0/codex-engineering-kit/releases/tag/v1.1.0-beta.1).
- **Expected checkout commit:** `e4d9430f23af6a248ee322559c5c5a391f3e3339`.
- **Supported test environment:** Windows x64, **PowerShell 7+** (`pwsh`), Python 3.11+, Git and the **complete official Codex CLI 0.155.1 Windows x64 package**. Use the SHA-256 checks in [install.md](install.md); an npm launcher or standalone binary is not an equivalent validated host.
- **Instructions:** Follow the [current Windows quickstart](quickstart.md) while testing the **fixed beta tag**, not the moving `main` source. The tag's embedded documentation is an older snapshot and may still describe the beta as unpublished; the current `main` instructions correct that wording without modifying the tag.

In a fresh PowerShell 7 session, record the version and clone the fixed release:

```powershell
$PSVersionTable.PSVersion
git clone --branch v1.1.0-beta.1 https://github.com/aydemir0/codex-engineering-kit.git cek-beta-test
git -C cek-beta-test rev-parse HEAD
```

If the printed commit is not the expected one, **stop**. Choose fresh, separate runtime, project and `CODEX_HOME` folders outside the source checkout. Do not install CEK in a real project for this test.

## Choose a test track

**Track A — credentials-free first use (recommended):** Follow quickstart sections 1–2. Record whether installation, plugin discovery, native host probe and the deterministic integrity demo succeed. These checks make **no model call** and should be attempted first. Stop on any failed prerequisite; do not disable runtime identity or security guards.

**Track B — optional model task:** Only after Track A, and only if you **personally choose** to authenticate and use model tokens, follow quickstart section 3 on its disposable calculator fixture. Use the official Codex device login for that isolated profile; do not copy authentication files or use a real codebase. Record RED, file edit, GREEN, verifier result and independent checks. A single successful model task is not evidence of broad reliability. Code Mode under the pinned CLI is still marked experimental.

## What to report

Record one feedback entry per developer/test, including negative results:

| Field | Example/expectation |
| --- | --- |
| Tester ID | Nonidentifying alias, e.g. T01 |
| Source identity | `v1.1.0-beta.1` and the exact resolved commit |
| Environment | Windows build/architecture, `$PSVersionTable.PSVersion`, Python version, full Codex CLI version |
| Selected track | A only / A + optional B |
| Start/end | Local clock timestamps for **time-to-first-success**; if blocked, report time-to-blocker |
| First outcome | PASS, FAIL, BLOCKED, or NOT_RUN — **do not relabel a skipped phase as PASS** |
| First friction | The first confusing instruction/error, sanitized exit code or error class |
| Actual result | Install, plugin discovery, demo, and (if run) model task independently |
| Follow-up | Would you use CEK for another task? Why/why not? |
| Issue link | GitHub issue URL if the problem can be reported safely |

Use the existing [GitHub bug report form](https://github.com/aydemir0/codex-engineering-kit/issues/new/choose) when a reproducible failure occurs. Report documentation confusion too, without inventing an error code.

**Privacy:** Never attach `auth.json`, `CODEX_HOME` archives, credentials, environment-variable dumps, private project paths, raw model transcripts, or unredacted session logs. Prefer a minimal synthetic reproduction and sanitized error text. If you suspect a security vulnerability, follow [SECURITY.md](../SECURITY.md) rather than posting exploit details publicly.

## Existing observed evidence and limits

On 18 November 2026, the operator ran one successful authenticated model task on **this exact beta tag**, following an earlier single-task success on a different package/commit. The [sanitized published-tag smoke summary](research/evidence/cek-beta-smoke-20261118.md) explains what passed and what remains unverified. Its local authenticated raw evidence is not public.

This first 3–5 tester sample is **qualitative discovery**. Do not publish a task-success percentage, comparative advantage or statistical reliability estimate from it. We are looking for reproducible adoption friction, not a favorable score.
