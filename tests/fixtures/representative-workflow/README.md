# Representative Workflow Fixture

This fixture is intentionally checked in with one deterministic failing test.

The task is bounded to `src/calculator.py`. The initial implementation returns
positive infinity for division by zero, while the requested behavior is to
raise `ValueError("division by zero")`.

The fixture exists only for CEK representative workflow acceptance.
