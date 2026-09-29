# ============================================================================
# Aura reactor thermal-hydraulics input
#
# GENERATED AUTOMATICALLY FROM THE MCNP MODEL.
#
# Edit the Python generator rather than manually changing values that are
# supposed to come from MCNP.
#
# MOOSE THM uses SI units:
#
#     length       m
#     mass         kg
#     time         s
#     temperature  K
#     pressure     Pa
# ============================================================================

# ----------------------------------------------------------------------------
# GLOBAL SIMULATION PARAMETERS
# ----------------------------------------------------------------------------

T_in = 300.0
m_dot_in = 1.0
p_out = 1000000.0

[GlobalParams]

  # Initial pressure of the fluid.
  initial_p = 1000000.0

  # Small nonzero initial velocity.
  initial_vel = 0.1

  # Initial temperature.
  initial_T = 300.0

  # No gravity for the initial model.
  #
  # CHANGE THIS when you model the actual vertical reactor.
  gravity_vector = '0 0 0'

  # Reconstruction option used by current THM tutorial examples.
  rdg_slope_reconstruction = full

  # Closure relation object.
  closures = thm_closures

  # Default fluid properties.
  fp = he
[]

# ----------------------------------------------------------------------------
# HELIUM FLUID PROPERTIES
# ----------------------------------------------------------------------------

[FluidProperties]

  [he]

    type = IdealGasFluidProperties

    # Helium molar mass [kg/mol].
    molar_mass = 4.0e-3

    # Ratio cp/cv.
    gamma = 1.67

    # ------------------------------------------------------------------------
    # PLACEHOLDERS:
    #
    # These are constant values for the initial model.
    #
    # For the actual reactor, replace them with appropriate temperature/
    # pressure-dependent helium property data if necessary.
    # ------------------------------------------------------------------------

    thermal_conductivity = 0.2556
    mu = 3.22639e-5
  []
[]

# ----------------------------------------------------------------------------
# THERMODYNAMIC CLOSURES
# ----------------------------------------------------------------------------

[Closures]

  [thm_closures]
    type = Closures1PhaseTHM
  []
[]

# ----------------------------------------------------------------------------
# THERMAL-HYDRAULIC COMPONENTS
# ----------------------------------------------------------------------------

[Components]

  # --------------------------------------------------------------------------
  # INLET
  #
  # Current starting condition:
  #
  #     prescribed mass flow rate
  #     prescribed inlet temperature
  #
  # --------------------------------------------------------------------------

  [inlet]

    type = InletMassFlowRateTemperature1Phase

    input = 'core_channel:in'

    m_dot = 1.0
    T = 300.0
  []

  # --------------------------------------------------------------------------
  # MAIN HELIUM FLOW CHANNEL
  # --------------------------------------------------------------------------

  [core_channel]

    type = FlowChannel1Phase

    position = '0 0 0'

    orientation = '0 0 1'

    # Active length [m].
    length = 1.0

    # Number of axial flow elements.
    n_elems = 25

    # ------------------------------------------------------------------------
    # PLACEHOLDERS:
    #
    # For the real assembly these need to be calculated from the PWR-style
    # fuel pin lattice.
    #
    # A       = coolant flow area
    # D_h     = hydraulic diameter
    # ------------------------------------------------------------------------

    A = 1.0e-3
    D_h = 1.0e-2
  []

  # --------------------------------------------------------------------------
  # OUTLET
  # --------------------------------------------------------------------------

  [outlet]

    type = Outlet1Phase

    input = 'core_channel:out'

    p = 1000000.0
  []

  # ==========================================================================
  # MCNP POWER DISTRIBUTION -- OPTIONAL
  # ==========================================================================
  #
  # Once Python has generated:
  #
  #     generated/mcnp_power.txt
  #
  # this function can be enabled.
  #
  # PiecewiseMultilinear can represent 3-D x/y/z data.
  #
  # --------------------------------------------------------------------------

  # [mcnp_power]
  #
  #   type = PiecewiseMultilinear
  #
  #   data_file = mcnp_power.txt
  #
  # []

  # ==========================================================================
  # HEAT STRUCTURE -- TODO
  # ==========================================================================
  #
  # This is where the actual fuel/clad thermal model will eventually go.
  #
  # Possible eventual approach:
  #
  #     HeatStructureFromFile3D
  #
  # using an Exodus mesh generated from the reactor geometry.
  #
  # Example skeleton:
  #
  # [fuel_heat_structure]
  #
  #   type = HeatStructureFromFile3D
  #
  #   file = reactor_mesh_in.e
  #
  #   position = '0 0 0'
  #
  #   initial_T = 300.0
  #
  # []
  #
  #
  # Then:
  #
  # [heat_generation]
  #
  #   type = HeatSourceFromTotalPower
  #
  #   hs = fuel_heat_structure
  #
  #   regions = 'fuel'
  #
  #   power = total_power
  #
  #   power_fraction = 1.0
  #
  #   power_shape_function = mcnp_power
  #
  # []
  #
  #
  # And:
  #
  # [total_power]
  #
  #   type = TotalPower
  #
  #   power = 1.0e6
  #
  # []
  #
  # These are deliberately left inactive until the mesh has named fuel
  # regions that MOOSE can identify.
  #
  # ==========================================================================
[]

# ----------------------------------------------------------------------------
# PRESSURE DROP MONITORING
# ----------------------------------------------------------------------------

[Postprocessors]

  [core_p_in]

    type = SideAverageValue

    boundary = 'core_channel:in'

    variable = p
  []

  [core_p_out]

    type = SideAverageValue

    boundary = 'core_channel:out'

    variable = p
  []

  [core_delta_p]

    type = ParsedPostprocessor

    pp_names = 'core_p_in core_p_out'

    expression = 'core_p_in - core_p_out'
  []
[]

# ----------------------------------------------------------------------------
# LINEAR / NONLINEAR PRECONDITIONING
# ----------------------------------------------------------------------------

[Preconditioning]

  [pc]

    type = SMP

    full = true
  []
[]

# ----------------------------------------------------------------------------
# EXECUTIONER
# ----------------------------------------------------------------------------

[Executioner]

  # Transient is a useful initial choice for THM.
  type = Transient

  solve_type = NEWTON

  line_search = basic

  start_time = 0.0

  end_time = 100.0

  dt = 1.0

  petsc_options_iname = '-pc_type'

  petsc_options_value = 'lu'

  nl_rel_tol = 1e-8

  nl_abs_tol = 1e-8

  nl_max_its = 25
[]

# ----------------------------------------------------------------------------
# OUTPUT
# ----------------------------------------------------------------------------

[Outputs]

  exodus = true

  execute_on = 'initial timestep_end'
[]
