# Codex Engineering Kit v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a public v0.1 Codex-native engineering toolkit with lean skills, role orchestration, deterministic verification, eval-driven workflows, approval-gated learning, safe MCP templates, Windows-first installation, CI, and portfolio-grade documentation.

**Architecture:** Keep only six active core skills and move engineering personas into orchestrator references so Codex context stays lean. Treat project rules, workflows, lifecycle behavior, MCP setup, and installation as explicit repository artifacts and PowerShell scripts rather than pretending Claude Code hook semantics exist in Codex.

**Tech Stack:** Markdown, YAML, JSON, PowerShell 7+, Python 3.11+ for portable content validation, GitHub Actions, OpenAI Codex skills/project instructions.

**Spec:** `docs/superpowers/specs/2026-09-02-codex-engineering-kit-design.md`

## Global Constraints

- Codex-native; no fake `PreToolUse`, `PostToolUse`, `Stop`, or `SessionStart` compatibility.
- Active skill catalog is limited to `orchestrator`, `continuous-learning`, `eval-harness`, `verification-loop`, `software-architecture`, and `concurrency-performance` for v0.1.
- Windows PowerShell is first-class in v0.1; later Linux/macOS support must remain possible.
- Installer is idempotent, supports `-DryRun`, refuses unsafe overwrite by default, and never writes secrets.
- Learned behavior is candidate-based and requires human approval before promotion.
- Public repository must contain no credentials, tokens, private transcripts, or user-specific project data.
- Deterministic graders are preferred over model graders when success can be mechanically checked.
- Attribution for adapted MIT material must live in `THIRD_PARTY_NOTICES.md`.
- A change is not release-ready unless required verification gates actually ran and passed.

---

## File Map

```text
.github/workflows/ci.yml                    Repository contract + PowerShell tests
skills/orchestrator/SKILL.md               Role/workflow routing skill
skills/orchestrator/agents/openai.yaml      Codex-visible metadata
skills/orchestrator/references/roles/*      Non-active engineering role contracts
skills/verification-loop/SKILL.md           Readiness verification contract
skills/eval-harness/SKILL.md                Capability/regression eval contract
skills/continuous-learning/SKILL.md         Candidate extraction/promotion contract
skills/software-architecture/*              Existing architecture skill, normalized into repo
skills/concurrency-performance/*            Performance/concurrency skill
rules/*.md                                  Engineering/security/testing/git/performance rules
contexts/*.md                               Development/review/research operating references
workflows/*.md                              Explicit feature/bugfix/review/release workflows
templates/AGENTS.md                         Safe project-level Codex instruction template
scripts/install.ps1                         Idempotent installer
scripts/update.ps1                          Safe updater
scripts/uninstall.ps1                       Toolkit-owned cleanup
scripts/verify.ps1                          Project-native readiness runner
scripts/learn-session.ps1                   Reviewable learning-candidate generator
scripts/codex-wrapper.ps1                   Explicit preflight/launch/post-session wrapper
mcp/templates/*.json                        Secret-free MCP templates
mcp/configure.ps1                           Local-only MCP config generator
tests/Test-Install.ps1                      Installer/update/uninstall behavior
tests/Test-Verify.ps1                       Verification behavior
tests/Test-Learning.ps1                     Learning safety behavior
tests/validate_content.py                   Skill/workflow/content contracts
examples/sample-project/*                   Verification fixture
README.md                                   Public portfolio entry point
CONTRIBUTING.md                             Contribution workflow
SECURITY.md                                 Security/reporting model
ROADMAP.md                                  Post-v0.1 roadmap
THIRD_PARTY_NOTICES.md                      Attribution
```

---

### Task 1: Repository contracts and validation harness

**Files:**
- Create: `tests/validate_content.py`
- Create: `tests/fixtures/invalid-skill/SKILL.md`
- Create: `.gitignore`
- Create: `.editorconfig`

**Interfaces:**
- Consumes: repository tree.
- Produces: `python tests/validate_content.py` with exit code `0` on valid repo and non-zero on contract violations.

- [ ] **Step 1: Write the failing validator contract**

Create `tests/validate_content.py` with checks for: required directories, exactly the six v0.1 active skill names, each skill containing `SKILL.md`, no `.claude/` paths in active v0.1 files, no obvious secret patterns (`sk-`, `ghp_`, `BEGIN PRIVATE KEY`), and no `TODO`/`TBD` in shipped contracts.

