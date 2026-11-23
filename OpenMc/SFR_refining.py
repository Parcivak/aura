import openmc
import math
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import openmc.deplete

# 1. Define Materials
fuel = openmc.Material(name='TRU-W-10Zr Fuel (Adjustable)')

# Define target weight fractions
tru_wt = 0.26  # Lower TRU to 20 wt% to decrease k_eff, altohugh higher weight closer Aligns heavy metal loading with MDPI Case V baseline.
zr_wt = 0.104
re_wt = 0.05 # 5% Rare Earth carryover from pyroprocessing
w_wt = 1.0 - tru_wt - zr_wt - re_wt # Make up the rest with Tungsten

# Normalized PWR Spent Fuel TRU Vector (Fractions sum to 1.0)
tru_vector = {
    'Pu238': 0.0301, 'Pu239': 0.5009, 'Pu240': 0.3193, 'Pu241': 0.0386, 'Pu242': 0.0319,
    'Np237': 0.0171, 'Am241': 0.0360, 'Am242_m1': 0.0022, 'Am243': 0.0118,
    'Cm242': 0.00002, 'Cm243': 0.0001, 'Cm244': 0.0075, 'Cm245': 0.0024, 'Cm246': 0.0014
}

# Add scaled TRU isotopes to the material
for nuclide, fraction in tru_vector.items():
    fuel.add_nuclide(nuclide, fraction * tru_wt, percent_type='wo')

fuel.add_element('Nd', 0.53 * re_wt, percent_type='wo')
fuel.add_element('Ce', 0.25 * re_wt, percent_type='wo')
fuel.add_element('Pr', 0.16 * re_wt, percent_type='wo')
fuel.add_element('La', 0.06 * re_wt, percent_type='wo')
fuel.add_element('W', w_wt, percent_type='wo')
fuel.add_element('Zr', zr_wt, percent_type='wo')
fuel.set_density('g/cm3', 15.0)

sodium = openmc.Material(name='Sodium')
sodium.add_element('Na', 1.0)
sodium.set_density('g/cm3', 0.85)

cladding = openmc.Material(name='HT9 Cladding')
cladding.add_element('Fe', 0.8455, percent_type='wo')
cladding.add_element('Cr', 0.12, percent_type='wo')
cladding.add_element('Mo', 0.01, percent_type='wo')
cladding.add_element('W', 0.005, percent_type='wo')
cladding.add_element('Ni', 0.005, percent_type='wo')
cladding.add_element('V', 0.0025, percent_type='wo')
cladding.add_element('C', 0.002, percent_type='wo')
cladding.set_density('g/cm3', 7.8)

b4c = openmc.Material(name='B4C Absorber')
b4c.add_element('B', 4.0)
b4c.add_element('C', 1.0)
b4c.set_density('g/cm3', 2.52)

inconel = openmc.Material(name='Inconel-600')
inconel.add_element('Ni', 0.72, percent_type='wo')
inconel.add_element('Cr', 0.155, percent_type='wo')
inconel.add_element('Fe', 0.08, percent_type='wo')
inconel.add_element('Mn', 0.005, percent_type='wo')
inconel.add_element('Si', 0.005, percent_type='wo')
inconel.add_element('Cu', 0.005, percent_type='wo')
inconel.add_element('C', 0.001, percent_type='wo')
inconel.set_density('g/cm3', 8.47)

shield_mat = openmc.Material.mix_materials(
    [cladding, sodium],
    [0.80, 0.20], #assumption
    'vo',
    name='Radial Shield'
)

gas = openmc.Material(name='Fission Gas / Void')
gas.add_nuclide('He4', 1.0)
gas.set_density('g/cm3', 0.001)

# New Material: Stainless Steel 316 for the Reactor Pressure Vessel
rpv_mat = openmc.Material(name='SS316 RPV')
rpv_mat.add_element('Fe', 0.66, percent_type='wo')
rpv_mat.add_element('Cr', 0.17, percent_type='wo')
rpv_mat.add_element('Ni', 0.12, percent_type='wo')
rpv_mat.add_element('Mo', 0.02, percent_type='wo')
rpv_mat.add_element('Mn', 0.02, percent_type='wo')
rpv_mat.add_element('Si', 0.01, percent_type='wo')
rpv_mat.set_density('g/cm3', 8.0)

materials = openmc.Materials([fuel, sodium, cladding, b4c, inconel, shield_mat, gas, rpv_mat])

