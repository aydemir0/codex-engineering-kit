import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from runtime.diagnostics.native_failure import diagnose, validate_result, NativeExecutionError
from runtime.workflow.native import run_native

class NativeFailureTests(unittest.TestCase):
    def test_distinct_classes_and_safe_operator_guidance(self):
        examples={'PLUGIN_DISCOVERY_FAILED':'PLUGIN_DISCOVERY_FAILED','CODE_MODE_HOST_MISSING':'HOST_UNAVAILABLE','CODE_MODE_HOST_OPERATION_FAILED':'TOOL_INVOCATION_FAILED','Permission denied':'PERMISSION_DENIED','Method invocation is supported only on core types in this language mode':'POWERSHELL_CLM_RESTRICTION','CODE_MODE_HOST_INVALID_JSON':'MALFORMED_RESPONSE','CODE_MODE_HOST_TIMEOUT':'TIMEOUT','CODE_MODE_HOST_ARTIFACT_FAILED':'ARTIFACT_VERIFICATION_FAILED'}
        for reason,code in examples.items():
            with self.subTest(code=code):
                d=diagnose(reason,'secret-token-must-not-be-exported').to_dict()
                self.assertEqual(d['code'],code);self.assertTrue(d['correctiveAction']);self.assertTrue(d['message'])
                self.assertNotIn('secret-token',json.dumps(d))
    def test_malformed_and_incomplete_response_fail_closed(self):
        for output in ['not-json','{}',json.dumps({'type':'turn.started'})]:
            with self.assertRaises(NativeExecutionError):validate_result(subprocess.CompletedProcess([],0,output,''))
    def test_red_command_failure_is_not_terminal_failure(self):
        output='\n'.join(json.dumps(r) for r in [{'type':'item.completed','item':{'type':'command_execution','status':'failed','exit_code':1}},{'type':'turn.completed'}])
        validate_result(subprocess.CompletedProcess([],0,output,''))
    def test_terminal_permission_failure_not_hidden_by_zero_exit(self):
        output=json.dumps({'type':'turn.failed','error':{'message':'Permission denied'}})
        with self.assertRaises(NativeExecutionError) as caught:validate_result(subprocess.CompletedProcess([],0,output,''))
        self.assertEqual(caught.exception.diagnostic.code.value,'PERMISSION_DENIED')
    def test_real_local_process_timeout_and_interruption(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('runtime.workflow.native.require_native_host',return_value={}),patch('runtime.workflow.native.build_exec_command',return_value=[sys.executable,'-c','import time; time.sleep(5)']):
                with self.assertRaises(NativeExecutionError) as caught:run_native(Path(sys.executable),'local',Path(d),{},timeout_seconds=0.1)
                self.assertEqual(caught.exception.diagnostic.code.value,'TIMEOUT')
    def test_real_local_success_and_malformed_process(self):
        with tempfile.TemporaryDirectory() as d:
            for output,ok in [(json.dumps({'type':'turn.completed'}),True),('bad-frame',False)]:
                with patch('runtime.workflow.native.require_native_host',return_value={}),patch('runtime.workflow.native.build_exec_command',return_value=[sys.executable,'-c','print('+repr(output)+')']):
                    if ok:self.assertEqual(run_native(Path(sys.executable),'local',Path(d),{},timeout_seconds=3).returncode,0)
                    else:
                        with self.assertRaises(NativeExecutionError):run_native(Path(sys.executable),'local',Path(d),{},timeout_seconds=3)

    def test_invalid_native_utf8_is_structured_failure(self):
        with tempfile.TemporaryDirectory() as d:
            with patch('runtime.workflow.native.require_native_host',return_value={}),patch('runtime.workflow.native.build_exec_command',return_value=[sys.executable,'-c','import sys; sys.stdout.buffer.write(bytes([255]))']):
                with self.assertRaises(NativeExecutionError) as caught:
                    run_native(Path(sys.executable),'local',Path(d),{},timeout_seconds=3)
                self.assertEqual(caught.exception.diagnostic.code.value,'MALFORMED_RESPONSE')

    def test_completed_turn_does_not_authorize_pending_turn(self):
        output='\n'.join(json.dumps(r) for r in [{'type':'turn.completed'},{'type':'turn.started'}])
        with self.assertRaises(NativeExecutionError):
            validate_result(subprocess.CompletedProcess([],0,output,''))
    def test_turkish_permission_denial_is_classified(self):
        self.assertEqual(diagnose('NATIVE_TOOL_INVOCATION_FAILED', 'Eri\u015fim engellendi').code.value, 'PERMISSION_DENIED')
