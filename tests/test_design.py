import unittest

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


if __name__ == "__main__":
    unittest.main()
