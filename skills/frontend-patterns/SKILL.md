---
name: frontend-patterns
description: Reviews component, rendering, state, accessibility, data-fetching, and measured frontend performance boundaries using repository evidence.
---

# Frontend Patterns

Use this skill for frontend changes where component ownership, client/server rendering, state ownership, data fetching, accessibility, interaction resilience, or measured web performance materially affects correctness. Treat framework conventions as repository-specific evidence, not universal architecture.

## Entry conditions

Use when the task has a concrete frontend boundary to inspect or change: component structure, rendering ownership, client/server transitions, state/data ownership, accessibility, async interaction, or measured browser performance. Keep the scope on the affected user-facing flow and its actual runtime constraints.

Do not move code client-side merely to simplify implementation.

## Repository evidence

Inspect the smallest relevant set of repository instructions, framework/runtime configuration, route/layout structure, server and client component markers, data-fetching utilities, state stores, cache configuration, styling system, accessibility utilities, tests, build output, and available runtime or browser measurements.

Identify which layer owns each piece of state and data, where rendering occurs, which boundaries hydrate, and which user interactions require client execution. Separate observed behavior from assumptions. Do not invent framework capabilities, caching semantics, or browser support not shown by the repository or runtime evidence.

## Rendering and client/server boundaries

Keep server-renderable work on the server when that preserves correctness, security, bundle size, and data locality. Introduce client boundaries only for browser APIs, local interaction state, subscriptions, or other verified client-only needs.

Trace hydration boundaries and serialized props across server/client transitions. Avoid sending secrets or unnecessary data to the browser. Check whether moving a boundary changes caching, streaming, prefetching, error handling, or authorization behavior.

Do not treat a framework directive or component template as evidence that an entire subtree belongs on the client.

## State and data ownership

Assign one owner to each mutable state source. Distinguish server state, URL/navigation state, persisted client state, derived view state, and ephemeral interaction state before choosing storage.

Do not duplicate server state into local state without an ownership reason.

Prefer derivation over synchronization when a value can be computed from authoritative inputs. When local state mirrors an external source by necessity, define synchronization direction, staleness behavior, reset conditions, and conflict handling.

For lists and dynamic trees, verify stable identity and keys. For async work, account for cancellation, stale responses, navigation races, overlapping mutations, optimistic updates, and rollback behavior. Inspect how data fetching and cache invalidation interact with mutation ownership.

## Accessibility and interaction

Accessibility regressions are correctness regressions.

Use semantic elements and platform behavior before custom interaction patterns. Verify keyboard reachability, focus order, visible focus, focus restoration after overlays/navigation, accessible names, form labels and errors, status announcements where needed, and non-pointer operation.

Preserve interaction under slow networks, repeated clicks, resize, zoom, reduced motion, and responsive layouts when material to the flow. Do not rely on color, hover, or pointer-only behavior to communicate required state.

## Error, loading, and empty states

Define behavior for initial loading, incremental loading, empty data, partial data, recoverable errors, terminal errors, offline/disconnected states when relevant, and permission-denied states. Keep loading/error UI aligned with the rendering boundary that owns the data.

Prevent duplicate submission and stale UI after mutation. For optimistic interfaces, specify rollback and reconciliation when the server rejects or transforms the change. Avoid masking failures with indefinite spinners or silent retries.

## Performance evidence

Do not claim a rendering change is faster without measurement.

Inspect evidence appropriate to the claim: bundle output, request waterfalls, render counts, profiler traces, browser performance recordings, runtime metrics, or Core Web Vitals. Treat Core Web Vitals as measured evidence only when the measurement source and environment are known.

Relate performance work to an identified bottleneck such as excessive JavaScript, hydration cost, repeated rendering, blocking data dependencies, oversized assets, layout instability, or interaction latency. Do not trade correctness or accessibility for an unmeasured speed hypothesis.

## Verification

Choose tests from the actual change surface: component/unit tests for pure state and rendering logic, integration tests for data and interaction ownership, accessibility checks, keyboard/focus tests, loading/error/empty-state coverage, async race/cancellation tests, responsive checks, and end-to-end coverage for critical flows.

When making performance claims, rerun the same measurement method before and after the change and report the environment and range rather than a single unsupported number. Preserve repository-native build, lint, typecheck, and test commands.

## Output contract

Return a concise evidence-bound review with:

1. observed rendering and client/server boundary;
2. state and data owners;
3. accessibility and interaction invariants;
4. loading, error, empty, and async race behavior;
5. cache/data-fetch implications;
6. measured performance evidence or the measurement still required;
7. executable verification gates and unresolved assumptions;
8. final decision: `Adopt`, `Reject`, `Experiment`, or `Needs evidence`.
