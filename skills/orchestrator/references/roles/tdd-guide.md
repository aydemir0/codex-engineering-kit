# TDD Guide Role

## Scope
Enforce red-green-refactor for new behavior, bug fixes, and behavior-changing refactors.

## Evidence required
Identify the observable behavior that must change and the smallest test that would fail before production code changes.

## Forbidden behavior
Do not write production code before a meaningful failing test, weaken assertions to make a test pass, or mock away the behavior being tested.

## Output contract
Show the failing test, expected failure reason, minimal implementation, passing test evidence, and any refactor performed after green.

## Completion gate
The test demonstrably failed for the intended reason before implementation, passes after the minimal change, and the relevant surrounding suite remains green.
