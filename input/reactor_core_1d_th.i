# 1D axial thermal-hydraulics model of an equivalent reactor core
#
# Purpose:
#   - One aggregate 1D helium coolant channel represents parallel core channels.
#   - One axisymmetric fuel/gap/cladding heat structure represents n_fuel_rods rods.
#   - MCNP axial heating shape is read from mcnp_axial_shape.csv as a function of z.
#   - TotalPower supplies absolute core power in W; the shape function is normalized
#     internally by HeatSourceFromTotalPower.
#
# IMPORTANT:
#   This is a starting template, not a validated reactor calculation. Replace every
#   marked equivalent-core / material / operating-condition placeholder. Keep all
#   lengths, areas, perimeters, pressure, temperature, power, and CSV z-values in SI
#   units (m, m^2, m, Pa, K, W). The 1D TH model does not directly reuse the detailed
#   Reactor-module mesh; derive equivalent channel/rod parameters from that geometry.

#######################################
# User-editable model parameters
#######################################

# Axial domain. If your reactor mesh uses 300.0 for a 300 cm active height, enter 3.0 m here.
core_length = 3.0              # m -- active heated length; update CSV z coordinates if changed
n_axial = 30                   # axial finite-volume / heat-structure intervals

# Equivalent-channel hydraulic parameters for the FULL core flow (not one individual subchannel).
core_flow_area = 0.50           # m^2 -- TODO: total coolant flow area from reactor geometry
core_wetted_perimeter = 60.0    # m per m axial length -- TODO: total wetted perimeter for equivalent channel
core_hydraulic_diameter = '${fparse 4.0 * core_flow_area / core_wetted_perimeter}'
core_friction_factor = 0.02     # Darcy friction factor placeholder; replace with a correlation/value

# Fuel-rod bundle representation. All dimensions are radial thicknesses in metres.
n_fuel_rods = 1000              # TODO: number of fuel rods represented by this homogenized structure
fuel_radius = 0.0040             # m -- TODO: actual fuel pellet radius
fuel_gap_thickness = 0.00010     # m -- TODO: effective gap thickness
clad_thickness = 0.00060         # m -- TODO: actual cladding thickness
rod_outer_radius = '${fparse fuel_radius + fuel_gap_thickness + clad_thickness}'
core_heated_perimeter = '${fparse 2.0 * pi * rod_outer_radius * n_fuel_rods}' # m per m axial length

# Operating conditions / source strength placeholders.
core_power = 1.0e8              # W -- TODO: total fission power represented by the model
m_dot_core = 100.0              # kg/s -- TODO: total core helium mass flow
T_in = 500.0                    # K -- TODO: inlet coolant temperature
p_out = 7.0e6                   # Pa -- TODO: outlet pressure
initial_velocity = 20.0         # m/s -- initial guess; should be consistent with mass flow / flow area
T_solid_initial = 700.0         # K -- initial fuel/gap/cladding temperature
wall_htc = 1.0e4                # W/(m^2 K) -- placeholder constant heat-transfer coefficient

#######################################
# Spatial functions
#######################################
[Functions]
  # Reads axial positions [m] and relative MCNP axial heating values from CSV.
  # The CSV must span the active length (or use endpoint values at z=0 and z=core_length).
  # Values need only be relative; the absolute heating is set by core_power above.
  [mcnp_axial_shape]
    type = PiecewiseLinear
    data_file = mcnp_axial_shape.csv
    format = rows
    x_index_in_file = 0
    y_index_in_file = 1
    axis = z
    extrap = false
  []
[]

#######################################
# Initial conditions / THM defaults
#######################################
[GlobalParams]
  initial_p = ${p_out}
  initial_vel = ${initial_velocity}
  initial_T = ${T_in}
  gravity_vector = '0 0 -9.81'
  closures = thm_closures
  fp = helium
  scaling_factor_1phase = '1 1e-2 1e-4'
[]

#######################################
# Fluid and solid properties
#######################################
[FluidProperties]
  # Simplified ideal-gas helium placeholder. Replace/validate against properties over
  # your actual pressure/temperature range before using results quantitatively.
  [helium]
    type = IdealGasFluidProperties
    molar_mass = 4.0026e-3
    gamma = 1.66
    k = 0.2556
    mu = 3.22639e-5
  []
[]

[Closures]
  [thm_closures]
    type = Closures1PhaseTHM
  []
[]

