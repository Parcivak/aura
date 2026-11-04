hole_radius = 0.644     # [cm]
pellet_radius =  0.494  # [cm]
clad_radius = 0.75      # [cm]

[Mesh]
  [concentric_circle]
    type = PolygonConcentricCircleMeshGenerator
    num_sides = 6
    num_sectors_per_side = '4 4 4 4 4 4'
    polygon_size_style = apothem
    polygon_size = ${fparse 1.2  * clad_radius}
    ring_radii = '${pellet_radius} ${hole_radius} ${clad_radius}'
    ring_intervals = '4 4 4'
    background_intervals = 4

    ring_block_ids = '1 2 3 4'
    ring_block_names = 'pellet gap clad background'
    background_block_ids = 4
    background_block_names = sodium
  []
[]
