import json
import unittest
from unittest.mock import patch
from tests import test_m2b_orchestration as fixtures
from runtime.workflow.coordinator import WorkflowCoordinator, TransitionError
from runtime.workflow.ledger import WorkflowLedger, LedgerError
from runtime.workflow.model import WorkflowState, FailureClass

class RecoveryIntegrityTests(unittest.TestCase):
    setUp = fixtures.M2BContractTests.setUp
    _candidate = fixtures.M2BContractTests._candidate
    _classification = fixtures.M2BContractTests._classification
    _plan = fixtures.M2BContractTests._plan
    _to_isolation = fixtures.M2BContractTests._to_isolation
    _to_green = fixtures.M2BContractTests._to_green
    def test_failed_and_blocked_state_survive_interruption(self):
        self._to_green()
        self.coordinator.fail(FailureClass.F9_TIMEOUT,'TIMEOUT')
        loaded=WorkflowCoordinator.load(WorkflowLedger(self.ledger.path))
        self.assertEqual(loaded.state,WorkflowState.FAILED)
        with self.assertRaises(TransitionError):loaded.resume(self._candidate(),'worktree-1')
    def test_blocked_state_survives_reload(self):
        self.coordinator.block(FailureClass.F4_TOOL_RUNTIME,'TOOL_FAILED')
        self.assertEqual(WorkflowCoordinator.load(WorkflowLedger(self.ledger.path)).state,WorkflowState.BLOCKED)
    def test_resume_checkpoint_has_no_duplicate_effects(self):
        self._to_green();before=self.ledger.path.read_bytes()
        loaded=WorkflowCoordinator.load(WorkflowLedger(self.ledger.path))
        loaded.resume(self._candidate(),'worktree-1');loaded.resume(self._candidate(),'worktree-1')
        self.assertEqual(loaded.state,WorkflowState.GREEN_CONFIRMED)
        self.assertEqual(before,self.ledger.path.read_bytes())
        with self.assertRaises(TransitionError):loaded.advance(WorkflowState.IMPLEMENTING,{})
    def test_duplicate_attempt_rejected(self):
        self.coordinator.fail(FailureClass.F9_TIMEOUT,'TIMEOUT')
        with self.assertRaises(TransitionError):self.coordinator.retry('attempt-1')
    def test_terminal_resume_and_retry_rejected(self):
        self.coordinator.state=WorkflowState.VERIFIED;self.coordinator.current_candidate=self._candidate()
        for action in [lambda:self.coordinator.resume(self._candidate(),'worktree-1'),lambda:self.coordinator.retry('again'),lambda:self.coordinator.fail(FailureClass.F4_TOOL_RUNTIME,'overwrite')]:
            with self.assertRaises(TransitionError):action()
    def test_partial_write_preserves_checkpoint(self):
        self._to_green();before=self.ledger.path.read_bytes()
        with patch('runtime.state.os.replace',side_effect=OSError('simulated interrupted replacement')):
            with self.assertRaises(OSError):self.coordinator.advance(WorkflowState.REVIEW_REQUESTED,{})
        self.assertEqual(before,self.ledger.path.read_bytes())
        self.assertEqual(WorkflowCoordinator.load(WorkflowLedger(self.ledger.path)).state,WorkflowState.GREEN_CONFIRMED)
    def test_altered_and_truncated_evidence_rejected(self):
        self._to_green();before=self.ledger.path.read_bytes()
        for data in [before[:-8],before.replace(b'GREEN_CONFIRMED',b'VERIFIED')]:
            self.ledger.path.write_bytes(data)
            with self.assertRaises(LedgerError):WorkflowLedger(self.ledger.path)
        self.ledger.path.write_bytes(before)

    def test_active_workflow_cannot_open_duplicate_execution(self):
        self._to_green()
        with self.assertRaises(TransitionError):
            self.coordinator.retry('concurrent-attempt')