# 2. Define Axial Planes
z_bottom = openmc.ZPlane(z0=0.0, boundary_type='vacuum')
z_core_bottom = openmc.ZPlane(z0=110.0)
z_core_top = openmc.ZPlane(z0=200.0)
z_bond_top = openmc.ZPlane(z0=218.0)
z_top = openmc.ZPlane(z0=370.0, boundary_type='vacuum')

# Axial Regions
lower_shield_reg = +z_bottom & -z_core_bottom
active_core_reg = +z_core_bottom & -z_core_top
bond_reg = +z_core_top & -z_bond_top
plenum_reg = +z_bond_top & -z_top

# 3. Define Pin Cell & Pin Lattice
r_clad_out = 0.375
r_clad_in = r_clad_out - 0.053 
r_fuel = r_clad_in * math.sqrt(0.75) 

fuel_cyl = openmc.ZCylinder(r=r_fuel)
clad_inner_cyl = openmc.ZCylinder(r=r_clad_in)
clad_outer_cyl = openmc.ZCylinder(r=r_clad_out)

pin_fuel = openmc.Cell(fill=fuel, region=-fuel_cyl)
pin_gap = openmc.Cell(fill=sodium, region=+fuel_cyl & -clad_inner_cyl)
pin_clad = openmc.Cell(fill=cladding, region=+clad_inner_cyl & -clad_outer_cyl)
pin_coolant = openmc.Cell(fill=sodium, region=+clad_outer_cyl)

# 2D Pin Universe
pin_univ = openmc.Universe(cells=[pin_fuel, pin_gap, pin_clad, pin_coolant])
empty_pin_univ = openmc.Universe(cells=[openmc.Cell(fill=sodium)])

# Inner Fuel Pin Lattice (217 pins = 9 rings)
inner_pin_lattice = openmc.HexLattice()
inner_pin_lattice.center = (0.0, 0.0)
inner_pin_lattice.pitch = (0.89,)
inner_pin_lattice.outer = empty_pin_univ
inner_pin_lattice.universes = [[pin_univ] * (6 * i) if i > 0 else [pin_univ] for i in reversed(range(9))]

# Outer Fuel Pin Lattice (271 pins = 10 rings)
outer_pin_lattice = openmc.HexLattice()
outer_pin_lattice.center = (0.0, 0.0)
outer_pin_lattice.pitch = (0.89,)
outer_pin_lattice.outer = empty_pin_univ
outer_pin_lattice.universes = [[pin_univ] * (6 * i) if i > 0 else [pin_univ] for i in reversed(range(10))]

# 4. Define Assembly Ducts
duct_outer_flat = 16.0 
inner_duct_thickness = 1.15
outer_duct_thickness = 0.37

inner_duct_inner_flat = duct_outer_flat - (2 * inner_duct_thickness)
outer_duct_inner_flat = duct_outer_flat - (2 * outer_duct_thickness)

duct_outer = openmc.model.HexagonalPrism(edge_length=duct_outer_flat / math.sqrt(3), orientation='y')
inner_duct_inner = openmc.model.HexagonalPrism(edge_length=inner_duct_inner_flat / math.sqrt(3), orientation='y')
outer_duct_inner = openmc.model.HexagonalPrism(edge_length=outer_duct_inner_flat / math.sqrt(3), orientation='y')

# 5. Construct Assembly Universes
def create_homogeneous_assembly(name, inner_material, duct_inner_surf):
    inner_cell = openmc.Cell(fill=inner_material, region=-duct_inner_surf)
    duct_cell = openmc.Cell(fill=cladding, region=+duct_inner_surf & -duct_outer)
    gap_outside = openmc.Cell(fill=sodium, region=+duct_outer)
    return openmc.Universe(name=name, cells=[inner_cell, duct_cell, gap_outside])

primary_cr_univ = create_homogeneous_assembly('Primary CR (Empty)', sodium, outer_duct_inner)
secondary_cr_univ = create_homogeneous_assembly('Secondary CR (Empty)', sodium, outer_duct_inner)

reflector_univ = create_homogeneous_assembly('Reflector', inconel, outer_duct_inner) #the reflector should be a mix. reflector_mix = openmc.Material.mix_materials( [inconel, sodium, cladding], [0.7543, 0.1582, 0.0875], 'vo', name='Homogenized Reflector'
b4c_shield_univ = create_homogeneous_assembly('B4C Shield', b4c, outer_duct_inner)
ivs_univ = create_homogeneous_assembly('IVS', sodium, outer_duct_inner)
radial_shield_univ = create_homogeneous_assembly('Radial Shield', shield_mat, outer_duct_inner)
empty_univ = openmc.Universe(name='Outside Core', cells=[openmc.Cell(fill=sodium)])

