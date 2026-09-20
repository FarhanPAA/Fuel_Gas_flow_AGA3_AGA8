import builtins
import importlib
import unittest
from unittest.mock import patch

import calculation as calculation_module
from calculation import calculate
from src.aga3 import AGA3ConvergenceError, flange_tap_cd, flange_tap_cd_constants
from src.constants import M3_PER_HOUR_TO_MMSCFD


def nominal_manual_gas_inputs(**overrides):
    """Return inputs for a synthetic, in-range gas case."""
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
    return inputs


def nominal_manual_gas_case(**overrides):
    """Calculate a synthetic, in-range gas case for diagnostic behavior tests."""
    return calculate(**nominal_manual_gas_inputs(**overrides))


class Aga3ApplicabilityTests(unittest.TestCase):
    def test_manual_modes_do_not_import_aga8(self):
        real_import = builtins.__import__

        def reject_aga8(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "src.aga8":
                raise AssertionError("manual property modes must not import AGA8")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=reject_aga8):
            reloaded = importlib.reload(calculation_module)
            z_result = reloaded.calculate(
                **nominal_manual_gas_inputs(return_diagnostics=True)
            )
            density_result = reloaded.calculate(
                **nominal_manual_gas_inputs(
                    manual_property_basis="density",
                    rho_f_manual=35.0,
                    rho_b_manual=0.75,
                    return_diagnostics=True,
                )
            )

        self.assertEqual(z_result["manual_property_basis"], "z_molar_mass")
        self.assertEqual(density_result["manual_property_basis"], "density")

    def test_invalid_enumerated_inputs_are_rejected(self):
        invalid_inputs = (
            ({"p_unit": "kPa"}, "p_unit"),
            ({"d_p_unit": "Pa"}, "d_p_unit"),
            ({"t_unit": "K"}, "t_unit"),
            ({"pressure_tap": "Middle"}, "pressure_tap"),
            ({"length_unit": "cm"}, "length_unit"),
            ({"manual_property_basis": "both"}, "manual_property_basis"),
        )
        for overrides, message in invalid_inputs:
            with self.subTest(overrides=overrides):
                with self.assertRaisesRegex(ValueError, message):
                    nominal_manual_gas_case(**overrides)

    def test_nonphysical_inputs_are_rejected(self):
        invalid_inputs = (
            ({"d_p": 0.0}, "d_p"),
            ({"d0": 0.0}, "d0"),
            ({"d0": 400.0}, "smaller than D0"),
            ({"mu": 0.0}, "mu"),
            ({"p_atm": 0.0}, "p_atm"),
            ({"p_b": 0.0}, "p_b"),
            ({"t": -273.15}, "absolute zero"),
            ({"p": -20.0}, "absolute pressure"),
            ({"alpha_d": float("nan")}, "alpha_d"),
            ({"z_f_manual": 0.0}, "z_f_manual"),
            ({"k_manual": 0.0}, "k_manual"),
        )
        for overrides, message in invalid_inputs:
            with self.subTest(overrides=overrides):
                with self.assertRaisesRegex(ValueError, message):
                    nominal_manual_gas_case(**overrides)

    def test_invalid_aga8_compositions_are_rejected_before_calculation(self):
        invalid_compositions = (
            ({"C1": 101.0, "N2": -1.0}, "N2.*nonnegative"),
            ({"C1": float("nan")}, "C1.*finite"),
            ({"C1": 99.0}, "must total 100 mol%"),
        )
        for composition, message in invalid_compositions:
            with self.subTest(composition=composition):
                with self.assertRaisesRegex(ValueError, message):
                    nominal_manual_gas_case(
                        gas_properties_given=False,
                        **composition,
                    )

    def test_structured_flow_units_are_explicit_and_legacy_alias_is_preserved(self):
        result = nominal_manual_gas_case(return_diagnostics=True)

        self.assertEqual(
            result["volumetric_flow"],
            result["base_volume_flow_mmscfd"],
        )
        self.assertGreater(result["base_volume_flow_m3_per_hour"], 0.0)
        self.assertAlmostEqual(
            result["base_volume_flow_m3_per_hour"] * M3_PER_HOUR_TO_MMSCFD,
            result["base_volume_flow_mmscfd"],
            places=12,
        )

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

    def test_direct_density_basis_matches_equivalent_z_and_molar_mass(self):
        derived = nominal_manual_gas_case(return_diagnostics=True)
        direct = nominal_manual_gas_case(
            manual_property_basis="density",
            rho_f_manual=derived["flowing_density_kg_m3"],
            rho_b_manual=derived["base_density_kg_m3"],
            z_f_manual=0.1,
            z_b_manual=0.1,
            molar_mass_manual=1.0,
            return_diagnostics=True,
        )

        self.assertEqual(direct["density_source"], "manual_density")
        self.assertEqual(direct["manual_property_basis"], "density")
        self.assertIsNone(direct["z_f"])
        self.assertIsNone(direct["z_b"])
        self.assertIsNone(direct["molar_mass"])
        self.assertAlmostEqual(direct["volumetric_flow"], derived["volumetric_flow"], places=12)

    def test_direct_density_basis_requires_both_positive_densities(self):
        with self.assertRaisesRegex(ValueError, "Flowing and base density"):
            nominal_manual_gas_case(
                manual_property_basis="density",
                rho_f_manual=10.0,
                rho_b_manual=None,
            )

        with self.assertRaisesRegex(ValueError, "rho_b_manual"):
            nominal_manual_gas_case(
                manual_property_basis="density",
                rho_f_manual=10.0,
                rho_b_manual=0.0,
            )

    def test_iteration_limit_raises_instead_of_returning_partial_result(self):
        constants = flange_tap_cd_constants(D=102.246, N=25.4, beta=0.496921)

        with self.assertRaisesRegex(AGA3ConvergenceError, "did not converge"):
            flange_tap_cd(constants, F_l=0.00486252, max_iter=1)

    def test_invalid_discharge_coefficient_is_rejected(self):
        with self.assertRaisesRegex(AGA3ConvergenceError, "finite and positive"):
            flange_tap_cd((0.0, 0.0, 0.0, 0.0, 0.0), F_l=0.01)


if __name__ == "__main__":
    unittest.main()
