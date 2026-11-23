# Frontend review — separate patched dependency candidate (22 Nov 2026)

**Not in the active benchmark protocol. Not approved as a production app.**

This new fixture candidate preserves the intentionally flawed historical
`app/page.tsx` *byte-for-byte* so the frontend review prompt can still
identify client/server state ownership and keyboard accessibility defects.
A minimal `app/layout.tsx` and isolated package dependencies permit a
future independent fixture validation.

| Dependency | Pinned candidate version | Rationale |
| --- | --- | --- |
| Next.js | `16.4.5` | November 3, 2026 security release on Active LTS; official [release](https://github.com/vercel/next.js/releases/tag/v16.4.5) |
| React and React DOM | `19.3.1` | October 2026 security release with fixes to React Server Components; official [React release](https://github.com/facebook/react/releases/tag/v19.3.1) |
| TypeScript and React/Node types | Exact versions in `package.json` | Required for an offline, reproducible Next.js TypeScript build |

The pinned `package-lock.json` is a *new* dependency graph, not an update to
`benchmarks/fixtures/frontend-review/package.json` (`next:15.0.0`,
`react:19.0.0`). The original benchmark case remains pinned to commit
`1dbf382b6e838ca351c6fb8818a64aa793176198` and is covered by its
frozen 45-run historical evidence. **No old run or result is reclassified.**
The original fixture has **41 unresolved Dependabot alerts** and must not be
installed, served, or deployed on a trusted machine.

## Promotion gates (not satisfied here)

1. Run a dependency advisory check against the new lockfile, then inspect
   `npm audit` results and GitHub Dependabot alerts with exact scope.
2. Verify build and rendering of this candidate **in a disposable isolated
   environment without valuable credentials**, not in historical campaign.
   The production compilation/typecheck/static generation are now verified;
   user interactions, the absent API route and end-to-end rendering are **not**
   verified.
3. Define a new benchmark case/protocol ID, source commit SHA and methodology
   hash. Do not silently add this candidate to the existing five-case,
   single-commit-pin protocol.
4. Only then authorize a new campaign, separately from the frozen results.

This folder is a **candidate**, not a security attestation and not part of
normal CEK installation. The intentionally flawed UI is review material, not
a recommendation to ship this page.

## Dependency-audit snapshot

On 22 Nov 2026, the candidate's lockfile was generated using
`npm install --package-lock-only --ignore-scripts --no-audit --no-fund`
against the public npm registry with an isolated user config. No package
scripts ran and no `node_modules` directory was installed.
A separate `npm audit --json` request on the generated lockfile reported
**0 vulnerabilities (0 critical, high, moderate, low)** across the
candidate's resolved dependency graph. This is a **date-scoped registry
advisory result**, not a guarantee that the candidate builds, runs securely,
or is safe for production. The audit does not clear the 41 alerts for the
*original* historical Next.js 15.0.0 package.

This candidate has **not** been promoted to the five-case benchmark or
executed as a model run. Any future execution must use isolated,
credentials-free infrastructure and new pinned evidence.

## Isolated dependency and production-build evidence (23 Nov 2026)

The candidate was copied byte-for-byte into a disposable isolated work area.
The public `node:22-bookworm-slim` image was pinned to digest
`sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee`.
A Docker-managed **Linux volume** was used so no normal Codex profile,
repository root, Docker credentials, or host secrets were mounted.
Installation used `npm ci --ignore-scripts --no-audit --no-fund` with
network access for public registry packages only. The actual
`npm run build` was then executed in a **separate network-disabled
container**, using non-root UID 1000, dropped Linux capabilities,
`no-new-privileges`, a read-only root filesystem, memory/CPU/process limits,
and an isolated temporary directory.

The first offline build exposed a missing `@types/node` TypeScript
dependency. The candidate now pins `@types/node:22.15.30` in both
`package.json` and the regenerated lockfile. Next.js initially
rewrote TypeScript config to use `jsx:react-jsx` and to include
`.next/dev/types/**/*.ts`; both settings are now declared in source.

After these corrections, a fresh `npm ci` and two offline production builds
passed, including TypeScript checks and static generation of `/` and
`/_not-found`. The final build **did not modify tsconfig.json** (before/after
SHA-256 identical: `0e55627f62d744ce2960e02ee7ee84854fc02f47252302031a1984f65e5fcb4f`).
A subsequent independent registry `npm audit --json --audit-level=low`
on the locked Linux dependency graph reported **0** findings across all
severity categories.

**Not yet verified:** actual API response, keyboard behavior, browser
interaction, networked runtime or the original case's 45 model runs.
A successful build is not a benchmark run or a product security certification.
The original vulnerable fixture and pinned historic benchmark remain untouched.
