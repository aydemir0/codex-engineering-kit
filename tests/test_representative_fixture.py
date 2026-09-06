from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "representative-workflow"


class RepresentativeFixtureContractTests(unittest.TestCase):
    def test_pristine_fixture_has_expected_intentional_red_state(self) -> None:
        self.assertTrue(
            FIXTURE.is_dir(),
            "representative workflow fixture is missing",
        )

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "fixture"
            shutil.copytree(FIXTURE, work)

            before = {
                path.relative_to(work): path.read_bytes()
                for path in work.rglob("*")
                if path.is_file()
            }

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-v",
                ],
                cwd=work,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )

            after = {
                path.relative_to(work): path.read_bytes()
                for path in work.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and not path.name.endswith(".pyc")
            }

        expected_before = {
            path: data
            for path, data in before.items()
            if "__pycache__" not in path.parts
            and not path.name.endswith(".pyc")
        }

        self.assertNotEqual(
            completed.returncode,
            0,
            "pristine fixture must begin in deterministic RED state",
        )
        self.assertIn(
            "test_divide_by_zero_raises_value_error",
            completed.stdout,
        )
        self.assertIn(
            "ValueError not raised",
            completed.stdout,
        )
        self.assertEqual(
            after,
            expected_before,
            "running the fixture tests must not mutate checked fixture content",
        )


if __name__ == "__main__":
    unittest.main()
