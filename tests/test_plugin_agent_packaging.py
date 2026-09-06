from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_REVIEWER = ROOT / "agents" / "reviewer.md"


class PluginAgentPackagingTests(unittest.TestCase):
    def test_plugin_packages_reviewer_on_native_agent_surface(self) -> None:
        self.assertTrue(
            PLUGIN_REVIEWER.is_file(),
            "plugin install must expose agents/reviewer.md",
        )

        text = PLUGIN_REVIEWER.read_text(encoding="utf-8")

        self.assertRegex(
            text,
            r"\A---\s*\n",
        )
        self.assertRegex(
            text,
            r"(?m)^name:\s*reviewer\s*$",
        )
        self.assertRegex(
            text,
            r"(?m)^description:\s*\S.+$",
        )

        body = re.sub(
            r"\A---.*?---\s*",
            "",
            text,
            count=1,
            flags=re.DOTALL,
        ).casefold()

        self.assertIn("do not modify files", body)
        self.assertIn("do not create commits", body)
        self.assertIn("evidence", body)
        self.assertIn("findings", body)


if __name__ == "__main__":
    unittest.main()