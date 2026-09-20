"""Verify the implementation against all AGA3 Part 4 section 4.3.4 cases."""

from dataclasses import dataclass
from typing import Any

from calculation import calculate


MMSCFD_TO_M3_PER_HOUR = 1_000_000.0 / (35.3147 * 24.0)

TOLERANCES_PPM = {
    "base_volume_flow_m3_h": 50.0,
    "mass_flow_kg_per_hour": 50.0,
    "flowing_orifice_bore_mm": 25.0,
    "velocity_of_approach_ev": 50.0,
    "fluid_expansion_factor_y": 50.0,
    "coefficient_of_discharge_cd": 50.0,
    "flowing_density_kg_m3": 100.0,
}

METRIC_LABELS = {
    "base_volume_flow_m3_h": "Base volume flow (m3/h)",
    "mass_flow_kg_per_hour": "Mass flow (kg/h)",
    "flowing_orifice_bore_mm": "Flowing orifice bore (mm)",
    "velocity_of_approach_ev": "Velocity factor Ev",
    "fluid_expansion_factor_y": "Expansion factor Y",
    "coefficient_of_discharge_cd": "Discharge coefficient Cd",
    "flowing_density_kg_m3": "Flowing density (kg/m3)",
}


@dataclass(frozen=True)
class StandardCase:
    number: int
    description: str
    inputs: dict[str, Any]
    expected: dict[str, float]


@dataclass(frozen=True)
class MetricResult:
    expected: float
    calculated: float
    ppm_deviation: float
    tolerance_ppm: float

    @property
    def passed(self) -> bool:
        return abs(self.ppm_deviation) <= self.tolerance_ppm


@dataclass(frozen=True)
class StandardCaseResult:
    case: StandardCase
    metrics: dict[str, MetricResult]
    density_source: str

    @property
    def passed(self) -> bool:
        return self.density_source == "manual_density" and all(
            metric.passed for metric in self.metrics.values()
        )


def _inputs(
    *,
    temperature_c: float,
    absolute_pressure_bar: float,
    differential_pressure_mbar: float,
    flowing_density_kg_m3: float,
    base_density_kg_m3: float,
    viscosity_cp: float,
    isentropic_exponent: float,
    pipe_diameter_mm: float,
    orifice_diameter_mm: float,
) -> dict[str, Any]:
    atmospheric_pressure_bar = 1.01325
    return {
        "p": absolute_pressure_bar - atmospheric_pressure_bar,
        "t": temperature_c,
        "d_p": differential_pressure_mbar,
        "p_atm": atmospheric_pressure_bar,
        "p_b": 1.01325,
        "p_unit": "bar",
        "d_p_unit": "mbar",
        "t_unit": "C",
        "t_base": 15.0,
        "pressure_tap": "Upstream",
        "length_unit": "mm",
        "d0": orifice_diameter_mm,
        "D0": pipe_diameter_mm,
        "d0_tb": 20.0,
        "D0_tb": 20.0,
        "alpha_d": 1.665e-5,
        "alpha_D": 1.116e-5,
        "mu": viscosity_cp,
        "gas_properties_given": True,
        "manual_property_basis": "density",
        "rho_f_manual": flowing_density_kg_m3,
        "rho_b_manual": base_density_kg_m3,
        "k_manual": isentropic_exponent,
        "return_diagnostics": True,
    }


