# Verification Engine

Codex Engineering Kit provides a cross-platform verification engine implemented in Python 3.11 standard-library code.

## Run it

```text
python -m verification.cli --project PATH --json
```

For Node/TypeScript repositories, an explicit package manager can be supplied with `--package-manager npm|pnpm|yarn|bun`. The PowerShell `scripts/verify.ps1` entry point is only a compatibility wrapper around this Python engine.

## Status semantics

Every verification step records its command, exit code, duration, status, and bounded evidence. Step status is exactly one of:

- `passed` — the command ran and exited successfully.
- `failed` — the command ran and failed, including timeouts.
- `skipped` — the gate was not discovered or was intentionally not run. `skipped` is never rewritten as `passed`.
- `unavailable` — a required discovered gate cannot run in the current environment.

Overall report status is:

- `failed` when any step failed;
- `partial` when required discovered evidence is unavailable, or when only generic checks are possible and no project-specific executable gate ran;
- `passed` when no step failed or is required-but-unavailable and at least one executable gate ran successfully.

The CLI exits with code `1` only for an overall `failed` report. `partial` is still explicit in the JSON but does not become a fabricated failure or success.

## Project classification

Classification priority is:

1. Node/TypeScript when `package.json` exists;
2. Python when Python project markers exist;
3. generic repository otherwise.

Generic checks include deterministic secret-like material scanning and `git diff --check` when the target is a Git worktree.

## Node package-manager resolution

Initial supported managers are exactly `npm`, `pnpm`, `yarn`, and `bun`. Resolution order is:

1. explicit CLI/package-manager setting;
2. `packageManager` in `package.json`;
3. a single manager lockfile;
4. an available non-npm manager, preferring `pnpm`, then `yarn`, then `bun`;
5. npm fallback only when `package.json` exists and npm is available.

An authoritative `packageManager` or lockfile choice that is not installed is `unavailable`; it does not silently fall through to npm. Conflicting manager lockfiles without a `packageManager` field are ambiguous and no manager is guessed.

## Repository-authored script permission warning

Discovered build, test, lint, and typecheck scripts are **repository-authored code executed with current user/Codex permissions**. Verification does not sandbox those project scripts or make them safe merely by discovering them. Review repository instructions and project configuration before running verification on untrusted code.

## Artifact

The default artifact is:

```text
<project>/.codex-kit/verification/latest.json
```

It is a versioned state document with:

- `schemaVersion: 1`
- `kind: verification-report`
- project type and path
- selected package manager when applicable
- every step's command, exit code, duration, status, and bounded evidence
- final report status

Captured process stdout/stderr is bounded before it reaches artifacts. Runtime artifacts stay under gitignored `.codex-kit/`; raw private transcripts, credentials, and tokens are not part of the verification report contract.
