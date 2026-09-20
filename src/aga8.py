import math

import pvtlib

from src.constants import (
    AGA8_COMPOSITION_TOLERANCE_MOL_PERCENT,
    AGA8_COMPOSITION_TOTAL_MOL_PERCENT,
    PSI_TO_BAR,
)


def validate_composition(composition):
    """Validate AGA8 component values expressed in mol percent."""
    for component, value in composition.items():
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(
                f"Gas composition component {component} must be a finite number; "
                f"received {value!r}."
            )
        if value < 0.0:
            raise ValueError(
                f"Gas composition component {component} must be nonnegative; "
                f"received {value!r}."
            )

    total = math.fsum(composition.values())
    if (
        abs(total - AGA8_COMPOSITION_TOTAL_MOL_PERCENT)
        > AGA8_COMPOSITION_TOLERANCE_MOL_PERCENT
    ):
        raise ValueError(
            "Gas composition must total 100 mol% within +/-0.001 mol%; "
            f"received {total:.9g} mol%."
        )
    return total

def calculate_gas_properties(
    p_psig,         # Upstream Pressure in PSIG
    t,              # Flow temperature in Celcius
    N2, CO2, C1, C2, C3, iC4, nC4, iC5, nC5, nC6, nC7, nC8, nC9, nC10, H2, O2, CO, H2O, H2S, He, Ar,
    p_base,         # Base Pressure in PSIA
    p_atm,          # Atmospheric Pressure in PSIA
    t_base,         # Base Temperature in Celcius
):
    '''
    calculate_from_PT expcects pressure to be in PSIA and Temperature in degree Celsius,
    gas composition in percentage
    '''
    p = (p_psig+p_atm)*PSI_TO_BAR
    p_base = p_base*PSI_TO_BAR 
    
    composition = {
        'N2': N2, 'CO2': CO2, 'C1': C1, 'C2': C2, 'C3': C3,
        'iC4': iC4, 'nC4': nC4, 'iC5': iC5, 'nC5': nC5,
        'nC6': nC6, 'nC7': nC7, 'nC8': nC8,
        'nC9': nC9, 'nC10': nC10,
        'H2': H2, 'O2': O2, 'CO': CO,
        'H2O': H2O, 'H2S': H2S,
        'He': He, 'Ar': Ar,
    }
    validate_composition(composition)
    calculator = pvtlib.AGA8('DETAIL')
    
    gas_properties_flow = calculator.calculate_from_PT(
        composition=composition,
        pressure= p,
        temperature= t
    )
    
    gas_properties_base = calculator.calculate_from_PT(
        composition=composition,
        pressure=p_base,
        temperature=t_base
    )
    
    gas_properties = {
        'z_f' : gas_properties_flow['z'],
        'z_b' : gas_properties_base['z'],
        'mm'  : gas_properties_base['mm'],
        'k'   : gas_properties_flow['kappa']
    }
    
    return gas_properties
