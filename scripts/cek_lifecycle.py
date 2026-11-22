from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

# Preserve the documented direct-script entry point as well as module imports.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.assurance.native_host import NativeHostError, RUNTIME_VERSION, require_complete_package, require_native_host

SUPPORTED_RUNTIME = f"codex-cli {RUNTIME_VERSION}"
PLUGIN_NAME = "codex-engineering-kit"
PROJECT_ASSET = Path(".codex/agents/reviewer.toml")
GLOBAL_STATE_NAME = "codex-engineering-kit.install.json"
PROJECT_STATE = Path(".codex/codex-engineering-kit.install.json")
SCHEMA_VERSION = 1
PACKAGED_FIXED_ASSETS = (Path(".codex-plugin/plugin.json"), Path("hooks/hooks.json"))
DEFAULT_CODEX_TIMEOUT_SECONDS = 120.0
MAX_CODEX_TIMEOUT_SECONDS = 900.0

CommandResult = dict[str, object]
Runner = Callable[[list[str], dict[str, str]], CommandResult]


class LifecycleError(RuntimeError):
    pass


class LifecycleTimeoutError(LifecycleError):
    """A native command may have partially mutated state before timing out."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_link_or_reparse(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(is_junction and is_junction())


def _reject_link_chain(root: Path, relative: Path) -> None:
    current = root
    if _is_link_or_reparse(current):
        raise LifecycleError(f"unsafe reparse/symlink boundary: {current}")
    for part in relative.parts:
        current = current / part
        if _is_link_or_reparse(current):
            raise LifecycleError(f"unsafe reparse/symlink boundary: {current}")


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    os.close(descriptor)
    try:
        shutil.copyfile(source, temporary)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LifecycleError(f"invalid {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise LifecycleError(f"invalid {label}: {path}")
    return payload


def _identity(repo: Path) -> tuple[str, str, str]:
    plugin = _load_json(repo / ".codex-plugin/plugin.json", "plugin manifest")
    marketplace = _load_json(repo / ".agents/plugins/marketplace.json", "marketplace manifest")
    name = plugin.get("name")
    version = plugin.get("version")
    marketplace_name = marketplace.get("name")
    entries = marketplace.get("plugins")
    if name != PLUGIN_NAME or not isinstance(version, str) or not version.strip():
        raise LifecycleError("unsupported CEK plugin identity or version")
    if not isinstance(marketplace_name, str) or not marketplace_name.strip():
        raise LifecycleError("invalid CEK marketplace identity")
    if not isinstance(entries, list) or not any(
        isinstance(entry, dict)
        and entry.get("name") == name
        and entry.get("source") == {"source": "local", "path": "."}
        for entry in entries
    ):
        raise LifecycleError("marketplace does not point to the local CEK plugin root")
    reviewer = repo / PROJECT_ASSET
    if not reviewer.is_file() or _is_link_or_reparse(reviewer):
        raise LifecycleError("shipped project-local reviewer asset is missing or unsafe")
    return name, version, marketplace_name


def _packaged_assets(repo: Path) -> list[dict[str, str]]:
    paths = list(PACKAGED_FIXED_ASSETS)
    paths.extend(sorted((path.relative_to(repo) for path in (repo / "skills").glob("*/SKILL.md")), key=str))
    if len(paths) <= len(PACKAGED_FIXED_ASSETS):
        raise LifecycleError("CEK has no shipped plugin-native skills")
    assets: list[dict[str, str]] = []
    for relative in paths:
        _reject_link_chain(repo, relative)
        source = repo / relative
        if not source.is_file() or _is_link_or_reparse(source):
            raise LifecycleError(f"shipped plugin asset is missing or unsafe: {relative.as_posix()}")
        assets.append({"path": relative.as_posix(), "sha256": _sha256(source)})
    return assets


def _environment(codex_home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["CODEX_HOME"] = str(codex_home)
    return env


def _codex_phase(args: Sequence[str]) -> str:
    """Report a bounded, static phase label without leaking command arguments."""
    if tuple(args) == ("--version",):
        return "runtime version"
    if len(args) >= 3 and tuple(args[:2]) == ("plugin", "marketplace"):
        return f"marketplace {args[2]}" if args[2] in {"list", "add", "remove"} else "marketplace command"
    if len(args) >= 2 and args[0] == "plugin":
        return f"plugin {args[1]}" if args[1] in {"list", "add", "remove"} else "plugin command"
    return "Codex command"


def _validated_timeout(seconds: float) -> float:
    if not math.isfinite(seconds) or not 0 < seconds <= MAX_CODEX_TIMEOUT_SECONDS:
        raise LifecycleError(
            f"Codex CLI timeout must be greater than zero and at most {MAX_CODEX_TIMEOUT_SECONDS:g} seconds"
        )
    return seconds


def _windows_taskkill() -> str | None:
    """Resolve taskkill using Windows' system directory, never caller-controlled PATH."""
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
    tool = Path(buffer.value) / "taskkill.exe"
    return str(tool) if tool.is_file() else None


