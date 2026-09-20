import streamlit as st
from calculation import calculate
from src.aga3 import AGA3ConvergenceError
from src.constants import (
    ABSOLUTE_ZERO_CELSIUS,
    ABSOLUTE_ZERO_FAHRENHEIT,
    AGA8_COMPOSITION_TOLERANCE_MOL_PERCENT,
    AGA8_COMPOSITION_TOTAL_MOL_PERCENT,
)

# ---------- Page setup (no emoji icon) ----------
st.set_page_config(page_title="AGA3 Fuel Gas Calculator", layout="wide")
st.title("Fuel Gas Consumption Calculation with AGA3")

# Safer spacing at the very top to avoid title clipping
st.markdown(
    """
    <style>
      .block-container {padding-top: 5rem; padding-bottom: 2.0rem;}
      div[data-testid="stMetricValue"] > div {font-weight: 700;}
      div[data-testid="stMetricLabel"] > p {font-size: 0.95rem;}
      .stAlert {margin-top: 0.2rem; margin-bottom: 0.6rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Constants ----------
STEP = 1e-6
FMT  = "%.6f"

# ---------- SECTION: Measurement Units ----------
with st.container(border=True):
    st.markdown("### Select Measurement Units")
    col1, col2 = st.columns(2)
    with col1:
        pressure_unit = st.selectbox(
            label="Select pressure unit",
            options=["psi", "bar"],
            help="Choose the unit for gauge, atmospheric, and base pressures."
        )
        temperature_unit = st.selectbox(
            label="Select temperature unit",
            options=["Fahrenheit", "Celsius"],
            help="All temperature fields below will use this unit."
        )
        if temperature_unit == "Fahrenheit":
            t_unit = "F"
        elif temperature_unit == "Celsius":
            t_unit = "C"
    with col2:
        dp_unit = st.selectbox(
            label="Select differential pressure unit",
            options=["mbar", "inwc"],
            help="DP transmitter output unit."
        )
        length_unit = st.selectbox(
            label="Enter length unit",
            options=["mm", "in"],
            help="Units for the reference-temperature orifice bore and meter-tube diameters."
        )

# ---------- SECTION: Gas Properties Mode ----------
with st.container(border=True):   
    st.markdown("### Gas Properties Mode")
    col1, col2 = st.columns(2)
    with col1:
        gas_properties_method = st.selectbox(
            label="Enter Gas Properties Calculation Method",
            options=["AGA8", "Manual"],
            help="AGA8 derives gas properties from composition. Manual mode accepts either Z with molar mass or direct densities."
        )
    gas_properties_given = (gas_properties_method == "Manual")
    with col2:
        if gas_properties_given:
            manual_property_method = st.selectbox(
                label="Select manual gas-property basis",
                options=["Compressibility and molar mass", "Flowing and base densities"],
                help="Choose one basis only. Direct density mode does not use Z or molar mass."
            )
            manual_property_basis = (
                "density" if manual_property_method == "Flowing and base densities" else "z_molar_mass"
            )

# ---------- FORM ----------
with st.form("main_form", clear_on_submit=False):
    # ----- Sensor inputs -----
    with st.container(border=True):
        st.markdown("### Enter Sensor Inputs")
        col1, col2 = st.columns(2)
        with col1:
            flow_pressure = st.number_input(
                f"Enter flowing gauge pressure in {pressure_unit}",
                step=STEP, format=FMT,
                help="Gauge pressure from PT (positive)."
            )
            pressure_tap = st.selectbox(
                label="Enter pressure sensor tapping position",
                options=["Upstream", "Downstream"],
                help="AGA-3 allows either; ensure it matches your DP impulse line scheme."
            )
            atm_pressure = st.number_input(
                f"Enter atmospheric pressure in {pressure_unit}",
                step=STEP, format=FMT,
                help="Local atmospheric pressure (absolute), e.g., 14.7 psia."
            )
        with col2:
            flow_temperature = st.number_input(
                f"Enter temperature in degree {temperature_unit}",
                step=STEP, format=FMT,
                help="Flowing temperature measured by RTD/thermowell."
            )
            differential_pressure = st.number_input(
                f"Enter differential Pressure in {dp_unit}",
                step=STEP, format=FMT,
                help="DP across orifice from DP transmitter."
            )

    # ----- Base conditions -----
    with st.container(border=True):
        st.markdown("### Enter Base Conditions")
        col1, col2 = st.columns(2)
        with col1:
            base_pressure = st.number_input(
                f"Enter absolute base pressure in {pressure_unit}",
                step=STEP, format=FMT,
                help="Typical: 14.696 psia (or 1.01325 bar)."
            )
        with col2:
            base_temp = st.number_input(
                f"Ente base temperature in {temperature_unit}",
                step=STEP, format=FMT,
                help="Common: 60°F or 15°C, depending on standard."
            )

    # ----- Orifice/Pipe geometry -----
    with st.container(border=True):
        st.markdown("### Enter Reference Geometry and Thermal Expansion")
        col1, col2 = st.columns(2)
        with col1:
            orifice_dia = st.number_input(
                f"Orifice bore diameter at reference temperature ({length_unit})",
                step=STEP, format=FMT,
                help="Enter the measured or certified bore before correction to flowing temperature."
            )
            pipe_dia = st.number_input(
                f"Meter-tube internal diameter at reference temperature ({length_unit})",
                step=STEP, format=FMT,
                help="Enter the measured or certified tube ID before correction to flowing temperature."
            )
            orifice_ref_temp = st.number_input(
                f"Orifice-bore reference temperature (°{temperature_unit})",
                step=STEP, format=FMT,
                help="Temperature at which the entered orifice bore was measured or certified."
            )
        with col2:
            pipe_ref_temp = st.number_input(
                f"Meter-tube diameter reference temperature (°{temperature_unit})",
                step=STEP, format=FMT,
                help="Temperature at which the entered meter-tube ID was measured or specified."
            )
            orifice_exp_coeff = st.number_input(
                f"Enter expansion coefficient for orifice per degree {temperature_unit}",
                step=1e-8, format="%.8f",
                help="Linear thermal expansion coefficient (e.g., ~1.1e-5/°C for SS)."
            )
            pipe_exp_coeff = st.number_input(
                f"Enter expansion coefficient for pipe per degree {temperature_unit}",
                step=1e-8, format="%.8f",
                help="Linear thermal expansion coefficient of pipe material."
            )

    # ----- Viscosity -----
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            mu = st.number_input(
                "Enter viscosity of gas in cP",
                step=STEP, format=FMT,
                help="Dynamic viscosity at flowing conditions (centipoise)."
            )
        with col2:
            st.write("")  # placeholder to keep two-column layout

    # ----- Gas properties OR composition -----
    if gas_properties_given:
        with st.container(border=True):
            st.markdown("### Enter Gas Properties (Manual)")
            col1, col2 = st.columns(2)
            with col1:
                k_manual = st.number_input(
                    "Isentropic expansion coefficient (k)",
                    step=STEP, format=FMT,
                    help="Often ~1.20–1.35 for natural gas."
                )
                if manual_property_basis == "z_molar_mass":
                    z_f_manual = st.number_input(
                        "Compressibility factor at flowing (Z_f)",
                        step=STEP, format=FMT
                    )
                else:
                    rho_f_manual = st.number_input(
                        "Flowing gas density (kg/m³)",
                        step=STEP, format=FMT,
                        help="Gas density at the flowing pressure and temperature."
                    )
            with col2:
                if manual_property_basis == "z_molar_mass":
                    z_b_manual = st.number_input(
                        "Compressibility factor at base (Z_b)",
                        step=STEP, format=FMT
                    )
                    molar_mass_manual = st.number_input(
                        "Molar mass of gas (g/mol)",
                        step=STEP, format=FMT
                    )
                else:
                    rho_b_manual = st.number_input(
                        "Base gas density (kg/m³)",
                        step=STEP, format=FMT,
                        help="Gas density at the selected base pressure and temperature."
                    )
    else:
        with st.container(border=True):
            st.markdown("### Enter Gas Composition in percentage")
            c1 = st.columns(4)
            N2  = c1[0].number_input("Nitrogen (N₂)",        min_value=0.0, max_value=100.0, value=0.0,  step=STEP, format=FMT)
            CO2 = c1[1].number_input("Carbon Dioxide (CO₂)", min_value=0.0, max_value=100.0, value=0.0,  step=STEP, format=FMT)
            C1  = c1[2].number_input("Methane (C₁)",         min_value=0.0, max_value=100.0, value=100.0, step=STEP, format=FMT)
            C2  = c1[3].number_input("Ethane (C₂)",          min_value=0.0, max_value=100.0, value=0.0,  step=STEP, format=FMT)

            c2 = st.columns(4)
            C3  = c2[0].number_input("Propane (C₃)",         min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            iC4 = c2[1].number_input("iso-Butane (i-C₄)",    min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            nC4 = c2[2].number_input("n-Butane (n-C₄)",      min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            iC5 = c2[3].number_input("iso-Pentane (i-C₅)",   min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)

            c3 = st.columns(4)
            nC5 = c3[0].number_input("n-Pentane (n-C₅)",     min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            nC6 = c3[1].number_input("n-Hexane (n-C₆)",      min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            nC7 = c3[2].number_input("n-Heptane (n-C₇)",     min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            nC8 = c3[3].number_input("n-Octane (n-C₈)",      min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)

            # --- Added species ---
            c4 = st.columns(4)
            H2  = c4[0].number_input("Hydrogen (H₂)",        min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            H2O = c4[1].number_input("Water (H₂O)",          min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            O2  = c4[2].number_input("Oxygen (O₂)",          min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            CO  = c4[3].number_input("Carbon Monoxide (CO)", min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)

            c5 = st.columns(4)
            H2S = c5[0].number_input("Hydrogen Sulfide (H₂S)", min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            He  = c5[1].number_input("Helium (He)",            min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            Ar  = c5[2].number_input("Argon (Ar)",             min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            c5[3].write("")  # keep 4-column alignment

            # --- nC9, nC10 added here ---
            c6 = st.columns(4)
            nC9  = c6[0].number_input("n-Nonane (n-C₉)",   min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            nC10 = c6[1].number_input("n-Decane (n-C₁₀)",  min_value=0.0, max_value=100.0, value=0.0, step=STEP, format=FMT)
            c6[2].write("")  # keep alignment
            c6[3].write("")

            total_pct = (
                N2 + CO2 + C1 + C2 + C3 + iC4 + nC4 + iC5 + nC5 + nC6 + nC7 + nC8
                + H2 + H2O + O2 + CO + H2S + He + Ar + nC9 + nC10
            )
            st.caption(f"Composition total: {total_pct:.6f} %")

            if (
                abs(total_pct - AGA8_COMPOSITION_TOTAL_MOL_PERCENT)
                > AGA8_COMPOSITION_TOLERANCE_MOL_PERCENT
            ):
                st.error("Composition should sum to 100%. Adjust the inputs.")

    # ----- Submit -----
    submitted = st.form_submit_button("Calculate")

    # ---------- VALIDATION ----------
    if submitted:
        errors = []

        # absolute zero per selected unit
        abs_zero = (
            ABSOLUTE_ZERO_FAHRENHEIT
            if t_unit == "F"
            else ABSOLUTE_ZERO_CELSIUS
        )
        temp_fields = [
            ("Flow temperature", flow_temperature),
            ("Base temperature", base_temp),
            ("Orifice reference temperature", orifice_ref_temp),
            ("Pipe reference temperature", pipe_ref_temp),
        ]
        for label, val in temp_fields:
            if val <= abs_zero:
                errors.append(f"{label} must be above absolute zero ({abs_zero}°{t_unit}).")

        # pressures / dp
        if flow_pressure < 0:
            errors.append("Flowing gauge pressure cannot be negative.")
        if atm_pressure <= 0:
            errors.append("Atmospheric pressure must be positive.")
        if base_pressure <= 0:
            errors.append("Absolute base pressure must be > 0.")
        if differential_pressure <= 0:
            errors.append("Differential pressure must be > 0.")

        # diameters and beta
        beta_for_warning = None
        if orifice_dia <= 0 or pipe_dia <= 0:
            errors.append("Reference-temperature orifice and meter-tube diameters must be > 0.")
        else:
            if pipe_dia <= orifice_dia:
                errors.append("Reference-temperature meter-tube diameter must exceed the orifice bore (β < 1).")
            else:
                beta_for_warning = orifice_dia / pipe_dia
                if not (0.10 <= beta_for_warning <= 0.75):
                    st.warning(
                        f"Preliminary β ratio is {beta_for_warning:.4f}. "
                        "The AGA3 range is 0.10–0.75; the final check uses thermally corrected diameters."
                    )

        # thermal expansion coefficients
        if orifice_exp_coeff <= 0:
            errors.append("Orifice expansion coefficient must be positive.")
        elif not (1e-7 <= orifice_exp_coeff <= 1e-4):
            st.warning(
                f"Orifice expansion coefficient looks unusual ({orifice_exp_coeff:g} per °{t_unit}). "
                "Typical metals ~1e-6–1e-5/°C."
            )

        if pipe_exp_coeff <= 0:
            errors.append("Pipe expansion coefficient must be positive.")
        elif not (1e-7 <= pipe_exp_coeff <= 1e-4):
            st.warning(
                f"Pipe expansion coefficient looks unusual ({pipe_exp_coeff:g} per °{t_unit}). "
                "Typical metals ~1e-6–1e-5/°C."
            )

        # viscosity
        if mu <= 0:
            errors.append("Viscosity must be > 0 cP.")

        # manual gas properties sanity
        if gas_properties_given:
            if k_manual <= 1.0 or k_manual > 2.0:
                st.warning("Isentropic exponent k is usually ~1.20–1.35 for natural gas. Your value is unusual.")
            if manual_property_basis == "z_molar_mass":
                if not (0 < z_f_manual <= 2):
                    errors.append("Compressibility factor at flowing must be between 0 and 2 (non-zero).")
                if not (0 < z_b_manual <= 2):
                    errors.append("Compressibility factor at base must be between 0 and 2 (non-zero).")
                if molar_mass_manual <= 0:
                    errors.append("Molar mass must be > 0 g/mol.")
            else:
                if rho_f_manual <= 0:
                    errors.append("Flowing gas density must be > 0 kg/m³.")
                if rho_b_manual <= 0:
                    errors.append("Base gas density must be > 0 kg/m³.")
        else:
            # enforce composition sum (blocks calc)
            if (
                abs(total_pct - AGA8_COMPOSITION_TOTAL_MOL_PERCENT)
                > AGA8_COMPOSITION_TOLERANCE_MOL_PERCENT
            ):
                errors.append("Composition must sum to 100.000%. Adjust the inputs.")

        if errors:
            st.error("Please fix the following before calculation:")
            for e in errors:
                st.write(f"• {e}")
            st.stop()

        # ---------- CALCULATION (logic unchanged) ----------
        try:
            with st.spinner("Computing AGA-3 flow ..."):
                if gas_properties_given:
                    manual_inputs = {
                        "manual_property_basis": manual_property_basis,
                        "k_manual": k_manual,
                    }
                    if manual_property_basis == "z_molar_mass":
                        manual_inputs.update({
                            "z_f_manual": z_f_manual,
                            "z_b_manual": z_b_manual,
                            "molar_mass_manual": molar_mass_manual,
                        })
                    else:
                        manual_inputs.update({
                            "rho_f_manual": rho_f_manual,
                            "rho_b_manual": rho_b_manual,
                        })

                    calculation_result = calculate(
                        p=flow_pressure, t=flow_temperature, d_p=differential_pressure, p_atm=atm_pressure,
                        p_unit=pressure_unit, p_b=base_pressure, d_p_unit=dp_unit, t_unit=t_unit, t_base=base_temp,
                        pressure_tap=pressure_tap, length_unit=length_unit, d0=orifice_dia, D0=pipe_dia,
                        d0_tb=orifice_ref_temp, D0_tb=pipe_ref_temp, alpha_d=orifice_exp_coeff, alpha_D=pipe_exp_coeff,
                        gas_properties_given=True, mu=mu, return_diagnostics=True, **manual_inputs
                    )
                else:
                    calculation_result = calculate(
                        p=flow_pressure, t=flow_temperature, d_p=differential_pressure, p_atm=atm_pressure,
                        p_unit=pressure_unit, p_b=base_pressure, d_p_unit=dp_unit, t_unit=t_unit, t_base=base_temp,
                        pressure_tap=pressure_tap, length_unit=length_unit, d0=orifice_dia, D0=pipe_dia,
                        d0_tb=orifice_ref_temp, D0_tb=pipe_ref_temp, alpha_d=orifice_exp_coeff, alpha_D=pipe_exp_coeff,
                        N2=N2, CO2=CO2, C1=C1, C2=C2, C3=C3, iC4=iC4, nC4=nC4, iC5=iC5, nC5=nC5,
                        nC6=nC6, nC7=nC7, nC8=nC8, nC9=nC9, nC10=nC10, H2=H2, O2=O2, CO=CO, H2O=H2O,
                        H2S=H2S, He=He, Ar=Ar, mu=mu, gas_properties_given=False,
                        return_diagnostics=True
                    )

            gas_flow = calculation_result['base_volume_flow_mmscfd']
            m3_per_hour = calculation_result['base_volume_flow_m3_per_hour']
            z_f = calculation_result['z_f']
            z_b = calculation_result['z_b']
            k = calculation_result['k']
            molar_mass = calculation_result['molar_mass']
                    
            # ---------- RESULTS ----------
            with st.container(border=True):
                st.subheader("Results")

                # Row 1
                r1c1, r1c2 = st.columns(2)
                with r1c1:
                    st.metric("Fuel Gas Flow", f"{gas_flow:.6f} MMSCF/D")
                with r1c2:
                    st.metric("Fuel Gas Flow", f"{m3_per_hour:,.2f} m³/h")

                if gas_properties_given == False:
                # Row 2
                    r2c1, r2c2 = st.columns(2)
                    with r2c1:
                        st.metric("Z (flow)", f"{z_f:.6f}")
                    with r2c2:
                        st.metric("Z (base)", f"{z_b:.6f}")

                    # Row 3
                    r3c1, r3c2 = st.columns(2)
                    with r3c1:
                        st.metric("k (isentropic exp.)", f"{k:.6f}")
                    with r3c2:
                        st.metric("Molar mass", f"{molar_mass:.5f} g/mol")

                if calculation_result['within_aga3_applicability']:
                    st.success("AGA3 applicability checks passed for the calculated operating point.")
                else:
                    st.warning("Result is outside one or more AGA3 applicability limits:")
                    for message in calculation_result['applicability_messages']:
                        st.write(f"• {message}")

                with st.expander("AGA3 calculation diagnostics"):
                    st.write(f"β ratio: {calculation_result['beta']:.6f}")
                    st.write(f"Pipe Reynolds number: {calculation_result['pipe_reynolds_number']:,.0f}")
                    st.write(
                        "Differential-pressure ratio "
                        f"x: {calculation_result['differential_pressure_ratio']:.6f}"
                    )
                    st.write(
                        "Flowing orifice bore: "
                        f"{calculation_result['flowing_orifice_bore_mm']:.6f} mm"
                    )
                    st.write(
                        "Flowing meter-tube diameter: "
                        f"{calculation_result['flowing_meter_tube_diameter_mm']:.6f} mm"
                    )
                    st.write(
                        "Flowing gas density: "
                        f"{calculation_result['flowing_density_kg_m3']:.6f} kg/m³"
                    )
                    st.write(
                        "Base gas density: "
                        f"{calculation_result['base_density_kg_m3']:.6f} kg/m³"
                    )
                    st.write(
                        "Discharge coefficient: "
                        f"{calculation_result['coefficient_of_discharge_cd']:.8f}"
                    )
                    st.write(
                        "Discharge-coefficient iteration: "
                        f"{calculation_result['coefficient_of_discharge_iterations']} iteration(s), "
                        f"{'converged' if calculation_result['coefficient_of_discharge_converged'] else 'not converged'}"
                    )
                    st.caption(
                        "The AGA3 nominal pipe-size requirement cannot be verified from internal diameter alone. "
                        "Confirm that the installation is nominal 2-inch Schedule 160 or larger."
                    )


        except AGA3ConvergenceError as e:
            st.error(f"AGA3 calculation stopped: {e}")
            st.info("No flow result was produced. Check the inputs and operating range.")
        except Exception as e:
            st.exception(e)
            st.error("Calculation failed. Re-check unit selections, ranges, and consistency of inputs.")
