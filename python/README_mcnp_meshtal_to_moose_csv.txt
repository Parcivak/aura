MCNP MESHTAL -> MOOSE axial power-shape CSV
==========================================

Script: mcnp_meshtal_to_moose_csv.py

What it does
------------
- Reads a standard text MESHTAL mesh-tally output for one Cartesian FMESH tally.
- Expects the unbinned X Y Z Result Rel Error columns.
- Collapses the 3-D mesh into one axial score per z-plane by summing across x/y.
- Writes a headerless, two-column CSV suitable for MOOSE PiecewiseLinear:
      z [m], dimensionless shape value
- Writes a separate diagnostics CSV with each axial plane's raw summed result.
- Streams the file, so it does not load the 7.4-million-cell mesh into memory.

No third-party Python packages are required.

First: check the MCNP tally
---------------------------
In the supplied input snippet, all FMESH lines start with 'c'. They are comments,
so MCNP will not execute the mesh tally until the card is uncommented.

Also, FMESH14:n by itself scores a neutron track-length mesh tally (not inherently
fission heating). For a fission-rate density mesh tally, MCNP's FM multiplier
convention commonly uses an FM card with reaction -6, for example:

    FMESH14:n GEOM=xyz ORIGIN=-210.0 -210.0 0.0
             IMESH=420.0 IINTS=200
             JMESH=420.0 JINTS=200
             KMESH=388.5 KINTS=185
    FM14:n -1 0 -6

Validate the multiplier against your MCNP version, materials, intended score, and
manual before using it. This scores a fission-rate density distribution, not
physical watts by itself. MOOSE's HeatSourceFromTotalPower expects a shape; its
separate TotalPower component supplies the total power. If you need a true local
energy-deposition field rather than a fission-rate proxy, use an appropriate
heating/energy-deposition tally and confirm what materials it includes. Do not
assume that a generic heating tally is fission-only.

Run
---

    python mcnp_meshtal_to_moose_csv.py meshtal --tally 14

The supplied mesh dimensions are the defaults (200 x 200 x 185). The command
writes mcnp_axial_shape.csv and mcnp_axial_profile_diagnostics.csv in the current
directory. Replace `meshtal` with the actual path/name of your mesh-tally output.

To match a 300 cm active core length, if it really is aligned with MCNP z=0:

    python mcnp_meshtal_to_moose_csv.py meshtal --tally 14 \
        --z-min-cm 0 --z-max-cm 300

This makes the function cover z=0 to z=3.0 m and interpolates the profile at the
cut endpoints. Only use those limits if they match the active heat structure in
MOOSE. The pasted FMESH geometry spans 0 to 388.5 cm (3.885 m), which is longer
than a 300 cm fuel-height definition.

If mesh dimensions change, pass matching values, for example:

    python mcnp_meshtal_to_moose_csv.py meshtal --tally 14 \
        --nx 200 --ny 200 --nz 185

The script intentionally fails rather than silently accepting a missing, partial,
or incompatible tally table.

MOOSE function
--------------
Use the shape CSV as your `PiecewiseLinear` data file, e.g.:

    [Functions]
      [mcnp_axial_shape]
        type = PiecewiseLinear
        data_file = mcnp_axial_shape.csv
        format = rows
        x_index_in_file = 0
        y_index_in_file = 1
        axis = z
      []
    []

MOOSE normalizes the shape function internally when used by
HeatSourceFromTotalPower; the CSV values are therefore dimensionless relative
values, not watts or W/m^3. Keep the raw diagnostic profile for plotting/checking.

Assumptions and limitations
---------------------------
- Standard text MESHTAL output, not a binary/XDMF file.
- A Cartesian mesh with no energy/time bins, with columns X Y Z Result Rel Error.
- Uniform voxel sizes; the provided mesh has uniform x/y/z bins. With equal voxel
  volumes, summing the scores across x/y gives the correct relative axial profile.
- The axial profile is only physically appropriate for fuel heating if the MCNP
  tally itself scores fuel fission rate/heating appropriately. This parser cannot
  infer that from the MESHTAL values alone.
