import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from verification.candidate import capture_manifest, assert_report_current, CandidateIntegrityError
from verification.runner import verify_project
from verification.model import VerificationStep

class CandidateIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); (self.root/'a.txt').write_bytes(b'base')
    def test_manifest_tracks_add_remove_and_edit(self):
        before=capture_manifest(self.root)
        for action in ['edit','add','remove']:
            with self.subTest(action=action):
                (self.root/'a.txt').write_bytes(b'base')
                if action=='edit': (self.root/'a.txt').write_bytes(b'changed')
                if action=='add': (self.root/'new.txt').write_bytes(b'new')
                if action=='remove': (self.root/'a.txt').unlink()
                self.assertNotEqual(before,capture_manifest(self.root))
                (self.root/'new.txt').unlink(missing_ok=True)
    def test_git_staged_unstaged_untracked_without_index_mutation(self):
        def git(*args): return subprocess.run(['git',*args],cwd=self.root,check=True,capture_output=True)
        git('init','-q');git('add','.');git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','base')
        original=capture_manifest(self.root)
        (self.root/'a.txt').write_bytes(b'staged');git('add','a.txt')
        index=(self.root/'.git/index').read_bytes()
        staged=capture_manifest(self.root);self.assertNotEqual(original,staged)
        (self.root/'a.txt').write_bytes(b'unstaged');(self.root/'new.txt').write_bytes(b'untracked')
        self.assertNotEqual(staged,capture_manifest(self.root))
        self.assertEqual(index,(self.root/'.git/index').read_bytes())
    def test_mutation_during_tests_fails_and_stale_report_rejected(self):
        (self.root/'tests').mkdir();(self.root/'tests/test_x.py').write_text('')
        def discover(root):
            (root/'a.txt').write_bytes(b'changed during tests')
            from types import SimpleNamespace
            return SimpleNamespace(steps=(VerificationStep('test',None,'passed',0,0,'ok'),))
        with patch('verification.runner.discover_python_steps',side_effect=discover): report=verify_project(self.root)
        self.assertEqual(report.status,'failed')
        with self.assertRaises(CandidateIntegrityError): assert_report_current(self.root,report)
    def test_missing_artifact_wrong_identity_and_report_output(self):
        from dataclasses import replace
        report=verify_project(self.root);assert_report_current(self.root,report)
        with self.assertRaises(CandidateIntegrityError): assert_report_current(self.root,replace(report,candidate_digest='0'*64))
        (self.root/'a.txt').unlink()
        with self.assertRaises(CandidateIntegrityError): assert_report_current(self.root,report)
    def test_foreign_sentinel_and_links(self):
        sentinel=self.root/'sentinel';sentinel.write_bytes(b'foreign')
        capture_manifest(self.root);self.assertEqual(sentinel.read_bytes(),b'foreign')
        import os
        os.link(sentinel,self.root/'hardlink')
        with self.assertRaises(CandidateIntegrityError):capture_manifest(self.root)

    def test_stale_pass_cannot_be_published(self):
        from verification.runner import report_record
        from types import SimpleNamespace
        (self.root/'tests').mkdir();(self.root/'tests/test_x.py').write_text('')
        step=VerificationStep('test',None,'passed',0,0,'ok')
        with patch('verification.runner.discover_python_steps',return_value=SimpleNamespace(steps=(step,))):
            report=verify_project(self.root)
        self.assertEqual(report.status,'passed')
        (self.root/'a.txt').write_bytes(b'changed after testing')
        with self.assertRaises(CandidateIntegrityError):report_record(report)
    def test_no_git_required_for_plain_project(self):
        with patch('verification.candidate.subprocess.run',side_effect=FileNotFoundError):
            self.assertEqual(len(capture_manifest(self.root)),1)

    def test_ignored_ancestor_does_not_hide_nested_project(self):
        subprocess.run(['git','init','-q'],cwd=self.root,check=True,capture_output=True)
        (self.root/'.gitignore').write_text('ignored/\n')
        nested=self.root/'ignored'/'project';nested.mkdir(parents=True)
        (nested/'artifact').write_bytes(b'v1');before=capture_manifest(nested)
        self.assertEqual(len(before),1)
        (nested/'artifact').write_bytes(b'v2')
        self.assertNotEqual(before,capture_manifest(nested))