Core assertion shape:

```python
EXPECTED_SKILLS = {
    "orchestrator",
    "continuous-learning",
    "eval-harness",
    "verification-loop",
    "software-architecture",
    "concurrency-performance",
}

actual = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
if actual != EXPECTED_SKILLS:
    fail(f"skill set mismatch: {sorted(actual)}")
```

- [ ] **Step 2: Run validator and confirm RED**

Run:

```powershell
python tests/validate_content.py
```

Expected: non-zero exit because required structure does not yet exist.

- [ ] **Step 3: Add repository hygiene files**

`.gitignore` must ignore at least:

```gitignore
.codex-kit/local/
.codex-kit/candidates/
.env
.env.*
!.env.example
*.log
.DS_Store
Thumbs.db
```

- [ ] **Step 4: Re-run validator**

Expected: still RED, but only for missing implementation artifacts.

- [ ] **Step 5: Commit**

```bash
git add tests .gitignore .editorconfig
git commit -m "test: define repository content contracts"
```

---

### Task 2: Orchestrator skill and role references

**Files:**
- Create: `skills/orchestrator/SKILL.md`
- Create: `skills/orchestrator/agents/openai.yaml`
- Create: `skills/orchestrator/references/roles/architect.md`
- Create: `skills/orchestrator/references/roles/planner.md`
- Create: `skills/orchestrator/references/roles/code-reviewer.md`
- Create: `skills/orchestrator/references/roles/security-reviewer.md`
- Create: `skills/orchestrator/references/roles/build-error-resolver.md`
- Create: `skills/orchestrator/references/roles/e2e-runner.md`
- Create: `skills/orchestrator/references/roles/tdd-guide.md`
- Create: `skills/orchestrator/references/roles/refactor-cleaner.md`
- Create: `skills/orchestrator/references/roles/doc-updater.md`

**Interfaces:**
- Consumes: a user task and repository evidence.
- Produces: selected role reference(s), execution order, evidence requirements, and completion gates without registering nine additional active skills.

- [ ] **Step 1: Extend validator with orchestrator contract**

Assert the nine role files exist and `SKILL.md` contains a routing table with at least `architecture`, `plan`, `review`, `security`, `build`, `e2e`, `tdd`, `refactor`, and `docs` intents.

- [ ] **Step 2: Run validator and confirm RED**

```powershell
python tests/validate_content.py
```

Expected: missing orchestrator/role failures.

- [ ] **Step 3: Implement orchestrator**

The skill must require repository inspection for repo-scoped work, forbid pretending references are autonomous background agents, and define deterministic routing such as:

```markdown
| Intent | Primary role | Required companion |
|---|---|---|
| new feature | planner | tdd-guide |
| architecture change | architect | planner |
| build failure | build-error-resolver | code-reviewer after fix |
| security-sensitive change | security-reviewer | code-reviewer |
| refactor | refactor-cleaner | code-reviewer |
```

Each role file must define: scope, evidence required, forbidden behavior, output contract, completion gate.

- [ ] **Step 4: Run validator and inspect skill size**

```powershell
python tests/validate_content.py
Get-ChildItem skills/orchestrator -Recurse | Measure-Object
```

Expected: orchestrator contracts pass and only one active orchestrator skill exists.

- [ ] **Step 5: Commit**

```bash
git add skills/orchestrator tests/validate_content.py
git commit -m "feat: add lean engineering orchestrator"
```

---

### Task 3: Core engineering skills

**Files:**
- Create: `skills/verification-loop/SKILL.md`
- Create: `skills/verification-loop/agents/openai.yaml`
- Create: `skills/eval-harness/SKILL.md`
- Create: `skills/eval-harness/agents/openai.yaml`
- Create: `skills/continuous-learning/SKILL.md`
- Create: `skills/continuous-learning/agents/openai.yaml`
- Create: `skills/software-architecture/SKILL.md`
- Create: `skills/software-architecture/agents/openai.yaml`
- Create: `skills/concurrency-performance/SKILL.md`
- Create: `skills/concurrency-performance/agents/openai.yaml`

**Interfaces:**
- Verification skill produces `READY`, `NOT READY`, or `PARTIAL` with executed command evidence.
- Eval skill stores project-local evals under `.codex-kit/evals/`.
- Learning skill emits candidates only; promotion requires explicit approval.
- Architecture and concurrency skills preserve the already-defined evidence-first contracts.

