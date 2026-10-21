import numpy as np
import openmc
import matplotlib.pyplot as plt
import math
import openmc.deplete

# =============================================================================
# 1. MATERIALS DEFINITIONS
# =============================================================================
# Extracting exact materials from pwr_core_source.py
fracu = 238.03 / (238.03 + 15.999 * 2)

fresh_fuel = openmc.Material(name='Fresh HALEU Fuel (19.75%)')
fresh_fuel.set_density('g/cm3', 10.29769)
fresh_fuel.add_nuclide('U235', 0.1975 * fracu, percent_type='wo')
fresh_fuel.add_nuclide('U238', 0.8025 * fracu, percent_type='wo')
fresh_fuel.add_nuclide('O16', 1 - fracu, percent_type='wo')

spent_fuel = openmc.Material(name='Spent Fuel')
spent_fuel.set_density('g/cm3', 10.29769)
spent_fuel.add_nuclide('U238', 0.9406 * fracu, percent_type='wo')
spent_fuel.add_nuclide('U235', 0.0103 * fracu, percent_type='wo')
spent_fuel.add_nuclide('U236', 0.0044 * fracu, percent_type='wo')
spent_fuel.add_nuclide('U234', 0.0002 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Pu238', 0.00018 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Pu239', 0.00567 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Pu240', 0.00221 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Pu241', 0.00119 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Pu242', 0.00049 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Np237', 0.00043 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Am241', 0.00022 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Am243', 0.0001 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Tc99', 0.00081 * fracu, percent_type='wo')
spent_fuel.add_nuclide('I129', 0.00017 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Cs135', 0.00131 * fracu, percent_type='wo')
spent_fuel.add_nuclide('Zr93', 0.00071 * fracu, percent_type='wo')
spent_fuel.add_nuclide('O16', 1 - fracu, percent_type='wo')

clad = openmc.Material(name='Zircaloy-4 Cladding')
clad.set_density('g/cm3', 6.56) # From MCNP m3 card
clad.add_nuclide('Zr90', 0.50244)
clad.add_nuclide('Zr91', 0.10957)
clad.add_nuclide('Zr92', 0.16748)
clad.add_nuclide('Zr94', 0.16973)
clad.add_nuclide('Zr96', 0.02734)

helium = openmc.Material(name='Helium Gap')
helium.set_density('g/cm3', 0.005) # From MCNP m2 card
helium.add_nuclide('He4', 1.0)

cold_water = openmc.Material(name='Cold Water Coolant')
cold_water.set_density('atom/b-cm', 0.07416)
cold_water.add_nuclide('H1', 2.0)
cold_water.add_nuclide('O16', 1.0)
cold_water.add_s_alpha_beta('c_H_in_H2O')

reflector = openmc.Material(name='Fast Reflector')
reflector.set_density('g/cm3', 11.34)
reflector.add_element('Pb', 1.0)

reflector2 = openmc.Material(name='Fast Reflector 2')
reflector2.set_density('g/cm3', 19.25)
reflector2.add_element('W', 1.0)

# 1. Calculate the volume of a single modeled fuel pin
# V = pi * r^2 * h
pin_radius = 0.4096 
pin_height = 485.153 - (-100.0) # 585.153 cm
pin_volume = math.pi * (pin_radius**2) * pin_height # ~308.41 cm^3

# 2. Total Fresh Fuel Volume
# 264 pins/assembly * 89 fresh assemblies
fresh_fuel.volume = pin_volume * 264 * 89
fresh_fuel.depletable = True

# 3. Total Spent Fuel Volume
# 264 pins/assembly * 68 spent assemblies
spent_fuel.volume = pin_volume * 264 * 68
spent_fuel.depletable = True

materials = openmc.Materials([fresh_fuel, spent_fuel, clad, helium, cold_water, reflector, reflector2])

# =============================================================================
# 2. GEOMETRY: SURFACES & PIN CELLS (Translated from MCNP)
# =============================================================================
# MCNP Surface Cards 1, 2, and 3
fuel_or = openmc.ZCylinder(r=0.4096)
gap_or = openmc.ZCylinder(r=0.41778)
clad_or = openmc.ZCylinder(r=0.47498)

# MCNP Guide Tube / Control Rod Surfaces 13 and 14
gt_inner = openmc.ZCylinder(r=0.5715)
gt_outer = openmc.ZCylinder(r=0.612)

# Fresh Fuel Pin Universe
cell_fresh_fuel = openmc.Cell(fill=fresh_fuel, region=-fuel_or)
cell_fresh_gap = openmc.Cell(fill=helium, region=+fuel_or & -gap_or)
cell_fresh_clad = openmc.Cell(fill=clad, region=+gap_or & -clad_or)
cell_fresh_cool = openmc.Cell(fill=helium, region=+clad_or)
fresh_pin = openmc.Universe(cells=[cell_fresh_fuel, cell_fresh_gap, cell_fresh_clad, cell_fresh_cool])

# Spent Fuel Pin Universe
cell_spent_fuel = openmc.Cell(fill=spent_fuel, region=-fuel_or)
cell_spent_gap = openmc.Cell(fill=helium, region=+fuel_or & -gap_or)
cell_spent_clad = openmc.Cell(fill=clad, region=+gap_or & -clad_or)
cell_spent_cool = openmc.Cell(fill=helium, region=+clad_or)
spent_pin = openmc.Universe(cells=[cell_spent_fuel, cell_spent_gap, cell_spent_clad, cell_spent_cool])

# Guide Tube Universe (Empty/Water-filled)
cell_gt_inner = openmc.Cell(fill=helium, region=-gt_inner)
cell_gt_clad = openmc.Cell(fill=clad, region=+gt_inner & -gt_outer)
cell_gt_outer = openmc.Cell(fill=helium, region=+gt_outer)
guide_pin = openmc.Universe(cells=[cell_gt_inner, cell_gt_clad, cell_gt_outer])

# =============================================================================
# 3. LATTICES: FRESH & SPENT ASSEMBLIES
# =============================================================================
# Assembly Pitch derived from MCNP px 0.63 -> 1.26 cm pitch
pitch = 1.26 
# Standard AP1000 17x17 Guide Tube Layout Locations
tube_x = np.array([5, 8, 11, 3, 13, 2, 5, 8, 11, 14, 2, 5, 8, 11, 14, 2, 5, 8, 11, 14, 3, 13, 5, 8, 11])
tube_y = np.array([2, 2, 2, 3, 3, 5, 5, 5, 5, 5, 8, 8, 8, 8, 8, 11, 11, 11, 11, 11, 13, 13, 14, 14, 14])

# Fresh HALEU Assembly
fresh_assembly = openmc.RectLattice(name='Fresh 19.75% HALEU Assembly')
fresh_assembly.pitch = (pitch, pitch)
fresh_assembly.lower_left = (-10.71, -10.71)
fresh_universes = np.tile(fresh_pin, (17, 17))
fresh_universes[tube_x, tube_y] = guide_pin
fresh_assembly.universes = fresh_universes

# Spent Fuel Assembly
spent_assembly = openmc.RectLattice(name='Spent Fuel Assembly')
spent_assembly.pitch = (pitch, pitch)
spent_assembly.lower_left = (-10.71, -10.71)
spent_universes = np.tile(spent_pin, (17, 17))
spent_universes[tube_x, tube_y] = guide_pin
spent_assembly.universes = spent_universes

# Encapsulate lattices into cells for the core geometry
# Bounding box for a single assembly (21.42 x 21.42 cm)
assembly_box = openmc.model.RectangularPrism(width=21.42, height=21.42)

# =============================================================================
# 5. ADDITIONAL MATERIALS FOR STRUCTURAL COMPONENTS
# =============================================================================
# SS304 for the Core Barrel (From MCNP m6)
ss304 = openmc.Material(name='SS304 Core Barrel')
ss304.set_density('g/cm3', 7.92)
ss304.add_element('Fe', 0.684, 'wo')
ss304.add_element('Cr', 0.19, 'wo')
ss304.add_element('Ni', 0.086, 'wo')
ss304.add_element('Mn', 0.02, 'wo')

# Carbon Steel for the Pressure Vessel (From MCNP m7)
carbon_steel = openmc.Material(name='SA-508 Carbon Steel RPV')
carbon_steel.set_density('g/cm3', 7.80)
carbon_steel.add_element('Fe', 0.965, 'wo')
carbon_steel.add_element('C', 0.009, 'wo')
carbon_steel.add_element('Mn', 0.013, 'wo')

materials.extend([ss304, carbon_steel])
materials.export_to_xml()

# =============================================================================
# 6. UNIVERSES FOR CORE LATTICE
# =============================================================================
# MCNP defined the assembly pitch (px 10.7, px -10.7) -> 21.4 cm bounding box
assembly_pitch = 21.4
assembly_prism = openmc.model.RectangularPrism(width=assembly_pitch, height=assembly_pitch)

# Convert the previously defined lattices into discrete universes
fresh_univ = openmc.Universe(name='Fresh Assembly Univ', cells=[openmc.Cell(fill=fresh_assembly)])
spent_univ = openmc.Universe(name='Spent Assembly Univ', cells=[openmc.Cell(fill=spent_assembly)])
water_univ = openmc.Universe(name='Water Assembly Univ', cells=[openmc.Cell(fill=reflector)])

# =============================================================================
# 7. CORE LATTICE DEFINITION (Manual Layout)
# =============================================================================
# Create short aliases to make the 17x17 manual grid readable
W = water_univ
F = fresh_univ
S = spent_univ

# Manually construct the 17x17 alternating checkerboard layout.
# You can alter any individual assembly location by swapping F, S, or W.
core_universes = [
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, S, S, S, W, W, W, W, W, W, W],
    [W, W, W, W, W, S, S, F, F, F, S, S, W, W, W, W, W],
    [W, W, W, W, S, F, F, F, F, F, F, F, S, W, W, W, W],
    [W, W, W, S, F, F, F, S, F, S, F, F, F, S, W, W, W],
    [W, W, S, F, F, F, S, F, S, F, S, F, F, F, S, W, W],
    [W, W, S, F, F, S, F, S, F, S, F, S, F, F, S, W, W],
    [W, S, F, F, S, F, S, F, S, F, S, F, S, F, F, S, W],
    [W, S, F, F, F, S, F, S, F, S, F, S, F, F, F, S, W],
    [W, S, F, F, S, F, S, F, S, F, S, F, S, F, F, S, W],
    [W, W, S, F, F, S, F, S, F, S, F, S, F, F, S, W, W],
    [W, W, S, F, F, F, S, F, S, F, S, F, F, F, S, W, W],
    [W, W, W, S, F, F, F, S, F, S, F, F, F, S, W, W, W],
    [W, W, W, W, S, F, F, F, F, F, F, F, S, W, W, W, W],
    [W, W, W, W, W, S, S, F, F, F, S, S, W, W, W, W, W],
    [W, W, W, W, W, W, W, S, S, S, W, W, W, W, W, W, W],
    [W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W, W]
]

core_lattice = openmc.RectLattice(name='Alternating PWR Core')
core_lattice.pitch = (assembly_pitch, assembly_pitch)
core_lattice.lower_left = (-17 * assembly_pitch / 2, -17 * assembly_pitch / 2)
core_lattice.universes = core_universes

# =============================================================================
# 8. CORE MACRO-GEOMETRY & BOUNDARIES
# =============================================================================
# Extracted directly from MCNP surface cards 1000 - 1003 & 1123 - 1124
barrel_inner = openmc.ZCylinder(r=169.85)
barrel_outer = openmc.ZCylinder(r=174.95)
rpv_inner = openmc.ZCylinder(r=202.0)
rpv_outer = openmc.ZCylinder(r=207.87, boundary_type='vacuum')

z_bottom = openmc.ZPlane(z0=-100.0, boundary_type='vacuum')
z_top = openmc.ZPlane(z0=485.153, boundary_type='vacuum')

# Combine bounding geometries to encapsulate the core lattice
core_region = -barrel_inner & +z_bottom & -z_top
cell_core = openmc.Cell(name='Core Lattice Region', fill=core_lattice, region=core_region)

cell_barrel = openmc.Cell(name='Core Barrel', fill=ss304, 
                          region=+barrel_inner & -barrel_outer & +z_bottom & -z_top)

cell_downcomer = openmc.Cell(name='Downcomer', fill=helium, 
                             region=+barrel_outer & -rpv_inner & +z_bottom & -z_top)

cell_rpv = openmc.Cell(name='Pressure Vessel', fill=carbon_steel, 
                       region=+rpv_inner & -rpv_outer & +z_bottom & -z_top)

# Build, encapsulate, and export
root_universe = openmc.Universe(cells=[cell_core, cell_barrel, cell_downcomer, cell_rpv])
geometry = openmc.Geometry(root_universe)
geometry.export_to_xml()

# =============================================================================
# SETTINGS
# =============================================================================
settings = openmc.Settings()
settings.batches = 50
settings.inactive = 10
settings.particles = 5000
settings.source = openmc.IndependentSource(space=openmc.stats.Box([-160, -160, -50], [160, 160, 300]))
settings.export_to_xml()

# =============================================================================
# PLOTTING
# =============================================================================

# Create a matplotlib figure and axis (Wider figsize accommodates the legend)
fig, ax = plt.subplots(figsize=(14, 12))

# Define a dictionary mapping your OpenMC Material objects to colors
mat_colors = {
    fresh_fuel: 'tomato',
    spent_fuel: 'darkred',
    clad: 'silver',
    helium: 'white',
    reflector: 'dodgerblue',
    ss304: 'dimgray',
    carbon_steel: 'black'
}

# Plot the root universe with the explicit colors dictionary and legend enabled
root_universe.plot(
    origin=(0.0, 0.0, 0.0),
    width=(420.0, 420.0),
    pixels=(2000, 2000),
    basis="xy",
    color_by="material",
    colors=mat_colors,  # Satisfies the ValueError requirement
    legend=True,
    legend_kwargs={'bbox_to_anchor': (1.05, 1), 'loc': 'upper left'},
    axes=ax,
)

# Format and save the figure
plt.title("Alternating Core Lattice Cross Section (XY)")
# bbox_inches="tight" ensures the external legend is not cropped out
plt.savefig("core_xy_slice.svg", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 9. TALLIES (Mesh for Flux Heatmap)
# =============================================================================
# Create a regular mesh that covers the entire XY footprint of the core
# (RPV radius is 207.87 cm, so a +/- 210 cm box captures everything)
mesh = openmc.RegularMesh()
mesh.dimension = [200, 200, 1]  # 200x200 resolution in XY, integrated over 1 bin in Z
mesh.lower_left = [-210.0, -210.0, -100.0] # Bounding box matching your z_bottom
mesh.upper_right = [210.0, 210.0, 485.153] # Bounding box matching your z_top

# Create a mesh filter and apply it to a new tally
mesh_filter = openmc.MeshFilter(mesh)
flux_tally = openmc.Tally(name='flux_heatmap')
flux_tally.filters = [mesh_filter]
flux_tally.scores = ['flux']

tallies = openmc.Tallies([flux_tally])
tallies.export_to_xml()

# =============================================================================
# EXECUTION
# =============================================================================
# Create the depletion operator linking your model to the chain file
operator = openmc.deplete.CoupledOperator(
    model=openmc.Model(geometry=geometry, materials=materials, settings=settings, tallies=tallies),
    chain_file="chain_endfb81_fast.xml"
)

# Define the power output and time steps
# Example: 3000 MW thermal power
power = 3000.0e6  # Power in Watts

# Define time steps (e.g., 5 steps of 30 days each = 150 days total)
time_steps = [30.0, 30.0, 30.0, 30.0, 30.0] # In days

# Use the Predictor Integrator to step through time
integrator = openmc.deplete.PredictorIntegrator(
    operator=operator,
    timesteps=time_steps,
    power=power
)

# Run the depletion simulation
print("Starting depletion calculation...")
integrator.integrate()

# =============================================================================
# 10. POST-PROCESSING (Matplotlib Heatmap)
# =============================================================================
# Load the statepoint file (assuming 50 batches as defined in your settings)
#sp = openmc.StatePoint('statepoint.50.h5')

# Extract the flux tally
#tally = sp.get_tally(name='flux_heatmap')

# Get the mean flux values and strip the empty Z-dimension using squeeze()
#flux_mean = tally.get_values(scores=['flux'], value='mean').squeeze()

# Reshape the flat 1D array into a 2D grid matching our 200x200 mesh
#flux_grid = flux_mean.reshape((200, 200))

# Plot the heat map
#fig, ax = plt.subplots(figsize=(10, 8))
# extent aligns the array indices with the physical coordinate space
#im = ax.imshow(flux_grid, origin='lower', extent=[-210, 210, -210, 210], cmap='jet')

#ax.set_xlabel('X Position (cm)')
#ax.set_ylabel('Y Position (cm)')
#ax.set_title('Core Radial Flux Heat Map (XY Integration)')
#fig.colorbar(im, ax=ax, label='Flux (neutron-cm / source-particle)')

#plt.savefig("flux_heatmap.svg", dpi=300, bbox_inches='tight')
#plt.close()

#print("Flux heatmap successfully saved to flux_heatmap.svg")

# Load the depletion results
results = openmc.deplete.Results("depletion_results.h5")

# Extract Time and K-effective
time, k = results.get_keff()
time_days = time / (24 * 60 * 60)

# Extract isotope masses (Assuming Material ID 1 is Fresh, 2 is Spent)
_, u235_fresh = results.get_mass("1", "U235")
_, pu239_spent = results.get_mass("2", "Pu239")

# Extract the new minor actinides from the spent fuel
_, np237_spent = results.get_mass("2", "Np237")
_, am241_spent = results.get_mass("2", "Am241")

# Plotting setup
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# Reactivity Plot
ax1.errorbar(time_days, k[:, 0], yerr=k[:, 1], fmt='-o', color='blue')
ax1.set_xlabel("Time (Days)")
ax1.set_ylabel("K-effective")
ax1.set_title("Core Reactivity vs. Time")
ax1.grid(True)

# Isotopic Mass Plot (Converted to kg for readability)
ax2.plot(time_days, u235_fresh / 1000, '-bo', label='U-235 (Fresh)')
ax2.plot(time_days, pu239_spent / 1000, '-ro', label='Pu-239 (Spent)')
ax2.plot(time_days, np237_spent / 1000, '-go', label='Np-237 (Spent)')
ax2.plot(time_days, am241_spent / 1000, '-mo', label='Am-241 (Spent)')

ax2.set_xlabel("Time (Days)")
ax2.set_ylabel("Mass (kg)")
ax2.set_title("Major & Minor Actinide Inventory vs. Time")
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.savefig("depletion_metrics.png", dpi=300)
print("Saved depletion plots to depletion_metrics.png")