from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any, Callable, Sequence

from .model import CleanupDisposition
from runtime.assurance.native_host import NativeHostError, require_native_host


from runtime.diagnostics.native_failure import NativeExecutionError, validate_result


class NativeWorkflowError(NativeExecutionError):
    pass


def build_exec_command(executable: Path, prompt: str) -> list[str]:
    if not prompt.strip():
        raise NativeWorkflowError("native workflow prompt is empty")
    return [
        str(executable.resolve(strict=True)),
        "exec",
        "--enable",
        "worktrees",
        "--worktree",
        "--approve-for-me",
        "--json",
        prompt,
    ]


def run_native(
    executable: Path,
    prompt: str,
    project: Path,
    env: dict[str, str],
    *,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    if timeout_seconds <= 0:
        raise NativeWorkflowError("native workflow timeout must be positive")
    start = time.monotonic()
    try:
        require_native_host(executable, timeout_seconds=min(timeout_seconds, 10))
    except NativeHostError as error:
        raise NativeWorkflowError(str(error)) from error
    remaining = timeout_seconds - (time.monotonic() - start)
    if remaining <= 0:
        raise NativeWorkflowError("CODE_MODE_HOST_TIMEOUT")
    try:
        result = subprocess.run(
            build_exec_command(executable, prompt), cwd=project, env=env,
            capture_output=True, shell=False, check=False, timeout=remaining,
        )
        # Decode on the calling thread: Windows subprocess reader threads can
        # otherwise swallow UnicodeDecodeError and return stdout=None.
        result = subprocess.CompletedProcess(
            result.args, result.returncode, result.stdout.decode("utf-8"), result.stderr.decode("utf-8"),
        )
        validate_result(result)
        return result
    except subprocess.TimeoutExpired as error:
        raise NativeWorkflowError("NATIVE_TIMEOUT") from error
    except UnicodeError as error:
        raise NativeWorkflowError("NATIVE_MALFORMED_RESPONSE") from error
    except PermissionError as error:
        raise NativeWorkflowError("NATIVE_PERMISSION_DENIED") from error
    except OSError as error:
        raise NativeWorkflowError("NATIVE_TOOL_INVOCATION_FAILED") from error
    except NativeExecutionError as error:
        raise NativeWorkflowError(error.diagnostic.reason_code, error.diagnostic.code.value) from error



def cleanup_worktree(ownership: dict[str, Any], remover: Callable[[], bool]) -> CleanupDisposition:
    if not ownership.get("pathMatches"):
        return CleanupDisposition.RETAINED_BY_POLICY
    record_owner = ownership.get("recordOwner")
    live_owner = ownership.get("liveOwner")
    if not record_owner or not live_owner or record_owner != live_owner:
        return CleanupDisposition.RETAINED_BY_POLICY
    return CleanupDisposition.REMOVED if remover() else CleanupDisposition.RETAINED_BY_POLICY
