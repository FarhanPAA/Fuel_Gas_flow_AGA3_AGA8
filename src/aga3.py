import math

PSI_TO_BAR = 0.06894757293178308
# AGA3 Part 4 Table 4-5: N3 = 27.7070 inH2O at 60 degF per psi.
INWC_TO_MBAR = 1000.0 * PSI_TO_BAR / 27.7070
R=0.0831451                 # ideal gas constant (bar, kg, m, K)

AGA3_BETA_MIN = 0.10
AGA3_BETA_MAX = 0.75
AGA3_MIN_ORIFICE_BORE_MM = 11.4  # 0.45 inch, rounded as stated in AGA3 Part 1
AGA3_MIN_PIPE_REYNOLDS = 4000.0
AGA3_MAX_DP_PRESSURE_RATIO = 0.20


class AGA3ConvergenceError(RuntimeError):
    """Raised when the AGA3 discharge-coefficient iteration is invalid or fails to converge."""


def flange_tap_cd_constants(D: float, N: float, beta: float):
    """
    Calculate the five AGA-3 discharge-coefficient constants (Cd0 … Cd4)
    for a flange-tapped orifice plate.

    Parameters
    ----------
    D    : float – internal pipe diameter at flowing temperature
    N    : float – N4 conversion constant (same length units as D)
    beta : float – bore ratio d/D

    Returns
    -------
    dict with keys 'Cd0' … 'Cd4'
    """

    # ----- fixed AGA-3 constants -----
    A0, A1, A2, A3, A4, A5, A6 = 0.5961, 0.0291, -0.229, 0.003, 2.8, 0.000511, 0.021
    S1, S2, S3, S4, S5, S6, S7, S8 = 0.0049, 0.0433, 0.0712, -0.1145, -0.2300, -0.0116, -0.5200, -0.1400

    # ----- step-by-step evaluation -----
    L1 = L2 = N / D                               # 1. tap positions
    M2 = 2.0 * L2 / (1.0 - beta)                  # 2. dam height

    Tu = (S2 + S3 * math.exp(-8.5 * L1) +
          S4 * math.exp(-6.0 * L2)) * beta**4 / (1.0 - beta**4)  # 3. upstream corr.

    Td = S6 * (M2 + S7 * M2**1.3) * beta**1.1     # 4. downstream corr.

    # 5. small-pipe correction
    Ts = 0.0 if D > A4 * N else A3 * (1.0 - beta) * (A4 - D / N)

    # 6. discharge-coefficient constants (Re = 4000)
    Cd0 = A0 + A1 * beta**2 + A2 * beta**8 + Tu + Td + Ts
    Cd1 = A5 * beta**0.7 * 250.0**0.7
    Cd2 = A6 * beta**4 * 250.0**0.35
    Cd3 = S1 * beta**(4 + 0.8) * 4.75**0.8 * 250.0**0.35
    Cd4 = (S5 * Tu + S8 * Td) * beta**0.8 * 4.75**0.8

    return (Cd0, Cd1, Cd2, Cd3, Cd4)

