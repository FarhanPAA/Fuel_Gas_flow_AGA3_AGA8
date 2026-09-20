import unittest

from standard_tests import STANDARD_CASES, TOLERANCES_PPM, evaluate_standard_cases


class StandardExamplesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = evaluate_standard_cases()

    def test_all_six_published_cases_are_included(self):
        self.assertEqual([case.number for case in STANDARD_CASES], [1, 2, 3, 4, 5, 6])
        self.assertEqual(len(self.results), 6)

    def test_published_tolerances_and_aga8_bypass(self):
        for result in self.results:
            with self.subTest(case=result.case.number, check="density source"):
                self.assertEqual(result.density_source, "manual_density")

            for name, metric in result.metrics.items():
                with self.subTest(case=result.case.number, metric=name):
                    self.assertEqual(metric.tolerance_ppm, TOLERANCES_PPM[name])
                    self.assertLessEqual(
                        abs(metric.ppm_deviation),
                        metric.tolerance_ppm,
                        msg=(
                            f"case {result.case.number} {name}: "
                            f"{metric.ppm_deviation:.3f} ppm exceeds "
                            f"{metric.tolerance_ppm:.1f} ppm"
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