def create_fuel_assembly(name, pin_lattice, duct_inner_surf):
    lower_cell = openmc.Cell(fill=shield_mat, region=-duct_inner_surf & lower_shield_reg)
    active_cell = openmc.Cell(fill=pin_lattice, region=-duct_inner_surf & active_core_reg) 
    bond_cell = openmc.Cell(fill=sodium, region=-duct_inner_surf & bond_reg)
    plenum_cell = openmc.Cell(fill=gas, region=-duct_inner_surf & plenum_reg)
    
    duct_cell = openmc.Cell(fill=cladding, region=+duct_inner_surf & -duct_outer & +z_bottom & -z_top)
    outer_coolant = openmc.Cell(fill=sodium, region=+duct_outer & +z_bottom & -z_top)
    
    return openmc.Universe(name=name, cells=[lower_cell, active_cell, bond_cell, plenum_cell, duct_cell, outer_coolant])

inner_fuel_assembly_univ = create_fuel_assembly('Inner Fuel Assembly', inner_pin_lattice, inner_duct_inner)
outer_fuel_assembly_univ = create_fuel_assembly('Outer Fuel Assembly', outer_pin_lattice, outer_duct_inner)

# 6. Define Full Core Lattice
core_lattice = openmc.HexLattice()
core_lattice.center = (0.0, 0.0)
core_lattice.pitch = (16.22,)
core_lattice.orientation = 'x'

# Map short variables for clean, manual formatting
P = primary_cr_univ
S = secondary_cr_univ
I = inner_fuel_assembly_univ
O = outer_fuel_assembly_univ
R = reflector_univ
B = b4c_shield_univ
V = ivs_univ
D = radial_shield_univ
E = empty_univ

# Explicit list of lists from outermost ring (14) to the center (0)
core_rings = [
    # Ring 14 (Outermost - 84 items with empty corners)
    [E, E, D, D, D, D, D, D, D, D, D, D, D, E] * 6,
    
    # Ring 13 (78 items)
    [D, D, V, V, V, V, V, V, V, V, V, V, D] * 6,
    
    # Ring 12 (72 items)
    [V, V, B, B, B, B, B, B, B, B, B, V] * 6,
    
    # Ring 11 (66 items)
    [B, B, R, R, R, R, R, R, R, R, B] * 6,
    
    # Ring 10 (60 items)
    [R] * 60,
    
    # Ring 9 (54 items)
    [P, O, O, O, O, O, O, O, O] * 6,
    
    # Ring 8 (48 items)
    [O, O, P, O, O, O, P, O] * 6,
    
    # Ring 7 (42 items - Outer Driver with 18 Primary CRs on the corners)
    [O] * 42,
    
    # Ring 6 (36 items - Outer Driver with Inner Drivers on the flats)
    [O, O, O, P, O, O] * 6,
    
    # Ring 5 (30 items)
    [S, I, I, I, I] * 6,
    
    # Ring 4 (24 items - Inner Driver with 6 Primary CRs on the corners)
    [I] * 24,
    
    # Ring 3 (18 items - Inner Driver with 6 Secondary CRs on the corners)
    [P, I, I] * 6,
    
    # Ring 2 (12 items - Inner Driver with 6 Primary CRs on the corners)
    [I] * 12,
    
    # Ring 1 (6 items)
    [I] * 6,
    
    # Ring 0 (Center item)
    [P]
]

core_lattice.universes = core_rings
core_lattice.outer = empty_univ

# 7. Final Geometry with Reactor Pressure Vessel
# Define radial boundaries for the RPV
rpv_inner = openmc.ZCylinder(r=230.0)
rpv_outer = openmc.ZCylinder(r=240.0, boundary_type='vacuum')

# Map the regions
core_cell = openmc.Cell(fill=core_lattice, region=-rpv_inner & +z_bottom & -z_top)
rpv_cell = openmc.Cell(fill=rpv_mat, region=+rpv_inner & -rpv_outer & +z_bottom & -z_top)

geometry = openmc.Geometry([core_cell, rpv_cell])

materials.export_to_xml()
geometry.export_to_xml()

# 8. Create Plots & Assign Distinct Colors
plot_colors = {
    fuel: (200, 50, 50),       # Red
    sodium: (150, 200, 255),   # Light Blue
    cladding: (150, 150, 150), # Gray
    b4c: (50, 150, 50),        # Green
    inconel: (150, 50, 200),   # Purple
    shield_mat: (200, 150, 50),# Orange
    gas: (255, 255, 255),      # White
    rpv_mat: (50, 50, 150)     # Dark Blue
}

