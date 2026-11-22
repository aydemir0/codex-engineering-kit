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
| TypeScript and React types | Exact versions in `package.json` | Candidate build reproducibility |

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
