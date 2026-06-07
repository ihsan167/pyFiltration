import math
import unittest

from pyfiltration.calculations import (
    cadr_from_airflow,
    cadr_from_decay,
    decay_rate_from_samples,
    fit_decay_from_samples,
    pm25_cadr_from_smoke_dust,
    required_cadr_for_clean_ach,
    required_cadr_for_target_concentration,
)


class CalculationTests(unittest.TestCase):
    def test_cadr_from_decay(self):
        self.assertAlmostEqual(cadr_from_decay(28.5, 5.0, 1.0), 114.0)

    def test_cadr_from_airflow(self):
        self.assertAlmostEqual(
            cadr_from_airflow(300.0, 0.95, bypass_fraction=0.05, mixing_effectiveness=0.9),
            243.675,
        )

    def test_pm25_cadr_from_smoke_dust(self):
        self.assertAlmostEqual(pm25_cadr_from_smoke_dust(200.0, 242.0), math.sqrt(48400.0))

    def test_required_cadr_for_clean_ach(self):
        self.assertAlmostEqual(required_cadr_for_clean_ach(54.0, 5.0, 0.3), 253.8)

    def test_required_cadr_for_target_concentration(self):
        result = required_cadr_for_target_concentration(
            room_volume_m3=54.0,
            target_concentration_ug_m3=60.0,
            source_generation_ug_h=500.0,
            ventilation_m3h=20.0,
            outdoor_concentration_ug_m3=5.0,
            natural_loss_ach=0.1,
        )
        self.assertAlmostEqual(result, 0.0)

    def test_decay_rate_from_samples(self):
        samples = [(0.0, 100.0), (10.0, 60.65306597), (20.0, 36.78794412)]
        self.assertAlmostEqual(decay_rate_from_samples(samples, time_unit="min"), 3.0, places=5)

    def test_decay_fit_reports_quality(self):
        samples = [(0.0, 100.0), (10.0, 60.65306597), (20.0, 36.78794412)]
        fit = fit_decay_from_samples(samples, time_unit="min")
        self.assertAlmostEqual(fit.rate_per_h, 3.0, places=5)
        self.assertAlmostEqual(fit.r_squared, 1.0, places=5)
        self.assertEqual(len(fit.adjusted_samples), 3)


if __name__ == "__main__":
    unittest.main()
