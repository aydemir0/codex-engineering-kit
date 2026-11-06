"""Functional Code Mode V1 prerequisite probe, with no model or profile access.

Protocol: OpenAI Codex rust-v0.155.1 code-mode-protocol/src/host.
This probes the real host and one bounded diagnostic tool, not Codex shell tools
or product task success. Release digests are pinned, never supplied by the host.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import stat
import struct
import subprocess
import tempfile
import threading
import time
from typing import BinaryIO

RUNTIME_VERSION = "0.155.1"

HOSTS = {
    "eba0f32c976667cb9298efafd98513e823eeda7b576a03ec658bb8be8d336316":
        "480da4a9a98b5b54d6656d731fbcc00c73fd4d0fc4b9aaceafc9fbdf08a7d523",
    "e4c11374bd9de8ad5c3b7617fd4654bb7839901edb0863f9930666863c7a021b":
        "1d0569ec6390b4f446ecc7cd66ec7e5103648d55e065d45dbca19120d0bbd056",
}
# Files from the SHA-256-verified official complete Windows x64 release archive.
# This narrower managed-install layout does not change standalone host support.
PACKAGE_FILES = {
    "codex-package.json": "64a1994514c461a7fbf5a73367a31c21d7f328ac07ec64a920994700eae5b3b9",
    "bin/codex.exe": "eba0f32c976667cb9298efafd98513e823eeda7b576a03ec658bb8be8d336316",
    "bin/codex-code-mode-host.exe": "480da4a9a98b5b54d6656d731fbcc00c73fd4d0fc4b9aaceafc9fbdf08a7d523",
    "codex-path/rg.exe": "14231169855ec5205cf5a1b6f1db358ff4aed4247c86b69ce8aae647c77f6680",
    "codex-resources/codex-command-runner.exe": "0431ee03aaf7e3c2ecda92017ef2fb9750d66221917467132c2136f078924b6c",
    "codex-resources/codex-windows-sandbox-setup.exe": "a430e15894ef450ee9003459597f95b3e3db5ac1e260f662bbc5d7db4e855047",
}
MAX_FRAME = 65536
CANARY = b"CEK_CODE_MODE_CAPABILITY_OK\n"


from runtime.diagnostics.native_failure import NativeExecutionError


class NativeHostError(NativeExecutionError):
    pass


def _regular(path: Path) -> None:
    for part in (*reversed(path.absolute().parents), path.absolute()):
        try:
            info = part.lstat()
        except FileNotFoundError as error:
            raise NativeHostError("CODE_MODE_HOST_MISSING") from error
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise NativeHostError("CODE_MODE_HOST_UNSAFE_PATH")
    if not path.is_file() or path.stat().st_nlink != 1:
        raise NativeHostError("CODE_MODE_HOST_UNSAFE_FILE")


def _exact(stream: BinaryIO, length: int) -> bytes:
    result = bytearray()
    while len(result) < length:
        chunk = stream.read(length - len(result))
        if not chunk:
            raise NativeHostError("CODE_MODE_HOST_TRUNCATED_FRAME")
        result.extend(chunk)
    return bytes(result)


def read_frame(stream: BinaryIO) -> dict:
    size = struct.unpack("<I", _exact(stream, 4))[0]
    if not 0 < size <= MAX_FRAME:
        raise NativeHostError("CODE_MODE_HOST_FRAME_LIMIT")
    try:
        result = json.loads(_exact(stream, size))
    except (UnicodeError, ValueError) as error:
        raise NativeHostError("CODE_MODE_HOST_INVALID_JSON") from error
    if not isinstance(result, dict):
        raise NativeHostError("CODE_MODE_HOST_INVALID_FRAME")
    return result


def resolve_host(executable: Path) -> Path:
    """Support official Windows package layout and adjacent standalone layout."""
    executable = executable.absolute()
    if executable.parent.name == "bin" and (executable.parent.parent / "codex-package.json").is_file():
        resources = executable.parent.parent / "codex-resources/codex-code-mode-host.exe"
        if resources.is_file():
            return resources
    return executable.with_name("codex-code-mode-host.exe")


def require_complete_package(executable: Path) -> None:
    """Require the reviewed managed-install package, not a launcher or partial copy."""
    executable = executable.absolute()
    if executable.name.casefold() != "codex.exe" or executable.parent.name.casefold() != "bin":
        raise NativeHostError("CODE_MODE_RUNTIME_COMPLETE_PACKAGE_REQUIRED")
    root = executable.parent.parent
    for relative, expected in PACKAGE_FILES.items():
        path = root / relative
        _regular(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise NativeHostError("CODE_MODE_RUNTIME_PACKAGE_DIGEST")


def require_native_host(executable: Path, *, timeout_seconds: float = 10) -> dict:
    if not 0 < timeout_seconds <= 30:
        raise NativeHostError("CODE_MODE_HOST_INVALID_TIMEOUT")
    started = time.monotonic()
    executable = executable.absolute()
    host = resolve_host(executable)
    _regular(host)
    _regular(executable)
    runtime_digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    expected = HOSTS.get(runtime_digest)
    if expected is None:
        raise NativeHostError("CODE_MODE_RUNTIME_UNSUPPORTED")
    # Query only a digest-approved executable, with no personal configuration,
    # credential environment or account/profile access.
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if key in os.environ}
    try:
        with tempfile.TemporaryDirectory(prefix="cek-runtime-version-") as directory:
            env["CODEX_HOME"] = str(Path(directory) / "unused-profile")
            version = subprocess.run([str(executable), "--version"], cwd=directory, env=env,
                                     capture_output=True, check=False, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as error:
        raise NativeHostError("CODE_MODE_HOST_TIMEOUT") from error
    except OSError as error:
        raise NativeHostError("CODE_MODE_RUNTIME_VERSION_FAILED") from error
    if version.returncode != 0 or version.stdout.strip() != f"codex-cli {RUNTIME_VERSION}".encode():
        raise NativeHostError("CODE_MODE_RUNTIME_VERSION_MISMATCH")
    remaining = timeout_seconds - (time.monotonic() - started)
    if remaining <= 0:
        raise NativeHostError("CODE_MODE_HOST_TIMEOUT")
    result = probe_host(host, expected_sha256=expected, timeout_seconds=remaining)
    return {**result, "runtimeVersion": RUNTIME_VERSION, "runtimeSHA256": runtime_digest}


def probe_host(host: Path, *, expected_sha256: str, timeout_seconds: float = 10) -> dict:
    if not 0 < timeout_seconds <= 30:
        raise NativeHostError("CODE_MODE_HOST_INVALID_TIMEOUT")
    deadline = time.monotonic() + timeout_seconds
    host = host.absolute()
    _regular(host)
    host_digest = hashlib.sha256(host.read_bytes()).hexdigest()
    if host_digest != expected_sha256:
        raise NativeHostError("CODE_MODE_HOST_DIGEST")
    transcript: list[dict] = []
    messages: queue.Queue = queue.Queue(maxsize=64)
    with tempfile.TemporaryDirectory(prefix="cek-native-host-probe-") as tmp:
        root = Path(tmp)
        # No inherited CODEX_HOME, tokens, proxy settings or OTEL configuration.
        env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if key in os.environ}
        env["CODEX_HOME"] = str(root / "unused-profile")
        try:
            process = subprocess.Popen([str(host), "--listen", "stdio"], cwd=root, env=env,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        except OSError as error:
            raise NativeHostError("CODE_MODE_HOST_START_FAILED") from error
        assert process.stdout is not None and process.stdin is not None

        def read_messages() -> None:
            try:
                for _ in range(64):
                    messages.put_nowait(read_frame(process.stdout))
            except (NativeHostError, OSError, queue.Full) as error:
                try:
                    messages.put_nowait(error)
                except queue.Full:
                    pass

        reader = threading.Thread(target=read_messages, daemon=True)
        reader.start()

        def send(value: dict) -> None:
            raw = json.dumps(value, separators=(",", ":")).encode()
            transcript.append({"sent": value})
            process.stdin.write(struct.pack("<I", len(raw)) + raw)
            process.stdin.flush()

        def receive() -> dict:
            try:
                value = messages.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty as error:
                raise NativeHostError("CODE_MODE_HOST_TIMEOUT") from error
            if isinstance(value, NativeHostError):
                raise value
            if isinstance(value, Exception):
                raise NativeHostError("CODE_MODE_HOST_PROTOCOL_FAILED") from value
            transcript.append({"received": value})
            if time.monotonic() > deadline:
                raise NativeHostError("CODE_MODE_HOST_TIMEOUT")
            return value

        def request(ident: int, value: dict) -> None:
            send({"type": "operation/request", "id": ident, "request": value})

        def success(value: dict) -> dict:
            result = value.get("result", {})
            if not isinstance(result, dict):
                raise NativeHostError("CODE_MODE_HOST_INVALID_FRAME")
            if result.get("status") != "ok" or not isinstance(result.get("value"), dict):
                raise NativeHostError("CODE_MODE_HOST_OPERATION_FAILED")
            return result["value"]

        def response(ident: int) -> dict:
            for _ in range(16):
                value = receive()
                if value.get("type") == "cell/closed":
                    continue
                if value.get("type") == "operation/response" and value.get("id") == ident:
                    return success(value)
                raise NativeHostError("CODE_MODE_HOST_UNEXPECTED_FRAME")
            raise NativeHostError("CODE_MODE_HOST_FRAME_LIMIT")

        calls = 0

        def execute(ident: int, source: str, tools: list[dict]) -> str:
            nonlocal calls
            request(ident, {"method": "session/execute", "sessionId": "cek-probe",
                "request": {"tool_call_id": "probe-" + str(ident), "enabled_tools": tools,
                    "source": source, "yield_time_ms": 10000, "max_output_tokens": 100}})
            started = None
            initial = None
            for _ in range(24):
                message = receive()
                kind = message.get("type")
                if kind == "cell/closed":
                    continue
                if kind == "operation/response" and message.get("id") == ident:
                    started = success(message)
                elif kind == "execute/initialResponse" and message.get("id") == ident:
                    initial = success(message)
                elif kind == "delegate/request" and tools:
                    invocation = message.get("request", {}).get("invocation", {})
                    if (message.get("sessionId") != "cek-probe" or calls != 0
                            or message["request"].get("type") != "tool/invoke"
                            or invocation.get("tool_name") != {"name": "cek_probe", "namespace": None}
                            or invocation.get("tool_kind") != "function" or invocation.get("input") != {"value": 42}):
                        raise NativeHostError("CODE_MODE_HOST_FOREIGN_DELEGATE")
                    with (root / "canary.txt").open("xb") as handle:
                        handle.write(CANARY)
                    calls += 1
                    send({"type": "delegate/response", "id": message["id"],
                          "result": {"status": "ok", "value": {"type": "tool/result", "result": "CEK_HOST_TOOL_OK"}}})
                else:
                    raise NativeHostError("CODE_MODE_HOST_UNEXPECTED_FRAME")
                if started is not None and initial is not None:
                    result = initial.get("Result", {})
                    if (started.get("type") != "execution/started" or not result
                            or result.get("cell_id") != started.get("cellId") or result.get("error_text") is not None):
                        raise NativeHostError("CODE_MODE_HOST_EXECUTION_FAILED")
                    return "".join(i.get("text", "") for i in result.get("content_items", []) if i.get("type") == "input_text")
            raise NativeHostError("CODE_MODE_HOST_FRAME_LIMIT")

        try:
            send({"type": "connection/hello", "supportedVersions": [1],
                  "requiredCapabilities": [], "optionalCapabilities": []})
            if receive() != {"type": "connection/ready", "selectedVersion": 1, "capabilities": []}:
                raise NativeHostError("CODE_MODE_HOST_HANDSHAKE_FAILED")
            request(1, {"method": "session/open", "sessionId": "cek-probe"})
            if response(1) != {"type": "session/ready", "sessionId": "cek-probe"}:
                raise NativeHostError("CODE_MODE_HOST_SESSION_FAILED")
            if execute(2, "text(6 * 7);", []) != "42":
                raise NativeHostError("CODE_MODE_HOST_EVALUATION_FAILED")
            tool = {"name": "cek_probe", "tool_name": {"name": "cek_probe", "namespace": None},
                    "description": "Write one fixed diagnostic canary", "kind": "function",
                    "input_schema": {"type": "object"}, "output_schema": None}
            if execute(3, "text(await tools.cek_probe({value: 42}));", [tool]) != "CEK_HOST_TOOL_OK":
                raise NativeHostError("CODE_MODE_HOST_TOOL_FAILED")
            if calls != 1 or (root / "canary.txt").read_bytes() != CANARY:
                raise NativeHostError("CODE_MODE_HOST_ARTIFACT_FAILED")
            request(4, {"method": "session/shutdown", "sessionId": "cek-probe"})
            if response(4) != {"type": "session/closed", "sessionId": "cek-probe"}:
                raise NativeHostError("CODE_MODE_HOST_SHUTDOWN_FAILED")
            process.stdin.close()
            if process.wait(timeout=max(0.001, deadline - time.monotonic())) != 0:
                raise NativeHostError("CODE_MODE_HOST_EXIT_FAILED")
        except subprocess.TimeoutExpired as error:
            raise NativeHostError("CODE_MODE_HOST_TIMEOUT") from error
        except (AttributeError, TypeError, ValueError, KeyError) as error:
            raise NativeHostError("CODE_MODE_HOST_INVALID_FRAME") from error
        except OSError as error:
            raise NativeHostError("CODE_MODE_HOST_IO_FAILED") from error
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            reader.join(timeout=1)
            process.stdout.close()
            if not process.stdin.closed:
                process.stdin.close()
    _regular(host)
    if hashlib.sha256(host.read_bytes()).hexdigest() != host_digest:
        raise NativeHostError("CODE_MODE_HOST_CHANGED")
    return {"hostSHA256": host_digest, "protocolVersion": 1, "evaluation": "PASS",
            "toolInvocation": "PASS", "artifactVerification": "PASS", "toolCalls": calls,
            "artifactSHA256": hashlib.sha256(CANARY).hexdigest(), "modelInvoked": False,
            "scope": "NATIVE_HOST_AND_BOUNDED_DIAGNOSTIC_DELEGATE_NOT_CODEX_SHELL_OR_PRODUCT_E2E",
            "protocolTranscript": transcript,
            "transcriptSHA256": hashlib.sha256(json.dumps(transcript, sort_keys=True).encode()).hexdigest()}
