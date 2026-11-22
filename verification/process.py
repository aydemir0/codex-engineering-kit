from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

MAX_CAPTURE_BYTES = 8192
BATCH_UNSAFE_ARGUMENT = re.compile(r'[&|<>^%!()\r\n"]')
# cmd.exe parses executable paths as shell syntax as well as argument values.
# Refuse unsafe batch paths instead of trying to double-escape nested cmd /c input.
BATCH_UNSAFE_PATH = re.compile(r'[&|<>^%!()\r\n"]')


def _system_cmd_executable() -> str | None:
    """Return the Windows system-directory cmd.exe, not an inherited COMSPEC/PATH."""
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_system_directory = kernel32.GetSystemDirectoryW
    get_system_directory.argtypes = [wintypes.LPWSTR, wintypes.UINT]
    get_system_directory.restype = wintypes.UINT
    buffer = ctypes.create_unicode_buffer(32768)
    length = get_system_directory(buffer, len(buffer))
    if not (0 < length < len(buffer)):
        return None
    candidate = Path(buffer.value) / "cmd.exe"
    return str(candidate) if candidate.is_file() else None


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

    invocation: list[str] | str = [resolved, *command[1:]]
    executable: str | None = None
    if os.name == "nt" and Path(resolved).suffix.casefold() in {".cmd", ".bat"}:
        if BATCH_UNSAFE_PATH.search(resolved):
            return ProcessResult(
                command=command,
                exit_code=None,
                duration_ms=0,
                status="failed",
                stdout_tail="",
                stderr_tail="",
                reason="Unsafe executable path rejected for Windows batch command",
            )
        unsafe = next((part for part in command[1:] if BATCH_UNSAFE_ARGUMENT.search(part)), None)
        if unsafe is not None:
            return ProcessResult(
                command=command,
                exit_code=None,
                duration_ms=0,
                status="failed",
                stdout_tail="",
                stderr_tail="",
                reason="Unsafe argument rejected for Windows batch command",
            )
        comspec = _system_cmd_executable()
        if comspec is None:
            return ProcessResult(
                command=command,
                exit_code=None,
                duration_ms=0,
                status="unavailable",
                stdout_tail="",
                stderr_tail="",
                reason="Trusted Windows system cmd.exe unavailable",
            )
        batch_command = subprocess.list2cmdline(invocation)
        command_prefix = subprocess.list2cmdline([comspec, "/d", "/s", "/c"])
        invocation = f'{command_prefix} "{batch_command}"'
        executable = comspec

    started = time.monotonic_ns()
    try:
        completed = subprocess.run(
            invocation,
            executable=executable,
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
