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

#Here we define each of the solid materials.
#Gap is also modeled as a solid conductor for the purposes of this model.
#Later we can calculate what a reasonable average conductivity of the gap should be,
# or we can change it to make the model more complex.
[Materials]
  [fuel]
    type = HeatConductionMaterial
    block = pellet
    thermal_conductivity = 0.26
  []

  [clad]
    type = HeatConductionMaterial
    temperature = temp_solid
    block = clad
    thermal_conductivity = 25
  []
  
  [gap]
    type = HeatConductionMaterial
    temperature = temp_solid
    block = gap
    thermal_conductivity = 8
  []

  [sodium]
    type = SodiumPropertiesMaterial
    temperature = temp_fluid
    block = background
    outputs = all
  []
[]