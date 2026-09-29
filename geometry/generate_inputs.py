#!/usr/bin/env python3
"""
generate_inputs.py

Build the initial MCNP -> MOOSE preprocessing pipeline for the Aura reactor.

This script has four primary jobs:

    1. Read the existing MCNP input with MontePy.
    2. Extract useful geometry/material information.
    3. Read MCNP mesh-tally heating data once MCNP has been run.
    4. Generate MOOSE HIT (.i) input files using pyhit.

The intended long-term workflow is:

    MCNP input
        |
        | MontePy
        v
    geometry/material data
        |
        | pyhit
        v
    MOOSE .i input
        |
        | MOOSE
        v
    Exodus .e mesh/output


    MCNP MESHTAL
        |
        | MCNPTools
        v
    q'''(x,y,z)
        |
        | Python
        v
    MOOSE-readable power function
        |
        v
    MOOSE thermal-hydraulics calculation

IMPORTANT:
------------
This is intentionally a STARTING POINT.

MCNP uses constructive solid geometry (CSG), while MOOSE uses a finite-element
mesh. There is no general-purpose "convert arbitrary MCNP CSG to a MOOSE FEM
mesh" operation here. For the reactor, the preferred approach is to extract the
geometric parameters from MCNP and reconstruct the thermal-hydraulic geometry
using MOOSE's Reactor Module.

The same principle applies to materials. MCNP material cards contain nuclear
composition, whereas MOOSE thermal-hydraulic materials need properties such as
density, heat capacity, conductivity, viscosity, etc.

Those two representations therefore require an explicit mapping.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ============================================================================
# THIRD-PARTY LIBRARY IMPORTS
# ============================================================================

# MontePy reads the MCNP input deck.
import montepy


def import_pyhit():
    """
    Import MOOSE's pyhit package.

    pyhit is part of the MOOSE source tree. Depending on how MOOSE was
    installed, the MOOSE Python directory may not already be on sys.path.

    This function first tries the normal import. If that fails, it attempts
    to locate MOOSE using the MOOSE_DIR environment variable.

    If this still fails, you should check your MOOSE environment and make
    sure the pyhit/HIT Python bindings have been built.
    """

    try:
        import pyhit
        return pyhit

    except ImportError:
        pass

    moose_dir = os.environ.get("MOOSE_DIR")

    if moose_dir is None:
        raise RuntimeError(
            "Could not import pyhit and MOOSE_DIR is not set.\n"
            "Set MOOSE_DIR to your MOOSE source directory, then try again."
        )

    moose_python = Path(moose_dir) / "python"

    if not moose_python.is_dir():
        raise RuntimeError(
            f"MOOSE_DIR was set to {moose_dir}, but {moose_python} does not exist."
        )

    sys.path.insert(0, str(moose_python))

    try:
        import pyhit
        return pyhit
    except ImportError as exc:
        raise RuntimeError(
            "Found MOOSE, but pyhit could not be imported.\n"
            "Check that the MOOSE HIT Python bindings have been built."
        ) from exc


pyhit = import_pyhit()


# ============================================================================
# OPTIONAL MCNP OUTPUT LIBRARY
# ============================================================================

def import_mcnptools():
    """
    Import LANL's MCNPTools Python bindings.

    MCNPTools is optional until an MCNP MESHTAL file exists.

    It provides the Python interface:

        from mcnptools import Meshtal

    which lets us read MCNP mesh tally coordinates and values.
    """

    try:
        import mcnptools
        return mcnptools

    except ImportError as exc:
        raise RuntimeError(
            "MCNPTools is not installed/importable.\n"
            "You only need this function once you begin reading MESHTAL data."
        ) from exc


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MCNP_INPUT = PROJECT_ROOT / "full-mcnp" / "Aura_MCNP_Model.inp"

GENERATED_DIR = PROJECT_ROOT / "generated"

GEOMETRY_JSON = GENERATED_DIR / "mcnp_geometry.json"

MESH_INPUT = GENERATED_DIR / "reactor_mesh.i"

THM_INPUT = GENERATED_DIR / "thm_channel.i"

POWER_DATA = GENERATED_DIR / "mcnp_power.txt"

# Change this later to the actual MCNP output file.
MESHTAL_FILE = PROJECT_ROOT / "full-mcnp" / "Aura_MCNP_Model.meshtal"


# ============================================================================
# USER-DEFINED MODEL CONFIGURATION
# ============================================================================

@dataclass
class ReactorConfig:
    """
    Configuration values that MCNP may provide or that must be supplied by
    the reactor design team.

    Initially these are placeholders.

    As we learn more about the MCNP model, values in this class should
    increasingly be populated automatically rather than manually.
    """

    # ------------------------------------------------------------------------
    # GEOMETRY
    # ------------------------------------------------------------------------

    # Active fuel height [m].
    fuel_height: float | None = None

    # Fuel radius [m].
    fuel_radius: float | None = None

    # Cladding outer radius [m].
    clad_outer_radius: float | None = None

    # Pin pitch [m].
    pin_pitch: float | None = None

    # Number of fuel pins in x/y directions.
    assembly_nx: int | None = None
    assembly_ny: int | None = None

    # ------------------------------------------------------------------------
    # HELIUM THERMAL-HYDRAULIC CONDITIONS
    # ------------------------------------------------------------------------

    # Inlet temperature [K].
    inlet_temperature: float = 300.0

    # Inlet mass flow rate [kg/s].
    #
    # This is a placeholder. Replace it with the actual design condition.
    inlet_mass_flow: float = 1.0

    # Outlet pressure [Pa].
    outlet_pressure: float = 1.0e6

    # Initial pressure [Pa].
    initial_pressure: float = 1.0e6

    # Initial helium velocity [m/s].
    initial_velocity: float = 0.1

    # ------------------------------------------------------------------------
    # REACTOR POWER
    # ------------------------------------------------------------------------

    # Total reactor/assembly power [W].
    #
    # This can be used to normalize the MCNP heating tally.
    total_power: float | None = None

    # ------------------------------------------------------------------------
    # MCNP TALLY
    # ------------------------------------------------------------------------

    # MCNP mesh-tally number containing energy deposition.
    heating_tally_number: int | None = None


# ============================================================================
# MCNP MATERIAL ROLE MAP
# ============================================================================

# Based on the output you showed, your current toy/full model has:

#     1 = uranium + oxygen
#     2 = helium
#     3 = Zr/Sn/O/Fe/Cr
#     4 = Ni/Cr/Fe/Nb/Mo/...
#     5 = Ag/In/Cd
#     6 = Fe/Cr/Ni/Mn/Si
#     7 = Fe/Mn/C/Ni/Si/...

# DO NOT assume these numbers will remain unchanged.
#
# This map is therefore deliberately kept in one place so it can be changed
# as the MCNP model evolves.

MATERIAL_ROLE_MAP = {
    1: "fuel",
    2: "helium",
    3: "cladding",
    4: "structural",
    5: "control_material",
    6: "structural",
    7: "structural",
}


# ============================================================================
# MCNP READING
# ============================================================================

def load_mcnp_problem(filename: Path):
    """
    Read an MCNP input file with MontePy.

    Parameters
    ----------
    filename:
        Path to the MCNP input deck.

    Returns
    -------
    montepy input object
        The parsed MCNP problem.
    """

    if not filename.exists():
        raise FileNotFoundError(f"MCNP input does not exist: {filename}")

    print(f"Reading MCNP input: {filename}")

    return montepy.read_input(filename)


# ============================================================================
# MATERIAL EXTRACTION
# ============================================================================

def extract_materials(problem) -> list[dict[str, Any]]:
    """
    Extract a simple JSON-serializable representation of the MCNP materials.

    This deliberately does NOT try to convert MCNP nuclear compositions into
    MOOSE thermal properties.

    MCNP materials describe nuclear composition.

    MOOSE thermal-hydraulic materials require quantities such as:

        density
        thermal conductivity
        specific heat
        viscosity
        equation of state
        etc.

    Therefore the result of this function is an intermediate description
    that we will later map to appropriate MOOSE properties.
    """

    materials = []

    for material in problem.materials:

        record = {
            "number": material.number,
            "description": str(material),
            "role": MATERIAL_ROLE_MAP.get(
                material.number,
                "unknown",
            ),
        }

        materials.append(record)

    return materials


# ============================================================================
# CELL EXTRACTION
# ============================================================================

def extract_cells(problem) -> list[dict[str, Any]]:
    """
    Extract MCNP cell information.

    Each MCNP cell can contain:

        material
        density
        CSG geometry
        universe information
        other cell parameters

    We record the information rather than attempting an automatic CSG ->
    finite-element conversion.

    The cell.geometry property is particularly useful for inspecting the CSG
    representation when developing this converter.
    """

    cells = []

    for cell in problem.cells:

        material_number = None

        if cell.material is not None:
            material_number = cell.material.number

        # MontePy exposes mass_density as a cell property.
        #
        # This will be None if the cell does not have a mass-density value
        # available in that representation.
        mass_density = getattr(cell, "mass_density", None)

        # Store the CSG expression as text for inspection.
        geometry_text = None

        try:
            if cell.geometry is not None:
                geometry_text = str(cell.geometry)
        except Exception:
            geometry_text = None

        cells.append(
            {
                "number": cell.number,
                "material_number": material_number,
                "material_role": MATERIAL_ROLE_MAP.get(
                    material_number,
                    "unknown",
                ),
                "mass_density": mass_density,
                "geometry": geometry_text,
                "description": str(cell),
            }
        )

    return cells


# ============================================================================
# SURFACE EXTRACTION
# ============================================================================

def extract_surface_candidates(problem) -> list[dict[str, Any]]:
    """
    Extract MCNP surfaces for inspection.

    MontePy knows how to parse MCNP surfaces, but an arbitrary CSG model is
    not directly equivalent to a MOOSE FEM mesh.

    This function therefore records:

        surface number
        string representation
        likely publicly-accessible geometric parameters

    The latter is intentionally exploratory. Different MCNP surface types
    expose different geometric information.

    This is the function that we will refine once we inspect your actual
    MCNP surface definitions in detail.
    """

    surfaces = []

    candidate_attributes = (
        "radius",
        "x0",
        "y0",
        "z0",
        "A",
        "B",
        "C",
        "D",
        "R",
    )

    for surface in problem.surfaces:

        record = {
            "number": surface.number,
            "description": str(surface),
            "type": type(surface).__name__,
            "parameters": {},
        }

        # Look for common geometric properties without relying on private
        # MontePy implementation details.
        for name in candidate_attributes:

            try:
                value = getattr(surface, name)
            except AttributeError:
                continue

            # Only save simple values.
            if isinstance(value, (int, float, str)):
                record["parameters"][name] = value

        surfaces.append(record)

    return surfaces


# ============================================================================
# COMPLETE MCNP GEOMETRY EXTRACTION
# ============================================================================

def extract_mcnp_geometry(problem) -> dict[str, Any]:
    """
    Extract all the information currently useful to the MOOSE preprocessing
    pipeline.

    This creates an intermediate JSON representation.

    That JSON file is intentionally human-readable. It provides us with a
    debugging checkpoint:

        MCNP -> JSON -> MOOSE

    rather than trying to debug:

        MCNP -> MOOSE

    all at once.
    """

    return {
        "input_file": str(MCNP_INPUT),
        "materials": extract_materials(problem),
        "cells": extract_cells(problem),
        "surfaces": extract_surface_candidates(problem),
    }


# ============================================================================
# GEOMETRY PARAMETER IDENTIFICATION
# ============================================================================

def identify_geometry_parameters(
    geometry_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Identify the actual reactor dimensions from the extracted MCNP data.

    THIS IS THE MAIN FUNCTION THAT WILL NEED TO BE DEVELOPED FOR YOUR MODEL.

    Initially, leave values as None.

    Once we inspect the actual MCNP surfaces, this function should identify
    things such as:

        fuel radius
        gap radius
        clad radius
        pin pitch
        active fuel height
        assembly width
        assembly pin count

    Example logic that will eventually be implemented:

        CZ surface #1 -> fuel radius
        CZ surface #2 -> gap radius
        CZ surface #3 -> clad radius

    and:

        PZ surfaces -> bottom/top fuel height

    and:

        PX/PY surfaces -> assembly bounds/pin positions.

    The exact mapping must come from the actual MCNP geometry, not assumptions.
    """

    geometry = {
        "fuel_radius_m": None,
        "gap_radius_m": None,
        "clad_outer_radius_m": None,
        "pin_pitch_m": None,
        "fuel_height_m": None,
        "assembly_width_m": None,
        "assembly_nx": None,
        "assembly_ny": None,
    }

    # ------------------------------------------------------------------------
    # TODO:
    #
    # Examine geometry_data["surfaces"] and fill these values automatically.
    #
    # Your current MCNP output shows several CZ, PZ, PX and PY surfaces, so
    # this is likely to be straightforward for this particular geometry.
    # ------------------------------------------------------------------------

    return geometry


