from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from runtime.workflow.lifecycle import NativeLifecycleError, extract_parent_identity, extract_reviewer_lifecycle


class M2BNativeLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.profile = Path(self.temporary.name) / "profile"
        self.session = self.profile / "sessions" / "2026" / "09" / "22" / "rollout.jsonl"
        self.session.parent.mkdir(parents=True)
        self.child_session = self.session.with_name("child.jsonl")

    def _write(self, *payloads: dict[str, object]) -> None:
        self.session.write_text(
            "\n".join(json.dumps(item) for item in payloads) + "\n",
            encoding="utf-8",
        )

    def _write_child(self, candidate_manifest: str = "c" * 64, candidate_tree: str = "d" * 40) -> None:
        result = {
            "disposition": "ACCEPT",
            "role": "reviewer",
            "findings": [],
            "candidateManifestDigest": candidate_manifest,
            "candidateTreeOid": candidate_tree,
        }
        self.child_session.write_text(
            "\n".join(
                json.dumps(item)
                for item in (
                    {
                        "type": "session_meta",
                        "payload": {
                            "id": "child-private",
                            "parent_thread_id": "parent-private",
                            "source": {
                                "subagent": {
                                    "thread_spawn": {
                                        "parent_thread_id": "parent-private",
                                        "agent_path": "/root/reviewer",
                                    }
                                }
                            },
                        },
                    },
                    {"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "workflow m2b-fixture"}]}},
                    {"type": "response_item", "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": json.dumps(result)}]}},
                )
            )
            + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _activity(kind: str, child: str, *, parent: str = "parent-private") -> dict[str, object]:
        return {
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "thread_id": parent,
                "item": {
                    "type": "SubAgentActivity",
                    "kind": kind,
                    "agent_thread_id": child,
                    "agent_path": "/root/reviewer",
                },
            },
        }

    def test_extracts_one_correlated_pair_without_exposing_session_ids(self) -> None:
        self._write(
            {"type": "session_meta", "payload": {"id": "parent-private", "source": "exec"}},
            {"type": "response_item", "payload": {"type": "message", "content": "workflow m2b-fixture"}},
            self._activity("started", "child-private"),
            self._activity("completed", "child-private"),
        )
        self._write_child()

        result = extract_reviewer_lifecycle(self.profile, "m2b-fixture")

        parent = "sha256:" + hashlib.sha256(b"parent-private").hexdigest()
        child = "sha256:" + hashlib.sha256(b"child-private").hexdigest()
        self.assertEqual(result["parentIdentity"], parent)
        self.assertEqual(result["childIdentity"], child)
        self.assertEqual(result["startChildIdentity"], child)
        self.assertEqual(result["stopChildIdentity"], child)
        self.assertEqual(result["agentType"], "reviewer")
        self.assertEqual(result["resultSourceChildIdentity"], child)
        self.assertEqual(result["structuredResult"]["candidateManifestDigest"], "c" * 64)
        self.assertEqual(result["structuredResult"]["candidateTreeOid"], "d" * 40)
        self.assertEqual(result["startEvent"], "SubagentStart")
        self.assertEqual(result["stopEvent"], "SubagentStop")
        self.assertNotIn("parent-private", json.dumps(result))
        self.assertNotIn("child-private", json.dumps(result))

    def test_rejects_lifecycle_without_child_emitted_structured_result(self) -> None:
        self._write(
            {"type": "session_meta", "payload": {"id": "parent-private", "source": "exec"}},
            {"type": "response_item", "payload": {"type": "message", "content": "workflow m2b-fixture"}},
            self._activity("started", "child-private"),
            self._activity("completed", "child-private"),
        )
        with self.assertRaisesRegex(NativeLifecycleError, "child-emitted structured result"):
            extract_reviewer_lifecycle(self.profile, "m2b-fixture")

    def test_extracts_parent_identity_before_reviewer_spawn(self) -> None:
        self._write(
            {"type": "session_meta", "payload": {"id": "parent-private", "source": "exec"}},
            {"type": "response_item", "payload": {"type": "message", "content": "workflow m2b-fixture"}},
        )

        result = extract_parent_identity(self.profile, "m2b-fixture")

        self.assertEqual(result["parentIdentity"], "sha256:" + hashlib.sha256(b"parent-private").hexdigest())
        self.assertNotIn("parent-private", json.dumps(result))

    def test_rejects_missing_or_ambiguous_lifecycle(self) -> None:
        self._write(
            {"type": "session_meta", "payload": {"id": "parent-private", "source": "exec"}},
            {"type": "response_item", "payload": {"type": "message", "content": "workflow m2b-fixture"}},
            self._activity("started", "child-one"),
        )
        with self.assertRaisesRegex(NativeLifecycleError, "matching reviewer lifecycle"):
            extract_reviewer_lifecycle(self.profile, "m2b-fixture")

        self._write(
            {"type": "session_meta", "payload": {"id": "parent-private", "source": "exec"}},
            {"type": "response_item", "payload": {"type": "message", "content": "workflow m2b-fixture"}},
            self._activity("started", "child-one"),
            self._activity("completed", "child-one"),
            self._activity("started", "child-two"),
            self._activity("completed", "child-two"),
        )
        with self.assertRaisesRegex(NativeLifecycleError, "exactly one reviewer lifecycle"):
            extract_reviewer_lifecycle(self.profile, "m2b-fixture")


if __name__ == "__main__":
    unittest.main()