def flange_tap_cd(cd_all, F_l, tol=5e-6, max_iter=50):
  XC = 1.142139337256165
  A  = 4.343524261523267
  B  = 3.764387693320165

  if not math.isfinite(F_l) or F_l <= 0.0:
      raise AGA3ConvergenceError(
          f"Iteration flow factor must be finite and positive; received {F_l!r}."
      )
  if not math.isfinite(tol) or tol <= 0.0:
      raise ValueError("Convergence tolerance must be finite and positive.")
  if not isinstance(max_iter, int) or max_iter < 1:
      raise ValueError("Maximum iteration count must be a positive integer.")

  Cd0, Cd1, Cd2, Cd3, Cd4 = cd_all

  Cd = Cd0
  if not math.isfinite(Cd) or Cd <= 0.0:
      raise AGA3ConvergenceError(
          f"Initial discharge coefficient must be finite and positive; received {Cd!r}."
      )

  for iterations in range(1, max_iter + 1):
      # Step 2 – dimensionless flow parameter X ------------------------------
      X = F_l / Cd

      # Step 3 – correlation Fc and derivative Dc ---------------------------
      if X < XC:  # low‑Re branch (4‑40 / 4‑41)
          Fc = (
              Cd0
              + (Cd1 * X ** 0.35 + Cd2 + Cd3 * X ** 0.8) * X ** 0.35
              + Cd4 * X ** 0.8
          )
          Dc = (
              (0.7 * Cd1 * X ** 0.35 + 0.35 * Cd2 + 1.15 * Cd3 * X ** 0.8)
              * X ** 0.35
              + 0.8 * Cd4 * X ** 0.8
          )
      else:       # high‑Re branch (4‑42 / 4‑43)
          Fc = (
              Cd0
              + Cd1 * X ** 0.7
              + (Cd2 + Cd3 * X ** 0.8) * (A - B / X)
              + Cd4 * X ** 0.8
          )
          Dc = (
              0.7 * Cd1 * X ** 0.7
              + (Cd2 + Cd3 * X ** 0.8) * B / X
              + 0.8 * Cd3 * (A - B / X) * X ** 0.8
              + 0.8 * Cd4 * X ** 0.8
          )

      # Step 4 – Newton update (4‑44) ---------------------------------------
      denominator = 1.0 + Dc / Cd
      if not all(math.isfinite(value) for value in (X, Fc, Dc, denominator)) or denominator == 0.0:
          raise AGA3ConvergenceError(
              f"Discharge-coefficient iteration produced an invalid intermediate value "
              f"at iteration {iterations}."
          )

      delta_Cd = (Cd - Fc) / denominator
      next_Cd = Cd - delta_Cd
      if not math.isfinite(next_Cd) or next_Cd <= 0.0:
          raise AGA3ConvergenceError(
              f"Discharge coefficient became invalid at iteration {iterations}: {next_Cd!r}."
          )
      Cd = next_Cd

      if abs(delta_Cd) < tol:
          X = F_l / Cd
          Cd_f = X > 1.0  # True → X > 1 → Re < 4,000
          return Cd, Cd_f, True, iterations, X

  raise AGA3ConvergenceError(
      f"Discharge coefficient did not converge to |delta Cd| < {tol:g} "
      f"within {max_iter} iterations; last |delta Cd| was {abs(delta_Cd):.6g}."
  )

