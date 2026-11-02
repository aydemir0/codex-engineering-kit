"""Credentials-free deterministic product demo; no Codex/model/benchmark calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from runtime.diagnostics.native_failure import NativeExecutionError, validate_result
from runtime.workflow.coordinator import TransitionError, WorkflowCoordinator
from runtime.workflow.ledger import WorkflowLedger
from runtime.workflow.model import CandidateIdentity, FailureClass, WorkflowState
from verification.candidate import CandidateIntegrityError, assert_report_current
from verification.runner import verify_project


def demonstrate() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="cek-product-demo-") as temporary:
        root = Path(temporary)
        project = root / "project"
        (project / "tests").mkdir(parents=True)
        source = project / "calculator.py"
        source.write_bytes(b"def increment(value):\n    return value + 1\n")
        (project / "tests" / "test_calculator.py").write_bytes(
            b"import unittest\nfrom calculator import increment\n"
            b"class IncrementTests(unittest.TestCase):\n"
            b"    def test_increment(self): self.assertEqual(increment(4), 5)\n"
        )
        sentinel = project / "foreign-sentinel.txt"
        sentinel.write_bytes(b"FOREIGN_OWNER_SENTINEL\n")
        sentinel_digest = hashlib.sha256(sentinel.read_bytes()).hexdigest()
        report = verify_project(project)
        if report.status != "passed":
            raise RuntimeError("LOCAL_VERIFICATION_DID_NOT_PASS")
        assert_report_current(project, report)
        source.write_bytes(b"def increment(value):\n    return value + 2\n")
        try:
            assert_report_current(project, report)
        except CandidateIntegrityError as error:
            stale_reason = str(error)
        else:
            raise RuntimeError("STALE_GREEN_NOT_REJECTED")

        # Synthetic local workflow identities only: no production authority.
        candidate = CandidateIdentity("a" * 40, None, "b" * 40, "c" * 64,
                                      "d" * 64, "e" * 64, "demo-worktree", None, True)
        ledger = WorkflowLedger(root / "workflow.json")
        workflow = WorkflowCoordinator.create(
            ledger=ledger, workflow_id="local-demo", attempt_id="attempt-1",
            task_digest="f" * 64, base_commit_sha="a" * 40,
            cek_sha="1" * 40, runtime_identity={"kind": "synthetic-local-fixture"},
        )
        workflow.advance(WorkflowState.CLASSIFIED, {"classification": {
            "taskClass": "BUG_FIX", "risk": "LOW", "tools": [], "tests": [], "review": "fixture"}})
        workflow.advance(WorkflowState.PLANNED, {"plan": dict.fromkeys(
            ("goal", "scope", "redStrategy", "commands", "reviewer", "security", "recovery"), "local fixture")})
        workflow.advance(WorkflowState.ISOLATION_READY, {
            "authorized": True, "candidate": candidate, "worktreeId": "demo-worktree"})
        workflow.advance(WorkflowState.RED_REQUIRED, {})
        workflow.advance(WorkflowState.RED_CONFIRMED, {
            "result": "FAIL", "failureKind": "BEHAVIOR", "commandDigest": "2" * 64,
            "expectedSignature": "synthetic fixture", "candidate": candidate,
            "worktreeId": "demo-worktree"})
        workflow.advance(WorkflowState.IMPLEMENTING, {})
        workflow.advance(WorkflowState.GREEN_REQUIRED, {})
        workflow.advance(WorkflowState.GREEN_CONFIRMED, {
            "result": "PASS", "fresh": True, "commandDigest": "3" * 64,
            "candidate": candidate, "worktreeId": "demo-worktree"})
        effect = root / "effect.txt"
        with effect.open("x", encoding="utf-8") as stream:
            stream.write("executed-once\n")
        before = ledger.path.read_bytes()
        restored = WorkflowCoordinator.load(WorkflowLedger(ledger.path))
        restored.resume(candidate, "demo-worktree")
        restored.resume(candidate, "demo-worktree")
        if before != ledger.path.read_bytes() or effect.read_text(encoding="utf-8") != "executed-once\n":
            raise RuntimeError("RECOVERY_REPLAYED_EFFECTS")
        checkpoint = restored.state.value
        restored.fail(FailureClass.F9_TIMEOUT, "LOCAL_DEMO_TIMEOUT")
        terminal = WorkflowCoordinator.load(WorkflowLedger(ledger.path))
        try:
            terminal.resume(candidate, "demo-worktree")
        except TransitionError as error:
            terminal_reason = str(error)
        else:
            raise RuntimeError("TERMINAL_EXECUTION_ACCEPTED")

        # Real local Python process, controlled protocol failure. Not a Codex call.
        event = {"type": "turn.failed", "error": {"message": "Permission denied"}}
        environment = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "TEMP", "TMP") if key in os.environ}
        process = subprocess.run(
            [sys.executable, "-B", "-c", "print(" + repr(json.dumps(event)) + ")"],
            cwd=root, env=environment, capture_output=True, encoding="utf-8",
            check=False, timeout=10,
        )
        try:
            validate_result(process)
        except NativeExecutionError as error:
            diagnostic = error.diagnostic.to_dict()
        else:
            raise RuntimeError("CONTROLLED_NATIVE_FAILURE_ACCEPTED")
        if diagnostic["code"] != "PERMISSION_DENIED":
            raise RuntimeError("INCORRECT_FAILURE_DIAGNOSIS")
        if hashlib.sha256(sentinel.read_bytes()).hexdigest() != sentinel_digest:
            raise RuntimeError("FOREIGN_SENTINEL_CHANGED")
        return {
            "status": "PASS",
            "verification": {"initialTests": "PASS", "staleGreen": "REJECTED",
                             "reason": stale_reason, "foreignSentinel": "PRESERVED"},
            "recovery": {"scope": "SYNTHETIC_LOCAL_WORKFLOW", "checkpoint": checkpoint,
                         "sideEffects": 1, "duplicateLedgerWrites": 0,
                         "terminalState": terminal.state.value, "terminalResume": terminal_reason},
            "nativeFailure": {"scope": "CONTROLLED_LOCAL_PROCESS_NOT_CODEX", **diagnostic},
            "modelCalls": 0, "authentications": 0, "countedAttempts": 0,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional new JSON file; never overwrites an existing file.")
    arguments = parser.parse_args(argv)
    if arguments.output and arguments.output.exists():
        parser.error("output already exists; choose a new path")
    result = demonstrate()
    text = json.dumps(result, indent=2, sort_keys=True)
    if arguments.output:
        with arguments.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
