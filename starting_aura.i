[Mesh]
  [generated_mesh]
    type = GeneratedMeshGenerator
    dim = 2
    nx = 20
    ny = 20
    xmin = -0.01
    xmax = 0.01
    ymin = -0.01
    ymax = 0.01
  []
[]

[Materials]
  # fuel properties
  # cladding properties
  # helium properties
[]

[Physics]
  # heat conduction / thermal hydraulics
[]

[Executioner]
  type = Steady
[]

[Outputs]
  exodus = true
[]
