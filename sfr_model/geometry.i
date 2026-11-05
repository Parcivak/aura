hole_radius = 0.644     # [cm]
pellet_radius =  0.494  # [cm]
clad_radius = 0.75      # [cm]
fuel_height = 300

[Mesh]
  [concentric_circle]
    type = PolygonConcentricCircleMeshGenerator
    num_sides = 6
    num_sectors_per_side = '4 4 4 4 4 4'
    polygon_size_style = apothem
    polygon_size = ${fparse 1.2  * clad_radius}
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

  [extruded_channel]
    type = AdvancedExtruderGenerator
    input = concentric_circle
    heights = ${fuel_height}
    num_layers = 1
    direction = '0 0 1'
    
    bottom_boundary = bottom
    top_boundary = top
    side_boundary = side
  []
[]
