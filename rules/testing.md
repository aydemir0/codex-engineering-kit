# Testing Rules

- New behavior and bug fixes start with a meaningful failing test when automated testing is practical.
- Test externally observable behavior and important invariants; avoid tests coupled only to implementation details.
- Prefer the smallest deterministic test layer that proves the behavior.
- Run the narrow test first, then the relevant surrounding suite.
- Skipped, unavailable, or unexecuted tests are never reported as passed.
- Regression tests must fail if the bug or behavior change is reverted.
- Security, migration, concurrency, and failure-path changes need tests appropriate to their risk.