- [ ] **Step 1: Add validator checks for metadata and forbidden behavior**

Require every skill to have `agents/openai.yaml`; forbid `auto_approve: true`, `.claude/skills`, and claims of automatic Codex hooks.

- [ ] **Step 2: Run validator and confirm RED**

```powershell
python tests/validate_content.py
```

- [ ] **Step 3: Implement the five remaining skill contracts**

Verification headings must include:

```markdown
### Commands executed
### Evidence
### Blocking failures
### Warnings
### Readiness
```

Eval contract must distinguish capability vs regression evals and deterministic/model/human graders. Learning contract must require candidate evidence, redaction, deduplication, and approval before promotion.

- [ ] **Step 4: Run validator**

```powershell
python tests/validate_content.py
```

Expected: skill-set and metadata checks PASS.

- [ ] **Step 5: Commit**

```bash
git add skills tests/validate_content.py
git commit -m "feat: add core Codex engineering skills"
```

---

### Task 4: Rules, contexts, workflows, and AGENTS template

**Files:**
- Create: `rules/engineering.md`
- Create: `rules/security.md`
- Create: `rules/testing.md`
- Create: `rules/git.md`
- Create: `rules/performance.md`
- Create: `contexts/dev.md`
- Create: `contexts/review.md`
- Create: `contexts/research.md`
- Create: `workflows/feature.md`
- Create: `workflows/bugfix.md`
- Create: `workflows/build-fix.md`
- Create: `workflows/architecture-review.md`
- Create: `workflows/code-review.md`
- Create: `workflows/security-review.md`
- Create: `workflows/refactor.md`
- Create: `workflows/e2e.md`
- Create: `workflows/eval.md`
- Create: `workflows/release.md`
- Create: `workflows/learn.md`
- Create: `workflows/checkpoint.md`
- Create: `templates/AGENTS.md`

**Interfaces:**
- Workflows consume repository evidence and selected role references.
- Every workflow produces an explicit decision/status and verification requirements.

- [ ] **Step 1: Add workflow contract tests**

Validator requires each workflow to contain these headings:

```markdown
## Entry conditions
## Evidence required
## Procedure
## Failure handling
## Verification
## Output contract
```

- [ ] **Step 2: Run validator and confirm RED**

- [ ] **Step 3: Implement concise, non-overlapping contracts**

`templates/AGENTS.md` must instruct Codex to inspect repo-local instructions first, preserve existing behavior, never invent passed tests, and never commit secrets.

- [ ] **Step 4: Run validator and grep for Claude-specific paths**

```powershell
python tests/validate_content.py
rg -n "\.claude|PreToolUse|PostToolUse|SessionStart|Stop hook" .
```

Expected: no active compatibility claims; historical attribution/docs references are allowed only where clearly described as source context.

- [ ] **Step 5: Commit**

```bash
git add rules contexts workflows templates tests/validate_content.py
git commit -m "feat: add Codex-native engineering workflows"
```

---

### Task 5: Safe installer, updater, and uninstaller

**Files:**
- Create: `scripts/install.ps1`
- Create: `scripts/update.ps1`
- Create: `scripts/uninstall.ps1`
- Create: `tests/Test-Install.ps1`

**Interfaces:**
- `install.ps1 [-DryRun] [-Force] [-CodexHome <path>]`
- `update.ps1 [-DryRun] [-Force] [-CodexHome <path>]`
- `uninstall.ps1 [-DryRun] [-CodexHome <path>]`
- Toolkit manifest written to `<CodexHome>/codex-engineering-kit.manifest.json` listing only toolkit-owned installed paths.

- [ ] **Step 1: Write failing Pester-free PowerShell test harness**

Use plain PowerShell assertions so CI needs no module install:

```powershell
function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}
```

Tests must verify dry-run writes nothing, first install copies six skills, second install is idempotent, conflicting user-owned target is refused without `-Force`, and uninstall removes only manifest-owned files.

- [ ] **Step 2: Run and confirm RED**

```powershell
pwsh -NoProfile -File tests/Test-Install.ps1
```

- [ ] **Step 3: Implement installer family**

Use `Join-Path`, `Resolve-Path`, `Test-Path`, and SHA-256 hashes. Never derive Codex home from a hard-coded username; default to `$env:CODEX_HOME` when set, otherwise `$HOME/.codex`.

- [ ] **Step 4: Run tests twice**

```powershell
pwsh -NoProfile -File tests/Test-Install.ps1
pwsh -NoProfile -File tests/Test-Install.ps1
```