def _stop_codex_tree(process: subprocess.Popen[str]) -> None:
    """Best-effort bounded cleanup; never leave the parent waiting indefinitely."""
    if process.poll() is None:
        if os.name == "nt":
            tool = _windows_taskkill()
            if tool is not None:
                try:
                    subprocess.run(
                        [tool, "/T", "/F", "/PID", str(process.pid)],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    pass
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                pass
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
    try:
        process.communicate(timeout=3)
    except (subprocess.TimeoutExpired, OSError):
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()
        try:
            process.wait(timeout=2)
        except (subprocess.TimeoutExpired, OSError):
            pass


def run_codex(
    executable: str,
    args: Sequence[str],
    env: Mapping[str, str],
    timeout_seconds: float = DEFAULT_CODEX_TIMEOUT_SECONDS,
) -> CommandResult:
    """Execute one bounded native Codex CLI operation and record its exact phase."""
    timeout = _validated_timeout(float(timeout_seconds))
    resolved = shutil.which(executable, path=env.get("PATH"))
    command = [resolved or executable, *args]
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            command,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
        )
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if process is not None:
            _stop_codex_tree(process)
        phase = _codex_phase(list(args))
        raise LifecycleTimeoutError(
            f"CODEX_CLI_TIMEOUT: phase={phase}; limit={timeout:g}s. "
            "Codex command did not finish; lifecycle success was not claimed. "
            "Existing managed-state manifests were not deleted by timeout handling. "
            "The CLI may have partially changed plugin state; inspect the isolated CODEX_HOME "
            "and retry verify once the CLI is responsive. Do not reinstall or clean up blindly."
        ) from None
    except OSError as exc:
        if process is not None:
            _stop_codex_tree(process)
        raise LifecycleError("Codex executable could not be started or read") from exc
    return {
        "returncode": process.returncode,
        "stdout": stdout.strip(),
        "stderr": stderr.strip(),
    }


def _checked(run: Runner, args: list[str], env: dict[str, str], label: str) -> dict[str, Any]:
    result = run(args, env)
    if result.get("returncode") != 0:
        stderr = str(result.get("stderr", "")).strip()
        detail = stderr.splitlines()[-1] if stderr else "no diagnostic returned"
        raise LifecycleError(f"{label} failed: {detail}")
    stdout = str(result.get("stdout", "")).strip()
    if not stdout:
        return {}
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise LifecycleError(f"{label} did not return JSON") from exc
    if not isinstance(payload, dict):
        raise LifecycleError(f"{label} did not return a JSON object")
    return payload


def _runtime(run: Runner, env: dict[str, str]) -> None:
    result = run(["--version"], env)
    actual = str(result.get("stdout", "")).strip()
    if result.get("returncode") != 0 or actual != SUPPORTED_RUNTIME:
        raise LifecycleError(f"managed onboarding requires Codex CLI {RUNTIME_VERSION}; found {actual or 'unavailable'}")


def _marketplaces(run: Runner, env: dict[str, str]) -> dict[str, Path]:
    payload = _checked(run, ["plugin", "marketplace", "list", "--json"], env, "marketplace list")
    entries = payload.get("marketplaces", [])
    if not isinstance(entries, list):
        raise LifecycleError("marketplace list returned an invalid payload")
    roots: dict[str, Path] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise LifecycleError("marketplace list returned an invalid entry")
        if entry["name"] != "codex-engineering-kit-dev":
            continue
        if not isinstance(entry.get("root"), str):
            raise LifecycleError("CEK marketplace list entry omitted its local root")
        roots[entry["name"]] = Path(entry["root"]).resolve(strict=False)
    return roots


