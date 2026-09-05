from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

SUPPORTED_MANAGERS = ("npm", "pnpm", "yarn", "bun")
AVAILABLE_PREFERENCE = ("pnpm", "yarn", "bun")
LOCKFILES = {
    "npm": ("package-lock.json", "npm-shrinkwrap.json"),
    "pnpm": ("pnpm-lock.yaml",),
    "yarn": ("yarn.lock",),
    "bun": ("bun.lock", "bun.lockb"),
}


@dataclass(frozen=True)
class ManagerSelection:
    name: str | None
    source: str
    detail: str | None = None


def _normalize_manager(raw: str) -> str:
    return raw.strip().split("@", 1)[0].casefold()


def _authoritative_selection(
    raw_name: str,
    source: str,
    which: Callable[[str], str | None],
) -> ManagerSelection:
    name = _normalize_manager(raw_name)
    if name not in SUPPORTED_MANAGERS:
        return ManagerSelection(None, source, f"unsupported-manager:{name}")
    if which(name) is None:
        return ManagerSelection(name, source, "unavailable")
    return ManagerSelection(name, source)


def _read_package_json(project_path: Path) -> dict:
    package_json = project_path / "package.json"
    if not package_json.is_file():
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def detect_package_manager(
    project_path: Path,
    explicit: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> ManagerSelection:
    project_path = Path(project_path)

    if explicit:
        return _authoritative_selection(explicit, "explicit", which)

    package_json = project_path / "package.json"
    if not package_json.is_file():
        return ManagerSelection(None, "project", "not-a-node-project")

    package = _read_package_json(project_path)
    package_manager = package.get("packageManager")
    if isinstance(package_manager, str) and package_manager.strip():
        return _authoritative_selection(package_manager, "packageManager", which)

    lockfile_managers = {
        manager
        for manager, filenames in LOCKFILES.items()
        if any((project_path / filename).is_file() for filename in filenames)
    }
    if len(lockfile_managers) > 1:
        return ManagerSelection(None, "lockfile", "ambiguous-lockfiles")
    if len(lockfile_managers) == 1:
        manager = next(iter(lockfile_managers))
        return _authoritative_selection(manager, "lockfile", which)

    for manager in AVAILABLE_PREFERENCE:
        if which(manager) is not None:
            return ManagerSelection(manager, "available")

    if which("npm") is not None:
        return ManagerSelection("npm", "fallback")

    return ManagerSelection(None, "availability", "no-manager-available")


def package_script_command(manager: str, script: str) -> list[str]:
    normalized = manager.casefold()
    if normalized not in SUPPORTED_MANAGERS:
        raise ValueError(f"unsupported package manager: {manager}")
    if normalized == "bun":
        return ["bun", "run", script]
    return [normalized, "run", script, "--silent"]
