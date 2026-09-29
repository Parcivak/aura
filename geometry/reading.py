import montepy

prob = montepy.read_input("../full-mcnp/Aura_MCNP_Model.inp")

print("Cells:")
for cell in prob.cells:
    print(
        cell.number,
        cell.material,
    )

print("\nMaterials:")
for mat in prob.materials:
    print(mat)

print("\nSurfaces:")
for surface in prob.surfaces:
    print(surface.number, surface)
