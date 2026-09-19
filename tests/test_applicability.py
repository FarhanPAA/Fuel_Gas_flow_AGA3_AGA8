import unittest

from calculation import calculate


def manual_example_1(**overrides):
    inputs = {
        "p": 199.3 - 14.73,
        "t": 86.0,
        "d_p": 20.0,
        "p_atm": 14.73,
        "p_b": 14.73,
        "p_unit": "psi",
        "d_p_unit": "inwc",
        "t_unit": "F",
        "t_base": 60.0,
        "pressure_tap": "Downstream",
        "length_unit": "in",
        "d0": 2.0,
        "D0": 4.025,
        "d0_tb": 68.0,
        "D0_tb": 68.0,
        "alpha_d": 9.25e-6,
        "alpha_D": 6.20e-6,
        "mu": 0.010268,
        "gas_properties_given": True,
        "z_f_manual": 0.973174,
        "z_b_manual": 0.997634,
        "molar_mass_manual": 28.9625 * 0.65,
        "k_manual": 1.30,
    }
    inputs.update(overrides)
    return calculate(**inputs)


class Aga3ApplicabilityTests(unittest.TestCase):
    def test_legacy_result_shape_is_preserved(self):
        self.assertEqual(len(manual_example_1()), 5)

    def test_standard_example_passes_applicability_checks(self):
        result = manual_example_1(return_diagnostics=True)

        self.assertTrue(result["within_aga3_applicability"])
        self.assertFalse(result["coefficient_of_discharge_low_reynolds_flag"])
        self.assertTrue(result["coefficient_of_discharge_converged"])
        self.assertGreaterEqual(result["pipe_reynolds_number"], 4000.0)
        self.assertGreater(result["differential_pressure_ratio"], 0.0)
        self.assertLess(result["differential_pressure_ratio"], 0.20)

    def test_geometry_flags_are_reported(self):
        result = manual_example_1(d0=0.40, return_diagnostics=True)

        self.assertTrue(result["applicability_flags"]["beta_ratio_out_of_range"])
        self.assertTrue(result["applicability_flags"]["orifice_bore_below_minimum"])
        self.assertFalse(result["within_aga3_applicability"])

    def test_low_reynolds_flag_is_exposed(self):
        result = manual_example_1(mu=100.0, return_diagnostics=True)

        self.assertTrue(result["applicability_flags"]["pipe_reynolds_number_below_minimum"])
        self.assertTrue(result["coefficient_of_discharge_low_reynolds_flag"])

    def test_pressure_ratio_flag_is_reported(self):
        result = manual_example_1(d_p=6000.0, return_diagnostics=True)

        self.assertTrue(result["applicability_flags"]["differential_pressure_ratio_out_of_range"])


if __name__ == "__main__":
    unittest.main()
