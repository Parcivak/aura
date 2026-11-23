[FunctorMaterials]
  # Liquid sodium properties (Fink & Leibowitz, ANL-RE-95/2) as native AD functors
  [sodium_rho]
    type = ADParsedFunctorMaterial
    block = 'sodium gap'
    property_name = rho
    expression = '1011.6 - 0.2205*T - 1.922e-5*T^2 + 5.637e-9*T^3' # [kg/m^3]
    functor_names = 'temp_fluid'
    functor_symbols = 'T'
  []

  [sodium_cp]
    type = ADParsedFunctorMaterial
    block = 'sodium gap'
    property_name = cp
    expression = '1658.2 - 0.8479*T + 4.454e-4*T^2 - 2.992e6/T^2' # [J/kg-K]
    functor_names = 'temp_fluid'
    functor_symbols = 'T'
  []

  [sodium_k]
    type = ADParsedFunctorMaterial
    block = 'sodium gap'
    property_name = k
    expression = '124.67 - 0.11381*T + 5.5226e-5*T^2 - 1.1842e-8*T^3' # [W/m-K]
    functor_names = 'temp_fluid'
    functor_symbols = 'T'
  []

  [sodium_mu]
    type = ADParsedFunctorMaterial
    block = 'sodium gap'
    property_name = mu
    expression = 'exp(-6.4406 - 0.3958*log(T) + 556.835/T)' # [Pa-s]
    functor_names = 'temp_fluid'
    functor_symbols = 'T'
  []

  [sodium_enthalpy]
    type = INSFVEnthalpyFunctorMaterial
    temperature = temp_fluid
    rho = rho
    cp = cp
    assumed_constant_cp = true
    block = 'sodium gap'
  []

  [fuel_conduction]
    type = ADParsedFunctorMaterial
    block = pellet
    property_name = thermal_conductivity_fuel
    expression = '(1.089e-5)*T^2 - 0.03244*T + 87.27' # [W/m-K]
    functor_names = 'temp_solid'
    functor_symbols = 'T'
  []

  [clad_conduction]
    type = ADParsedFunctorMaterial
    block = clad
    property_name = thermal_conductivity_clad
    expression = '29.65 + (6.668e-2)*T + (2.184e-4)*T^2 - (2.527e-7)*T^3 + (9.621e-11)*T^4' # [W/m-K]
    functor_names = 'temp_solid'
    functor_symbols = 'T'
  []
[]

[Materials]
  [fuel]
    type = ADHeatConductionMaterial
    block = pellet
    temperature = temp_solid
    specific_heat = 134
    declare_suffix = fuel
  []

  [fuel_density]
    type = ADGenericConstantMaterial
    block = pellet
    prop_names = 'density'
    prop_values = '15800' # [kg/m^3]
  []

  [clad]
    type = ADHeatConductionMaterial
    block = clad
    temperature = temp_solid
    specific_heat = 500 # [J/kg-K] HT9 cladding pseudo-transient heat capacity
    declare_suffix = clad
  []

  [clad_density]
    type = ADGenericConstantMaterial
    block = clad
    prop_names = 'density'
    prop_values = '7750' # [kg/m^3]
  []
[]
