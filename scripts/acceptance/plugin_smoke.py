from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

PLUGIN_MANIFEST = Path(".codex-plugin/plugin.json")
MARKETPLACE_MANIFEST = Path(".agents/plugins/marketplace.json")
SCHEMA_VERSION = 1


def build_environment(base_env: Mapping[str, str], codex_home: Path) -> dict[str, str]:
    env = dict(base_env)
    env["CODEX_HOME"] = str(codex_home)
    return env


def find_plugin(payload: Mapping[str, Any], name: str) -> tuple[str, dict[str, Any]]:
    for location in ("installed", "available"):
        entries = payload.get(location, [])
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("name") == name:
                return location, entry
    raise LookupError(f"plugin {name!r} was not present in installed or available results")


def _looks_like_local_path(value: str) -> bool:
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    if value.startswith("\\\\") or value.startswith("//?/"):
        return True
    return value.startswith(("/home/", "/Users/", "/tmp/", "/var/", "/private/"))


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if key in {"installedPath", "root", "path"}:
                continue
            sanitized[key] = _sanitize_value(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str) and _looks_like_local_path(value):
        return "<redacted-local-path>"
    return value


def sanitize_record(record: Mapping[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in record.items():
        if key in {"stdout", "stderr"}:
            continue
        sanitized[key] = _sanitize_value(value)
    return sanitized


def _resolve_executable(args: Sequence[str], env: Mapping[str, str]) -> list[str]:
    if not args:
        raise ValueError("command must contain an executable")
    command = list(args)
    executable = command[0]
    if Path(executable).is_absolute() or Path(executable).parent != Path("."):
        return command
    resolved = shutil.which(executable, path=env.get("PATH"))
    if resolved:
        command[0] = resolved
    return command


def run_command(args: Sequence[str], env: Mapping[str, str]) -> dict[str, Any]:
    command = _resolve_executable(args, env)
    completed = subprocess.run(
        command,
        env=dict(env),
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    parsed: Any = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "args": list(args),
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "parsed": parsed,
    }


def require_success(record: Mapping[str, Any], label: str) -> None:
    if record.get("returncode") == 0:
        return
    stderr = str(record.get("stderr", "")).strip()
    detail = stderr.splitlines()[-1] if stderr else "no stderr returned"
    raise RuntimeError(f"{label} failed with exit code {record.get('returncode')}: {detail}")


def require_json(record: Mapping[str, Any], label: str) -> dict[str, Any]:
    require_success(record, label)
    payload = record.get("parsed")
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} did not return a JSON object")
    return payload


def load_identity(repo: Path) -> tuple[str, str]:
    plugin_path = repo / PLUGIN_MANIFEST
    marketplace_path = repo / MARKETPLACE_MANIFEST
    if not plugin_path.is_file():
        raise FileNotFoundError(f"missing {PLUGIN_MANIFEST}")
    if not marketplace_path.is_file():
        raise FileNotFoundError(f"missing {MARKETPLACE_MANIFEST}")

    plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin_name = plugin.get("name")
    marketplace_name = marketplace.get("name")
    if not isinstance(plugin_name, str) or not plugin_name:
        raise ValueError("plugin manifest has no valid name")
    if not isinstance(marketplace_name, str) or not marketplace_name:
        raise ValueError("marketplace manifest has no valid name")
    return plugin_name, marketplace_name


def _marketplace_present(payload: Mapping[str, Any], marketplace_name: str) -> bool:
    entries = payload.get("marketplaces", [])
    if not isinstance(entries, list):
        return False
    return any(isinstance(entry, dict) and entry.get("name") == marketplace_name for entry in entries)


def _record_for_artifact(record: Mapping[str, Any], repo: Path) -> dict[str, Any]:
    copy = dict(record)
    args = []
    repo_text = str(repo)
    for item in copy.get("args", []):
        args.append("<repo-root>" if item == repo_text else item)
    copy["args"] = args
    return sanitize_record(copy)


def execute_smoke(codex: str, repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    plugin_name, marketplace_name = load_identity(repo)
    records: list[dict[str, Any]] = []
    checks: dict[str, bool] = {}
    temp_home_text = ""

    with tempfile.TemporaryDirectory(prefix="cek-codex-home-") as temp_home:
        temp_home_path = Path(temp_home)
        temp_home_text = str(temp_home_path)
        env = build_environment(os.environ, temp_home_path)

        version_record = run_command([codex, "--version"], env)
        require_success(version_record, "codex --version")
        runtime_version = version_record["stdout"]
        records.append(_record_for_artifact(version_record, repo))

        marketplace_add = run_command(
            [codex, "plugin", "marketplace", "add", str(repo), "--json"], env
        )
        require_success(marketplace_add, "marketplace add")
        records.append(_record_for_artifact(marketplace_add, repo))

        marketplace_list = run_command(
            [codex, "plugin", "marketplace", "list", "--json"], env
        )
        marketplace_payload = require_json(marketplace_list, "marketplace list")
        checks["marketplace_registered"] = _marketplace_present(
            marketplace_payload, marketplace_name
        )
        if not checks["marketplace_registered"]:
            raise RuntimeError(
                f"marketplace {marketplace_name!r} was not present after registration"
            )
        records.append(_record_for_artifact(marketplace_list, repo))

        available_record = run_command(
            [codex, "plugin", "list", "--available", "--json"], env
        )
        if available_record["returncode"] != 0:
            fallback_record = run_command([codex, "plugin", "list", "--json"], env)
            require_success(fallback_record, "plugin list fallback")
            records.append(_record_for_artifact(available_record, repo))
            records.append(_record_for_artifact(fallback_record, repo))
            preinstall_payload = require_json(fallback_record, "plugin list fallback")
            discovery_mode = "list-json-fallback"
        else:
            records.append(_record_for_artifact(available_record, repo))
            preinstall_payload = require_json(available_record, "plugin list --available")
            discovery_mode = "list-available-json"

        try:
            preinstall_location, _ = find_plugin(preinstall_payload, plugin_name)
            checks["plugin_preinstall_discovered"] = True
        except LookupError:
            preinstall_location = "not-listed"
            checks["plugin_preinstall_discovered"] = False

        add_record = run_command(
            [
                codex,
                "plugin",
                "add",
                f"{plugin_name}@{marketplace_name}",
                "--json",
            ],
            env,
        )
        add_payload = require_json(add_record, "plugin add")
        records.append(_record_for_artifact(add_record, repo))
        checks["plugin_add_returned_expected_name"] = add_payload.get("name") == plugin_name
        checks["plugin_add_returned_expected_marketplace"] = (
            add_payload.get("marketplaceName") == marketplace_name
        )
        if not all(
            (
                checks["plugin_add_returned_expected_name"],
                checks["plugin_add_returned_expected_marketplace"],
            )
        ):
            raise RuntimeError("plugin add returned unexpected plugin identity")

        final_record = run_command([codex, "plugin", "list", "--json"], env)
        final_payload = require_json(final_record, "final plugin list")
        final_location, final_plugin = find_plugin(final_payload, plugin_name)
        checks["plugin_final_installed"] = (
            final_location == "installed" and final_plugin.get("installed") is True
        )
        checks["plugin_final_enabled"] = final_plugin.get("enabled") is True
        records.append(_record_for_artifact(final_record, repo))
        if not checks["plugin_final_installed"]:
            raise RuntimeError("plugin was not proven installed in the disposable Codex home")

    checks["temporary_codex_home_removed"] = not Path(temp_home_text).exists()
    if not checks["temporary_codex_home_removed"]:
        raise RuntimeError("temporary CODEX_HOME still exists after acceptance run")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "result": "PASS",
        "runtimeVersion": runtime_version,
        "disposableCodexHome": True,
        "plugin": {
            "name": plugin_name,
            "marketplaceName": marketplace_name,
            "preinstallLocation": preinstall_location,
            "discoveryMode": discovery_mode,
        },
        "checks": checks,
        "commands": records,
    }


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test Codex Engineering Kit plugin packaging in a disposable CODEX_HOME."
    )
    parser.add_argument("--codex", default="codex", help="Codex CLI executable or path")
    parser.add_argument("--repo", required=True, help="Repository root containing the plugin")
    parser.add_argument("--output", required=True, help="JSON result path outside the repository")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = Path(args.repo)
    output = Path(args.output).expanduser().resolve()
    try:
        result = execute_smoke(args.codex, repo)
    except Exception as exc:  # acceptance runner must surface a concise operator failure
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: plugin acceptance evidence written to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
