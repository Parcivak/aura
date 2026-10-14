# Run with:
#
#   ./aura-opt -i generated/starting_mesh.i --mesh-only

[Mesh]
  [rmp]
    type = ReactorMeshParams
    dim = 3
    geom = Square

    # Center-to-center distance between adjacent assemblies.
    #
    #     17 * pin_pitch
    assembly_pitch = 21.42

    axial_regions = '300.0'
    axial_mesh_intervals = '300'

    # Boundary IDs for the 3-D core
    bottom_boundary_id = 201
    top_boundary_id = 202
    radial_boundary_id = 200

    # Give regions useful block names.
    region_id_as_block_name = true
  []


  [fuel_pin]
    type = PinMeshGenerator
    reactor_params = rmp
    # Unique ID for this pin type
    pin_type = 1

    pitch = 1.26

    # Number of azimuthal divisions per quadrant.
    num_sectors = 4

    quad_center_elements = true

    # 1 - fuel
    # 2 - gap
    # 3 - cladding 
    # 4 - helium
    region_ids = '1 2 3 4'
    ring_radii = '0.4096 0.41778 0.47498'

    mesh_intervals = '2 1 2 1'

  []


  [fuel_assembly]
    type = AssemblyMeshGenerator
    assembly_type = 1
    inputs = 'fuel_pin'

    # 17 x 17 fuel-pin lattice
    pattern = '0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
               0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0'

    # Helium fills the region between the outer pins.
    background_intervals = 1
    background_region_id = 4
  []


  [core]
    type = CoreMeshGenerator
    inputs = 'empty fuel_assembly'

    # 1 = fuel assembly
    # 0 = empty

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

  [y_plane]
  type = PlaneDeletionGenerator
  input = core
  normal = '-1 0 0'
  point = '0 0 0'
  []

  [xy_plane]
  type = PlaneDeletionGenerator
  input = y_plane
  normal = '1 -1 0'
  point = '0 0 0'
  []
[]

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

 [./console]
    type = Console
    verbose = true  # Enables verbose console screen printouts
  [../]
[]