# ============================================================================
# WRITE GEOMETRY JSON
# ============================================================================

def write_geometry_json(
    geometry_data: dict[str, Any],
    filename: Path,
) -> None:
    """
    Write the extracted MCNP geometry/material data to JSON.

    JSON is used as a debugging/intermediate format. It is not intended to
    become the final MOOSE input format.
    """

    filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open("w") as f:
        json.dump(
            geometry_data,
            f,
            indent=2,
            default=str,
        )

    print(f"Wrote geometry summary: {filename}")


# ============================================================================
# MCNP MESH TALLY READING
# ============================================================================

def read_mcnp_mesh_tally(
    meshtal_file: Path,
    tally_number: int,
) -> dict[str, Any]:
    """
    Read one MCNP MESHTAL tally using MCNPTools.

    MCNPTools exposes:

        GetXRBounds()
        GetYZBounds()
        GetZTBounds()
        GetXRBins()
        GetYZBins()
        GetZTBins()
        GetValue(i, j, k)

    for mesh tallies.

    For a Cartesian mesh these correspond to the x/y/z mesh dimensions.

    The returned raw values remain in the units produced by MCNP.

    Do not normalize them until we know exactly what tally type and
    normalization your MCNP calculation uses.
    """

    mcnptools = import_mcnptools()

    if not meshtal_file.exists():
        raise FileNotFoundError(
            f"MESHTAL file does not exist: {meshtal_file}"
        )

    print(f"Reading MCNP MESHTAL: {meshtal_file}")

    meshtal = mcnptools.Meshtal(str(meshtal_file))

    tally = meshtal.GetTally(tally_number)

    # Mesh boundary coordinates.
    x_bounds = list(tally.GetXRBounds())
    y_bounds = list(tally.GetYZBounds())
    z_bounds = list(tally.GetZTBounds())

    # Mesh-center coordinates.
    x_centers = list(tally.GetXRBins())
    y_centers = list(tally.GetYZBins())
    z_centers = list(tally.GetZTBins())

    nx = len(x_centers)
    ny = len(y_centers)
    nz = len(z_centers)

    values = []

    for k in range(nz):

        for j in range(ny):

            for i in range(nx):

                value = tally.GetValue(i, j, k)

                values.append(float(value))

    return {
        "tally_number": tally_number,
        "x_bounds": x_bounds,
        "y_bounds": y_bounds,
        "z_bounds": z_bounds,
        "x_centers": x_centers,
        "y_centers": y_centers,
        "z_centers": z_centers,
        "nx": nx,
        "ny": ny,
        "nz": nz,
        "values": values,
    }


