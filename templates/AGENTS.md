# AGENTS.md

## Operating principles

- Read this file and any deeper repository-local instruction files before editing.
- Inspect the relevant implementation, tests, schemas, and build/deploy configuration before repository-specific recommendations.
- Preserve existing working behavior unless the requested change requires otherwise.
- Prefer small reversible changes; avoid unrelated refactors.
- For new behavior and bug fixes, write a meaningful failing test first when automated testing is practical.
- Use repository-native commands and package managers.
- Never claim a build, test, migration, deployment, benchmark, or security check passed unless it actually ran successfully.
- Never commit credentials, tokens, private keys, secret-bearing local configuration, or private learned-session data.
- Treat authentication, authorization, data isolation, uploads, external fetches, and privileged operations as security boundaries.
- Measure performance before optimizing and keep concurrency bounded.

## Completion contract

Before declaring work complete, report:

1. files/behavior changed;
2. tests and verification commands actually run;
3. blocking failures and warnings;
4. migration/rollback implications when relevant;
5. final status: `READY`, `NOT READY`, or `PARTIAL`.
