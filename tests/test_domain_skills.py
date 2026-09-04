from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BACKEND_HEADINGS = (
    "## Entry conditions",
    "## Repository evidence",
    "## Data and transaction boundaries",
    "## API and service contracts",
    "## Failure, retry, and idempotency",
    "## Security boundaries",
    "## Observability",
    "## Verification",
    "## Output contract",
)

FRONTEND_HEADINGS = (
    "## Entry conditions",
    "## Repository evidence",
    "## Rendering and client/server boundaries",
    "## State and data ownership",
    "## Accessibility and interaction",
    "## Error, loading, and empty states",
    "## Performance evidence",
    "## Verification",
    "## Output contract",
)

FRONTEND_PRINCIPLES = (
    "Do not move code client-side merely to simplify implementation.",
    "Do not duplicate server state into local state without an ownership reason.",
    "Do not claim a rendering change is faster without measurement.",
    "Accessibility regressions are correctness regressions.",
)

BACKEND_PRINCIPLES = (
    "Do not recommend a service split without an ownership or scaling boundary.",
    "Do not claim a query or cache change is faster without measurement.",
    "Treat retries, idempotency, and transaction boundaries as one failure model.",
)

FORBIDDEN_MACHINE_PATHS = (
    "c:\\users\\",
    "/users/",
    "/home/",
)

MODEL_SLUG_PATTERNS = (
    re.compile(r"(?i)\bgpt-[a-z0-9_.-]+\b"),
    re.compile(r"(?i)\bo[1-9](?:-[a-z0-9_.-]+)?\b"),
)


class BackendPatternsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_dir = ROOT / "skills" / "backend-patterns"
        self.skill_file = self.skill_dir / "SKILL.md"
        self.metadata_file = self.skill_dir / "agents" / "openai.yaml"

    def _read_required(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_backend_skill_files_and_metadata_are_portable(self) -> None:
        skill_text = self._read_required(self.skill_file)
        metadata_text = self._read_required(self.metadata_file)

        self.assertTrue(skill_text.startswith("---\n"))
        self.assertRegex(skill_text, r"(?m)^name:\s*backend-patterns\s*$")
        self.assertRegex(skill_text, r"(?m)^description:\s*\S.+$")

        for key in ("display_name", "short_description", "default_prompt"):
            self.assertRegex(metadata_text, rf"(?m)^\s*{key}:\s*\S.+$")
        self.assertIn("$backend-patterns", metadata_text)
        self.assertNotRegex(metadata_text, r"(?m)^\s*model\s*:")

        combined = f"{skill_text}\n{metadata_text}"
        self.assertNotRegex(combined, r"\b(?:TODO|TBD)\b")
        lowered = combined.casefold()
        for marker in FORBIDDEN_MACHINE_PATHS:
            self.assertNotIn(marker, lowered)
        for pattern in MODEL_SLUG_PATTERNS:
            self.assertIsNone(pattern.search(combined), f"model hard-coding matched {pattern.pattern}")

    def test_backend_skill_has_required_sections(self) -> None:
        skill_text = self._read_required(self.skill_file)
        for heading in BACKEND_HEADINGS:
            self.assertIn(heading, skill_text)

    def test_backend_skill_preserves_evidence_bound_principles(self) -> None:
        skill_text = self._read_required(self.skill_file)
        for principle in BACKEND_PRINCIPLES:
            self.assertIn(principle, skill_text)


class FrontendPatternsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill_dir = ROOT / "skills" / "frontend-patterns"
        self.skill_file = self.skill_dir / "SKILL.md"
        self.metadata_file = self.skill_dir / "agents" / "openai.yaml"

    def _read_required(self, path: Path) -> str:
        self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_frontend_skill_files_and_metadata_are_portable(self) -> None:
        skill_text = self._read_required(self.skill_file)
        metadata_text = self._read_required(self.metadata_file)

        self.assertTrue(skill_text.startswith("---\n"))
        self.assertRegex(skill_text, r"(?m)^name:\s*frontend-patterns\s*$")
        self.assertRegex(skill_text, r"(?m)^description:\s*\S.+$")

        for key in ("display_name", "short_description", "default_prompt"):
            self.assertRegex(metadata_text, rf"(?m)^\s*{key}:\s*\S.+$")
        self.assertIn("$frontend-patterns", metadata_text)
        self.assertNotRegex(metadata_text, r"(?m)^\s*model\s*:")

        combined = f"{skill_text}\n{metadata_text}"
        self.assertNotRegex(combined, r"\b(?:TODO|TBD)\b")
        lowered = combined.casefold()
        for marker in FORBIDDEN_MACHINE_PATHS:
            self.assertNotIn(marker, lowered)
        for pattern in MODEL_SLUG_PATTERNS:
            self.assertIsNone(pattern.search(combined), f"model hard-coding matched {pattern.pattern}")

    def test_frontend_skill_has_required_sections(self) -> None:
        skill_text = self._read_required(self.skill_file)
        for heading in FRONTEND_HEADINGS:
            self.assertIn(heading, skill_text)

    def test_frontend_skill_preserves_evidence_bound_principles(self) -> None:
        skill_text = self._read_required(self.skill_file)
        for principle in FRONTEND_PRINCIPLES:
            self.assertIn(principle, skill_text)


if __name__ == "__main__":
    unittest.main()
