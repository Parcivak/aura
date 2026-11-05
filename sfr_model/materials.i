[FunctorMaterials]
  [sodium_viscosity]
    type = ADGenericFunctorMaterial
    prop_names = 'mu'
    prop_values = '0.00042'
    block = background
  []
  
  [sodium_enthalpy]
  type = INSFVEnthalpyFunctorMaterial
  temperature = temp_fluid
  rho = rho
  h_in = h
  assumed_constant_cp = false
  block = background
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
    temperature = temp_solid
    block = clad
  []
  
  [gap]
  []

  [sodium]
    type = SodiumPropertiesMaterial
    temperature = temp_fluid
    block = background
    outputs = all
  []
[]