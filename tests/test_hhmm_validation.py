import subprocess
import sys
import unittest
from datetime import datetime
from pathlib import Path

import iob

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestHHMMValidation(unittest.TestCase):
    def test_parser_rejects_invalid_minute(self):
        now = datetime(2024, 1, 1, 12, 0, 0)
        with self.assertRaises(ValueError) as ctx:
            iob._parse_hhmm_to_elapsed_today_or_yesterday("12:99", now, 5 * 60)
        self.assertIn("minute must be 0-59", str(ctx.exception))

    def test_cli_reports_invalid_hhmm(self):
        result = subprocess.run(
            [sys.executable, "iob.py", "1", "12:99"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("minute must be 0-59", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