STANDARD_CASES = (
    StandardCase(
        1,
        "High-beta incompressible flow",
        _inputs(
            temperature_c=98.89,
            absolute_pressure_bar=1.01325,
            differential_pressure_mbar=274.159,
            flowing_density_kg_m3=941.75,
            base_density_kg_m3=999.01,
            viscosity_cp=0.28250,
            isentropic_exponent=-1.0,
            pipe_diameter_mm=49.262,
            orifice_diameter_mm=36.909,
        ),
        {
            "base_volume_flow_m3_h": 20.4856596,
            "mass_flow_kg_per_hour": 20465.3772,
            "flowing_orifice_bore_mm": 36.95748,
            "velocity_of_approach_ev": 1.208835,
            "fluid_expansion_factor_y": 1.0,
            "coefficient_of_discharge_cd": 0.6100592,
            "flowing_density_kg_m3": 941.75,
        },
    ),
    StandardCase(
        2,
        "Low-Reynolds-number incompressible flow",
        _inputs(
            temperature_c=-17.78,
            absolute_pressure_bar=1.01325,
            differential_pressure_mbar=22.380,
            flowing_density_kg_m3=932.26,
            base_density_kg_m3=910.83,
            viscosity_cp=1865.0,
            isentropic_exponent=-1.0,
            pipe_diameter_mm=202.729,
            orifice_diameter_mm=40.481,
        ),
        {
            "base_volume_flow_m3_h": 11.918736,
            "mass_flow_kg_per_hour": 10855.944,
            "flowing_orifice_bore_mm": 40.45554,
            "velocity_of_approach_ev": 1.000795,
            "fluid_expansion_factor_y": 1.0,
            "coefficient_of_discharge_cd": 1.147522,
            "flowing_density_kg_m3": 932.26,
        },
    ),
    StandardCase(
        3,
        "Compressible gas flow",
        _inputs(
            temperature_c=-17.78,
            absolute_pressure_bar=13.7895,
            differential_pressure_mbar=139.877,
            flowing_density_kg_m3=32.783,
            base_density_kg_m3=1.86131,
            viscosity_cp=0.013520,
            isentropic_exponent=1.3198,
            pipe_diameter_mm=102.270,
            orifice_diameter_mm=67.667,
        ),
        {
            "base_volume_flow_m3_h": 4462.9776,
            "mass_flow_kg_per_hour": 8306.9856,
            "flowing_orifice_bore_mm": 67.62443,
            "velocity_of_approach_ev": 1.112137,
            "fluid_expansion_factor_y": 0.9963337,
            "coefficient_of_discharge_cd": 0.6054364,
            "flowing_density_kg_m3": 32.783,
        },
    ),
    StandardCase(
        4,
        "Small-bore gas flow at low differential pressure",
        _inputs(
            temperature_c=-17.78,
            absolute_pressure_bar=13.7895,
            differential_pressure_mbar=5.595,
            flowing_density_kg_m3=32.783,
            base_density_kg_m3=1.86131,
            viscosity_cp=0.013520,
            isentropic_exponent=1.3198,
            pipe_diameter_mm=49.262,
            orifice_diameter_mm=4.961,
        ),
        {
            "base_volume_flow_m3_h": 4.3118244,
            "mass_flow_kg_per_hour": 8.025642,
            "flowing_orifice_bore_mm": 4.957879,
            "velocity_of_approach_ev": 1.000051,
            "fluid_expansion_factor_y": 0.9998739,
            "coefficient_of_discharge_cd": 0.6029605,
            "flowing_density_kg_m3": 32.783,
        },
    ),
    StandardCase(
        5,
        "Small-bore gas flow at high differential pressure",
        _inputs(
            temperature_c=-17.78,
            absolute_pressure_bar=13.7895,
            differential_pressure_mbar=1096.635,
            flowing_density_kg_m3=32.783,
            base_density_kg_m3=1.86131,
            viscosity_cp=0.013520,
            isentropic_exponent=1.3198,
            pipe_diameter_mm=49.262,
            orifice_diameter_mm=4.961,
        ),
        {
            "base_volume_flow_m3_h": 58.494996,
            "mass_flow_kg_per_hour": 108.87732,
            "flowing_orifice_bore_mm": 4.957879,
            "velocity_of_approach_ev": 1.000051,
            "fluid_expansion_factor_y": 0.9752926,
            "coefficient_of_discharge_cd": 0.5989986,
            "flowing_density_kg_m3": 32.783,
        },
    ),
    StandardCase(
        6,
        "Very-low-Reynolds-number incompressible flow",
        _inputs(
            temperature_c=-17.78,
            absolute_pressure_bar=1.01325,
            differential_pressure_mbar=5.595,
            flowing_density_kg_m3=932.26,
            base_density_kg_m3=910.83,
            viscosity_cp=1865.0,
            isentropic_exponent=-1.0,
            pipe_diameter_mm=202.729,
            orifice_diameter_mm=20.241,
        ),
        {
            "base_volume_flow_m3_h": 1.49732244,
            "mass_flow_kg_per_hour": 1363.806,
            "flowing_orifice_bore_mm": 20.22827,
            "velocity_of_approach_ev": 1.000050,
            "fluid_expansion_factor_y": 1.0,
            "coefficient_of_discharge_cd": 1.154086,
            "flowing_density_kg_m3": 932.26,
        },
    ),
)


