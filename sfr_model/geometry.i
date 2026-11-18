pellet_radius =  0.227097  # [cm]
hole_radius = 0.268089     # [cm]
clad_radius = 0.309081      # [cm]
fuel_height = 90

[Mesh]
# First generate the concentric circles of the fuel, gap, clad, and surrounding hexagon for the sodium.
  [concentric_circle]
    type = PolygonConcentricCircleMeshGenerator
    num_sides = 6
    num_sectors_per_side = '4 4 4 4 4 4'
    polygon_size_style = apothem
    polygon_size = ${fparse 1.165113  * clad_radius}
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

#Extrude the hexagon with concentric circles out into a fuel assembly, again based on the variables delcared at start of file.
  [extruded_channel]
    type = AdvancedExtruderGenerator
    input = concentric_circle
    heights = ${fuel_height}
    num_layers = 1
    direction = '0 0 1'
  []
  
#We need named boundaries at the top and bottom to be the inlet and outlet of the sodium, create those here.
  [sodium_inlet]
    type = ParsedGenerateSideset
    input = extruded_channel

    combinatorial_geometry = 'abs(z) < 1e-8'
    included_subdomains = sodium
    include_only_external_sides = true
    normal = '0 0 -1'

    new_sideset_name = sodium_inlet
  []

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
