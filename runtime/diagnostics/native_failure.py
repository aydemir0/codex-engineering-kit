"""Fail-closed native failure reporting. Never export raw tool or credential text."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import json
import re
from subprocess import CompletedProcess

class NativeFailureCode(str, Enum):
    PLUGIN_DISCOVERY_FAILED = 'PLUGIN_DISCOVERY_FAILED'
    HOST_UNAVAILABLE = 'HOST_UNAVAILABLE'
    TOOL_INVOCATION_FAILED = 'TOOL_INVOCATION_FAILED'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    POWERSHELL_CLM_RESTRICTION = 'POWERSHELL_CLM_RESTRICTION'
    MALFORMED_RESPONSE = 'MALFORMED_RESPONSE'
    TIMEOUT = 'TIMEOUT'
    ARTIFACT_VERIFICATION_FAILED = 'ARTIFACT_VERIFICATION_FAILED'
    UNKNOWN = 'UNKNOWN'
GUIDANCE = {NativeFailureCode.PLUGIN_DISCOVERY_FAILED: ('Required plugin discovery failed.', 'Verify the intended local plugin installation and exact inventory; do not change account plugins automatically.'), NativeFailureCode.HOST_UNAVAILABLE: ('The pinned Code Mode host is missing, unsafe or unusable.', 'Verify the complete official runtime package and pinned hashes; stop on identity or path mismatch.'), NativeFailureCode.TOOL_INVOCATION_FAILED: ('A required native operation failed.', 'Inspect bounded local tool evidence and correct the invocation; preserve the failed attempt.'), NativeFailureCode.PERMISSION_DENIED: ('Effective policy denied access.', 'Use an approved writable disposable workspace; obtain operator approval if policy disallows it. Do not escalate automatically.'), NativeFailureCode.POWERSHELL_CLM_RESTRICTION: ('PowerShell Constrained Language Mode rejected an operation.', 'Use permitted cmdlets such as Set-Content and Get-Content; keep CLM and managed policy enabled.'), NativeFailureCode.MALFORMED_RESPONSE: ('Native response is malformed or incomplete.', 'Check runtime/protocol compatibility and preserve the response locally; do not accept completion.'), NativeFailureCode.TIMEOUT: ('Native execution exceeded its deadline.', 'Preserve the checkpoint and failed attempt; investigate the stalled operation before any explicit retry.'), NativeFailureCode.ARTIFACT_VERIFICATION_FAILED: ('Required artifact verification failed.', 'Check exact artifact bytes and candidate identity; rerun affected verification only after a correction.'), NativeFailureCode.UNKNOWN: ('Native execution failed for an unclassified reason.', 'Inspect local evidence without exporting credentials; do not claim verified success.')}

@dataclass(frozen=True)
class NativeFailure:
    code: NativeFailureCode
    reason_code: str

    def to_dict(self) -> dict[str, str]:
        message, action = GUIDANCE[self.code]
        return {'status': 'BLOCKED', 'code': self.code.value, 'reasonCode': self.reason_code, 'message': message, 'correctiveAction': action}

def diagnose(reason: str, detail: str='') -> NativeFailure:
    text = (reason + ' ' + detail).casefold()
    if 'clm' in text or 'constrainedlangu' in text or 'this language mode' in text or ('bu dil modundaki' in text):
        code = NativeFailureCode.POWERSHELL_CLM_RESTRICTION
    elif any(x in text for x in ['permission denied', 'access denied', 'eri\u015fim engellendi', 'permission_denied']):
        code = NativeFailureCode.PERMISSION_DENIED
    elif 'timeout' in text or 'timed out' in text:
        code = NativeFailureCode.TIMEOUT
    elif any((x in text for x in ['plugin_discovery', 'plugin discovery', 'failed to load plugin', 'plugin not found'])):
        code = NativeFailureCode.PLUGIN_DISCOVERY_FAILED
    elif 'artifact' in text:
        code = NativeFailureCode.ARTIFACT_VERIFICATION_FAILED
    elif any((x in text for x in ['invalid_json', 'invalid_frame', 'truncated_frame', 'unexpected_frame', 'malformed', 'incomplete_response', 'frame_limit'])):
        code = NativeFailureCode.MALFORMED_RESPONSE
    elif any((x in text for x in ['operation_failed', 'tool_failed', 'execution_failed', 'foreign_delegate', 'tool_invocation'])):
        code = NativeFailureCode.TOOL_INVOCATION_FAILED
    elif reason.startswith('CODE_MODE_'):
        code = NativeFailureCode.HOST_UNAVAILABLE
    else:
        code = NativeFailureCode.UNKNOWN
    safe = reason if re.fullmatch('[A-Z][A-Z0-9_]{0,95}', reason) else code.value
    return NativeFailure(code, safe)

class NativeExecutionError(RuntimeError):

    def __init__(self, reason: str, detail: str=''):
        self.diagnostic = diagnose(reason, detail)
        super().__init__(self.diagnostic.reason_code)

def validate_result(result: CompletedProcess[str]) -> None:
    completed = False
    for line in result.stdout.splitlines():
        try:
            row = json.loads(line)
        except (ValueError, TypeError) as error:
            raise NativeExecutionError('NATIVE_MALFORMED_RESPONSE') from error
        if not isinstance(row, dict):
            raise NativeExecutionError('NATIVE_MALFORMED_RESPONSE')
        if row.get('type') in {'error', 'turn.failed'}:
            error = row.get('error', {})
            detail = error.get('message', '') if isinstance(error, dict) else ''
            detail += ' ' + str(row.get('message', ''))
            raise NativeExecutionError('NATIVE_TOOL_INVOCATION_FAILED', detail)
        if row.get('type') == 'turn.started':
            completed = False
        if row.get('type') == 'turn.completed':
            completed = True
    if result.returncode:
        raise NativeExecutionError('NATIVE_TOOL_INVOCATION_FAILED', result.stderr)
    if not completed:
        raise NativeExecutionError('NATIVE_INCOMPLETE_RESPONSE')
