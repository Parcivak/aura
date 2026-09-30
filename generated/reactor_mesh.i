# ============================================================================
# Aura reactor mesh
#
# INITIAL DEVELOPMENT VERSION
#
# This creates a simple 3-D rectangular domain so that the MCNP -> MOOSE
# workflow can be tested before the complete reactor assembly geometry is
# generated.
#
# Eventually replace the GeneratedMeshGenerator section with the MOOSE
# Reactor Module geometry:
#
#     pin
#       |
#       v
#     patterned Cartesian assembly
#       |
#       v
#     3-D reactor/core mesh
# ============================================================================

[Mesh]

  [generated_mesh]

    type = GeneratedMeshGenerator

    dim = 3

    nx = 20
    ny = 20
    nz = 25

    xmin = -0.01
    xmax = 0.01

    ymin = -0.01
    ymax = 0.01

    zmin = 0.0
    zmax = 385.153 # Active fuel height obtained from MCNP geometry.
  []

  # ==========================================================================
  # FUTURE REACTOR MODULE MESH
  # ==========================================================================
  #
  # The final model should look conceptually like:
  #
  # [pin]
  #   type = PolygonConcentricCircleMeshGenerator
  #   ...
  # []
  #
  # [assembly]
  #   type = PatternedCartesianMeshGenerator
  #   ...
  # []
  #
  # The exact pattern will be generated from the MCNP assembly definition.
  #
  # ==========================================================================
[]

[Outputs]

  exodus = true
[]
