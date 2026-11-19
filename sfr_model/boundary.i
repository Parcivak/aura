[Mesh/fuel_pin]
  type = FileMeshGenerator
  file = ./geometry_in.e
[]

inlet_rate = 15         #m/s
outlet_pressure = 75000  #In pa
inlet_temp = 600        #K

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
    expression = 'q / (pi * r^2)'
  []
[]

[FVBCs]
  [inlet_vel_x]
    type = INSFVInletVelocityBC
    boundary = sodium_inlet
    variable = vel_x
    functor = 0
  []
  [inlet_vel_y]
    type = INSFVInletVelocityBC
    boundary = sodium_inlet
    variable = vel_y
    functor = 0
  []
  [inlet_vel_z]
    type = INSFVInletVelocityBC
    boundary = sodium_inlet
    variable = vel_z
    functor = ${inlet_rate}
  []

  [inlet_temp]
    type = FVDirichletBC
    boundary = sodium_inlet
    variable = temp_fluid
    value = ${inlet_temp}
  []

  [outlet_pressure]
    type = INSFVOutletPressureBC
    boundary = sodium_outlet
    variable = pressure
    function = ${outlet_pressure}
  []

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

  [no_slip_x]
    type = INSFVNoSlipWallBC
    boundary = 'clad_sodium_sodium_side'
    variable = vel_x
    function = 0
  []
  [no_slip_y]
    type = INSFVNoSlipWallBC
    boundary = 'clad_sodium_sodium_side'
    variable = vel_y
    function = 0
  []
  [no_slip_z]
    type = INSFVNoSlipWallBC
    boundary = 'clad_sodium_sodium_side'
    variable = vel_z
    function = 0
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