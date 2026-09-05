from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

MAX_CAPTURE_BYTES = 8192


@dataclass(frozen=True)
class ProcessResult:
    command: tuple[str, ...]
    exit_code: int | None
    duration_ms: int
    status: str
    stdout_tail: str
    stderr_tail: str
    reason: str = ""


def _bounded_tail(text: str, max_bytes: int = MAX_CAPTURE_BYTES) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return text
    return encoded[-max_bytes:].decode("utf-8", errors="replace")


def _coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _resolve_executable(command: str) -> str | None:
    candidate = Path(command)
    if candidate.is_file():
        return str(candidate.resolve())
    return shutil.which(command)


def run_command(
    args: Sequence[str],
    cwd: Path,
    timeout_seconds: float = 120,
) -> ProcessResult:
    if not args:
        raise ValueError("command must contain at least one argument")

    command = tuple(str(part) for part in args)
    resolved = _resolve_executable(command[0])
    if resolved is None:
        return ProcessResult(
            command=command,
            exit_code=None,
            duration_ms=0,
            status="unavailable",
            stdout_tail="",
            stderr_tail="",
            reason=f"Executable not found: {command[0]}",
        )

    invocation = [resolved, *command[1:]]
    if os.name == "nt" and Path(resolved).suffix.casefold() in {".cmd", ".bat"}:
        comspec = os.environ.get("COMSPEC") or shutil.which("cmd.exe") or "cmd.exe"
        invocation = [
            comspec,
            "/d",
            "/s",
            "/c",
            subprocess.list2cmdline(invocation),
        ]

    started = time.monotonic_ns()
    try:
        completed = subprocess.run(
            invocation,
            cwd=str(cwd),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = max(0, (time.monotonic_ns() - started) // 1_000_000)
        return ProcessResult(
            command=command,
            exit_code=None,
            duration_ms=duration_ms,
            status="failed",
            stdout_tail=_bounded_tail(_coerce_text(exc.stdout)),
            stderr_tail=_bounded_tail(_coerce_text(exc.stderr)),
            reason=f"Command timeout after {timeout_seconds} seconds",
        )
    except FileNotFoundError:
        duration_ms = max(0, (time.monotonic_ns() - started) // 1_000_000)
        return ProcessResult(
            command=command,
            exit_code=None,
            duration_ms=duration_ms,
            status="unavailable",
            stdout_tail="",
            stderr_tail="",
            reason=f"Executable not found: {command[0]}",
        )
    except OSError as exc:
        duration_ms = max(0, (time.monotonic_ns() - started) // 1_000_000)
        return ProcessResult(
            command=command,
            exit_code=None,
            duration_ms=duration_ms,
            status="failed",
            stdout_tail="",
            stderr_tail="",
            reason=f"Command execution failed: {exc}",
        )

    duration_ms = max(0, (time.monotonic_ns() - started) // 1_000_000)
    return ProcessResult(
        command=command,
        exit_code=completed.returncode,
        duration_ms=duration_ms,
        status="passed" if completed.returncode == 0 else "failed",
        stdout_tail=_bounded_tail(completed.stdout or ""),
        stderr_tail=_bounded_tail(completed.stderr or ""),
    )
