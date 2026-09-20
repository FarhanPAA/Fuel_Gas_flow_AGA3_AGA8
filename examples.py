# examples.py
# Minimal examples: one common print function + 5 explicit calculate() calls.
# Notes:
# - Use p_unit="psi" or "bar" (code only special-cases "bar"; anything else is treated as psi).
# - Use t_unit="C" or "F" (code checks only "F").
# - Use d_p_unit="mbar" or "inwc" (NOT "inH2O").
# - For t_unit="F": pass alpha_* in per-°F (i.e., alpha_C * 5/9). The function converts to per-°C internally.
# - mu is viscosity in cP.
# - Gas compositions are in percent and should sum to ~100.

from calculation import calculate
from src.constants import MILLIMETRES_PER_INCH

def print_result(title, result_tuple):
    q, zf, zb, k, mm = result_tuple
    print(f"\n[{title}]")
    print(f"  Volumetric flow @ base: {q:.6f}")
    print(f"  z_f (flowing):         {zf:.6f}")
    print(f"  z_b (base):            {zb:.6f}")
    print(f"  k (isentropic):        {k:.6f}")
    print(f"  M (g/mol):             {mm:.6f}")


# ---------------- EXAMPLE 1 ----------------
r1 = calculate(
    p=450.0,            # psig
    t=30.0,             # °C
    d_p=250.0,          # mbar
    p_atm=14.696,       # psia
    p_b=14.696,         # psia base
    p_unit="psi",
    d_p_unit="mbar",
    t_unit="C",
    t_base=15.556,      # 60°F in °C
    pressure_tap="Upstream",
    length_unit="mm",
    d0=247.768, D0=387.535,
    d0_tb=20.0, D0_tb=20.0,
    alpha_d=8.89e-6, alpha_D=6.20e-6,  # per-°C
    mu=0.0103,          # cP
    # Composition (percent)
    N2=0.223, CO2=0.198, C1=96.284, C2=2.210, C3=0.624,
    iC4=0.175, nC4=0.139, iC5=0.064, nC5=0.031,
    nC6=0.025, nC7=0.022, nC8=0.005, nC9=0.000, nC10=0.000,
    H2=0.000, O2=0.000, CO=0.000, H2O=0.000, H2S=0.000, He=0.000, Ar=0.000,
    gas_properties_given=False
    # z_f_manual, z_b_manual, molar_mass_manual, k_manual not used when gas_properties_given=False
)
print_result("Example 1: psi + mbar, °C, Upstream, AGA8, mm", r1)

# ---------------- EXAMPLE 2 ----------------
r2 = calculate(
    p=31.0,             # barg
    t=25.0,             # °C
    d_p=18.0,           # inWC
    p_atm=1.01325,      # bar(a)
    p_b=1.01325,        # bar(a)
    p_unit="bar",
    d_p_unit="inwc",
    t_unit="C",
    t_base=15.556,      # 60°F in °C
    pressure_tap="Downstream",
    length_unit="mm",
    d0=247.768, D0=387.535,
    d0_tb=20.0, D0_tb=20.0,
    alpha_d=8.89e-6, alpha_D=6.20e-6,  # per-°C
    mu=0.0100,          # cP
    # Composition (percent)
    N2=0.223, CO2=0.198, C1=96.284, C2=2.210, C3=0.624,
    iC4=0.175, nC4=0.139, iC5=0.064, nC5=0.031,
    nC6=0.025, nC7=0.022, nC8=0.005, nC9=0.000, nC10=0.000,
    H2=0.000, O2=0.000, CO=0.000, H2O=0.000, H2S=0.000, He=0.000, Ar=0.000,
    gas_properties_given=False
)
print_result("Example 2: bar + inWC, °C, Downstream, AGA8, mm", r2)

