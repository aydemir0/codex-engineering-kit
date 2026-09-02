# Contributing

Thanks for helping improve Codex Engineering Kit.

The project favors a small, explicit engineering surface over a large catalog of overlapping skills. Changes should be easy to review, test, and reverse.

## Development setup

```powershell
git clone https://github.com/aydemir0/codex-engineering-kit.git
cd codex-engineering-kit
```

Run the repository contracts before opening a pull request:

```powershell
python tests/validate_content.py
pwsh -NoProfile -File tests/Test-Install.ps1
pwsh -NoProfile -File tests/Test-Verify.ps1
pwsh -NoProfile -File tests/Test-Learning.ps1
pwsh -NoProfile -File tests/Test-Mcp.ps1
```

## Contribution workflow

1. Create a focused feature branch.
2. Inspect the relevant design/workflow contracts before changing behavior.
3. For behavior changes, write or extend a failing contract test first when practical.
4. Implement the smallest change that satisfies the contract.
5. Run the narrow test, then the full repository checks.
6. Review the final diff for unrelated changes and secret-bearing content.
7. Open a pull request describing behavior, verification evidence, and any unresolved limitation.

## Adding or changing skills

v0.1 intentionally exposes exactly six active skills. Adding another active skill is an architectural change because every skill increases the visible skill surface and context budget.

A proposal for a new active skill should explain:

- why an existing core skill or orchestrator reference cannot own the behavior;
- expected trigger conditions;
- overlap with existing skills;
- why the context cost is justified;
- validation and migration impact.

Every active skill must include:

```text
skills/<name>/SKILL.md
skills/<name>/agents/openai.yaml
```

`agents/openai.yaml` must contain a short human-facing name/description and a default prompt that explicitly invokes `$<skill-name>`.

## Role references

Prefer a role reference beneath `skills/orchestrator/references/roles/` when specialized engineering behavior does not need to be an independently discoverable active skill.

Role contracts should define:

- scope;
- evidence required;
- forbidden behavior;
- output contract;
- completion gate.

## Workflow contracts

Every file under `workflows/` must contain:

```markdown
## Entry conditions
## Evidence required
## Procedure
## Failure handling
## Verification
## Output contract
```

Do not treat a workflow as an invisible hook. If behavior requires execution, expose it through an inspectable script, repository instruction, or explicit Codex workflow.

## PowerShell scripts

v0.1 is PowerShell 7+ first-class.

Scripts that modify local state must:

- support safe failure behavior;
- avoid writing credentials;
- use explicit paths rather than usernames hard-coded into the repository;
- distinguish toolkit-owned and user-owned files;
- provide `-DryRun` for destructive or state-changing operations when applicable.

Installer changes must preserve manifest ownership and idempotence.

## Security and secrets

Never commit:

- API keys or tokens;
- private keys;
- `.env` files containing real credentials;
- raw private session transcripts;
- private project data;
- generated local MCP authentication state.

Use obviously synthetic fixture values in tests and keep them below the repository's secret-pattern thresholds where possible.

For a vulnerability, follow [`SECURITY.md`](SECURITY.md) instead of posting exploit details in a public issue.

## Documentation

Documentation must describe behavior that exists and has been verified. Do not advertise planned capabilities as shipped.

When an interface, install command, verification contract, or trust boundary changes, update the corresponding README/docs in the same pull request.

## Pull request expectations

A good PR explains:

- the actual problem;
- the chosen change and alternatives rejected when relevant;
- tests/verification actually run;
- security/compatibility implications;
- any remaining validation that requires a specific external environment.

Do not mark unavailable validation as passed.