def _installed_plugin(run: Runner, env: dict[str, str], name: str) -> dict[str, Any] | None:
    payload = _checked(run, ["plugin", "list", "--json"], env, "plugin list")
    entries = payload.get("installed", [])
    if not isinstance(entries, list):
        raise LifecycleError("plugin list returned an invalid payload")
    return next(
        (entry for entry in entries if isinstance(entry, dict) and entry.get("name") == name),
        None,
    )


def _global_state(path: Path) -> dict[str, Any]:
    state = _load_json(path, "managed plugin state")
    packaged_assets = state.get("packagedAssets")
    if (
        state.get("schemaVersion") != SCHEMA_VERSION
        or state.get("kind") != "cek-managed-plugin-install"
        or state.get("pluginName") != PLUGIN_NAME
        or not isinstance(state.get("marketplaceName"), str)
        or not isinstance(state.get("pluginVersion"), str)
        or not isinstance(state.get("marketplaceOwned"), bool)
        or not isinstance(state.get("repoRoot"), str)
        or not isinstance(state.get("installedPath"), str)
        or not isinstance(packaged_assets, list)
        or not packaged_assets
        or any(
            not isinstance(asset, dict)
            or not isinstance(asset.get("path"), str)
            or re.fullmatch(r"[0-9a-f]{64}", str(asset.get("sha256", ""))) is None
            for asset in packaged_assets
        )
    ):
        raise LifecycleError("invalid managed plugin state identity")
    return state


def _project_state(path: Path) -> dict[str, Any]:
    state = _load_json(path, "managed project state")
    assets = state.get("assets")
    if (
        state.get("schemaVersion") != SCHEMA_VERSION
        or state.get("kind") != "cek-managed-project-install"
        or not isinstance(state.get("pluginVersion"), str)
        or not isinstance(assets, list)
        or len(assets) != 1
        or assets[0].get("path") != PROJECT_ASSET.as_posix()
        or not isinstance(assets[0].get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", assets[0]["sha256"]) is None
    ):
        raise LifecycleError("invalid managed project state identity")
    return state


def _preflight(repo: Path, project: Path, codex_home: Path) -> tuple[Path, Path, Path]:
    repo = repo.resolve(strict=True)
    project = project.resolve(strict=True)
    codex_home = codex_home.resolve(strict=False)
    if not repo.is_dir() or not project.is_dir():
        raise LifecycleError("repository and project paths must be existing directories")
    # Local plugin installation snapshots its source; overlapping state can copy itself.
    if repo == codex_home or repo in codex_home.parents or codex_home in repo.parents:
        raise LifecycleError("CEK_SOURCE_PROFILE_OVERLAP: use separate source and CODEX_HOME directories; preserve existing state")
    _reject_link_chain(project, PROJECT_ASSET)
    _reject_link_chain(project, PROJECT_STATE)
    if codex_home.exists():
        _reject_link_chain(codex_home, Path(GLOBAL_STATE_NAME))
    return repo, project, codex_home


def _state_payloads(
    repo: Path,
    version: str,
    marketplace: str,
    marketplace_owned: bool,
    installed_path: Path,
    packaged_assets: list[dict[str, str]],
    reviewer_hash: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    global_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "cek-managed-plugin-install",
        "pluginName": PLUGIN_NAME,
        "pluginVersion": version,
        "marketplaceName": marketplace,
        "marketplaceOwned": marketplace_owned,
        "repoRoot": str(repo),
        "installedPath": str(installed_path),
        "packagedAssets": packaged_assets,
    }
    project_payload = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "cek-managed-project-install",
        "pluginVersion": version,
        "assets": [{"path": PROJECT_ASSET.as_posix(), "sha256": reviewer_hash}],
    }
    return global_payload, project_payload


