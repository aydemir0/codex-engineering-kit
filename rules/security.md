# Security Rules

- Never commit or print credentials, tokens, private keys, or secret-bearing local configuration.
- Distinguish authentication from authorization; privileged actions require server-side enforcement where applicable.
- Treat tenant/data isolation, uploads, external fetches, deserialization, and privileged integrations as trust boundaries.
- Validate untrusted input and encode/escape output for the destination context.
- Do not weaken security controls to make tests or demos pass.
- Prefer least privilege for MCP/integration permissions.
- Security-sensitive changes require explicit evidence, regression checks, and human review when risk remains high.
