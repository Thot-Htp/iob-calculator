import unittest

import iob


class TestIOBPrecision(unittest.TestCase):
    def test_total_rounds_once(self):
        doses = [
            (1.804925322024908, 83.1664139320608),
            (2.305398039790803, 210.94229647403006),
            (2.3763598284324625, 250.0312414589015),
        ]

        raw_values = [
            iob.iob_exponential_oref(u, e, round_result=False) for u, e in doses
        ]
        expected_total = round(sum(raw_values), 2)

        self.assertEqual(expected_total, iob.iob_total_from_elapsed(doses))

    def test_round_result_flag(self):
        units = 1.804925322024908
        elapsed = 83.1664139320608

        raw_value = iob.iob_exponential_oref(units, elapsed, round_result=False)
        rounded_value = iob.iob_exponential_oref(units, elapsed)

        self.assertNotAlmostEqual(raw_value, rounded_value)
        self.assertEqual(round(raw_value, 2), rounded_value)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