# ============================================================================
# MCNP POWER NORMALIZATION
# ============================================================================

def normalize_heating_to_total_power(
    mesh_data: dict[str, Any],
    total_power_W: float,
    energy_conversion_J_per_MeV: float = 1.602176634e-13,
) -> list[float]:
    """
    Convert MCNP mesh energy-deposition results into W/m^3 by normalizing
    the entire distribution to a specified reactor power.

    This is intended for MCNP energy-deposition mesh tallies that are
    normalized per source particle.

    The important advantage of this approach is that we do NOT need to know
    the absolute MCNP source rate.

    Suppose MCNP gives:

        q_i = MeV / cm^3 / source particle

    and the mesh cell volume is:

        V_i [cm^3]

    Then:

        E_source = sum(q_i * V_i)

    gives the deposited energy per source particle.

    We calculate the source rate corresponding to the requested reactor
    power and then obtain:

        q_i [W/m^3]

    This should be verified against the exact tally definition in your
    MCNP manual/output.

    IMPORTANT FOR KCODE:
    --------------------
    For a criticality calculation, reactor power normalization has to be
    handled carefully. Do NOT blindly multiply a kcode tally by particles/s.

    Normalizing the calculated spatial distribution to the desired total
    reactor power is often the cleaner route.
    """

    x_bounds = mesh_data["x_bounds"]
    y_bounds = mesh_data["y_bounds"]
    z_bounds = mesh_data["z_bounds"]

    nx = mesh_data["nx"]
    ny = mesh_data["ny"]
    nz = mesh_data["nz"]

    raw_values = mesh_data["values"]

    # First calculate total deposited energy per source particle.
    #
    # MCNP energy deposition mesh tallies are commonly expressed per volume,
    # e.g. MeV/cm^3/source particle.
    deposited_MeV_per_source = 0.0

    index = 0

    for k in range(nz):

        dz_cm = z_bounds[k + 1] - z_bounds[k]

        for j in range(ny):

            dy_cm = y_bounds[j + 1] - y_bounds[j]

            for i in range(nx):

                dx_cm = x_bounds[i + 1] - x_bounds[i]

                volume_cm3 = dx_cm * dy_cm * dz_cm

                deposited_MeV_per_source += (
                    raw_values[index] * volume_cm3
                )

                index += 1

    deposited_J_per_source = (
        deposited_MeV_per_source
        * energy_conversion_J_per_MeV
    )

    if deposited_J_per_source <= 0.0:

        raise ValueError(
            "MCNP heating tally integrates to zero or a negative value."
        )

    # Number of source particles per second required to produce the desired
    # total reactor power.
    source_rate = total_power_W / deposited_J_per_source

    print(
        "Calculated equivalent MCNP source rate:",
        source_rate,
        "particles/s"
    )

    # Convert every mesh bin from:
    #
    #     MeV/cm^3/source
    #
    # to:
    #
    #     W/m^3
    #
    # using:
    #
    #     MeV/cm^3
    #       *
    #     J/MeV
    #       *
    #     source/s
    #       *
    #     1e6 cm^3/m^3
    #

    conversion = (
        energy_conversion_J_per_MeV
        * source_rate
        * 1.0e6
    )

    return [
        value * conversion
        for value in raw_values
    ]