plots = openmc.Plots()

# Radial (x-y) cross-section of the full core at active core mid-plane (z=155.0 cm)
core_plot_xy = openmc.Plot()
core_plot_xy.filename = 'full_core_xy'
core_plot_xy.basis = 'xy'
core_plot_xy.origin = (0.0, 0.0, 155.0)
core_plot_xy.width = (500.0, 500.0)
core_plot_xy.pixels = (2500, 2500)
core_plot_xy.color_by = 'material'
core_plot_xy.colors = plot_colors
plots.append(core_plot_xy)

# Axial (x-z) cross-section of the full core through the center
core_plot_xz = openmc.Plot()
core_plot_xz.filename = 'full_core_xz'
core_plot_xz.basis = 'xz'
core_plot_xz.origin = (0.0, 0.0, 185.0) 
core_plot_xz.width = (500.0, 370.0)
core_plot_xz.pixels = (2500, 2500)
core_plot_xz.color_by = 'material'
core_plot_xz.colors = plot_colors
plots.append(core_plot_xz)

# Radial (x-y) cross-section of a single assembly (zoomed in at the origin)
assembly_plot_xy = openmc.Plot()
assembly_plot_xy.filename = 'assembly_xy'
assembly_plot_xy.basis = 'xy'
assembly_plot_xy.origin = (16.22, 0.0, 155.0) 
assembly_plot_xy.width = (18.0, 18.0) 
assembly_plot_xy.pixels = (800, 800)
assembly_plot_xy.color_by = 'material'
assembly_plot_xy.colors = plot_colors
plots.append(assembly_plot_xy)

plots.export_to_xml()

# Run OpenMC in plotting mode (generates .ppm files)
openmc.plot_geometry()

# 9. Process Images with Matplotlib to Add Axes and Legends
mat_labels = {
    'TRU-W-10Zr Fuel': (200/255, 50/255, 50/255),
    'Sodium Coolant': (150/255, 200/255, 255/255),
    'HT9 Cladding': (150/255, 150/255, 150/255),
    'B4C Absorber': (50/255, 150/255, 50/255),
    'Inconel-600': (150/255, 50/255, 200/255),
    'Radial Shield (Fe)': (200/255, 150/255, 50/255),
    'Fission Gas / Void': (255/255, 255/255, 255/255),
    'SS316 RPV': (50/255, 50/255, 150/255)
}
legend_patches = [mpatches.Patch(color=c, label=l) for l, c in mat_labels.items()]

plot_info = {
    'full_core_xy': {
        'extent': [-250.0, 250.0, -250.0, 250.0], 
        'xlabel': 'X (cm)', 'ylabel': 'Y (cm)', 
        'title': 'Full Core Radial Cross-Section'
    },
    'full_core_xz': {
        'extent': [-250.0, 250.0, 0.0, 370.0], 
        'xlabel': 'X (cm)', 'ylabel': 'Z (cm)', 
        'title': 'Full Core Axial Cross-Section'
    },
    'assembly_xy': {
        'extent': [16.22 - 9.0, 16.22 + 9.0, -9.0, 9.0], 
        'xlabel': 'X (cm)', 'ylabel': 'Y (cm)', 
        'title': 'Inner Assembly Radial Cross-Section'
    }
}

# Apply formatting and save as PNGs
for name, info in plot_info.items():
    ppm_file = f"{name}.ppm"
    png_file = f"{name}.png"
    
    # Check if OpenMC generated a .ppm or .png file natively
    raw_file = ppm_file if os.path.exists(ppm_file) else (png_file if os.path.exists(png_file) else None)
    
    if raw_file:
        # Load the raw image into memory
        img = plt.imread(raw_file)
        
        # Initialize figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Plot image with physical dimensions
        ax.imshow(img, extent=info['extent'])
        ax.set_xlabel(info['xlabel'])
        ax.set_ylabel(info['ylabel'])
        ax.set_title(info['title'])
        
        # Add legend outside the plot box
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        ax.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1, 0.5), framealpha=1.0)
        
        # Save the formatted image, overwriting the raw .png if necessary
        plt.savefig(png_file, bbox_inches='tight', dpi=300)
        plt.close()
        
        # Clean up the raw .ppm file if it was used
        if raw_file == ppm_file:
            os.remove(ppm_file)
            
        print(f"Formatted and saved {png_file}")
    else:
        print(f"Warning: Could not find raw plot output for {name}")

