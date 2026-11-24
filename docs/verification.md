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

- `failed` when any step failed.
- `partial` when required evidence is unavailable, a detected test family
  could not run, or the project has no runnable test gate.
- `passed` when the detected test families are covered, the required checks
  succeeded, and the candidate remained stable during verification.

The CLI exits with code `1` for `failed`. Use `--require-complete` in CI to
also reject `partial` with exit code `2`. See
[test-family coverage](verification/test-coverage.md) for discovery limits.

## Project classification

Classification priority is:

1. Node/TypeScript when `package.json` exists;
2. Python when Python project markers exist;
3. generic repository otherwise.

Generic checks include deterministic secret-like material scanning and `git diff --check` when the target is a Git worktree.

When Node and Python markers coexist in the same project root, CEK retains
the Node classification and runs both the Node preset and the discovered
Python tests. The Python steps have distinct names such as `tests-python`.

To verify independent project roots under a common checkout, specify each
root with a relative path. For example, use the following command with
[the TypeScript/Python example](../examples/typescript-python-contract/README.md).

```text
python -m verification.cli --project PATH --include-project client --include-project service --require-complete --json
```

Explicit scopes replace automatic checks at the common root. Repository-level
checks and the candidate manifest still cover the common root. The report
lists the selected directories under `projectRoots` and prefixes each
project's steps and test families with its directory. A failure in any scope
fails the aggregate. A scope without a covered test family makes it partial
when the checks that ran pass. Paths must denote separate, existing
directories under the root.

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
- detected test families and their statuses
- final report status

Captured process stdout/stderr is bounded before it reaches artifacts. Runtime artifacts stay under gitignored `.codex-kit/`; raw private transcripts, credentials, and tokens are not part of the verification report contract.
