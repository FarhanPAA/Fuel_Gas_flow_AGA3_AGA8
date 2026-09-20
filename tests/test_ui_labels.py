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


if __name__ == "__main__":
    unittest.main()
