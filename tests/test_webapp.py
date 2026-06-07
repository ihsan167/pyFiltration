import unittest

from pyfiltration.webapp import _lab_cadr_from_payload


class WebAppTests(unittest.TestCase):
    def test_lab_cadr_payload_uses_decay_difference(self):
        result = _lab_cadr_from_payload(
            {
                "chamber_volume_m3": 28.5,
                "time_unit": "min",
                "background_concentration": 0,
                "natural_samples": [[0, 100], [10, 96.72], [20, 93.56], [30, 90.48]],
                "purifier_samples": [[0, 100], [10, 49.66], [20, 24.66], [30, 12.25]],
            }
        )
        self.assertAlmostEqual(result["natural_decay_per_h"], 0.2, places=2)
        self.assertAlmostEqual(result["purifier_decay_per_h"], 4.2, places=2)
        self.assertAlmostEqual(result["cadr_m3h"], 114.0, places=1)
        self.assertFalse(result["warnings"])


if __name__ == "__main__":
    unittest.main()
