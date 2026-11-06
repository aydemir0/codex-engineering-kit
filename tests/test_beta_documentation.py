"""Public beta identity, bounded evidence and onboarding consistency."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class BetaDocumentationTests(unittest.TestCase):
    def test_candidate_identity_and_user_entrypoints_agree(self):
        version = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())['version']
        self.assertEqual(version, '1.1.0-beta.1')
        for name in ('README.md', 'docs/quickstart.md', 'docs/release/v1.1-beta.1.md'):
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertIn(version, text)
            self.assertIn('unpublished', text)
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for name in ('docs/quickstart.md', 'docs/troubleshooting.md', 'docs/release/v1.1-beta.1.md'):
            self.assertIn(name, readme)
            self.assertTrue((ROOT / name).is_file())

    def test_new_runtime_claim_retains_exact_observation_and_provenance(self):
        evidence = ROOT / 'docs/research/evidence/cek-real-workflow-20261106.json'
        record = json.loads(evidence.read_text(encoding='utf-8'))
        self.assertEqual(record['sourceCommit'], 'e5dc24941f9f3b858f1534d8404598579c5d8564')
        self.assertEqual(record['testedPluginVersion'], '1.0.0')
        self.assertEqual(record['attempts'], 1)
        self.assertEqual(record['result'], 'PASS')
        self.assertEqual(record['betaArtifactModelExecution'], 'NOT_RUN')
        self.assertEqual(record['execution']['red']['exitCode'], 1)
        self.assertEqual(record['execution']['green']['testsPassed'], 2)
        self.assertEqual(record['skills'], {'CEK':8, 'userGlobal':143, 'system':5, 'globalSource':'user-global .agents/skills', 'accountSyncOrigin':'NOT_ASSUMED', 'contextBudgetWarning':True})
        self.assertTrue(record['sanitized'])
        self.assertFalse(record['provenance']['rawArtifactsPublic'])
        digests = record['provenance']['rawArtifactDigests']
        self.assertEqual(len(digests), 12)
        for item in digests:
            self.assertEqual(Path(item['path']).name, item['path'])
            self.assertRegex(item['sha256'], r'^[0-9a-f]{64}$')
        self.assertNotRegex(evidence.read_text(encoding='utf-8'), r'(?:[A-Za-z]:[\\/]|/Users/|/home/|ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})')
        current = json.loads((ROOT / 'release_contracts/compatibility.json').read_text())['currentProductRuntime']
        self.assertIn(evidence.relative_to(ROOT).as_posix(), current['evidence'])
        self.assertEqual(current['modelDrivenWorkflow'], record['result'])

    def test_quickstart_preserves_permission_and_install_boundaries(self):
        text = (ROOT / 'docs/quickstart.md').read_text(encoding='utf-8')
        self.assertIn('New-Item -ItemType Directory -Path $CekProfile', text)
        self.assertIn("$CekLocal = Join-Path $env:TEMP 'cek-beta-first-use'", text)
        self.assertIn('windows.sandbox="unelevated"', text)
        self.assertIn('sandbox_workspace_write.network_access=false', text)
        for line in text.splitlines():
            if line.startswith('& $CekCodex exec'):
                self.assertIn('--approve-for-me', line)
                self.assertNotIn('--sandbox', line)
                self.assertNotIn('--dangerously', line)
        notes = (ROOT / 'docs/release/v1.1-beta.1.md').read_text(encoding='utf-8')
        self.assertIn('no model rerun on the beta artifact', notes)
        self.assertIn('does not close or waive an M4 gate', notes)
        self.assertIn('No baseline or performance advantage', notes)

if __name__ == '__main__':
    unittest.main()