# ============================================================================
# WRITE MOOSE POWER FUNCTION DATA
# ============================================================================

def write_moose_power_data(
    mesh_data: dict[str, Any],
    power_values_W_m3: list[float],
    filename: Path,
) -> None:
    """
    Write MCNP-derived power data in the format expected by MOOSE's
    PiecewiseMultilinear function.

    MOOSE supports multidimensional PiecewiseMultilinear functions using
    data files containing:

        AXIS X
        ...
        AXIS Y
        ...
        AXIS Z
        ...
        DATA
        ...

    We use the MCNP mesh-bin CENTERS as the interpolation coordinates.

    NOTE:
    -----
    MCNP mesh tallies are generally cell-centered data while
    PiecewiseMultilinear performs interpolation. This is a good first
    implementation.

    Once the model is working, PiecewiseMulticonstant can be investigated
    if a piecewise-constant representation matching the MCNP tally cells is
    preferred.
    """

    filename.parent.mkdir(parents=True, exist_ok=True)

    x = mesh_data["x_centers"]
    y = mesh_data["y_centers"]
    z = mesh_data["z_centers"]

    nx = mesh_data["nx"]
    ny = mesh_data["ny"]
    nz = mesh_data["nz"]

    with filename.open("w") as f:

        f.write("# MCNP-derived volumetric heat generation [W/m^3]\n")
        f.write("# Data ordering: x fastest, then y, then z\n\n")

        f.write("AXIS X\n")
        f.write(" ".join(f"{value:.12e}" for value in x))
        f.write("\n\n")

        f.write("AXIS Y\n")
        f.write(" ".join(f"{value:.12e}" for value in y))
        f.write("\n\n")

        f.write("AXIS Z\n")
        f.write(" ".join(f"{value:.12e}" for value in z))
        f.write("\n\n")

        f.write("DATA\n")

        index = 0

        for k in range(nz):

            for j in range(ny):

                for i in range(nx):

                    f.write(
                        f"{power_values_W_m3[index]:.12e}\n"
                    )

                    index += 1

    print(f"Wrote MOOSE power data: {filename}")


