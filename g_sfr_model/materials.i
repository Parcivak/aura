[FunctorMaterials]
  [sodium_viscosity]
    type = ADGenericFunctorMaterial
    prop_names = 'mu'
    prop_values = '0.0026' # [Pa-s]
    block = 'sodium gap'
  []

  [sodium_enthalpy]
    type = INSFVEnthalpyFunctorMaterial
    temperature = temp_fluid
    rho = rho
    h_in = h
    assumed_constant_cp = false
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

[FluidProperties]
  [sodium]
    type = SodiumProperties
  []
[]

[Functions]
  # Optional ParsedFunctions (kept commented for reference; FVDiffusion uses the FunctorMaterials above)
  # [k_fuel]
  #   type = ParsedFunction
  #   expression = '(1.089e-5)*t^2 - 0.03244*t + 87.27' # [W/m-K]
  # []
  # [k_clad]
  #   type = ParsedFunction
  #   expression = '29.65 + (6.668e-2)*t + (2.184e-4)*t^2 - (2.527e-7)*t^3 + (9.621e-11)*t^4' # [W/m-K]
  # []

  # Kept active so [Materials]/[clad] parses cleanly now and is ready for transient runs
  [cp_clad]
    type = ParsedFunction
    expression = '0.257*t + 380' # [J/kg-K]
  []
[]

[Materials]
  # Used for transient heat capacity (rho * cp * dT/dt) when transient kernels are enabled
  [fuel]
    type = HeatConductionMaterial
    block = pellet
    temperature = temp_solid
    specific_heat = 134
    # density = 15800 # [kg/m^3] Uncomment and set fuel density for transient runs
    declare_suffix = fuel
  []

  [clad]
    type = HeatConductionMaterial
    block = clad
    temperature = temp_solid
    specific_heat_temperature_function = cp_clad
    # density = 7750 # [kg/m^3] Uncomment and set HT9 cladding density for transient runs
    declare_suffix = clad
  []

  [sodium]
    type = SodiumPropertiesMaterial
    temperature = temp_fluid
    block = 'sodium gap'
    outputs = all
  []
[]