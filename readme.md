# AGA3 Flow (with optional AGA8 properties)

Returns base-condition volumetric flow via **AGA3** detail method.

If `gas_properties_given = False`, gas properties (`z_f`, `z_b`, `molar_mass`, `k`) are computed from composition via **AGA8**.

---
Python Version Used: 3.13.6

## Function Summary

- **Input:** operating conditions, units, meter geometry/expansion data, optional gas composition, optional manual gas-property overrides  
- **Output:** `(volumetric_flow, z_f, z_b, k, molar_mass)`  
- **Extras:** Handles unit conversions (psi↔bar, °C↔°F, mbar↔inWC) and downstream-tap logic.

---

## Inputs

### Operating & Units

- `p` *(float)* — **Flowing gauge pressure** in `p_unit`.
- `t` *(float)* — **Flowing temperature** in `t_unit`.
- `d_p` *(float)* — **Orifice differential pressure** in `d_p_unit`.
- `p_atm` *(float)* — **Atmospheric pressure (absolute)** in `p_unit`.
- `p_b` *(float)* — **Base pressure (absolute)** in `p_unit`.
- `t_base` *(float)* — **Base temperature** in `t_unit`.
- `p_unit` *('psi' | 'bar')* — Unit for `p`, `p_atm`, `p_b`.
- `t_unit` *('C' | 'F')* — Unit for `t` and `t_base`.
- `d_p_unit` *('mbar' | 'inwc')* — Unit for `d_p`.
- `pressure_tap` *('Upstream' | 'Downstream')* — If `'Downstream'`, upstream static is inferred as **`p + d_p`** (with proper unit conversion).

### Meter Geometry & Thermal Expansion

- `length_unit` *('mm' | 'in')* — Length unit for diameters.
- `d0`, `D0` *(float)* — **Orifice** & **pipe** diameters at their reference temperatures (`d0_tb`, `D0_tb`, in `t_unit`).
- `d0_tb`, `D0_tb` *(float)* — **Reference temperatures** (match `t_unit`) for `d0`, `D0`.
- `alpha_d`, `alpha_D` *(float)* — **Linear thermal expansion coefficients** in inverse degrees matching `t_unit`: use 1/°C with `t_unit = 'C'` and 1/°F with `t_unit = 'F'`. Fahrenheit coefficients are converted internally to 1/°C.
- `mu` *(float)* — **Dynamic gas viscosity** at flowing conditions in **centipoise (cP)**.

### Gas Composition (mol %)

Unspecified components default to **0**:

`N2, CO2, C1, C2, C3, iC4, nC4, iC5, nC5, nC6, nC7, nC8, nC9, nC10, H2, O2, CO, H2O, H2S, He, Ar`

### Manual Override for Gas Properties

- `gas_properties_given` *(bool, default `False`)* — If **True**, bypass AGA8 and use the basis selected by `manual_property_basis`.
- `manual_property_basis` *('z_molar_mass' | 'density')* — Select one mutually exclusive manual basis. The default preserves the existing Z-and-molar-mass behavior.
- `z_f_manual`, `z_b_manual` *(float)* — Compressibility at flowing/base when `manual_property_basis = 'z_molar_mass'`.
- `molar_mass_manual` *(float, g/mol)* — Mixture molar mass when `manual_property_basis = 'z_molar_mass'`.
- `rho_f_manual`, `rho_b_manual` *(float, kg/m³)* — Flowing and base density when `manual_property_basis = 'density'`; both values are required and Z/molar mass are not used.
- `k_manual` *(float)* — Isentropic exponent (`k = C_p/C_v`).

---

## Outputs

Returns a **5-tuple**:

1. `volumetric_flow` — Base-condition flow rate (unit per your `aga3_calculate` implementation).
2. `z_f` — Compressibility at **flowing** conditions, or `None` with the direct-density basis.
3. `z_b` — Compressibility at **base** conditions, or `None` with the direct-density basis.
4. `k` — Isentropic exponent at **flowing** conditions.
5. `molar_mass` — Mixture **g/mol**, or `None` with the direct-density basis.

With `return_diagnostics = True`, the result also includes `flowing_density_kg_m3`, `base_density_kg_m3`, and `density_source` for every property basis.

---

## Notes (Concise)

- **Pressures**
  - `p` is **gauge pressure**.
  - `p_atm` and `p_b` are **absolute pressure**.
  - If `p_unit = 'bar'`, inputs are internally converted to **psi** as needed.

- **Temperatures & Expansion**
  - If `t_unit = 'F'`, temperatures convert to **°C** internally.
  - `alpha_d`/`alpha_D` are assumed per **°C/°F**, according to chosen temperature unit; if inputs are in °F, coefficients are converted automatically.

- **Tap Location**
  - With `pressure_tap = 'Downstream'`, the upstream static used for AGA8/AGA3 is **`p + d_p`** (after unit alignment).

---

## Disclaimer

This documentation and any associated calculations are provided **as-is** for engineering reference. **Outputs are not guaranteed**; validate results against official AGA3/AGA8 standards, calibrated instruments, and site-specific procedures before use in operations or billing.

## Streamlit Demo App

A minimal **Streamlit** UI has been built **on top of this `calculate(...)` function** to help test inputs and visualize results. You can wire your fields (pressure/temperature/DP/geometry/composition) to the function and display the returned tuple.

**Live demo:** [aga3calculation.streamlit.app](https://aga3calculation.streamlit.app/)

> **Heads-up:** On Streamlit Community Cloud the app may be sleeping after inactivity.
> The first load can take ~30–60 seconds to start.

**Quick start:**

```bash
pip install -r requirements.txt  # ensure streamlit and dependencies are installed
streamlit run web.py             # app.py calls calculate(...) under the hood
```

## Minimal Usage Sketch (Python)

```python
vol_flow, zf, zb, k, M = calculate(
    p=..., t=..., d_p=..., p_atm=..., p_b=...,
    p_unit='psi', t_unit='C', d_p_unit='mbar',
    t_base=..., pressure_tap='Upstream',
    length_unit='mm',
    d0=..., D0=..., d0_tb=..., D0_tb=...,
    alpha_d=..., alpha_D=...,
    mu=...,
    # Option A: auto AGA8 from composition
    N2=..., CO2=..., C1=..., C2=..., C3=..., iC4=..., nC4=...,  # etc.
    gas_properties_given=False,
    # Option B: manual Z and molar mass
    # gas_properties_given=True,
    # manual_property_basis='z_molar_mass',
    # z_f_manual=..., z_b_manual=..., molar_mass_manual=..., k_manual=...
    # Option C: manual flowing and base densities
    # gas_properties_given=True,
    # manual_property_basis='density',
    # rho_f_manual=..., rho_b_manual=..., k_manual=...
)
```
