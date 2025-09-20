import subprocess
import sys
import unittest
from pathlib import Path

import iob

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestPeakValidation(unittest.TestCase):
    def test_iob_function_requires_positive_peak(self):
        with self.assertRaises(ValueError):
            iob.iob_exponential_oref(1.0, 30.0, PEAK_min=0)

        with self.assertRaises(ValueError):
            iob.iob_exponential_oref(1.0, 30.0, PEAK_min=-10)

    def test_cli_reports_peak_error(self):
        result = subprocess.run(
            [sys.executable, "iob.py", "1", "30", "--peak", "0"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("peak must be a positive", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