# ============================================================================
# MOOSE INPUT TEMPLATE
# ============================================================================

# This is deliberately a BEGINNER thermal-hydraulics model.
#
# It represents a single helium flow channel.
#
# Once this works, we'll replace the simple channel/heat source representation
# with the actual fuel assembly/subchannel geometry.

THM_TEMPLATE = r"""
# ============================================================================
# Aura reactor thermal-hydraulics input
#
# GENERATED AUTOMATICALLY FROM THE MCNP MODEL.
#
# Edit the Python generator rather than manually changing values that are
# supposed to come from MCNP.
#
# MOOSE THM uses SI units:
#
#     length       m
#     mass         kg
#     time         s
#     temperature  K
#     pressure     Pa
# ============================================================================


# ----------------------------------------------------------------------------
# GLOBAL SIMULATION PARAMETERS
# ----------------------------------------------------------------------------

T_in = 300.0
m_dot_in = 1.0
p_out = 1.0e6


[GlobalParams]

  # Initial pressure of the fluid.
  initial_p = 1.0e6

  # Small nonzero initial velocity.
  initial_vel = 0.1

  # Initial temperature.
  initial_T = 300.0

  # No gravity for the initial model.
  #
  # CHANGE THIS when you model the actual vertical reactor.
  gravity_vector = '0 0 0'

  # Reconstruction option used by current THM tutorial examples.
  rdg_slope_reconstruction = full

  # Closure relation object.
  closures = thm_closures

  # Default fluid properties.
  fp = he

[]


# ----------------------------------------------------------------------------
# HELIUM FLUID PROPERTIES
# ----------------------------------------------------------------------------

[FluidProperties]

  [he]

    type = IdealGasFluidProperties

    # Helium molar mass [kg/mol].
    molar_mass = 4.0e-3

    # Ratio cp/cv.
    gamma = 1.67

    # ------------------------------------------------------------------------
    # PLACEHOLDERS:
    #
    # These are constant values for the initial model.
    #
    # For the actual reactor, replace them with appropriate temperature/
    # pressure-dependent helium property data if necessary.
    # ------------------------------------------------------------------------

    thermal_conductivity = 0.2556
    mu = 3.22639e-5

  []

[]


# ----------------------------------------------------------------------------
# THERMODYNAMIC CLOSURES
# ----------------------------------------------------------------------------

[Closures]

  [thm_closures]
    type = Closures1PhaseTHM
  []

[]


# ----------------------------------------------------------------------------
# THERMAL-HYDRAULIC COMPONENTS
# ----------------------------------------------------------------------------

[Components]

  # --------------------------------------------------------------------------
  # INLET
  #
  # Current starting condition:
  #
  #     prescribed mass flow rate
  #     prescribed inlet temperature
  #
  # --------------------------------------------------------------------------

  [inlet]

    type = InletMassFlowRateTemperature1Phase

    input = 'core_channel:in'

    m_dot = 1.0
    T = 300.0

  []


  # --------------------------------------------------------------------------
  # MAIN HELIUM FLOW CHANNEL
  # --------------------------------------------------------------------------

  [core_channel]

    type = FlowChannel1Phase

    position = '0 0 0'

    orientation = '0 0 1'

    # Active length [m].
    length = 1.0

    # Number of axial flow elements.
    n_elems = 25

    # ------------------------------------------------------------------------
    # PLACEHOLDERS:
    #
    # For the real assembly these need to be calculated from the PWR-style
    # fuel pin lattice.
    #
    # A       = coolant flow area
    # D_h     = hydraulic diameter
    # ------------------------------------------------------------------------

    A = 1.0e-3
    D_h = 1.0e-2

  []


  # --------------------------------------------------------------------------
  # OUTLET
  # --------------------------------------------------------------------------

  [outlet]

    type = Outlet1Phase

    input = 'core_channel:out'

    p = 1.0e6

  []


  # ==========================================================================
  # MCNP POWER DISTRIBUTION -- OPTIONAL
  # ==========================================================================
  #
  # Once Python has generated:
  #
  #     generated/mcnp_power.txt
  #
  # this function can be enabled.
  #
  # PiecewiseMultilinear can represent 3-D x/y/z data.
  #
  # --------------------------------------------------------------------------

  # [mcnp_power]
  #
  #   type = PiecewiseMultilinear
  #
  #   data_file = mcnp_power.txt
  #
  # []


  # ==========================================================================
  # HEAT STRUCTURE -- TODO
  # ==========================================================================
  #
  # This is where the actual fuel/clad thermal model will eventually go.
  #
  # Possible eventual approach:
  #
  #     HeatStructureFromFile3D
  #
  # using an Exodus mesh generated from the reactor geometry.
  #
  # Example skeleton:
  #
  # [fuel_heat_structure]
  #
  #   type = HeatStructureFromFile3D
  #
  #   file = reactor_mesh_in.e
  #
  #   position = '0 0 0'
  #
  #   initial_T = 300.0
  #
  # []
  #
  #
  # Then:
  #
  # [heat_generation]
  #
  #   type = HeatSourceFromTotalPower
  #
  #   hs = fuel_heat_structure
  #
  #   regions = 'fuel'
  #
  #   power = total_power
  #
  #   power_fraction = 1.0
  #
  #   power_shape_function = mcnp_power
  #
  # []
  #
  #
  # And:
  #
  # [total_power]
  #
  #   type = TotalPower
  #
  #   power = 1.0e6
  #
  # []
  #
  # These are deliberately left inactive until the mesh has named fuel
  # regions that MOOSE can identify.
  #
  # ==========================================================================

[]


# ----------------------------------------------------------------------------
# PRESSURE DROP MONITORING
# ----------------------------------------------------------------------------

[Postprocessors]

  [core_p_in]

    type = SideAverageValue

    boundary = 'core_channel:in'

    variable = p

  []


  [core_p_out]

    type = SideAverageValue

    boundary = 'core_channel:out'

    variable = p

  []


  [core_delta_p]

    type = ParsedPostprocessor

    pp_names = 'core_p_in core_p_out'

    expression = 'core_p_in - core_p_out'

  []

[]


# ----------------------------------------------------------------------------
# LINEAR / NONLINEAR PRECONDITIONING
# ----------------------------------------------------------------------------

[Preconditioning]

  [pc]

    type = SMP

    full = true

  []

[]


# ----------------------------------------------------------------------------
# EXECUTIONER
# ----------------------------------------------------------------------------

[Executioner]

  # Transient is a useful initial choice for THM.
  type = Transient

  solve_type = NEWTON

  line_search = basic

  start_time = 0.0

  end_time = 100.0

  dt = 1.0

  petsc_options_iname = '-pc_type'

  petsc_options_value = 'lu'

  nl_rel_tol = 1e-8

  nl_abs_tol = 1e-8

  nl_max_its = 25

[]


# ----------------------------------------------------------------------------
# OUTPUT
# ----------------------------------------------------------------------------

[Outputs]

  exodus = true

  execute_on = 'initial timestep_end'

[]

"""


