import unittest

from pyfiltration.config import design_inputs_from_mapping
from pyfiltration.config import load_design_config
from pyfiltration.design import design_air_purifier


class DesignTests(unittest.TestCase):
    def test_example_design_produces_cadr_and_area(self):
        inputs = load_design_config("examples/home_air_purifier.json")
        result = design_air_purifier(inputs)
        self.assertGreater(result.loaded_p_cadr_m3h, result.required_p_cadr_m3h)
        self.assertGreater(result.loaded_f_cadr_m3h, result.required_f_cadr_m3h)
        self.assertGreater(result.required_media_area_m2, 0)
        self.assertGreater(result.frontal_area_m2, 0)
        self.assertGreater(result.formaldehyde_service_life_h or 0, 0)

    def test_mapping_loader_supports_ui_payload(self):
        payload = {
            "room": {
                "name": "Test room",
                "length_m": 4.0,
                "width_m": 3.0,
                "height_m": 2.5,
                "mixing_effectiveness": 0.9,
            },
            "particle": {
                "target_clean_ach": 5.0,
                "existing_removal_ach": 0.2,
                "single_pass_efficiency": 0.95,
            },
            "formaldehyde": {
                "target_clean_ach": 2.0,
                "existing_removal_ach": 0.1,
                "single_pass_efficiency": 0.5,
            },
            "filter": {
                "media_velocity_limit_m_s": 0.2,
                "pleat_area_multiplier": 6.0,
                "bypass_fraction": 0.02,
                "pressure_drop_ref_pa": 45.0,
                "pressure_drop_ref_velocity_m_s": 0.2,
                "pressure_drop_exponent": 1.3,
                "loaded_pressure_drop_multiplier": 1.6,
            },
            "fan": {
                "free_airflow_m3h": 300.0,
                "shutoff_pressure_pa": 180.0,
                "system_pressure_pa": 15.0,
                "curve_exponent": 1.7,
            },
            "safety_factor": 1.1,
        }
        result = design_air_purifier(design_inputs_from_mapping(payload))
        self.assertGreater(result.loaded_p_cadr_m3h, 0)


if __name__ == "__main__":
    unittest.main()
