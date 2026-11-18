# Converted from cm to m to match SI material properties (W/m-K, Pa-s, kg/m^3)
pellet_radius = 0.00227097  # [m] (0.227097 cm)
hole_radius   = 0.00268089  # [m] (0.268089 cm)
clad_radius   = 0.00309081  # [m] (0.309081 cm)
fuel_height   = 0.90        # [m] (90 cm)

[Mesh]
  # Generate concentric circles for fuel, sodium bond gap, cladding, and surrounding hexagonal sodium subchannel
  [concentric_circle]
    type = PolygonConcentricCircleMeshGenerator
    num_sides = 6
    num_sectors_per_side = '4 4 4 4 4 4'
    polygon_size_style = apothem
    polygon_size = ${fparse 1.165113 * clad_radius}
    ring_radii = '${pellet_radius} ${hole_radius} ${clad_radius}'
    ring_intervals = '4 4 4'
    quad_center_elements = true

    ring_block_ids = '1 2 3'
    ring_block_names = 'pellet gap clad'

    background_block_ids = 4
    background_intervals = 5
    background_block_names = sodium

    external_boundary_id = 100

    create_inward_interface_boundaries = true
    create_outward_interface_boundaries = true

    inward_interface_boundary_names = '
      fuel_gap_gap_side
      gap_clad_clad_side
      clad_sodium_sodium_side'

    outward_interface_boundary_names = '
      fuel_gap_fuel_side
      gap_clad_gap_side
      clad_sodium_clad_side'
  []

  # Extrude the 2D hex-pin cross section axially into a 3D fuel channel
  [extruded_channel]
    type = AdvancedExtruderGenerator
    input = concentric_circle
    heights = ${fuel_height}
    num_layers = 45
    direction = '0 0 1'
  []

  # Bottom inlet boundary for flowing sodium coolant (z = 0)
  [sodium_inlet]
    type = ParsedGenerateSideset
    input = extruded_channel

    combinatorial_geometry = 'abs(z) < 1e-8'
    included_subdomains = sodium
    include_only_external_sides = true
    normal = '0 0 -1'

    new_sideset_name = sodium_inlet
  []

  # Top outlet boundary for flowing sodium coolant (z = fuel_height)
  [sodium_outlet]
    type = ParsedGenerateSideset
    input = sodium_inlet

    combinatorial_geometry = 'abs(z - ${fuel_height}) < 1e-8'
    included_subdomains = sodium
    include_only_external_sides = true
    normal = '0 0 1'

    new_sideset_name = sodium_outlet
  []
[]