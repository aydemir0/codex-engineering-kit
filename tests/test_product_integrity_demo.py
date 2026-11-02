import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.demo_product_integrity import main

class ProductIntegrityDemoTests(unittest.TestCase):
    def test_real_clean_process_demo(self):
        result = subprocess.run([sys.executable, "-B", "-m", "scripts.demo_product_integrity"],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True,
                                encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["verification"]["staleGreen"], "REJECTED")
        self.assertEqual(report["recovery"]["sideEffects"], 1)
        self.assertEqual(report["recovery"]["duplicateLedgerWrites"], 0)
        self.assertEqual(report["nativeFailure"]["code"], "PERMISSION_DENIED")
        self.assertEqual(report["authentications"], 0)
        self.assertNotIn(tempfile.gettempdir(), result.stdout)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "foreign.json"
            path.write_bytes(b"FOREIGN_OWNER")
            with self.assertRaises(SystemExit):
                main(["--output", str(path)])
            self.assertEqual(path.read_bytes(), b"FOREIGN_OWNER")
