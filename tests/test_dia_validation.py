import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path

import iob

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestDIAValidation(unittest.TestCase):
    def test_iob_function_requires_positive_dia(self):
        with self.assertRaises(ValueError):
            iob.iob_exponential_oref(1.0, 30.0, DIA_hours=0)

        with self.assertRaises(ValueError):
            iob.iob_exponential_oref(1.0, 30.0, DIA_hours=-3)

    def test_total_requires_positive_dia(self):
        with self.assertRaises(ValueError):
            iob.iob_total_from_elapsed([(1.0, 30.0)], DIA_hours=0)

    def test_cli_reports_dia_error(self):
        result = subprocess.run(
            [sys.executable, "iob.py", "1", "30", "--dia", "0"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dia must be a positive number of hours", result.stderr.lower())
        self.assertNotIn("Traceback", result.stderr)

    def test_parse_pairs_requires_positive_dia(self):
        now = datetime(2024, 1, 1, 12, 0, 0)

        with self.assertRaisesRegex(ValueError, "positive number of hours"):
            iob.parse_pairs(["1", "30"], now, 0)

        with self.assertRaisesRegex(ValueError, "positive number of hours"):
            iob.parse_pairs(["1", "30"], now, -5)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
