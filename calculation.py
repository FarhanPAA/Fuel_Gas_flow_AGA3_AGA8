from src.aga8 import calculate_gas_properties
from src.aga3 import aga3_calculate
PSI_TO_BAR = 0.06894757293178308
# AGA3 Part 4 Table 4-5: N3 = 27.7070 inH2O at 60 degF per psi.
INWC_TO_MBAR = 1000.0 * PSI_TO_BAR / 27.7070

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
    return_diagnostics = False          # Return structured AGA3 results instead of the legacy tuple
):
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

    
    if gas_properties_given == False:
        
        properties = calculate_gas_properties (p_psig=p_u, p_atm= p_atm,p_base=p_b, t=t, t_base=t_base, N2=N2, CO2=CO2, C1=C1, C2=C2,C3=C3,iC4=iC4, nC4=nC4,iC5=iC5, nC5=nC5, nC6=nC6, nC7=nC7, nC8=nC8, nC9 = nC9, nC10= nC10, H2 = H2, O2 = O2, CO = CO, H2O = H2O, H2S = H2S, He = He, Ar= Ar)
        z_f= properties['z_f']
        z_b= properties['z_b']
        molar_mass = properties['mm']
        k= properties['k']
    else:
        z_f = z_f_manual
        z_b = z_b_manual
        molar_mass = molar_mass_manual
        k= k_manual
    
    result = aga3_calculate(p=p_u,t=t,d_p=d_p, p_atm=p_atm , p_b=p_b ,d_p_unit=d_p_unit, t_b=t_base,  d0=d0, D0=D0, d0_tb = d0_tb, D0_tb = D0_tb, alpha_d = alpha_d, alpha_D = alpha_D ,Z_f=z_f,Z_b=z_b, M_gas=molar_mass, k=k, mu=mu, length_unit=length_unit)
    
    if return_diagnostics:
        return {
            **result,
            'z_f': z_f,
            'z_b': z_b,
            'k': k,
            'molar_mass': molar_mass,
        }

    return result['volumetric_flow'], z_f, z_b, k, molar_mass
