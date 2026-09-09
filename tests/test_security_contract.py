from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
THREAT_MODEL = ROOT / "docs" / "security" / "threat-model.md"
PUBLIC_ARTIFACT_ROOTS = (
    ROOT / "docs" / "research" / "evidence",
    ROOT / "docs" / "release",
    ROOT / "docs" / "submission",
    ROOT / "release_contracts",
)
SECRET_PATTERNS = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{16,}\b"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(
        r"authorization[\"']?\s*[:=]\s*[\"']?Bearer\s+[^\"\s,;}]+",
        re.IGNORECASE,
    ),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"[A-Za-z]:(?:\\{1,2})Users(?:\\{1,2})", re.IGNORECASE),
    re.compile(r"/(?:Users|home)/[^/\s]+/"),
)


class SecurityDocumentationContractTests(unittest.TestCase):
    def test_public_artifact_patterns_cover_github_fine_grained_pats(self) -> None:
        synthetic = "github_pat_" + ("F" * 40)
        self.assertTrue(any(pattern.search(synthetic) for pattern in SECRET_PATTERNS))

    def test_threat_model_covers_every_ws4_family_and_non_sandbox_boundary(self) -> None:
        self.assertTrue(THREAT_MODEL.is_file(), "missing docs/security/threat-model.md")
        text = THREAT_MODEL.read_text(encoding="utf-8").casefold()
        for family in (
            "prompt/instruction injection",
            "unsafe shell/tool guidance",
            "destructive writes",
            "secrets and credentials",
            "local-state leakage",
            "mcp/app permission boundaries",
            "dependency provenance",
            "install/update ownership",
            "learned-content promotion",
            "plugin metadata and external url trust",
        ):
            self.assertIn(family, text)
        self.assertIn("guardrails, not a sandbox", text)
        self.assertIn("../../security.md", text)

    def test_public_security_evidence_has_no_raw_sensitive_values(self) -> None:
        violations: list[str] = []
        for root in PUBLIC_ARTIFACT_ROOTS:
            if not root.is_dir():
                continue
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.casefold() not in {".md", ".json"}:
                    continue
                text = path.read_text(encoding="utf-8")
                if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                    violations.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(violations, [])

    def test_every_local_runtime_state_directory_is_gitignored(self) -> None:
        ignored = {
            line.strip()
            for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for path in (
            ".codex-kit/local/",
            ".codex-kit/candidates/",
            ".codex-kit/hooks/",
            ".codex-kit/evals/",
            ".codex-kit/verification/",
        ):
            self.assertIn(path, ignored)

    def test_ci_actions_are_immutable_and_attribution_is_present(self) -> None:
        unpinned: list[str] = []
        for workflow in (ROOT / ".github" / "workflows").glob("*.yml"):
            for line in workflow.read_text(encoding="utf-8").splitlines():
                match = re.search(r"\buses:\s*([^\s]+)", line)
                if not match or match.group(1).startswith("./"):
                    continue
                reference = match.group(1).rsplit("@", 1)[-1]
                if not re.fullmatch(r"[0-9a-fA-F]{40}", reference):
                    unpinned.append(f"{workflow.name}: {match.group(1)}")
        self.assertEqual(unpinned, [])
        self.assertTrue((ROOT / "LICENSE").is_file())
        notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        self.assertIn("MIT License", notices)

    def test_mcp_templates_are_secret_free_local_permission_declarations(self) -> None:
        allowed_keys = {
            "provider",
            "login_required",
            "required_environment",
            "configuration_scope",
            "notes",
        }
        for path in (ROOT / "mcp" / "templates").glob("*.json"):
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self.assertEqual(set(data), allowed_keys, path.name)
            self.assertEqual(data["configuration_scope"], "local-only", path.name)
            self.assertTrue(data["login_required"] or data["required_environment"], path.name)
            self.assertNotRegex(raw, r"(?i)(authorization|api[_-]?key|token)\s*[=:]\s*\S+")

    def test_plugin_external_urls_are_https_and_bound_to_declared_owner(self) -> None:
        plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        urls = (
            plugin["author"]["url"],
            plugin["homepage"],
            plugin["repository"],
            plugin["interface"]["websiteURL"],
        )
        for value in urls:
            parsed = urlparse(value)
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.hostname, "github.com")
            segments = [segment for segment in parsed.path.split("/") if segment]
            self.assertGreaterEqual(len(segments), 1)
            self.assertEqual(segments[0].casefold(), "aydemir0")


if __name__ == "__main__":
    unittest.main()
