import math

from src.aga3 import aga3_calculate
from src.constants import (
    ABSOLUTE_ZERO_CELSIUS,
    ABSOLUTE_ZERO_FAHRENHEIT,
    INWC_TO_MBAR,
    PSI_TO_BAR,
)


def _require_choice(name, value, allowed):
    if value not in allowed:
        choices = ", ".join(repr(choice) for choice in allowed)
        raise ValueError(f"{name} must be one of: {choices}; received {value!r}.")


def _require_finite(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number; received {value!r}.")


def _require_positive(name, value):
    _require_finite(name, value)
    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero; received {value!r}.")


def _validate_temperature(name, value, unit):
    _require_finite(name, value)
    absolute_zero = (
        ABSOLUTE_ZERO_CELSIUS if unit == "C" else ABSOLUTE_ZERO_FAHRENHEIT
    )
    if value <= absolute_zero:
        raise ValueError(
            f"{name} must be above absolute zero ({absolute_zero} deg{unit}); "
            f"received {value!r}."
        )

def calculate(
    p,                                  # Gauge Pressure of flowing gas 
    t,                                  # Flow Temperature
    d_p,                                # Differential Pressure
    p_atm,                              # Atmospheric Pressure
    p_b,                                # Base pressure for Volumetric Measurement
    p_unit,                             # Units of Pressure ('psig', 'barg')
    d_p_unit,                           # Differential Pressure Unit ('mbar', 'inwc')
    t_unit,                             # Temperature Unit (Celsius, Fahrenheit)
    t_base,                             # Base Temperature for Volumetric Measurement
    pressure_tap,                       # Pressure sensor tapping position relative to orifice ('Upstream', 'Downstream')
    length_unit,                        # Units of length ('in', 'mm') for orifice and pipe             
    d0,                                 # Diameter of Orifice at reference temperature
    D0,                                 # Diameter of pipe at reference temperature
    d0_tb,                              # Reference Temperature for orifice diameter
    D0_tb,                              # Reference Temperature for pipe diameter
    alpha_d,                            # Temperature expansion coefficient for orifice
    alpha_D,                            # Temperature expansion coefficient for pipe
    mu,                                 # Viscosity of Gas
                                        # Gas Composition
    N2 =0, CO2 = 0, C1 = 0, C2 = 0, C3 = 0 , iC4= 0 , nC4 = 0 , iC5 = 0 , nC5 = 0 , nC6 = 0 , nC7= 0 , nC8= 0, nC9= 0, nC10= 0, H2 = 0, O2 = 0, CO = 0, H2O = 0, H2S = 0, He = 0, Ar = 0, 
                                        ##############
    gas_properties_given = False,       # Manual Entry of Gas Properties if True
    z_f_manual = 0.99,                  # Manual entry for gas compressibility at flowing condition
    z_b_manual = 0.995,                 # Manual entry of gas compressibility at base condition
    molar_mass_manual = 16.83,          # Manual entry of molar mass at g/mol
    k_manual =1.3,                      # Manual entry of isentropic expansion coefficient
    return_diagnostics = False,         # Return structured AGA3 results instead of the legacy tuple
    manual_property_basis = "z_molar_mass", # "z_molar_mass" or "density"
    rho_f_manual = None,                # Manual flowing density in kg/m3
    rho_b_manual = None                 # Manual base density in kg/m3
):
    _require_choice("p_unit", p_unit, ("psi", "bar"))
    _require_choice("d_p_unit", d_p_unit, ("mbar", "inwc"))
    _require_choice("t_unit", t_unit, ("C", "F"))
    _require_choice("pressure_tap", pressure_tap, ("Upstream", "Downstream"))
    _require_choice("length_unit", length_unit, ("mm", "in"))
    if not isinstance(gas_properties_given, bool):
        raise ValueError("gas_properties_given must be a boolean.")
    if not isinstance(return_diagnostics, bool):
        raise ValueError("return_diagnostics must be a boolean.")

    _require_finite("p", p)
    _require_positive("p_atm", p_atm)
    _require_positive("p_b", p_b)
    _require_positive("d_p", d_p)
    _require_positive("d0", d0)
    _require_positive("D0", D0)
    if d0 >= D0:
        raise ValueError("d0 must be smaller than D0.")
    _require_positive("mu", mu)
    _require_finite("alpha_d", alpha_d)
    _require_finite("alpha_D", alpha_D)
    _validate_temperature("t", t, t_unit)
    _validate_temperature("t_base", t_base, t_unit)
    _validate_temperature("d0_tb", d0_tb, t_unit)
    _validate_temperature("D0_tb", D0_tb, t_unit)

    if gas_properties_given:
        _require_choice(
            "manual_property_basis",
            manual_property_basis,
            ("z_molar_mass", "density"),
        )
        _require_finite("k_manual", k_manual)
        if k_manual == 0.0:
            raise ValueError(
                "k_manual must be positive for a gas or negative for an "
                "incompressible standard case."
            )
        if manual_property_basis == "z_molar_mass":
            _require_positive("z_f_manual", z_f_manual)
            _require_positive("z_b_manual", z_b_manual)
            _require_positive("molar_mass_manual", molar_mass_manual)
        else:
            if rho_f_manual is None or rho_b_manual is None:
                raise ValueError(
                    "Flowing and base density must be provided for manual density mode."
                )
            _require_positive("rho_f_manual", rho_f_manual)
            _require_positive("rho_b_manual", rho_b_manual)

    if p_unit == 'bar':
        p = p/PSI_TO_BAR
        p_b = p_b/PSI_TO_BAR
        p_atm = p_atm/PSI_TO_BAR
        
    if t_unit == 'F':
        t = (t-32)*5/9
        t_base = (t_base-32)*5/9
        d0_tb = (d0_tb-32)*5/9
        D0_tb = (D0_tb-32)*5/9
        alpha_D = alpha_D*9/5
        alpha_d = alpha_d*9/5
        
    if pressure_tap == 'Downstream':
        if d_p_unit == 'mbar':
            p_u = p + d_p/(1000*PSI_TO_BAR)
        elif d_p_unit == 'inwc':
            p_u = p + (d_p*INWC_TO_MBAR)/(1000*PSI_TO_BAR)
    if pressure_tap == 'Upstream':
        p_u = p

    if p_u + p_atm <= 0.0:
        raise ValueError(
            "Flowing absolute pressure must be greater than zero after applying "
            "atmospheric pressure and tap correction."
        )

    
    rho_f_input = None
    rho_b_input = None

    if gas_properties_given == False:
        # Keep AGA8 optional for both manual-property modes. Import it only when
        # composition-derived properties are actually requested.
        from src.aga8 import calculate_gas_properties

        properties = calculate_gas_properties (p_psig=p_u, p_atm= p_atm,p_base=p_b, t=t, t_base=t_base, N2=N2, CO2=CO2, C1=C1, C2=C2,C3=C3,iC4=iC4, nC4=nC4,iC5=iC5, nC5=nC5, nC6=nC6, nC7=nC7, nC8=nC8, nC9 = nC9, nC10= nC10, H2 = H2, O2 = O2, CO = CO, H2O = H2O, H2S = H2S, He = He, Ar= Ar)
        z_f= properties['z_f']
        z_b= properties['z_b']
        molar_mass = properties['mm']
        k= properties['k']
    else:
        k= k_manual
        if manual_property_basis == "z_molar_mass":
            z_f = z_f_manual
            z_b = z_b_manual
            molar_mass = molar_mass_manual
        elif manual_property_basis == "density":
            z_f = None
            z_b = None
            molar_mass = None
            rho_f_input = rho_f_manual
            rho_b_input = rho_b_manual
    
    result = aga3_calculate(p=p_u,t=t,d_p=d_p, p_atm=p_atm , p_b=p_b ,d_p_unit=d_p_unit, t_b=t_base,  d0=d0, D0=D0, d0_tb = d0_tb, D0_tb = D0_tb, alpha_d = alpha_d, alpha_D = alpha_D ,Z_f=z_f,Z_b=z_b, M_gas=molar_mass, k=k, mu=mu, length_unit=length_unit, rho_f_manual=rho_f_input, rho_b_manual=rho_b_input)
    
    if return_diagnostics:
        return {
            **result,
            'z_f': z_f,
            'z_b': z_b,
            'k': k,
            'molar_mass': molar_mass,
            'manual_property_basis': manual_property_basis if gas_properties_given else 'aga8',
        }

    return result['volumetric_flow'], z_f, z_b, k, molar_mass
