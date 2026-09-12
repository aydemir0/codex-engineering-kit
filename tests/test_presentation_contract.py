from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "docs" / "presentation" / "openai-project-brief.md"
INDEX = ROOT / "docs" / "presentation" / "evidence-index.md"
DEMO = ROOT / "docs" / "demo" / "representative-workflow.md"
EVIDENCE = ROOT / "docs" / "research" / "evidence" / "codex-v1-ws8-presentation.md"


class PresentationContractTests(unittest.TestCase):
    def test_required_presentation_assets_exist(self) -> None:
        for path in (BRIEF, INDEX, DEMO):
            self.assertTrue(path.is_file(), str(path.relative_to(ROOT)))

    def test_brief_preserves_benchmark_and_runtime_truth(self) -> None:
        text = BRIEF.read_text(encoding="utf-8")
        folded = text.casefold()

        for wording in (
            "45 authenticated runs",
            "A: 15/15 PASS",
            "B: 15/15 PASS",
            "C: 4/15 PASS",
            "34 PASS / 11 retained FAIL",
            "9 missing-lifecycle failures",
            "2 quality-contract failures",
            "no retry or replacement",
            "Codex CLI 0.153.0",
            "project-local reviewer",
            "plugin-native custom agents",
            "unsupported/deferred",
            "no Codex Desktop behavior is inferred",
            "unauthorized connector startup warning",
            "hooks are guardrails, not a sandbox",
        ):
            self.assertIn(wording.casefold(), folded)

        for forbidden in (
            "fully secure",
            "universally production-grade",
            "openai endorsed",
            "openai verified",
            "benchmark superior",
            "everything claude code does not support codex",
        ):
            self.assertNotIn(forbidden, folded)

    def test_brief_contains_the_evidence_flow_in_order(self) -> None:
        text = BRIEF.read_text(encoding="utf-8")
        flow = (
            "task -> orchestrator -> classify -> plan -> RED -> implementation "
            "-> GREEN -> real reviewer subagent -> verify -> hooks/state/evidence "
            "-> sanitized machine-checkable record -> release claim/evidence contract"
        )
        self.assertIn(flow, text)

    def test_evidence_index_maps_closed_workstreams_to_committed_evidence(self) -> None:
        text = INDEX.read_text(encoding="utf-8")
        for workstream in ("WS1", "WS2", "WS3", "WS4", "WS5", "WS6", "WS7", "WS8"):
            self.assertIn(workstream, text)
        for path in (
            "docs/release/claim-evidence-matrix.md",
            "docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md",
            "docs/research/evidence/codex-v1-representative-workflow.md",
            "docs/research/evidence/codex-v1-ws4-security.md",
            "docs/research/evidence/codex-v1-ws5-skill-agent-stocktake.md",
            "docs/research/evidence/codex-v1-ws6-benchmark.md",
            "docs/research/evidence/codex-v1-ws7-clean-install.md",
            "docs/research/evidence/codex-v1-ws8-presentation.md",
        ):
            self.assertIn(path, text)

    def test_demo_uses_the_proven_fixture_and_distinct_reviewer_evidence(self) -> None:
        text = DEMO.read_text(encoding="utf-8")
        for wording in (
            "tests/fixtures/representative-workflow",
            "disposable copy",
            "$codex-engineering-kit:orchestrator",
            "classify",
            "plan",
            "ValueError(\"division by zero\")",
            "RED",
            "GREEN",
            "READY",
            "distinct project-local reviewer",
            "SubagentStart",
            "SubagentStop",
            "python scripts/acceptance/workflow_evidence.py validate --record <sanitized-record>",
            "docs/research/evidence/codex-v1-representative-workflow.md",
        ):
            self.assertIn(wording, text)

    def test_readme_links_the_presentation_entrypoints(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for path in (
            "docs/presentation/openai-project-brief.md",
            "docs/presentation/evidence-index.md",
            "docs/demo/representative-workflow.md",
        ):
            self.assertIn(path, text)

    def test_ws8_evidence_is_sanitized_and_bound_to_the_reviewed_candidate(self) -> None:
        text = EVIDENCE.read_text(encoding="utf-8")
        self.assertIn("bb54d45126b243e92f5a8c2913f2947b6d9f3929", text)
        self.assertIn("252 tests", text)
        self.assertIn("Independent final review: PASS", text)
        self.assertIn("No remote mutation", text)
        self.assertNotRegex(
            text,
            r"(?i)(auth\.json|bearer\s+[A-Za-z0-9._-]+|session[_ -]?id|thread[_ -]?id)",
        )
        self.assertNotRegex(text, r"(?:[A-Za-z]:[\\/]|/Users/|/home/)")


if __name__ == "__main__":
    unittest.main()