def aga3_calculate(
    p,                           # in psig
    t,                           # flow temperature in Celcius
    d_p,                         # differential pressure, in mbar depending on d_p_unit
    Z_f,                         # compressibility at flowing
    Z_b,                         # compressibility at base
    M_gas,                       # molecular weight of gas
    d0,                          # orifice dia at reference temp (length_unit)
    D0,                          # pipe dia at reference temp (length_unit)
    p_atm,                       # Atmospheric Pressure in psia
    d_p_unit,                    # 'mbar', 'inwc'
    p_b,                         # base pressure in psia
    t_b,                         # base temperature in Celcius
    d0_tb,                       # orifice reference temp in degree celcius
    D0_tb,                       # pipe reference temp in degree celcius
    alpha_d,                     # temp coeff of orifice in degree celcius
    alpha_D,                     # temp coeff of pipe in degree celcius
    k,                           # isentropic exponent
    mu,                          # viscosity in cP
    length_unit                  # "mm", "in"
):       
  '''
  The Formulas are implemented assuming pressure to be in absolute bar, temperature in Kelvin,
  differential pressure in mbar and density in kg/m3. So units are first converted.
  Different Unit Constants are used to handle unit mismatch
  '''  
  p = (p + p_atm)*PSI_TO_BAR
  p_b =  p_b*PSI_TO_BAR
    
  if d_p_unit == "mbar":
    d_p = d_p
  elif d_p_unit == "inwc":
    d_p = d_p*INWC_TO_MBAR
  else:
    print("Differential Pressure Unit not recognized")

  p_u = p

  t = t+273.15
  t_b = t_b+273.15
  d0_tb = d0_tb+273.15
  D0_tb = D0_tb+273.15

  if length_unit == "in":
    d0 = d0*25.4
    D0 = D0*25.4
  elif length_unit == "mm":
    d0 = d0
    D0 = D0
  else:
    print("Length Unit not recognized")

  # Density at flowing condition (kg/m3)
  rho_f = (p_u*M_gas)/(Z_f*R*t)
  rho_b = (p_b*M_gas)/(Z_b*R*t_b)

  d = d0*(1+alpha_d*(t-d0_tb))
  D = D0*(1+alpha_D*(t-D0_tb))
  beta = d/D

  E_v = 1/(1-beta**4)**(1/2)

  x = d_p/(p_u*1000) # d_p in mbar and p_u in bar
  if k>0:
    Y_p = (0.41+0.35*beta**4)/k
    Y = 1-Y_p*x
  else:
    Y = 1

  F_le = (4000*0.1*D*mu)/(E_v*Y*d**2)
  F_lp = (2*rho_f*d_p)**(1/2)

  if F_le< (1000*F_lp):
    F_l = F_le/F_lp
  else:
    F_l = 1000

  Cd_all = flange_tap_cd_constants(D, 25.4, beta)
  Cd, Cd_f, cd_converged, cd_iterations, X = flange_tap_cd(Cd_all, F_l)
  F_mass = (3.1415926/4)*0.03600*E_v*d**2
  qm= F_mass*Cd*Y*F_lp
  qb = F_mass*Cd*Y*F_lp/rho_b

  qb_MMSCFD = qb*35.3147*24/10**6 # Converted to MMSCFD Unit

  pipe_reynolds_number = 4000.0 / X
  applicability_flags = {
      'beta_ratio_out_of_range': not (AGA3_BETA_MIN <= beta <= AGA3_BETA_MAX),
      'orifice_bore_below_minimum': not (d > AGA3_MIN_ORIFICE_BORE_MM),
      'pipe_reynolds_number_below_minimum': pipe_reynolds_number < AGA3_MIN_PIPE_REYNOLDS,
      'differential_pressure_ratio_out_of_range': not (0.0 < x < AGA3_MAX_DP_PRESSURE_RATIO),
      'coefficient_of_discharge_low_reynolds': Cd_f,
      'coefficient_of_discharge_not_converged': not cd_converged,
  }
  applicability_messages = []
  if applicability_flags['beta_ratio_out_of_range']:
      applicability_messages.append(
          f"Beta ratio {beta:.6g} is outside the AGA3 range "
          f"{AGA3_BETA_MIN:.2f} to {AGA3_BETA_MAX:.2f}."
      )
  if applicability_flags['orifice_bore_below_minimum']:
      applicability_messages.append(
          f"Flowing orifice bore {d:.6g} mm must be greater than "
          f"{AGA3_MIN_ORIFICE_BORE_MM:.1f} mm (0.45 inch)."
      )
  if applicability_flags['pipe_reynolds_number_below_minimum']:
      applicability_messages.append(
          f"Pipe Reynolds number {pipe_reynolds_number:.6g} is below 4,000; "
          "the coefficient of discharge is outside its supported range."
      )
  if applicability_flags['differential_pressure_ratio_out_of_range']:
      applicability_messages.append(
          f"Differential-pressure ratio x={x:.6g} must be greater than 0 and less than 0.20."
      )
  if applicability_flags['coefficient_of_discharge_not_converged']:
      applicability_messages.append(
          f"Coefficient-of-discharge iteration did not converge within {cd_iterations} iterations."
      )

  dict = {
      'volumetric_flow': qb_MMSCFD,
      'beta': beta,
      'velocity_of_approach_ev': E_v,
      'fluid_expansion_factor_y': Y,
      'coefficient_of_discharge_cd': Cd,
      'coefficient_of_discharge_low_reynolds_flag': Cd_f,
      'coefficient_of_discharge_converged': cd_converged,
      'coefficient_of_discharge_iterations': cd_iterations,
      'pipe_reynolds_number': pipe_reynolds_number,
      'differential_pressure_ratio': x,
      'flowing_orifice_bore_mm': d,
      'flowing_meter_tube_diameter_mm': D,
      'applicability_flags': applicability_flags,
      'applicability_messages': applicability_messages,
      'within_aga3_applicability': not any(applicability_flags.values()),
  }

  return dict