Expected: both PASS, proving test isolation/idempotence.

- [ ] **Step 5: Commit**

```bash
git add scripts/install.ps1 scripts/update.ps1 scripts/uninstall.ps1 tests/Test-Install.ps1
git commit -m "feat: add safe Windows installer lifecycle"
```

---

### Task 6: Evidence-based verification runner and sample project

**Files:**
- Create: `scripts/verify.ps1`
- Create: `tests/Test-Verify.ps1`
- Create: `examples/sample-project/package.json`
- Create: `examples/sample-project/src/index.ts`
- Create: `examples/sample-project/tests/smoke.test.mjs`
- Create: `examples/sample-project/tsconfig.json`

**Interfaces:**
- `verify.ps1 -ProjectPath <path> [-Json]`
- JSON result contains `commands`, `build`, `typecheck`, `lint`, `tests`, `security`, `diff`, `readiness`.

- [ ] **Step 1: Write failing verification tests**

Test command discovery from `package.json`; test missing command becomes `SKIPPED` with evidence rather than fake `PASS`; test any failed required gate produces `NOT_READY`.

- [ ] **Step 2: Run and confirm RED**

```powershell
pwsh -NoProfile -File tests/Test-Verify.ps1
```

- [ ] **Step 3: Implement project-native command discovery**

Prefer scripts in `package.json`; support common Python fallbacks only when matching config files exist. Capture command, exit code, and bounded output. Never shell-expand user-provided command text from learned candidates.

- [ ] **Step 4: Verify sample project**

```powershell
pwsh -NoProfile -File scripts/verify.ps1 -ProjectPath examples/sample-project
```

Expected: evidence-based report with no fabricated gates.

- [ ] **Step 5: Commit**

```bash
git add scripts/verify.ps1 tests/Test-Verify.ps1 examples/sample-project
git commit -m "feat: add evidence-based verification runner"
```

---

### Task 7: Continuous-learning candidate pipeline and wrapper

**Files:**
- Create: `scripts/learn-session.ps1`
- Create: `scripts/codex-wrapper.ps1`
- Create: `tests/Test-Learning.ps1`
- Create: `docs/learning.md`

**Interfaces:**
- `learn-session.ps1 -InputPath <path> -OutputPath <path>` produces sanitized candidate JSON/Markdown only.
- `codex-wrapper.ps1` performs preflight, launches `codex`, and optionally runs candidate extraction on explicitly provided session summary input; it does not claim invisible Codex hook access.

- [ ] **Step 1: Write failing learning safety tests**

Fixtures must include a reusable pattern, a one-off typo, and a fake secret. Assertions: reusable pattern retained, typo rejected, secret redacted/rejected, no executable shell content is auto-run, candidate output is not installed as a skill.

- [ ] **Step 2: Run and confirm RED**

```powershell
pwsh -NoProfile -File tests/Test-Learning.ps1
```

- [ ] **Step 3: Implement candidate schema**

Candidate fields:

```json
{
  "title": "string",
  "category": "error_resolution|user_correction|workaround|debugging_technique|project_specific",
  "evidence": ["string"],
  "confidence": "low|medium|high",
  "scope": "project|general",
  "contains_sensitive_data": false,
  "promotion_status": "pending_review"
}
```

- [ ] **Step 4: Run tests and manual dry run**

```powershell
pwsh -NoProfile -File tests/Test-Learning.ps1
```

- [ ] **Step 5: Commit**

```bash
git add scripts/learn-session.ps1 scripts/codex-wrapper.ps1 tests/Test-Learning.ps1 docs/learning.md
git commit -m "feat: add approval-gated learning pipeline"
```

---

### Task 8: Safe MCP templates and local configuration

**Files:**
- Create: `mcp/templates/github.json`
- Create: `mcp/templates/supabase.json`
- Create: `mcp/templates/vercel.json`
- Create: `mcp/templates/railway.json`
- Create: `mcp/templates/cloudflare.json`
- Create: `mcp/configure.ps1`
- Create: `tests/Test-Mcp.ps1`

**Interfaces:**
- `configure.ps1 -Provider <name> -OutputPath <path> [-DryRun]`
- Templates reference environment-variable names or login instructions only; no real secrets.

- [ ] **Step 1: Write failing template tests**

Reject templates containing token-looking literal values; require `required_environment` or `login_required` metadata.

- [ ] **Step 2: Run and confirm RED**

