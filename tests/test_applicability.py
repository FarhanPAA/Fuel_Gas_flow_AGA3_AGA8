import unittest

from calculation import calculate
from src.aga3 import AGA3ConvergenceError, flange_tap_cd, flange_tap_cd_constants


def nominal_manual_gas_case(**overrides):
    """Return a synthetic, in-range gas case for diagnostic behavior tests."""
    inputs = {
        "p": 450.0,
        "t": 30.0,
        "d_p": 250.0,
        "p_atm": 14.696,
        "p_b": 14.696,
        "p_unit": "psi",
        "d_p_unit": "mbar",
        "t_unit": "C",
        "t_base": 15.556,
        "pressure_tap": "Upstream",
        "length_unit": "mm",
        "d0": 247.768,
        "D0": 387.535,
        "d0_tb": 20.0,
        "D0_tb": 20.0,
        "alpha_d": 8.89e-6,
        "alpha_D": 6.20e-6,
        "mu": 0.0103,
        "gas_properties_given": True,
        "z_f_manual": 0.93,
        "z_b_manual": 0.98,
        "molar_mass_manual": 17.10,
        "k_manual": 1.30,
    }
    inputs.update(overrides)
    return calculate(**inputs)


class Aga3ApplicabilityTests(unittest.TestCase):
    def test_legacy_result_shape_is_preserved(self):
        self.assertEqual(len(nominal_manual_gas_case()), 5)

    def test_geometry_flags_are_reported(self):
        result = nominal_manual_gas_case(d0=0.40, return_diagnostics=True)

        self.assertTrue(result["applicability_flags"]["beta_ratio_out_of_range"])
        self.assertTrue(result["applicability_flags"]["orifice_bore_below_minimum"])
        self.assertFalse(result["within_aga3_applicability"])

    def test_low_reynolds_flag_is_exposed(self):
        result = nominal_manual_gas_case(mu=100.0, return_diagnostics=True)

        self.assertTrue(result["applicability_flags"]["pipe_reynolds_number_below_minimum"])
        self.assertTrue(result["coefficient_of_discharge_low_reynolds_flag"])

    def test_pressure_ratio_flag_is_reported(self):
        result = nominal_manual_gas_case(d_p=7000.0, return_diagnostics=True)

        self.assertTrue(result["applicability_flags"]["differential_pressure_ratio_out_of_range"])

    def test_iteration_limit_raises_instead_of_returning_partial_result(self):
        constants = flange_tap_cd_constants(D=102.246, N=25.4, beta=0.496921)

        with self.assertRaisesRegex(AGA3ConvergenceError, "did not converge"):
            flange_tap_cd(constants, F_l=0.00486252, max_iter=1)

    def test_invalid_discharge_coefficient_is_rejected(self):
        with self.assertRaisesRegex(AGA3ConvergenceError, "finite and positive"):
            flange_tap_cd((0.0, 0.0, 0.0, 0.0, 0.0), F_l=0.01)


if __name__ == "__main__":
    unittest.main()
