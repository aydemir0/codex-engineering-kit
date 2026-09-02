# Refactor Workflow

## Entry conditions
A behavior-preserving structural cleanup has a concrete target such as duplication, dead code, oversized units, or dependency tangling.

## Evidence required
Call sites, public interfaces, behavioral tests, dependency direction, and runtime usage of code considered for deletion/extraction.

## Procedure
1. Route to `refactor-cleaner`.
2. State the behavior/invariant that must not change.
3. Add characterization tests when protection is weak.
4. Make the smallest structural change.
5. Remove obsolete compatibility code only with usage evidence.
6. Review the resulting diff for scope creep.

## Failure handling
Stop if behavior cannot be protected or usage cannot be established. Separate feature changes into their own workflow.

## Verification
Run characterization/regression tests, relevant build/type/lint gates, and code review.

## Output contract
Describe smell, invariant, files changed, removed/extracted elements, verification evidence, and readiness.
