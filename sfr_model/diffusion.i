!include ./materials.i
!include ./boundary.i
advected_interp_method = 'average'
velocity_interp_method = 'rc'

[Mesh/fuel_pin]
  type = FileMeshGenerator
  file = ./geometry.e
[]

[Variables]
  [temp_solid]
    initial_condition = 600
    block = background
  []

  # Sodium velocity
  [vel_x]
    type = INSFVVelocityVariable
    block = background
  []

  [vel_y]
    type = INSFVVelocityVariable
    block = background
  []

  [vel_z]
    type = INSFVVelocityVariable
    block = background
  []

  [pressure]
    type = INSFVPressureVariable
    block = background
  []

  [temp_fluid]
    type = INSFVEnergyVariable
    initial_condition = 600
    block = background
  []

  [lambda]
    family = SCALAR
    order = first
    block = background
  []
[]

[AuxVariables]
  [U]
    order = CONSTANT
    family = MONOMIAL
    fv = true
  []
[]

[AuxKernels]
  [mag]
    type = VectorMagnitudeAux
    variable = U
    x = vel_x
    y = vel_y
    z = vel_z
  []
[]

[FVKernels]
  [mass]
    type = INSFVMassAdvection
    variable = pressure
    advected_interp_method = ${advected_interp_method}
    velocity_interp_method = ${velocity_interp_method}
    rho = rho
    block = background
  []
  [mean_zero_pressure]
    type = FVIntegralValueConstraint
    variable = pressure
    lambda = lambda
    block = background
  []


  [u_advection]
    type = INSFVMomentumAdvection
    variable = vel_x
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'x'
    block = background
  []
  [u_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_x
    mu = mu
    momentum_component = 'x'
    block = background
  []
  [u_pressure]
    type = INSFVMomentumPressure
    variable = vel_x
    momentum_component = 'x'
    pressure = pressure
    block = background
  []

  [v_advection]
    type = INSFVMomentumAdvection
    variable = vel_y
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'y'
    block = background
  []
  [v_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_y
    mu = mu
    momentum_component = 'y'
    block = background
  []
  [v_pressure]
    type = INSFVMomentumPressure
    variable = vel_y
    momentum_component = 'y'
    pressure = pressure
    block = background
  []

  [w_advection]
    type = INSFVMomentumAdvection
    variable = vel_z
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'z'
    block = background
  []
  [w_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_z
    mu = mu
    momentum_component = 'z'
    block = background
  []
  [w_pressure]
    type = INSFVMomentumPressure
    variable = vel_z
    momentum_component = 'z'
    pressure = pressure
    block = background
  []

  [temp_conduction]
    type = FVDiffusion
    coeff = 'k'
    variable = temp_fluid
    block = background
  []

  [temp_advection]
    type = INSFVEnergyAdvection
    variable = temp_fluid
    advected_quantity = rho_h
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    block = background
  []

  [solid_conduction]
    type = HeatConduction
    variable = temp_solid
  []
[]

[Executioner]
  type = Steady
  solve_type = 'NEWTON'
  petsc_options_iname = '-pc_type -pc_factor_shift_type'
  petsc_options_value = 'lu NONZERO'
  nl_rel_tol = 1e-12
[]

[Outputs]
  exodus = true
[]