# ============================================================================
# MOOSE MESH TEMPLATE
# ============================================================================

# This is intentionally a simple generated mesh.
#
# Once the extraction functions are developed, replace this with:
#
#     PolygonConcentricCircleMeshGenerator
#     PatternedCartesianMeshGenerator
#     extrusion / assembly mesh generators
#
# from the Reactor Module.
#
# Doing this in stages makes debugging dramatically easier.

MESH_TEMPLATE = r"""
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
    xmax =  0.01

    ymin = -0.01
    ymax =  0.01

    zmin = 0.0
    zmax = 1.0

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
"""


# ============================================================================
# PYHIT HELPERS
# ============================================================================

def add_parameter_comment(node, parameter: str, comment: str) -> None:
    """
    Attach a comment to a MOOSE parameter.

    This is useful for documenting automatically generated values.
    """

    try:
        node.setComment(parameter, comment)
    except Exception:
        # A comment is helpful but should never prevent generation.
        pass


def find_node(root, path: str):
    """
    Find a MOOSE HIT node by its full path.

    Example:

        /Mesh/generated_mesh

    Returns
    -------
    pyhit.Node
        The requested node.

    Raises
    ------
    RuntimeError
        If the requested node cannot be found.
    """

    node = root

    # Remove leading slash.
    parts = [
        part
        for part in path.strip("/").split("/")
        if part
    ]

    for part in parts:

        next_node = None

        for child in node.children:

            if child.name == part:
                next_node = child
                break

        if next_node is None:
            raise RuntimeError(
                f"Could not find MOOSE HIT node: {path}"
            )

        node = next_node

    return node


