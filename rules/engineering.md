# Engineering Rules

- Read repository-local instructions before editing.
- Inspect relevant implementation and tests before proposing repository-specific changes.
- Preserve working public behavior unless change is explicitly required.
- Prefer small reversible changes over rewrites.
- Keep modules cohesive and dependencies intentional.
- Treat data ownership, transactions, deployment, observability, and rollback as engineering concerns, not afterthoughts.
- Never claim a command, test, deploy, or migration ran unless it actually ran.
- Separate facts, assumptions, and recommendations.
- Escalate hidden architectural complexity instead of forcing a local patch through it.