def install(repo: Path, project: Path, codex_home: Path, run: Runner) -> dict[str, Any]:
    repo, project, codex_home = _preflight(repo, project, codex_home)
    env = _environment(codex_home)
    _runtime(run, env)
    name, version, marketplace = _identity(repo)
    global_path = codex_home / GLOBAL_STATE_NAME
    project_path = project / PROJECT_STATE
    target = project / PROJECT_ASSET
    if global_path.exists() or project_path.exists():
        raise LifecycleError("CEK is already managed here; use update or verify")
    if target.exists():
        raise LifecycleError(f"unowned project-local reviewer exists: {target}; preserve or move it first")

    present_marketplaces = _marketplaces(run, env)
    if marketplace in present_marketplaces and present_marketplaces[marketplace] != repo:
        raise LifecycleError(
            f"marketplace {marketplace!r} is registered to a different local root"
        )
    if _installed_plugin(run, env, name) is not None:
        raise LifecycleError("CEK plugin is already installed outside this managed lifecycle")

    marketplace_owned = marketplace not in present_marketplaces
    plugin_added = False
    marketplace_added = False
    try:
        if marketplace_owned:
            payload = _checked(
                run,
                ["plugin", "marketplace", "add", str(repo), "--json"],
                env,
                "marketplace add",
            )
            if payload.get("marketplaceName") != marketplace:
                raise LifecycleError("marketplace add returned an unexpected identity")
            marketplace_added = True
        payload = _checked(
            run,
            ["plugin", "add", f"{name}@{marketplace}", "--json"],
            env,
            "plugin add",
        )
        if payload.get("name") != name or payload.get("marketplaceName") != marketplace:
            raise LifecycleError("plugin add returned an unexpected identity")
        if payload.get("version") != version:
            raise LifecycleError("plugin add returned a version that differs from the source manifest")
        installed_value = payload.get("installedPath")
        if not isinstance(installed_value, str):
            raise LifecycleError("plugin add did not return its installed cache path")
        installed_path = Path(installed_value).resolve(strict=True)
        cache_root = (codex_home / "plugins" / "cache").resolve(strict=False)
        if installed_path != cache_root and cache_root not in installed_path.parents:
            raise LifecycleError("plugin add returned an installed path outside the disposable Codex cache")
        plugin_added = True

        reviewer = repo / PROJECT_ASSET
        reviewer_hash = _sha256(reviewer)
        packaged_assets = _packaged_assets(repo)
        for asset in packaged_assets:
            _reject_link_chain(installed_path, Path(asset["path"]))
            installed_asset = installed_path / asset["path"]
            if not installed_asset.is_file() or _sha256(installed_asset) != asset["sha256"]:
                raise LifecycleError(f"packaged plugin asset is missing or differs: {asset['path']}")
        _atomic_copy(reviewer, target)
        global_payload, project_payload = _state_payloads(
            repo, version, marketplace, marketplace_owned, installed_path, packaged_assets, reviewer_hash
        )
        _atomic_json(project_path, project_payload)
        _atomic_json(global_path, global_payload)
    except Exception as exc:
        if target.exists() and _sha256(target) == _sha256(repo / PROJECT_ASSET):
            target.unlink()
        if project_path.exists():
            project_path.unlink()
        if global_path.exists():
            global_path.unlink()
        # The CLI could have changed native plugin state before a timeout.
        # Never issue a second, potentially destructive CLI mutation in this
        # uncertain state; preserve the marketplace for an operator to inspect.
        if not isinstance(exc, LifecycleTimeoutError):
            if plugin_added:
                try:
                    _checked(run, ["plugin", "remove", f"{name}@{marketplace}", "--json"], env, "rollback plugin remove")
                except LifecycleError:
                    pass
            if marketplace_added:
                try:
                    _checked(run, ["plugin", "marketplace", "remove", marketplace, "--json"], env, "rollback marketplace remove")
                except LifecycleError:
                    pass
        raise
    return {"status": "installed", "pluginVersion": version, "projectAsset": PROJECT_ASSET.as_posix()}


