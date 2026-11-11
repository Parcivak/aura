[Mesh/fuel_pin]
  type = FileMeshGenerator
  file = ./geometry_in.e
[]

inlet_rate = 30

[FVBCs]

  [outlet_x]
    type = INSFVInletVelocityBC
    boundary = sodium_outlet
    variable = vel_x
    functor = 0
  []
  [outlet_y]
    type = INSFVInletVelocityBC
    boundary = sodium_outlet
    variable = vel_y
    functor = 0
  []
  [outlet_z]
    type = INSFVInletVelocityBC
    boundary = sodium_outlet
    variable = vel_z
    functor = ${inlet_rate}
  []

  [side_x]
    type = INSFVSymmetryVelocityBC
    boundary = 10000
    variable = vel_x
    u = vel_x
    v = vel_y
    w = vel_z
    mu = mu
    momentum_component = x
  []

  [side_y]
    type = INSFVSymmetryVelocityBC
    boundary = 10000
    variable = vel_y
    u = vel_x
    v = vel_y
    w = vel_z
    mu = mu
    momentum_component = y
  []

  [side_z]
    type = INSFVSymmetryVelocityBC
    boundary = 10000
    variable = vel_z
    u = vel_x
    v = vel_y
    w = vel_z
    mu = mu
    momentum_component = z
  []

  [side_pressure]
    type = INSFVSymmetryPressureBC
    boundary = 10000
    variable = pressure
  []

[]