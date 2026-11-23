!include ./boundary.i
!include ./materials.i

advected_interp_method = 'upwind'
velocity_interp_method = 'rc'

[GlobalParams]
  rhie_chow_user_object = 'rc'
[]

[Variables]
  [temp_solid]
    type = MooseVariableFVReal
    initial_condition = 650
    block = 'pellet clad'
  []

  # Flowing sodium velocity & pressure (restricted to 'sodium' only; 'gap' is stagnant conduction)
  [vel_x]
    type = INSFVVelocityVariable
    initial_condition = 0
    block = sodium
  []

  [vel_y]
    type = INSFVVelocityVariable
    initial_condition = 0
    block = sodium
  []

  [vel_z]
    type = INSFVVelocityVariable
    initial_condition = ${inlet_rate}
    block = sodium
  []

  [pressure]
    type = INSFVPressureVariable
    block = sodium
  []

  [temp_fluid]
    type = INSFVEnergyVariable
    initial_condition = 650
    block = 'sodium gap'
  []
[]

[AuxVariables]
  [U]
    order = CONSTANT
    family = MONOMIAL
    fv = true
    initial_condition = ${inlet_rate}
    block = sodium
  []
[]

[AuxKernels]
  [mag]
    type = VectorMagnitudeAux
    variable = U
    x = vel_x
    y = vel_y
    z = vel_z
    block = sodium
  []
[]

[UserObjects]
  [rc]
    type = INSFVRhieChowInterpolator
    u = vel_x
    v = vel_y
    w = vel_z
    pressure = pressure
    block = sodium
  []
[]

[FVKernels]
  # --- Mass Conservation (flowing sodium only) ---
  [mass]
    type = INSFVMassAdvection
    variable = pressure
    advected_interp_method = ${advected_interp_method}
    velocity_interp_method = ${velocity_interp_method}
    rho = rho
    block = sodium
  []

  # --- Momentum Conservation (flowing sodium only) ---
  [u_advection]
    type = INSFVMomentumAdvection
    variable = vel_x
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'x'
    block = sodium
  []
  [u_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_x
    mu = mu
    momentum_component = 'x'
    block = sodium
  []
  [u_pressure]
    type = INSFVMomentumPressure
    variable = vel_x
    momentum_component = 'x'
    pressure = pressure
    block = sodium
  []

  [v_advection]
    type = INSFVMomentumAdvection
    variable = vel_y
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'y'
    block = sodium
  []
  [v_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_y
    mu = mu
    momentum_component = 'y'
    block = sodium
  []
  [v_pressure]
    type = INSFVMomentumPressure
    variable = vel_y
    momentum_component = 'y'
    pressure = pressure
    block = sodium
  []

  [w_advection]
    type = INSFVMomentumAdvection
    variable = vel_z
    velocity_interp_method = ${velocity_interp_method}
    advected_interp_method = ${advected_interp_method}
    rho = rho
    momentum_component = 'z'
    block = sodium
  []
  [w_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_z
    mu = mu
    momentum_component = 'z'
    block = sodium
  []
  [w_pressure]
    type = INSFVMomentumPressure
    variable = vel_z
    momentum_component = 'z'
    pressure = pressure
    block = sodium
  []

  # --- Fluid & Gap Energy Conservation ---
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
    block = sodium
  []

  # --- Solid Fuel & Cladding Conduction ---
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

  [heat_source]
    type = FVBodyForce
    variable = temp_solid
    function = volumetric_heat
    block = pellet
  []
  # =========================================================================
  # TRANSIENT TIME DERIVATIVE KERNELS (Uncomment all below for transient runs)
  # =========================================================================
   [u_time]
     type = INSFVMomentumTimeDerivative
     variable = vel_x
     rho = rho
     momentum_component = 'x'
     block = sodium
   []
   [v_time]
     type = INSFVMomentumTimeDerivative
     variable = vel_y
     rho = rho
     momentum_component = 'y'
     block = sodium
   []
   [w_time]
     type = INSFVMomentumTimeDerivative
     variable = vel_z
     rho = rho
     momentum_component = 'z'
     block = sodium
   []
   [temp_fluid_time]
     type = INSFVEnergyTimeDerivative
     variable = temp_fluid
     rho = rho
     dh_dt = dh_dt
     block = 'sodium gap'
   []
   [fuel_time]
     type = FVHeatConductionTimeDerivative
     variable = temp_solid
     specific_heat = specific_heat_fuel
     block = pellet
   []
   [clad_time]
     type = FVHeatConductionTimeDerivative
     variable = temp_solid
     specific_heat = specific_heat_clad
     block = clad
   []
[]

# ===========================================================================
# EXECUTIONER (Comment out [Executioner] below & uncomment Transient for transients)
# ===========================================================================
# [Executioner]
#  type = Steady
#  solve_type = 'NEWTON'
#  petsc_options_iname = '-pc_type -pc_factor_shift_type'
#  petsc_options_value = 'lu NONZERO'
#  nl_rel_tol = 1e-7
#  nl_abs_tol = 1e-7
#  nl_max_its = 500
#  line_search = 'bt'
# []

[Executioner]
  type = Transient
  solve_type = 'NEWTON'
  petsc_options_iname = '-pc_type -pc_factor_shift_type'
  petsc_options_value = 'lu NONZERO'
  automatic_scaling = true
  start_time = 0.0
  end_time = 5.0
  [TimeStepper]
    type = IterationAdaptiveDT
    dt = 0.005
    optimal_iterations = 4
    iteration_window = 1
    growth_factor = 1.25
    cutback_factor = 0.5
  []
  dtmax = 0.02
  nl_rel_tol = 1e-7
  nl_abs_tol = 1e-7
  nl_max_its = 30
  steady_state_detection = true
  steady_state_tolerance = 1e-7
[]

[Outputs]
  exodus = true
[]