# 10. Define Simulation Settings and Tallies
settings = openmc.Settings()
settings.batches = 100
settings.inactive = 20
settings.particles = 100000

lower_left = [-230.0, -230.0, 110.0]
upper_right = [230.0, 230.0, 200.0]
spatial_dist = openmc.stats.Box(lower_left, upper_right, only_fissionable=True)

source = openmc.IndependentSource(space=spatial_dist)
settings.source = source

settings.export_to_xml()

tallies = openmc.Tallies()

mesh = openmc.RegularMesh()
mesh.dimension = [200, 200]
mesh.lower_left = [-250.0, -250.0]
mesh.upper_right = [250.0, 250.0]
mesh_filter = openmc.MeshFilter(mesh)

flux_mesh_tally = openmc.Tally(name='flux_mesh')
flux_mesh_tally.filters = [mesh_filter]
flux_mesh_tally.scores = ['flux']
tallies.append(flux_mesh_tally)

e_points = np.logspace(-5, 8, 200)
e_func_filter = openmc.EnergyFunctionFilter(e_points, e_points)

e_mesh_tally = openmc.Tally(name='energy_mesh')
e_mesh_tally.filters = [mesh_filter, e_func_filter]
e_mesh_tally.scores = ['flux']
tallies.append(e_mesh_tally)

energy_bins = np.logspace(-3, 7, 500)
energy_filter = openmc.EnergyFilter(energy_bins)
univ_filter = openmc.UniverseFilter([inner_fuel_assembly_univ, outer_fuel_assembly_univ])

spectra_tally = openmc.Tally(name='assembly_spectra')
spectra_tally.filters = [univ_filter, energy_filter]
spectra_tally.scores = ['flux']
tallies.append(spectra_tally)

tallies.export_to_xml()

# 11. Run the Simulation
openmc.run()

# 12. Post-Process and Plot Tallies
sp = openmc.StatePoint(f'statepoint.{settings.batches}.h5')

flux_tally = sp.get_tally(name='flux_mesh')
flux_mean = flux_tally.get_slice(scores=['flux']).mean.reshape(200, 200)

plt.figure(figsize=(8, 6))
plt.imshow(flux_mean, origin='lower', extent=[-250, 250, -250, 250], cmap='viridis')
plt.colorbar(label='Neutron Flux (Arbitrary Units)')
plt.title('Core Radial Flux Distribution')
plt.xlabel('X (cm)')
plt.ylabel('Y (cm)')
plt.savefig('flux_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

e_tally = sp.get_tally(name='energy_mesh')
e_flux_mean = e_tally.get_slice(scores=['flux']).mean.reshape(200, 200)

avg_energy = np.zeros_like(flux_mean)
mask = flux_mean > 0
avg_energy[mask] = e_flux_mean[mask] / flux_mean[mask]

plt.figure(figsize=(8, 6))
plt.imshow(avg_energy / 1e6, origin='lower', extent=[-250, 250, -250, 250], cmap='plasma')
plt.colorbar(label='Average Energy (MeV)')
plt.title('Average Neutron Energy Distribution')
plt.xlabel('X (cm)')
plt.ylabel('Y (cm)')
plt.savefig('avg_energy_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

spec_tally = sp.get_tally(name='assembly_spectra')

inner_flux = spec_tally.get_values(
    filters=[openmc.UniverseFilter], 
    filter_bins=[(inner_fuel_assembly_univ.id,)], 
    value='mean'
).flatten()

outer_flux = spec_tally.get_values(
    filters=[openmc.UniverseFilter], 
    filter_bins=[(outer_fuel_assembly_univ.id,)], 
    value='mean'
).flatten()

energies = energy_filter.values
du = np.log(energies[1:] / energies[:-1])
e_mid = 0.5 * (energies[1:] + energies[:-1])

inner_phi_lethargy = inner_flux / du
outer_phi_lethargy = outer_flux / du

plt.figure(figsize=(8, 6))
plt.plot(e_mid, inner_phi_lethargy, label='Inner Driver Assemblies')
plt.plot(e_mid, outer_phi_lethargy, label='Outer Driver Assemblies')
plt.xscale('log')
plt.xlabel('Energy (eV)')
plt.ylabel('Flux per Unit Lethargy ($\phi / \Delta u$)')
plt.title('Neutron Spectrum in Fuel Assemblies')
plt.legend()
plt.grid(True, which="both", ls="--", alpha=0.5)
plt.savefig('assembly_spectra.png', dpi=300, bbox_inches='tight')
plt.close()

print("Tally plots successfully generated and saved.")