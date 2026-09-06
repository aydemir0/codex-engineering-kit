from __future__ import annotations


def divide(a: float, b: float) -> float:
    if b == 0:
        return float("inf")
    return a / b
