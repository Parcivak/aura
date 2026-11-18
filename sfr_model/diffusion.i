!include ./boundary.i
!include ./materials.i
advected_interp_method = 'average'
velocity_interp_method = 'rc'

[GlobalParams]
  rhie_chow_user_object = 'rc'
[]

[Variables]
  [temp_solid]	
    type = MooseVariableFVReal
    initial_condition = 600
    block = 'pellet clad'
  []

  # Sodium velocity
  [vel_x]
    type = INSFVVelocityVariable
    block = 'sodium gap'
  []

  [vel_y]
    type = INSFVVelocityVariable
    block = 'sodium gap'
  []

  [vel_z]
    type = INSFVVelocityVariable
    block = 'sodium gap'
  []

  [pressure]
    type = INSFVPressureVariable
    block = 'sodium gap'
  []

  [temp_fluid]
    type = INSFVEnergyVariable
    initial_condition = 600
    block = 'sodium gap'
  []

  [lambda]
    family = SCALAR
    order = first
    block = 'sodium gap'
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
    block = 'sodium gap'
  []
[]

[UserObjects]
  [rc]
    type = INSFVRhieChowInterpolator
    u = vel_x
    v = vel_y
    w = vel_z
    pressure = pressure
    block = 'sodium gap'
  []
[]

[FVKernels]
  [mass]
    type = INSFVMassAdvection
    variable = pressure
    advected_interp_method = ${advected_interp_method}
    velocity_interp_method = ${velocity_interp_method}
    rho = rho
    block = 'sodium gap'
  []
  [mean_zero_pressure]
    type = FVIntegralValueConstraint
    variable = pressure
    lambda = lambda
    block = 'sodium gap'
  []


  [u_advection]
    type = INSFVMomentumAdvection
    variable = vel_x
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'x'
    block = 'sodium gap'
  []
  [u_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_x
    mu = mu
    momentum_component = 'x'
    block = 'sodium gap'
  []
  [u_pressure]
    type = INSFVMomentumPressure
    variable = vel_x
    momentum_component = 'x'
    pressure = pressure
    block = 'sodium gap'
  []

  [v_advection]
    type = INSFVMomentumAdvection
    variable = vel_y
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'y'
    block = 'sodium gap'
  []
  [v_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_y
    mu = mu
    momentum_component = 'y'
    block = 'sodium gap'
  []
  [v_pressure]
    type = INSFVMomentumPressure
    variable = vel_y
    momentum_component = 'y'
    pressure = pressure
    block = 'sodium gap'
  []

  [w_advection]
    type = INSFVMomentumAdvection
    variable = vel_z
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'z'
    block = 'sodium gap'
  []
  [w_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_z
    mu = mu
    momentum_component = 'z'
    block = 'sodium gap'
  []
  [w_pressure]
    type = INSFVMomentumPressure
    variable = vel_z
    momentum_component = 'z'
    pressure = pressure
    block = 'sodium gap'
  []

  [temp_conduction]
    type = FVDiffusion
    coeff = 'k'
    variable = temp_fluid
    block = 'sodium gap'
  []

  [temp_advection]
    type = INSFVEnergyAdvection
    variable = temp_fluid
    advected_quantity = rho_h
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    block = 'sodium gap'
  []

  [fuel_conduction]
    type = FVDiffusion
    variable = temp_solid
    coeff = thermal_conductivity_fuel
    block = pellet
  []

  [clad_conduction]
    type = FVDiffusion
    variable = temp_solid
    coeff = thermal_conductivity_clad
    block = clad
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