# ---------------- EXAMPLE 3 (Manual props) ----------------
r3 = calculate(
    p=500.0,            # psig
    t=35.0,             # °C
    d_p=320.0,          # mbar
    p_atm=14.696,       # psia
    p_b=14.696,         # psia
    p_unit="psi",
    d_p_unit="mbar",
    t_unit="C",
    t_base=15.556,      # 60°F in °C
    pressure_tap="Upstream",
    length_unit="mm",
    d0=247.768, D0=387.535,
    d0_tb=20.0, D0_tb=20.0,
    alpha_d=8.89e-6, alpha_D=6.20e-6,  # per-°C
    mu=0.0105,          # cP
    # Composition (percent) – not used when gas_properties_given=True but included for completeness
    N2=0.223, CO2=0.198, C1=96.284, C2=2.210, C3=0.624,
    iC4=0.175, nC4=0.139, iC5=0.064, nC5=0.031,
    nC6=0.025, nC7=0.022, nC8=0.005, nC9=0.000, nC10=0.000,
    H2=0.000, O2=0.000, CO=0.000, H2O=0.000, H2S=0.000, He=0.000, Ar=0.000,
    gas_properties_given=True,
    z_f_manual=0.93,
    z_b_manual=0.98,
    molar_mass_manual=17.10,  # g/mol
    k_manual=1.28
)
print_result("Example 3: Manual props, psi + mbar, °C, Upstream, mm", r3)

# ---------------- EXAMPLE 4 (Fahrenheit + inches) ----------------
r4 = calculate(
    p=600.0,            # psig
    t=86.0,             # °F
    d_p=120.0,          # inWC
    p_atm=14.696,       # psia
    p_b=14.696,         # psia
    p_unit="psi",
    d_p_unit="inwc",
    t_unit="F",         # triggers internal °F→°C and alpha_* scaling
    t_base=60.0,        # °F
    pressure_tap="Upstream",
    length_unit="in",
    d0=247.768/MILLIMETRES_PER_INCH,
    D0=387.535/MILLIMETRES_PER_INCH,   # inches
    d0_tb=68.0, D0_tb=68.0,             # °F reference temps
    # Pass alpha per-°F here (alpha_C * 5/9). Function multiplies by 9/5 to get per-°C.
    alpha_d=8.89e-6 * (5.0/9.0),
    alpha_D=6.20e-6 * (5.0/9.0),
    mu=0.0103,          # cP
    # Composition (percent)
    N2=0.223, CO2=0.198, C1=96.284, C2=2.210, C3=0.624,
    iC4=0.175, nC4=0.139, iC5=0.064, nC5=0.031,
    nC6=0.025, nC7=0.022, nC8=0.005, nC9=0.000, nC10=0.000,
    H2=0.000, O2=0.000, CO=0.000, H2O=0.000, H2S=0.000, He=0.000, Ar=0.000,
    gas_properties_given=False
)
print_result("Example 4: psi + inWC, °F, Upstream, AGA8, inches", r4)

# ---------------- EXAMPLE 5 (low DP, Downstream) ----------------
r5 = calculate(
    p=20.0,             # barg
    t=20.0,             # °C
    d_p=30.0,           # mbar (low DP)
    p_atm=1.01325,      # bar(a)
    p_b=1.01325,        # bar(a)
    p_unit="bar",
    d_p_unit="mbar",
    t_unit="C",
    t_base=15.556,      # 60°F in °C
    pressure_tap="Downstream",
    length_unit="mm",
    d0=247.768, D0=387.535,
    d0_tb=20.0, D0_tb=20.0,
    alpha_d=8.89e-6, alpha_D=6.20e-6,  # per-°C
    mu=0.0098,          # cP
    # Composition (percent)
    N2=0.223, CO2=0.198, C1=96.284, C2=2.210, C3=0.624,
    iC4=0.175, nC4=0.139, iC5=0.064, nC5=0.031,
    nC6=0.025, nC7=0.022, nC8=0.005, nC9=0.000, nC10=0.000,
    H2=0.000, O2=0.000, CO=0.000, H2O=0.000, H2S=0.000, He=0.000, Ar=0.000,
    gas_properties_given=False
)
print_result("Example 5: bar + mbar, °C, Downstream, low DP, AGA8, mm", r5)
