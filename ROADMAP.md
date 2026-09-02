# Roadmap

Codex Engineering Kit is intentionally small in v0.1. The roadmap prioritizes stronger evidence and portability before adding more active skills.

## v0.1 — Engineering foundation

- lean six-skill catalog;
- orchestrator with focused role references;
- repository-first software architecture guidance;
- concurrency/performance evidence discipline;
- deterministic verification runner;
- capability/regression eval workflow;
- review-gated continuous learning;
- idempotent Windows PowerShell installer/update/uninstall;
- secret-free MCP provider metadata;
- CI for content and PowerShell contracts;
- public architecture/security/contribution documentation.

## v0.2 — Cross-platform installation

- Linux installer parity;
- macOS installer parity;
- shared manifest/ownership contract across platforms;
- cross-platform CI matrix;
- platform-specific path and shell safety tests.

## v0.3 — Verification adapters

- richer project command discovery;
- explicit adapters for common Python/Node build systems;
- configurable required/optional gates;
- structured verification artifacts;
- safer dependency/security scanner integration when tools are present.

## v0.4 — Evals and checkpoints

- reusable deterministic eval adapters;
- richer baseline comparison;
- checkpoint schema and validation;
- explicit session handoff tooling;
- reproducible examples for agent reliability measurements.

## Later exploration

- broader MCP setup validation;
- reusable project presets without embedding secrets;
- signed/reproducible release artifacts;
- opt-in skill packaging/distribution;
- integration tests against future Codex capabilities when officially available.

## Non-goals unless the architecture changes

The project does not currently plan to prioritize:

- a huge marketplace of overlapping active skills;
- pretending another coding agent's hook API exists in Codex;
- remote telemetry by default;
- silent promotion of learned session output;
- autonomous destructive changes to user repositories;
- storing integration credentials in repository configuration.