def load_moose_template(template: str):
    """
    Parse a MOOSE HIT input template into a pyhit tree.

    We use pyhit.parse rather than assembling raw .i text ourselves.

    This gives us the advantages of:

        - MOOSE's own input parser
        - structured modification
        - formatting
        - comments
        - fewer string-concatenation errors
    """

    return pyhit.parse(template)


# ============================================================================
# GENERATE THE MESH INPUT
# ============================================================================

def generate_mesh_input(
    config: ReactorConfig,
    geometry: dict[str, Any],
    output_file: Path,
) -> None:
    """
    Generate the MOOSE mesh input file.

    At first this creates a simple 3-D rectangular mesh.

    As the MCNP geometry extraction is developed, the values below should be
    replaced by the Reactor Module mesh-generator hierarchy.
    """

    root = load_moose_template(MESH_TEMPLATE)

    mesh = find_node(root, "/Mesh/generated_mesh")

    # ------------------------------------------------------------------------
    # Determine whether useful MCNP dimensions were found.
    #
    # We currently use explicit values from ReactorConfig as an override.
    # This makes it possible to get a working MOOSE mesh immediately.
    # ------------------------------------------------------------------------

    if config.fuel_height is not None:
        mesh["zmax"] = config.fuel_height

    elif geometry.get("fuel_height_m") is not None:
        mesh["zmax"] = geometry["fuel_height_m"]

    # ------------------------------------------------------------------------
    # Assembly dimensions are not automatically converted into the rectangular
    # test mesh yet.
    #
    # These values are intentionally easy to change.
    # ------------------------------------------------------------------------

    add_parameter_comment(
        mesh,
        "zmax",
        "Active fuel height obtained from MCNP geometry.",
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    pyhit.write(str(output_file), root)

    print(f"Wrote MOOSE mesh input: {output_file}")


# ============================================================================
# GENERATE THERMAL-HYDRAULICS INPUT
# ============================================================================

def generate_thm_input(
    config: ReactorConfig,
    power_file: Path | None,
    output_file: Path,
) -> None:
    """
    Generate the MOOSE thermal-hydraulics input file.

    The base model is the standard single-phase FlowChannel1Phase structure.

    If a power data file is supplied, the MCNP power function is added to
    the Functions block.

    The actual HeatStructure coupling remains a commented TODO until the
    reactor mesh contains properly named fuel/cladding regions.
    """

    root = load_moose_template(THM_TEMPLATE)

    # ------------------------------------------------------------------------
    # Find the root-level simulation parameters.
    #
    # Root parameters are valid HIT parameters in a MOOSE input file.
    # ------------------------------------------------------------------------

    root["T_in"] = config.inlet_temperature

    root["m_dot_in"] = config.inlet_mass_flow

    root["p_out"] = config.outlet_pressure

    # ------------------------------------------------------------------------
    # Update the inlet component.
    # ------------------------------------------------------------------------

    inlet = find_node(root, "/Components/inlet")

    inlet["m_dot"] = config.inlet_mass_flow

    inlet["T"] = config.inlet_temperature

    # ------------------------------------------------------------------------
    # Update outlet pressure.
    # ------------------------------------------------------------------------

    outlet = find_node(root, "/Components/outlet")

    outlet["p"] = config.outlet_pressure

    # ------------------------------------------------------------------------
    # Update initial conditions.
    # ------------------------------------------------------------------------

    global_params = find_node(root, "/GlobalParams")

    global_params["initial_p"] = config.initial_pressure

    global_params["initial_vel"] = config.initial_velocity

    global_params["initial_T"] = config.inlet_temperature

    # ------------------------------------------------------------------------
    # Insert MCNP power function if one exists.
    #
    # PiecewiseMultilinear supports multidimensional x/y/z data.
    # ------------------------------------------------------------------------

    if power_file is not None:

        functions = root.append("Functions")

        power_function = functions.append(
            "mcnp_power",
            type="PiecewiseMultilinear",
            data_file=str(power_file),
        )

        power_function.setComment(
            "MCNP-derived volumetric heat generation.",
        )

    # ------------------------------------------------------------------------
    # Write the generated file.
    # ------------------------------------------------------------------------

    output_file.parent.mkdir(parents=True, exist_ok=True)

    pyhit.write(str(output_file), root)

    print(f"Wrote MOOSE THM input: {output_file}")


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main() -> None:
    """
    Main preprocessing workflow.

    The current version performs:

        1. MCNP input reading
        2. MCNP geometry extraction
        3. geometry JSON output
        4. MOOSE mesh input generation
        5. MOOSE THM input generation

    MCNP power processing is only performed if:

        - MESHTAL exists
        - heating_tally_number is supplied
        - total_power is supplied
    """

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------------
    # User-adjustable reactor configuration.
    # ------------------------------------------------------------------------

    config = ReactorConfig(

        # These are placeholders until the geometry extraction is completed.
        fuel_height=None,
        fuel_radius=None,
        clad_outer_radius=None,
        pin_pitch=None,

        assembly_nx=None,
        assembly_ny=None,

        # Initial THM values.
        inlet_temperature=300.0,
        inlet_mass_flow=1.0,
        outlet_pressure=1.0e6,

        initial_pressure=1.0e6,
        initial_velocity=0.1,

        # --------------------------------------------------------------------
        # Set these once your MCNP calculation and tally are ready.
        #
        # For now leave them as None.
        # --------------------------------------------------------------------
        total_power=None,
        heating_tally_number=None,
    )

    # ------------------------------------------------------------------------
    # 1. READ MCNP INPUT
    # ------------------------------------------------------------------------

    problem = load_mcnp_problem(MCNP_INPUT)

    # ------------------------------------------------------------------------
    # 2. EXTRACT MCNP GEOMETRY/MATERIAL INFORMATION
    # ------------------------------------------------------------------------

    geometry_data = extract_mcnp_geometry(problem)

    # ------------------------------------------------------------------------
    # 3. IDENTIFY GEOMETRIC PARAMETERS
    #
    # Initially this will return many None values.
    # ------------------------------------------------------------------------

    geometry = identify_geometry_parameters(
        geometry_data,
    )

    # ------------------------------------------------------------------------
    # 4. SAVE INTERMEDIATE GEOMETRY DATA
    # ------------------------------------------------------------------------

    write_geometry_json(
        {
            "raw": geometry_data,
            "identified_parameters": geometry,
        },
        GEOMETRY_JSON,
    )

    # ------------------------------------------------------------------------
    # 5. GENERATE MOOSE MESH INPUT
    # ------------------------------------------------------------------------

    generate_mesh_input(
        config=config,
        geometry=geometry,
        output_file=MESH_INPUT,
    )

    # ------------------------------------------------------------------------
    # 6. GENERATE MOOSE THERMAL-HYDRAULICS INPUT
    # ------------------------------------------------------------------------

    power_file = None

    # Only try to process the MCNP heating tally if everything required has
    # been supplied.
    if (
        MESHTAL_FILE.exists()
        and config.heating_tally_number is not None
        and config.total_power is not None
    ):

        print("MCNP MESHTAL found; processing heating data.")

        # --------------------------------------------------------------
        # Read MCNP mesh tally.
        # --------------------------------------------------------------

        mesh_data = read_mcnp_mesh_tally(
            MESHTAL_FILE,
            config.heating_tally_number,
        )

        # --------------------------------------------------------------
        # Convert/normalize the MCNP energy-deposition distribution.
        # --------------------------------------------------------------

        power_values = normalize_heating_to_total_power(
            mesh_data,
            config.total_power,
        )

        # --------------------------------------------------------------
        # Write a MOOSE PiecewiseMultilinear data file.
        # --------------------------------------------------------------

        write_moose_power_data(
            mesh_data,
            power_values,
            POWER_DATA,
        )

        power_file = POWER_DATA

    else:

        print(
            "\nMCNP power data not generated yet.\n"
            "This is expected until a MESHTAL file and heating tally are available."
        )

    # ------------------------------------------------------------------------
    # 7. GENERATE THE THM INPUT
    # ------------------------------------------------------------------------

    generate_thm_input(
        config=config,
        power_file=power_file,
        output_file=THM_INPUT,
    )

    # ------------------------------------------------------------------------
    # FINAL MESSAGE
    # ------------------------------------------------------------------------

    print("\nGeneration complete.")
    print(f"Geometry summary : {GEOMETRY_JSON}")
    print(f"Mesh input       : {MESH_INPUT}")
    print(f"THM input        : {THM_INPUT}")

    if power_file is not None:
        print(f"MCNP power data  : {power_file}")


# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
