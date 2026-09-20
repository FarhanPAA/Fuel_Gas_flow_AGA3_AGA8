import unittest

from streamlit.testing.v1 import AppTest


class GeometryInputLabelTests(unittest.TestCase):
    def test_diameter_inputs_explicitly_request_reference_values(self):
        app = AppTest.from_file("web.py")
        app.run(timeout=30)

        self.assertFalse(app.exception)
        labels = {widget.label for widget in app.number_input}
        self.assertIn("Orifice bore diameter at reference temperature (mm)", labels)
        self.assertIn("Meter-tube internal diameter at reference temperature (mm)", labels)
        self.assertIn("Orifice-bore reference temperature (°Fahrenheit)", labels)
        self.assertIn("Meter-tube diameter reference temperature (°Fahrenheit)", labels)

    def test_manual_density_basis_is_mutually_exclusive_with_z_inputs(self):
        app = AppTest.from_file("web.py")
        app.run(timeout=30)

        gas_method = next(
            widget
            for widget in app.selectbox
            if widget.label == "Enter Gas Properties Calculation Method"
        )
        gas_method.set_value("Manual")
        app.run(timeout=30)

        property_basis = next(
            widget
            for widget in app.selectbox
            if widget.label == "Select manual gas-property basis"
        )
        property_basis.set_value("Flowing and base densities")
        app.run(timeout=30)

        self.assertFalse(app.exception)
        labels = {widget.label for widget in app.number_input}
        self.assertIn("Flowing gas density (kg/m³)", labels)
        self.assertIn("Base gas density (kg/m³)", labels)
        self.assertNotIn("Compressibility factor at flowing (Z_f)", labels)
        self.assertNotIn("Compressibility factor at base (Z_b)", labels)
        self.assertNotIn("Molar mass of gas (g/mol)", labels)


if __name__ == "__main__":
    unittest.main()
