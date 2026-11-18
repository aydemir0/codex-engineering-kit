"""Shipped PowerShell entrypoints require PowerShell 7 or newer."""

from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = {
    "mcp/configure.ps1",
    "scripts/codex-wrapper.ps1",
    "scripts/install.ps1",
    "scripts/learn-session.ps1",
    "scripts/uninstall.ps1",
    "scripts/update.ps1",
    "scripts/verify.ps1",
}


def run_script(shell, script, fixture, env, *args):
    return subprocess.run(
        [shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", ROOT / script, *args],
        cwd=fixture,
        env=env,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=30,
    )


def snapshot(root):
    return {
        path.relative_to(root): sha256(path.read_bytes()).digest() if path.is_file() else None
        for path in root.rglob("*")
    }


class PowerShellEntrypointTests(unittest.TestCase):
    def test_all_shipped_entrypoints_declare_powershell_7(self):
        scripts = {
            path.relative_to(ROOT).as_posix()
            for directory in ("mcp", "scripts")
            for path in (ROOT / directory).rglob("*.ps1")
        }
        self.assertEqual(scripts, ENTRYPOINTS)
        for script in sorted(ENTRYPOINTS):
            with self.subTest(script=script):
                first_line = (ROOT / script).read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first_line, "#Requires -Version 7.0")

    @unittest.skipUnless(os.name == "nt", "requires Windows PowerShell 5.1")
    def test_windows_powershell_rejects_all_entrypoints_without_writing(self):
        system32 = Path(os.environ["SystemRoot"]) / "System32"
        legacy = system32 / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        pwsh = shutil.which("pwsh")
        self.assertIsNotNone(pwsh, "fixture setup requires PowerShell 7")

        version = subprocess.run(
            [legacy, "-NoProfile", "-NonInteractive", "-Command", "$PSVersionTable.PSVersion.ToString()"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertRegex(version.stdout.strip(), r"^5\.1(?:\.\d+)*$")

        with tempfile.TemporaryDirectory(prefix="cek-powershell-contract-") as directory:
            fixture = Path(directory) / "fixture"
            # PowerShell may cache startup data outside the managed fixture.
            shell_home = Path(directory) / "shell-home"
            shell_home.mkdir()
            home = fixture / "profile"
            project = fixture / "project"
            project.mkdir(parents=True)
            env = {
                "SystemRoot": os.environ["SystemRoot"],
                "ComSpec": str(system32 / "cmd.exe"),
                "PATH": os.pathsep.join((str(fixture), str(system32))),
                "PATHEXT": ".COM;.EXE;.BAT;.CMD",
                "CODEX_HOME": str(home),
                "TEMP": str(shell_home),
                "TMP": str(shell_home),
                "USERPROFILE": str(shell_home),
                "APPDATA": str(shell_home),
                "LOCALAPPDATA": str(shell_home),
            }
            # Record unexpected delegation without resolving the developer's tools.
            for name in ("codex", "python"):
                (fixture / f"{name}.cmd").write_text(
                    f'@echo invoked>"%~dp0{name}-called.txt"\n', encoding="ascii"
                )
            observations = fixture / "observations.json"
            observations.write_text("[]", encoding="ascii")
            for sentinel in (fixture / "foreign.txt", project / "foreign.txt"):
                sentinel.write_bytes(b"preserve this exact content\r\n")

            managed = fixture / "installed"
            installed = run_script(pwsh, "scripts/install.ps1", fixture, env, "-CodexHome", managed)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertTrue((managed / "codex-engineering-kit.manifest.json").is_file())
            (managed / "foreign.txt").write_bytes(b"user-owned file in managed home")

            cases = {
                "mcp/configure.ps1": ("-Provider", "github", "-OutputPath", fixture / "mcp.json"),
                "scripts/codex-wrapper.ps1": (),
                "scripts/install.ps1": ("-CodexHome", home),
                "scripts/learn-session.ps1": ("-InputPath", observations, "-OutputPath", fixture / "learning.json"),
                "scripts/uninstall.ps1": ("-CodexHome", managed),
                "scripts/update.ps1": ("-CodexHome", fixture / "update-profile"),
                "scripts/verify.ps1": ("-ProjectPath", project),
            }
            self.assertEqual(set(cases), ENTRYPOINTS)
            for script, args in cases.items():
                with self.subTest(script=script):
                    before = snapshot(fixture)
                    result = run_script(legacy, script, fixture, env, *args)
                    after = snapshot(fixture)
                    changed = sorted(
                        str(path) for path in before.keys() | after.keys()
                        if path not in before or path not in after or before[path] != after[path]
                    )
                    self.assertFalse(
                        result.returncode == 0
                        or "ScriptRequiresUnmatchedPSVersion" not in result.stderr
                        or changed,
                        f"exit={result.returncode}, changed={changed}, stderr={result.stderr}",
                    )

            updated = run_script(pwsh, "scripts/update.ps1", fixture, env, *cases["scripts/update.ps1"])
            self.assertEqual(updated.returncode, 0, updated.stderr)
            self.assertTrue((fixture / "update-profile/codex-engineering-kit.manifest.json").is_file())
            wrapper = run_script(pwsh, "scripts/codex-wrapper.ps1", fixture, env)
            self.assertEqual(wrapper.returncode, 0, wrapper.stderr)
            self.assertEqual((fixture / "codex-called.txt").read_bytes(), b"invoked\r\n")
