# ============================================================
# reactor_mesh.i
#
# First-pass geometry for the Aura reactor.
#
# Geometry:
#   - Square PWR-style fuel assemblies
#   - 17 x 17 fuel-pin lattice
#   - Cylindrical fuel
#   - Fuel-cladding gap
#   - Zircaloy cladding
#   - Helium coolant filling the assembly
#   - Multiple assemblies arranged in a roughly circular core
#
# This file ONLY generates the mesh.
#
# Run with:
#
#   ./aura-opt -i geometry/reactor_mesh.i --mesh-only
#
# ============================================================


[Mesh]

  # ----------------------------------------------------------
  # Global reactor geometry parameters
  # ----------------------------------------------------------
  #
  # "Square" means that the pin lattice and assembly lattice
  # are Cartesian/square rather than hexagonal.
  #
  [rmp]
    type = ReactorMeshParams

    dim = 3
    geom = Square

    # --------------------------------------------------------
    # CHANGE THIS
    #
    # Center-to-center distance between adjacent assemblies.
    #
    # For a PWR-like 17x17 assembly this will ultimately be
    # approximately:
    #
    #     17 * pin_pitch
    #
    # but use the actual assembly pitch from your MCNP model.
    # --------------------------------------------------------
    assembly_pitch = 21.42

    # --------------------------------------------------------
    # Axial geometry
    #
    # CHANGE THESE to match the active fuel length.
    #
    # This example has one axial region.
    # --------------------------------------------------------
    axial_regions = '300.0'
    axial_mesh_intervals = '30'

    # Boundary IDs for the 3-D core
    bottom_boundary_id = 201
    top_boundary_id = 202
    radial_boundary_id = 200

    # Give regions useful block names.
    region_id_as_block_name = true
  []


  # ==========================================================
  # FUEL PIN
  # ==========================================================
  #
  # This defines ONE fuel pin.
  #
  # The radii below are examples only.
  # Replace them with the dimensions from MCNP.
  #
  # ring_radii:
  #
  #   fuel radius
  #   outer cladding radius
  #
  # The regions are:
  #
  #   region 1 = fuel
  #   region 2 = gap
  #   region 3 = cladding
  #   region 4 = helium background
  #
  # ==========================================================

  [fuel_pin]
    type = PinMeshGenerator

    reactor_params = rmp

    # Unique ID for this pin type
    pin_type = 1

    # --------------------------------------------------------
    # CHANGE THIS
    #
    # Center-to-center fuel pin spacing.
    # --------------------------------------------------------
    pitch = 1.26

    # Number of azimuthal divisions per quadrant.
    #
    # Increase this later if the cylindrical geometry needs
    # more resolution.
    num_sectors = 6

    # Use quadrilateral elements around the center.
    quad_center_elements = true

    # --------------------------------------------------------
    # CHANGE THESE
    #
    # Example:
    #
    #   0.4096 = fuel radius
    #   0.41778 = outside of cladding
    
#
    # MOOSE interprets the rings as concentric radial regions.
    # --------------------------------------------------------
    ring_radii = '0.4096 0.41778'

    # Number of radial mesh intervals:
    #
    #   fuel
    #   gap
    #   cladding/background
    #
    mesh_intervals = '4 1 2'

    # Region IDs:
    #
    #   1 = fuel
    #   2 = gap
    #   3 = cladding
    #   4 = helium coolant
    #
    region_ids = '1 2 3 4'

  []


  # ==========================================================
  # FUEL ASSEMBLY
  # ==========================================================
  #
  # Construct a 17 x 17 assembly from the fuel pin.
  #
  # Every position currently contains a fuel pin.
  #
  # Later we can replace selected positions with:
  #
  #   - control rods
  #   - guide tubes
  #   - instrumentation tubes
  #   - burnable absorbers
  #
  # ==========================================================

  [fuel_assembly]
    type = AssemblyMeshGenerator

    assembly_type = 1

    inputs = 'fuel_pin'

    # --------------------------------------------------------
    # 17 x 17 fuel-pin lattice
    # --------------------------------------------------------

    pattern = '1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1;
               1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1'

    # Helium fills the region between the outer pins.
    background_intervals = 1
    background_region_id = 4

  []


  # ==========================================================
  # CORE
  # ==========================================================
  #
  # The numbers below refer to the input assemblies.
  #
  # 1 = fuel assembly
  # 0 = empty location
  #
  # This is deliberately a rough circular core rather than
  # trying to reproduce your MCNP core exactly yet.
  #
  # We can replace this pattern with the exact MCNP assembly
  # loading map later.
  #
  # ==========================================================

  [core]
    type = CoreMeshGenerator

    inputs = 'fuel_assembly'

    # 1 = fuel assembly
    # 0 = empty
    #
    # Rough circular arrangement.
    pattern = '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 1 1 1 0 0 0 0 0 0 0;
               0 0 0 0 0 1 1 1 1 1 1 1 0 0 0 0 0;
               0 0 0 0 1 1 1 1 1 1 1 1 1 0 0 0 0;
               0 0 0 1 1 1 1 1 1 1 1 1 1 1 0 0 0;
               0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0;
               0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0;
               0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0;
               0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0;
               0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0;
               0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0;
               0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0;
               0 0 0 1 1 1 1 1 1 1 1 1 1 1 0 0 0;
               0 0 0 0 1 1 1 1 1 1 1 1 1 0 0 0 0;
               0 0 0 0 0 1 1 1 1 1 1 1 0 0 0 0 0;
               0 0 0 0 0 0 0 1 1 1 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'

    dummy_assembly_name = empty

    extrude = true

  []

[]

# ============================================================
# This is a mesh-only input file.
# ============================================================

[Problem]
  solve = false
[]

[Executioner]
  type = Steady
[]

[Outputs]

  [out]
    type = Exodus

    # Include Reactor Module IDs in the Exodus output.
    output_extra_element_ids = true

  []

  file_base = reactor_mesh

[]
