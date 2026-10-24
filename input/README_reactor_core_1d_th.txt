Starter files
=============

reactor_core_1d_th.i
  MOOSE Thermal Hydraulics single-phase 1D equivalent-core model.

mcnp_axial_shape.csv
  Example-only axial profile. Replace with MCNP axial tally-derived values.
  Format: z [m], relative axial heating (no header; two numeric columns).
  The default .i file uses linear interpolation versus global z.

Before using results:
1. Verify all lengths are in metres. If the Reactor mesh uses centimetres (e.g. 300 cm),
   convert its active length to metres for this TH model and the CSV z coordinates.
2. Set core_flow_area, core_wetted_perimeter, core rod count, rod radii, core_power,
   m_dot_core, T_in, p_out, and material properties from your design.
3. Replace the sample axial profile with MCNP values at axial bin centres in metres.
   If tally bins have unequal heights, use a suitable length-weighted representation.
4. Scale MCNP tallies to a total core power in watts, or set core_power from the known
   rated/core power. The function values specify shape; they do not determine total power.
5. The helium properties, gap effective conductivity, constant heat-transfer coefficient,
   and solid properties are placeholders. Validate/update them before interpreting results.
6. This is a one-channel lumped model: it does not preserve pin-to-pin, radial, assembly-
   to-assembly, bypass-flow, or local 3D power variations. The detailed Reactor-module mesh
   is used to derive equivalent hydraulic parameters, not as the mesh solved by this .i file.

Run with a MOOSE executable built with the ThermalHydraulics module, for example:
  ./your-app-opt -i reactor_core_1d_th.i