[SolidProperties]
  # Constant values are placeholders. Replace with temperature-dependent properties.
  [uo2]
    type = ThermalFunctionSolidProperties
    rho = 10970.0       # kg/m^3, approximate placeholder
    cp = 300.0          # J/(kg K), placeholder
    k = 3.0             # W/(m K), placeholder
  []

  # The gap is approximated as an effective radial layer. Its conductivity should
  # represent the gap gas, pressure, contact, and any other applicable gap conductance.
  [gap_effective]
    type = ThermalFunctionSolidProperties
    rho = 1.0            # kg/m^3; artificial low thermal mass for the effective gap layer
    cp = 1000.0           # J/(kg K), placeholder
    k = 0.2               # W/(m K), placeholder effective conductivity
  []

  [cladding]
    type = ThermalFunctionSolidProperties
    rho = 6500.0         # kg/m^3, approximate placeholder
    cp = 330.0            # J/(kg K), placeholder
    k = 16.0              # W/(m K), placeholder
  []
[]

#######################################
# 1D components
#######################################
[Components]
  [total_power]
    type = TotalPower
    power = ${core_power}
  []

  # One equivalent channel represents all parallel coolant passages in the core.
  [core_channel]
    type = FlowChannel1Phase
    position = '0 0 0'
    orientation = '0 0 1'
    length = ${core_length}
    n_elems = ${n_axial}
    A = ${core_flow_area}
    D_h = ${core_hydraulic_diameter}
    f = ${core_friction_factor}
  []

  # Composite radial fuel/gap/cladding structure; num_rods scales it to the full
  # group of rods. This assumes rods share one axial power shape and similar conditions.
  [fuel_rods]
    type = HeatStructureCylindrical
    num_rods = ${n_fuel_rods}
    position = '0 0 0'
    orientation = '0 0 1'
    length = ${core_length}
    n_elems = ${n_axial}
    names = 'fuel gap clad'
    widths = '${fuel_radius} ${fuel_gap_thickness} ${clad_thickness}'
    n_part_elems = '4 1 2'
    solid_properties = 'uo2 gap_effective cladding'
    solid_properties_T_ref = '1000 700 700'
    initial_T = ${T_solid_initial}
  []

  # Apply the MCNP-derived AXIAL SHAPE in the fuel region. This object distributes
  # core_power over the fuel volume and normalizes the spatial shape internally.
  [fission_heating]
    type = HeatSourceFromTotalPower
    hs = fuel_rods
    regions = fuel
    power = total_power
    power_shape_function = mcnp_axial_shape
    power_fraction = 1.0
  []

  # Couple the outside of the cladding to the aggregate coolant channel.
  # P_hf is the TOTAL heated perimeter for all represented rods per axial length.
  [fuel_to_coolant]
    type = HeatTransferFromHeatStructure1Phase
    hs = fuel_rods
    hs_side = outer
    flow_channel = core_channel
    P_hf = ${core_heated_perimeter}
    Hw = ${wall_htc}
  []

  [inlet]
    type = InletMassFlowRateTemperature1Phase
    input = 'core_channel:in'
    m_dot = ${m_dot_core}
    T = ${T_in}
  []

  [outlet]
    type = Outlet1Phase
    input = 'core_channel:out'
    p = ${p_out}
  []
[]

#######################################
# Monitoring outputs
#######################################
[Postprocessors]
  [coolant_inlet_temperature]
    type = SideAverageValue
    boundary = 'core_channel:in'
    variable = T
    execute_on = 'initial timestep_end'
  []

  [coolant_outlet_temperature]
    type = SideAverageValue
    boundary = 'core_channel:out'
    variable = T
    execute_on = 'initial timestep_end'
  []

  [coolant_inlet_pressure]
    type = SideAverageValue
    boundary = 'core_channel:in'
    variable = p
    execute_on = 'initial timestep_end'
  []

  [coolant_outlet_pressure]
    type = SideAverageValue
    boundary = 'core_channel:out'
    variable = p
    execute_on = 'initial timestep_end'
  []

  [coolant_pressure_drop]
    type = DifferencePostprocessor
    value1 = coolant_inlet_pressure
    value2 = coolant_outlet_pressure
    execute_on = 'initial timestep_end'
  []

  # Add ADHeatRateConvection1Phase later if you want a separate integral of
  # the convective heat rate; its P_hf input in some MOOSE versions expects
  # a variable name rather than the scalar perimeter accepted by the component.
[]

#######################################
# Solver and output
#######################################
[Preconditioning]
  [SMP_PJFNK]
    type = SMP
    full = true
  []
[]

[Executioner]
  type = Transient
  scheme = bdf2
  start_time = 0.0
  dt = 0.1
  num_steps = 100

  solve_type = PJFNK
  line_search = basic
  nl_rel_tol = 1e-6
  nl_abs_tol = 1e-6
  nl_max_its = 30
  l_tol = 1e-4
  l_max_its = 100
  abort_on_solve_fail = true
[]

[Outputs]
  [exodus]
    type = Exodus
  []
  [csv]
    type = CSV
  []
[]