```powershell
pwsh -NoProfile -File tests/Test-Mcp.ps1
```

- [ ] **Step 3: Implement templates/configurator**

Missing optional MCP credentials must produce a provider-specific error and must not affect installer/verification functionality.

- [ ] **Step 4: Run tests**

- [ ] **Step 5: Commit**

```bash
git add mcp tests/Test-Mcp.ps1
git commit -m "feat: add secret-safe MCP configuration templates"
```

---

### Task 9: CI, documentation, attribution, and portfolio surface

**Files:**
- Modify: `README.md`
- Create: `.github/workflows/ci.yml`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `ROADMAP.md`
- Create: `THIRD_PARTY_NOTICES.md`
- Create: `docs/architecture.md`

**Interfaces:**
- CI runs content validator and PowerShell tests on pull requests/pushes.
- README gives an external developer enough information to understand, install, verify, and evaluate the project.

- [ ] **Step 1: Define CI before polishing docs**

Workflow jobs:

```yaml
- python tests/validate_content.py
- pwsh -NoProfile -File tests/Test-Install.ps1
- pwsh -NoProfile -File tests/Test-Verify.ps1
- pwsh -NoProfile -File tests/Test-Learning.ps1
- pwsh -NoProfile -File tests/Test-Mcp.ps1
```

- [ ] **Step 2: Add accurate attribution**

`THIRD_PARTY_NOTICES.md` must name `WorldFlowAI/everything-claude-code`, its MIT licensing, the categories of ideas/material adapted, and explicitly state no endorsement.

- [ ] **Step 3: Rewrite README as portfolio-quality product documentation**

Required sections:

```markdown
# Codex Engineering Kit
Why it exists
Architecture
Core capabilities
Quick start
Example workflow
Verification model
Continuous learning safety
MCP integrations
Supported environments
Security model
Roadmap
Attribution
Contributing
```

Include a Mermaid architecture diagram and a concrete Windows install example using a temporary clone + `scripts/install.ps1`.

- [ ] **Step 4: Run complete local verification**

```powershell
python tests/validate_content.py
pwsh -NoProfile -File tests/Test-Install.ps1
pwsh -NoProfile -File tests/Test-Verify.ps1
pwsh -NoProfile -File tests/Test-Learning.ps1
pwsh -NoProfile -File tests/Test-Mcp.ps1
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add .github README.md CONTRIBUTING.md SECURITY.md ROADMAP.md THIRD_PARTY_NOTICES.md docs/architecture.md
git commit -m "docs: prepare Codex Engineering Kit v0.1"
```

---

### Task 10: Final release gate and pull request

**Files:**
- Modify only if verification finds defects.

**Interfaces:**
- Produces a reviewable PR from `feat/initial-architecture` to `main` with evidence and no unresolved blockers.

- [ ] **Step 1: Run final repository scan**

```powershell
python tests/validate_content.py
rg -n "sk-[A-Za-z0-9]|ghp_[A-Za-z0-9]|BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY" .
git status --short
git diff main...HEAD --stat
```

Expected: validator PASS, secret scan has no real credentials, tree clean.

- [ ] **Step 2: Run all PowerShell verification suites**

```powershell
Get-ChildItem tests/Test-*.ps1 | ForEach-Object {
    & pwsh -NoProfile -File $_.FullName
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

Expected: exit `0`.

- [ ] **Step 3: Self-review against acceptance criteria**

Confirm all ten design-spec acceptance criteria have direct evidence; any unavailable real-machine/Codex-listing validation is explicitly marked as pending external verification rather than claimed passed.

- [ ] **Step 4: Open PR**

PR title:

```text
feat: launch Codex Engineering Kit v0.1
```

PR body must summarize architecture, tests run, security/attribution notes, and any validation that still requires the user's Windows Codex machine.

- [ ] **Step 5: Stop before merge**

Do not merge automatically. User reviews the public portfolio surface and final PR first.

---

## Plan Self-Review

- Spec coverage: all v0.1 acceptance criteria map to Tasks 1–10.
- Placeholder scan: no implementation steps rely on `TODO`, `TBD`, or unspecified error handling.
- Interface consistency: installer uses toolkit manifest ownership; verification emits explicit evidence/readiness; learning never promotes automatically; MCP templates stay secret-free.
- Scope: cross-platform parity, telemetry, marketplace compatibility, and autonomous repo modification remain deferred exactly as specified.
