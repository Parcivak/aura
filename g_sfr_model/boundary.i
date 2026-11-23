[Mesh/fuel_pin]
  type = FileMeshGenerator
  file = ./geometry_in.e
[]

inlet_rate = 12   # [m/s] Axial inlet velocity (adjust to target mass flow rate)
inlet_temp = 650  # [K]   Sodium inlet temperature

[Functions]
  [linear_heat]
    type = PiecewiseLinear
    axis = 2
    data_file = heat_rate.csv
    format = columns
    x_index_in_file = 0
    y_index_in_file = 1
  []

  [volumetric_heat]
    type = ParsedFunction
    symbol_names = 'q r'
    symbol_values = 'linear_heat 0.00227097' # radius in meters
    expression = '(q / (pi * r^2)) * min(t / 0.5, 1.0)'
  []
[]

[FVBCs]
  # --- Sodium Inlet (bottom, z = 0) ---
  [inlet_x]
    type = INSFVInletVelocityBC
    boundary = sodium_inlet
    variable = vel_x
    functor = 0
  []
  [inlet_y]
    type = INSFVInletVelocityBC
    boundary = sodium_inlet
    variable = vel_y
    functor = 0
  []
  [inlet_z]
    type = INSFVInletVelocityBC
    boundary = sodium_inlet
    variable = vel_z
    functor = ${inlet_rate}
  []
  [inlet_temperature]
    type = FVDirichletBC
    boundary = sodium_inlet
    variable = temp_fluid
    value = ${inlet_temp}
  []

  # --- Sodium Outlet (top, z = fuel_height) ---
  # Note: Do not apply velocity FVBCs on the outlet when using INSFVOutletPressureBC
  [outlet_pressure]
    type = INSFVOutletPressureBC
    boundary = sodium_outlet
    variable = pressure
    functor = 0
  []

  # --- Cladding Outer Surface No-Slip Wall ---
  [clad_wall_x]
    type = INSFVNoSlipWallBC
    boundary = clad_sodium_sodium_side
    variable = vel_x
    function = 0
  []
  [clad_wall_y]
    type = INSFVNoSlipWallBC
    boundary = clad_sodium_sodium_side
    variable = vel_y
    function = 0
  []
  [clad_wall_z]
    type = INSFVNoSlipWallBC
    boundary = clad_sodium_sodium_side
    variable = vel_z
    function = 0
  []

  # --- Outer Hexagonal Subchannel Symmetry (external_boundary_id = 100) ---
  [side_x]
    type = INSFVSymmetryVelocityBC
    boundary = 100
    variable = vel_x
    u = vel_x
    v = vel_y
    w = vel_z
    mu = mu
    momentum_component = x
  []
  [side_y]
    type = INSFVSymmetryVelocityBC
    boundary = 100
    variable = vel_y
    u = vel_x
    v = vel_y
    w = vel_z
    mu = mu
    momentum_component = y
  []
  [side_z]
    type = INSFVSymmetryVelocityBC
    boundary = 100
    variable = vel_z
    u = vel_x
    v = vel_y
    w = vel_z
    mu = mu
    momentum_component = z
  []
  [side_pressure]
    type = INSFVSymmetryPressureBC
    boundary = 100
    variable = pressure
  []
[]

[FVInterfaceKernels]
  [fuel_gap]
    type = FVDiffusionInterface
    boundary = fuel_gap_gap_side

    variable1 = temp_fluid
    variable2 = temp_solid

    subdomain1 = gap
    subdomain2 = pellet

    coeff1 = k
    coeff2 = thermal_conductivity_fuel
  []

  [clad_gap]
    type = FVDiffusionInterface
    boundary = gap_clad_gap_side

    variable1 = temp_fluid
    variable2 = temp_solid

    subdomain1 = gap
    subdomain2 = clad

    coeff1 = k
    coeff2 = thermal_conductivity_clad
  []

  [clad_sodium]
    type = FVDiffusionInterface
    boundary = clad_sodium_sodium_side

    variable1 = temp_fluid
    variable2 = temp_solid

    subdomain1 = sodium
    subdomain2 = clad

    coeff1 = k
    coeff2 = thermal_conductivity_clad
  []
[]
