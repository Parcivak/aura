[Mesh/fuel_pin]
  type = FileMeshGenerator
  file = ./concentric_circle_in.e
[]

[Variables]
  [temp_solid]
    initial_condition = 600
  []

  # Sodium velocity
  [vel_x]
    type = INSFVVelocityVariable
  []

  [vel_y]
    type = INSFVVelocityVariable
  []

  # Sodium pressure
  [pressure]
    type = INSFVPressureVariable
  []

  # Sodium temperature
  [temp_fluid]
    type = INSFVEnergyVariable
    initial_condition = 600
  []
[]

[Kernels]
  [diffusion]
    type = Diffusion
    variable = temp
  []

  [x_advection]
    type = INSFVMomentumAdvection
    variable = vel_x
    rho = 850
    momentum_component = x
  []

  [x_viscosity]
    type = INSFVMomentumDiffusion
    variable = vel_x
    mu = 0.0003
    momentum_component = x
  []

  [x_pressure]
    type = INSFVMomentumPressure
    variable = vel_x
    pressure = pressure
    momentum_component = x
  []
[]

[materials]
  [fuel]
    type = HeatConductionMaterial
    block = pellet
    thermal_conductivity = 0.26
  []

  [clad]
    type = HT9Thermal
    temperature = temp
    block = clad
  []
  
  [gap]
  []

  [sodium]
    type = SodiumPropertiesMaterial
    temperature = temp
    block = background
  []
[]

[Executioner]
  type = Steady
[]

[Outputs]
  exodus = true
[]
