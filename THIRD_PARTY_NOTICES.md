# Third-Party Notices

Codex Engineering Kit is an independent implementation. Its native Codex plugin packaging, hook/runtime code, project-local subagents, state/compaction runtime, verification/eval tooling, worktree acceptance, release contracts, installer ownership model, learning-candidate safety model, workflows, and documentation are maintained in this repository.

## Everything Claude Code / ECC

Some high-level ideas about organizing coding-agent workflows were inspired by the open-source **Everything Claude Code** project by **Affaan Mustafa**, historically published as `affaan-m/everything-claude-code` and currently available as `affaan-m/ECC`.

Upstream project: https://github.com/affaan-m/ECC

Upstream license: MIT License

Upstream copyright notice:

> Copyright (c) 2026 Affaan Mustafa

High-level concepts reviewed while designing CEK included:

- focused engineering roles/agents;
- reusable workflow/skill organization;
- verification loops;
- eval-driven development;
- session learning/checkpoint ideas;
- development/review/research context organization;
- MCP configuration organization.

CEK's v0.2 native Codex implementation is not a representation of Claude-specific lifecycle behavior. Native `.codex-plugin` packaging, `hooks/hooks.json` integration, the Python hook dispatcher, `.codex/agents` custom-agent definitions, versioned `.codex-kit` state/compaction handling, and Plan F compatibility/release evidence were implemented specifically against CEK's Codex design and repository evidence.

CEK does **not** present Claude-specific hook names, command semantics, or lifecycle APIs as Codex capabilities.

No endorsement by Affaan Mustafa, the upstream project, Anthropic, or OpenAI is implied.

Where a future contribution directly incorporates a substantial portion of third-party MIT-licensed source code rather than independently reimplementing a concept, the corresponding copyright and license notice must be preserved with that material.
