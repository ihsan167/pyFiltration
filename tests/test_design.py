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

    def test_fixed_filter_media_area_evaluates_delivered_cadr(self):
        inputs = load_design_config("examples/home_air_purifier.json")
        payload = {
            "room": {
                "name": inputs.room.name,
                "length_m": inputs.room.length_m,
                "width_m": inputs.room.width_m,
                "height_m": inputs.room.height_m,
                "mixing_effectiveness": inputs.room.mixing_effectiveness,
            },
            "particle": {
                "target_clean_ach": inputs.particle.target_clean_ach,
                "existing_removal_ach": inputs.particle.existing_removal_ach,
                "single_pass_efficiency": inputs.particle.single_pass_efficiency,
            },
            "formaldehyde": {
                "target_clean_ach": inputs.formaldehyde.target_clean_ach,
                "existing_removal_ach": inputs.formaldehyde.existing_removal_ach,
                "target_concentration_ug_m3": inputs.formaldehyde.target_concentration_ug_m3,
                "source_generation_ug_h": inputs.formaldehyde.source_generation_ug_h,
                "outdoor_concentration_ug_m3": inputs.formaldehyde.outdoor_concentration_ug_m3,
                "ventilation_m3h": inputs.formaldehyde.ventilation_m3h,
                "single_pass_efficiency": inputs.formaldehyde.single_pass_efficiency,
                "challenge_concentration_ug_m3": inputs.formaldehyde.challenge_concentration_ug_m3,
                "carbon_mass_g": inputs.formaldehyde.carbon_mass_g,
                "capacity_mg_per_g": inputs.formaldehyde.capacity_mg_per_g,
                "capacity_utilization": inputs.formaldehyde.capacity_utilization,
                "temperature_c": inputs.formaldehyde.temperature_c,
                "relative_humidity_percent": inputs.formaldehyde.relative_humidity_percent,
            },
            "filter": {
                "media_velocity_limit_m_s": inputs.filter.media_velocity_limit_m_s,
                "pleat_area_multiplier": inputs.filter.pleat_area_multiplier,
                "fixed_media_area_m2": 0.45,
                "bypass_fraction": inputs.filter.bypass_fraction,
                "pressure_drop_ref_pa": inputs.filter.pressure_drop_ref_pa,
                "pressure_drop_ref_velocity_m_s": inputs.filter.pressure_drop_ref_velocity_m_s,
                "pressure_drop_exponent": inputs.filter.pressure_drop_exponent,
                "loaded_pressure_drop_multiplier": inputs.filter.loaded_pressure_drop_multiplier,
            },
            "fan": {
                "free_airflow_m3h": inputs.fan.free_airflow_m3h,
                "shutoff_pressure_pa": inputs.fan.shutoff_pressure_pa,
                "system_pressure_pa": inputs.fan.system_pressure_pa,
                "curve_exponent": inputs.fan.curve_exponent,
                "power_w": inputs.fan.power_w,
            },
            "safety_factor": inputs.safety_factor,
        }
        result = design_air_purifier(design_inputs_from_mapping(payload))
        self.assertEqual(result.media_area_basis, "user-defined fixed media")
        self.assertAlmostEqual(result.required_media_area_m2, 0.45)
        self.assertLess(result.loaded_p_cadr_m3h, result.required_p_cadr_m3h)
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