def ppm_deviation(calculated: float, expected: float) -> float:
    """Return signed parts-per-million deviation from the published value."""
    return (calculated / expected - 1.0) * 1_000_000.0


def evaluate_standard_cases() -> list[StandardCaseResult]:
    """Run all six published cases through the public ``calculate`` API."""
    results = []
    for case in STANDARD_CASES:
        diagnostics = calculate(**case.inputs)
        calculated = {
            "base_volume_flow_m3_h": (
                diagnostics["volumetric_flow"] * MMSCFD_TO_M3_PER_HOUR
            ),
            "mass_flow_kg_per_hour": diagnostics["mass_flow_kg_per_hour"],
            "flowing_orifice_bore_mm": diagnostics["flowing_orifice_bore_mm"],
            "velocity_of_approach_ev": diagnostics["velocity_of_approach_ev"],
            "fluid_expansion_factor_y": diagnostics["fluid_expansion_factor_y"],
            "coefficient_of_discharge_cd": diagnostics[
                "coefficient_of_discharge_cd"
            ],
            "flowing_density_kg_m3": diagnostics["flowing_density_kg_m3"],
        }
        metrics = {
            name: MetricResult(
                expected=case.expected[name],
                calculated=value,
                ppm_deviation=ppm_deviation(value, case.expected[name]),
                tolerance_ppm=TOLERANCES_PPM[name],
            )
            for name, value in calculated.items()
        }
        results.append(
            StandardCaseResult(
                case=case,
                metrics=metrics,
                density_source=diagnostics["density_source"],
            )
        )
    return results


def print_results(results: list[StandardCaseResult]) -> None:
    print("AGA3 Part 4 section 4.3.4 standard verification")
    print("Direct published densities are used; AGA8 is bypassed.\n")
    print(
        "Case  Published Q  Calculated Q    Q ppm  Published mass  "
        "Calculated mass  Mass ppm  Status"
    )
    print(
        "      (m3/h)       (m3/h)                  (kg/h)          "
        "(kg/h)"
    )
    for result in results:
        volume = result.metrics["base_volume_flow_m3_h"]
        mass = result.metrics["mass_flow_kg_per_hour"]
        print(
            f"{result.case.number:>4}  {volume.expected:>11.6f}  "
            f"{volume.calculated:>12.6f}  {volume.ppm_deviation:>7.3f}  "
            f"{mass.expected:>14.6f}  {mass.calculated:>15.6f}  "
            f"{mass.ppm_deviation:>8.3f}  "
            f"{'PASS' if result.passed else 'FAIL'}"
        )

        failed_metrics = [
            (name, metric)
            for name, metric in result.metrics.items()
            if not metric.passed
        ]
        if result.density_source != "manual_density":
            print(f"      FAIL density source: {result.density_source}")
        for name, metric in failed_metrics:
            print(
                f"      FAIL {name}: {metric.ppm_deviation:.3f} ppm "
                f"(limit {metric.tolerance_ppm:.1f} ppm)"
            )

    print("\nDetailed tolerance checks")
    print("Case  Metric                       Expected       Calculated    ppm       Limit  Status")
    for result in results:
        for name, metric in result.metrics.items():
            print(
                f"{result.case.number:>4}  {METRIC_LABELS[name]:<27}  "
                f"{metric.expected:>12.7g}  {metric.calculated:>12.7g}  "
                f"{metric.ppm_deviation:>8.3f}  {metric.tolerance_ppm:>8.1f}  "
                f"{'PASS' if metric.passed else 'FAIL'}"
            )

    passed_count = sum(result.passed for result in results)
    print(f"\nOverall: {passed_count}/{len(results)} cases passed")


def main() -> int:
    results = evaluate_standard_cases()
    print_results(results)
    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
