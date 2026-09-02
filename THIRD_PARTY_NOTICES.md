# Third-Party Notices

Codex Engineering Kit is an independent implementation. Its Codex-specific architecture, installer ownership model, verification runner, learning-candidate safety model, workflows, and documentation are maintained in this repository.

## Everything Claude Code / ECC

Some high-level ideas about organizing coding-agent workflows were inspired by the open-source **Everything Claude Code** project by **Affaan Mustafa**, historically published as `affaan-m/everything-claude-code` and currently available as `affaan-m/ECC`.

Upstream project: https://github.com/affaan-m/ECC

Upstream license: MIT License

Upstream copyright notice:

> Copyright (c) 2026 Affaan Mustafa

Concepts reviewed while designing this project included:

- focused engineering roles/agents;
- reusable workflow/skill organization;
- verification loops;
- eval-driven development;
- session learning/checkpoint ideas;
- development/review/research context organization;
- MCP configuration organization.

Codex Engineering Kit does **not** represent Claude-specific hook names, command semantics, or lifecycle APIs as native Codex capabilities. Those concepts were redesigned around Codex skills, role references, explicit workflows, project instructions, PowerShell scripts, and local-only integration metadata.

No endorsement by Affaan Mustafa, the upstream project, Anthropic, or OpenAI is implied.

Where a future contribution directly incorporates a substantial portion of third-party MIT-licensed source code rather than independently reimplementing a concept, the corresponding copyright and license notice must be preserved with that material.
