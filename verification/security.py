from __future__ import annotations

import re
import time
from pathlib import Path

from verification.model import VerificationStep

EXCLUDED_DIRS = {".git", ".codex-kit", "node_modules", "dist", "build", "coverage"}
MAX_FILE_BYTES = 1_048_576
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def _iter_files(project_path: Path):
    for path in project_path.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(project_path)
        if any(part in EXCLUDED_DIRS for part in relative.parts[:-1]):
            continue
        yield path, relative


def scan_secret_patterns(project_path: Path) -> VerificationStep:
    project_path = Path(project_path)
    started = time.monotonic_ns()
    matches: list[str] = []

    for path, relative in _iter_files(project_path):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            matches.append(relative.as_posix())

    duration_ms = max(0, (time.monotonic_ns() - started) // 1_000_000)
    if matches:
        bounded = ", ".join(sorted(set(matches))[:20])
        return VerificationStep(
            name="security",
            command=None,
            status="failed",
            exit_code=1,
            duration_ms=duration_ms,
            evidence=f"Secret-like material detected in: {bounded}",
        )

    return VerificationStep(
        name="security",
        command=None,
        status="passed",
        exit_code=0,
        duration_ms=duration_ms,
        evidence="No configured secret-like patterns detected.",
    )