def _managed(repo: Path, project: Path, codex_home: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    global_state = _global_state(codex_home / GLOBAL_STATE_NAME)
    project_state = _project_state(project / PROJECT_STATE)
    if Path(global_state["repoRoot"]).resolve(strict=False) != repo:
        raise LifecycleError("managed marketplace belongs to a different CEK checkout")
    return global_state, project_state


def verify(repo: Path, project: Path, codex_home: Path, run: Runner) -> dict[str, Any]:
    repo, project, codex_home = _preflight(repo, project, codex_home)
    env = _environment(codex_home)
    _runtime(run, env)
    name, version, marketplace = _identity(repo)
    global_state, project_state = _managed(repo, project, codex_home)
    marketplaces = _marketplaces(run, env)
    if marketplaces.get(marketplace) != repo:
        raise LifecycleError("managed marketplace is missing or points to a different local root")
    target = project / PROJECT_ASSET
    source = repo / PROJECT_ASSET
    if not target.is_file() or _sha256(target) != project_state["assets"][0]["sha256"]:
        raise LifecycleError("project-local reviewer is missing or modified")
    if _sha256(target) != _sha256(source):
        raise LifecycleError("project-local reviewer differs from the current shipped asset; run update")
    installed_path = Path(global_state["installedPath"]).resolve(strict=False)
    cache_root = (codex_home / "plugins" / "cache").resolve(strict=False)
    if installed_path != cache_root and cache_root not in installed_path.parents:
        raise LifecycleError("managed plugin cache path is outside CODEX_HOME")
    current_assets = _packaged_assets(repo)
    if global_state["packagedAssets"] != current_assets:
        raise LifecycleError("managed packaged plugin assets differ from the current source; run update")
    for asset in current_assets:
        _reject_link_chain(installed_path, Path(asset["path"]))
        installed_asset = installed_path / asset["path"]
        if not installed_asset.is_file() or _sha256(installed_asset) != asset["sha256"]:
            raise LifecycleError(f"packaged plugin asset is missing or modified: {asset['path']}")
    plugin = _installed_plugin(run, env, name)
    if (
        plugin is None
        or plugin.get("installed") is not True
        or plugin.get("enabled") is not True
        or plugin.get("marketplaceName") != marketplace
        or plugin.get("version") != version
        or global_state["pluginVersion"] != version
        or project_state["pluginVersion"] != version
    ):
        raise LifecycleError("installed plugin identity/version is incomplete; run update")
    return {"status": "verified", "pluginVersion": version, "projectAsset": PROJECT_ASSET.as_posix()}


def update(repo: Path, project: Path, codex_home: Path, run: Runner) -> dict[str, Any]:
    repo, project, codex_home = _preflight(repo, project, codex_home)
    env = _environment(codex_home)
    _runtime(run, env)
    name, version, marketplace = _identity(repo)
    global_state, project_state = _managed(repo, project, codex_home)
    target = project / PROJECT_ASSET
    if not target.is_file() or _sha256(target) != project_state["assets"][0]["sha256"]:
        raise LifecycleError("modified project-local reviewer detected; preserve it before update")
    if _marketplaces(run, env).get(marketplace) != repo:
        raise LifecycleError("managed marketplace is missing or points to a different local root")
    current = _installed_plugin(run, env, name)
    if current is None:
        raise LifecycleError("managed CEK plugin is missing; uninstall cleanly before reinstalling")
    if current.get("marketplaceName") != marketplace:
        raise LifecycleError("managed plugin is registered to a different marketplace")
    payload = _checked(
        run,
        ["plugin", "add", f"{name}@{marketplace}", "--json"],
        env,
        "plugin reinstall",
    )
    if payload.get("name") != name or payload.get("marketplaceName") != marketplace or payload.get("version") != version:
        raise LifecycleError("plugin reinstall returned an unexpected identity or version")
    installed_value = payload.get("installedPath")
    if not isinstance(installed_value, str):
        raise LifecycleError("plugin reinstall did not return its installed cache path")
    installed_path = Path(installed_value).resolve(strict=True)
    cache_root = (codex_home / "plugins" / "cache").resolve(strict=False)
    if installed_path != cache_root and cache_root not in installed_path.parents:
        raise LifecycleError("plugin reinstall returned a path outside the Codex cache")
    reviewer = repo / PROJECT_ASSET
    reviewer_hash = _sha256(reviewer)
    packaged_assets = _packaged_assets(repo)
    for asset in packaged_assets:
        _reject_link_chain(installed_path, Path(asset["path"]))
        installed_asset = installed_path / asset["path"]
        if not installed_asset.is_file() or _sha256(installed_asset) != asset["sha256"]:
            raise LifecycleError(f"packaged plugin asset is missing or differs: {asset['path']}")
    _atomic_copy(reviewer, target)
    global_payload, project_payload = _state_payloads(
        repo,
        version,
        marketplace,
        global_state["marketplaceOwned"],
        installed_path,
        packaged_assets,
        reviewer_hash,
    )
    _atomic_json(project / PROJECT_STATE, project_payload)
    _atomic_json(codex_home / GLOBAL_STATE_NAME, global_payload)
    return {"status": "updated", "fromVersion": global_state["pluginVersion"], "toVersion": version}


def uninstall(repo: Path, project: Path, codex_home: Path, run: Runner) -> dict[str, Any]:
    repo, project, codex_home = _preflight(repo, project, codex_home)
    env = _environment(codex_home)
    _runtime(run, env)
    name, _version, marketplace = _identity(repo)
    global_path = codex_home / GLOBAL_STATE_NAME
    project_path = project / PROJECT_STATE
    if not global_path.exists() and not project_path.exists():
        return {"status": "already-clean", "preserved": []}
    if not global_path.exists() or not project_path.exists():
        raise LifecycleError("incomplete managed lifecycle state; refusing destructive cleanup")
    global_state, project_state = _managed(repo, project, codex_home)
    marketplaces = _marketplaces(run, env)
    if marketplaces.get(marketplace) != repo:
        raise LifecycleError("managed marketplace is missing or points to a different local root")
    plugin = _installed_plugin(run, env, name)
    if plugin is not None and plugin.get("marketplaceName") != marketplace:
        raise LifecycleError("managed plugin is registered to a different marketplace")
    if plugin is not None:
        _checked(run, ["plugin", "remove", f"{name}@{marketplace}", "--json"], env, "plugin remove")
    if global_state["marketplaceOwned"] and marketplace in marketplaces:
        _checked(run, ["plugin", "marketplace", "remove", marketplace, "--json"], env, "marketplace remove")
        if marketplace in _marketplaces(run, env):
            raise LifecycleError("marketplace removal was not confirmed; refusing to remove lifecycle state")

    preserved: list[str] = []
    target = project / PROJECT_ASSET
    if target.exists():
        if target.is_file() and _sha256(target) == project_state["assets"][0]["sha256"]:
            target.unlink()
        else:
            preserved.append(PROJECT_ASSET.as_posix())
    project_path.unlink()
    global_path.unlink()
    return {"status": "uninstalled", "preserved": preserved}


def verify_clean(repo: Path, project: Path, codex_home: Path, run: Runner) -> dict[str, Any]:
    repo, project, codex_home = _preflight(repo, project, codex_home)
    env = _environment(codex_home)
    _runtime(run, env)
    name, _version, marketplace = _identity(repo)
    if (codex_home / GLOBAL_STATE_NAME).exists() or (project / PROJECT_STATE).exists():
        raise LifecycleError("managed lifecycle state remains")
    if _installed_plugin(run, env, name) is not None:
        raise LifecycleError("CEK plugin remains installed")
    if marketplace in _marketplaces(run, env):
        raise LifecycleError(
            "CEK marketplace remains registered; inspect whether it is user-owned before considering cleanup complete"
        )
    return {
        "status": "clean",
        "unownedReviewerPresent": (project / PROJECT_ASSET).exists(),
    }


def _cli_codex_timeout(value: str) -> float:
    try:
        seconds = float(value)
        _validated_timeout(seconds)
    except (ValueError, LifecycleError) as exc:
        raise argparse.ArgumentTypeError(
            f"timeout must be > 0 and <= {MAX_CODEX_TIMEOUT_SECONDS:g} seconds"
        ) from exc
    return seconds


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the CEK native plugin and project-local reviewer lifecycle.")
    parser.add_argument("action", choices=("install", "verify", "update", "uninstall", "verify-clean"))
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--project", required=True)
    parser.add_argument("--codex-home", default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    parser.add_argument("--codex", default="codex")
    parser.add_argument(
        "--codex-timeout-seconds",
        type=_cli_codex_timeout,
        default=DEFAULT_CODEX_TIMEOUT_SECONDS,
        metavar="SECONDS",
        help="Per Codex CLI subprocess timeout (default: 120s, maximum: 900s).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    runner: Runner = lambda command, env: run_codex(
        args.codex, command, env, timeout_seconds=args.codex_timeout_seconds
    )
    actions = {
        "install": install,
        "verify": verify,
        "update": update,
        "uninstall": uninstall,
        "verify-clean": verify_clean,
    }
    try:
        executable = Path(shutil.which(args.codex) or args.codex)
        require_complete_package(executable)
        require_native_host(executable)
        result = actions[args.action](Path(args.repo), Path(args.project), Path(args.codex_home), runner)
    except (LifecycleError, NativeHostError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
