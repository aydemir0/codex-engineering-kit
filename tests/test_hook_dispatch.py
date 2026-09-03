from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hooks.scripts.hook_dispatch import dispatch


class HookDispatchBehaviorTests(unittest.TestCase):
    def payload(self, event: str, cwd: Path, **extra: object) -> dict[str, object]:
        base: dict[str, object] = {
            "hook_event_name": event,
            "session_id": "session-1",
            "turn_id": "turn-1",
            "cwd": str(cwd),
        }
        base.update(extra)
        return base

    def test_pre_tool_use_allows_normal_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch(
                self.payload(
                    "PreToolUse",
                    Path(tmp),
                    tool_name="Bash",
                    tool_use_id="tool-1",
                    tool_input={"command": "git status"},
                )
            )
        self.assertEqual(result, {})

    def test_pre_tool_use_denies_narrow_destructive_root_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch(
                self.payload(
                    "PreToolUse",
                    Path(tmp),
                    tool_name="Bash",
                    tool_use_id="tool-2",
                    tool_input={"command": "rm -rf /"},
                )
            )
        specific = result["hookSpecificOutput"]
        self.assertEqual(specific["hookEventName"], "PreToolUse")
        self.assertEqual(specific["permissionDecision"], "deny")
        self.assertIn("destructive", specific["permissionDecisionReason"].lower())

    def test_session_start_emits_bounded_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch(self.payload("SessionStart", Path(tmp), source="startup"))
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertLessEqual(len(context), 6000)
        self.assertIn("Codex Engineering Kit", context)

    def test_precompact_to_compact_session_start_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            dispatch(self.payload("PreCompact", cwd, trigger="auto"))
            checkpoint = cwd / ".codex-kit" / "hooks" / "compact-state.json"
            self.assertTrue(checkpoint.is_file())
            state = json.loads(checkpoint.read_text(encoding="utf-8"))
            self.assertEqual(state["sessionId"], "session-1")
            self.assertEqual(state["turnId"], "turn-1")
            self.assertEqual(state["trigger"], "auto")

            resumed = dispatch(
                self.payload(
                    "SessionStart",
                    cwd,
                    source="compact",
                    session_id="session-1",
                    turn_id="turn-2",
                )
            )
            context = resumed["hookSpecificOutput"]["additionalContext"]
            self.assertIn("turn-1", context)
            self.assertIn("auto", context)

    def test_post_tool_use_records_metadata_without_raw_input_or_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            dispatch(
                self.payload(
                    "PostToolUse",
                    cwd,
                    tool_name="Bash",
                    tool_use_id="tool-3",
                    tool_input={"command": "echo SUPER_SECRET_VALUE"},
                    tool_response={"output": "SUPER_SECRET_RESPONSE"},
                )
            )
            evidence = (cwd / ".codex-kit" / "hooks" / "events.jsonl").read_text(
                encoding="utf-8"
            )
        self.assertIn("PostToolUse", evidence)
        self.assertIn("tool-3", evidence)
        self.assertNotIn("SUPER_SECRET_VALUE", evidence)
        self.assertNotIn("SUPER_SECRET_RESPONSE", evidence)

    def test_session_end_writes_cheap_snapshot_without_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            dispatch(
                self.payload(
                    "SessionEnd",
                    cwd,
                    reason="normal",
                    transcript_path="C:/private/transcript.jsonl",
                )
            )
            snapshot_path = cwd / ".codex-kit" / "hooks" / "session-end.json"
            self.assertTrue(snapshot_path.is_file())
            snapshot_text = snapshot_path.read_text(encoding="utf-8")
        self.assertIn("session-1", snapshot_text)
        self.assertNotIn("transcript", snapshot_text.lower())
        self.assertNotIn("C:/private", snapshot_text)

    def test_subagent_lifecycle_records_bounded_identity_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            dispatch(
                self.payload(
                    "SubagentStart",
                    cwd,
                    agent_id="agent-1",
                    agent_type="reviewer",
                    transcript_path="C:/private/subagent.jsonl",
                )
            )
            dispatch(
                self.payload(
                    "SubagentStop",
                    cwd,
                    agent_id="agent-1",
                    agent_type="reviewer",
                    stop_hook_active=True,
                )
            )
            evidence = (cwd / ".codex-kit" / "hooks" / "events.jsonl").read_text(
                encoding="utf-8"
            )
        self.assertIn("agent-1", evidence)
        self.assertIn("reviewer", evidence)
        self.assertNotIn("C:/private", evidence)


if __name__ == "__main__":
    unittest.main()
