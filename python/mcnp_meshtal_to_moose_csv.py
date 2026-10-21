#!/usr/bin/env python3
"""Collapse an MCNP Cartesian FMESH tally into a MOOSE axial power-shape CSV.

This is a streaming parser for the standard text MESHTAL format for a single,
non-energy-binned Cartesian mesh tally whose data columns are:
    X  Y  Z  Result  Rel Error

It expects a uniform mesh with all voxels printed. Defaults match the user's
FMESH card: 200 x 200 x 185 bins over x/y/z = 420/420/388.5 cm.

Output mcnp_axial_shape.csv is headerless CSV with:
    z [m], relative axial score [-]
MOOSE's HeatSourceFromTotalPower normalizes the spatial shape function itself,
so the relative score is divided by its maximum only for convenient scaling.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Iterable

TALLY_HEADER_RE = re.compile(r"^\s*Mesh\s+Tally\s+Number\s+(\d+)\b", re.IGNORECASE)


def parse_mcnp_float(token: str) -> float:
    """Parse common MCNP floating-point formats, including D or omitted E."""
    token = token.strip().replace("D", "E").replace("d", "E")
    try:
        return float(token)
    except ValueError:
        # Some FORTRAN-style outputs omit E in values like 1.23456-03.
        match = re.fullmatch(r"([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d{2,3})", token)
        if match:
            return float(f"{match.group(1)}E{match.group(2)}")
        raise


def is_xyz_result_header(line: str) -> bool:
    tokens = line.lower().split()
    # Typical MCNP text MESHTAL heading: X Y Z Result Rel Error
    return (
        len(tokens) >= 6
        and tokens[0:4] == ["x", "y", "z", "result"]
        and "error" in tokens[4:]
    )


def read_mesh_tally(
    meshtal_path: Path,
    tally_number: int,
    expected_nx: int,
    expected_ny: int,
    expected_nz: int,
) -> tuple[list[float], list[float], list[int], int]:
    """Stream a tally and return sorted z-centres (cm), axial sums, counts, rows."""
    in_target_tally = False
    found_tally = False
    found_table_header = False
    rows_read = 0
    axial_sum: dict[float, float] = defaultdict(float)
    axial_count: dict[float, int] = defaultdict(int)

    try:
        handle = meshtal_path.open("r", encoding="utf-8", errors="replace")
    except OSError as exc:
        raise RuntimeError(f"Cannot open MESHTAL file '{meshtal_path}': {exc}") from exc

    with handle:
        for line_number, line in enumerate(handle, start=1):
            tally_match = TALLY_HEADER_RE.match(line)
            if tally_match:
                current_number = int(tally_match.group(1))
                if in_target_tally and current_number != tally_number:
                    # We have reached the next tally after the desired one.
                    break
                in_target_tally = current_number == tally_number
                if in_target_tally:
                    found_tally = True
                continue

            if not in_target_tally:
                continue

            if not found_table_header:
                if is_xyz_result_header(line):
                    found_table_header = True
                continue

            parts = line.split()
            if len(parts) != 5:
                # Ignore blank lines and explanatory/footer text. A dimension
                # check below catches truncated or unsupported table formats.
                continue

            try:
                x_cm, y_cm, z_cm, result, rel_error = (
                    parse_mcnp_float(part) for part in parts
                )
            except ValueError:
                continue

            if not all(math.isfinite(v) for v in (x_cm, y_cm, z_cm, result, rel_error)):
                raise RuntimeError(
                    f"Non-finite value in tally {tally_number} at MESHTAL line {line_number}."
                )

            # MCNP prints the same z-centre for every voxel in the same axial
            # plane. Rounding protects grouping against text-rounding noise.
            z_key = round(z_cm, 6)
            axial_sum[z_key] += result
            axial_count[z_key] += 1
            rows_read += 1

    if not found_tally:
        raise RuntimeError(
            f"Tally {tally_number} was not found in '{meshtal_path}'. "
            "Confirm that the FMESH card is enabled and that this is the MESHTAL file."
        )
    if not found_table_header:
        raise RuntimeError(
            f"Tally {tally_number} was found, but its 'X Y Z Result Rel Error' table was not. "
            "This script expects a standard, non-energy-binned Cartesian MESHTAL table."
        )

    z_centres = sorted(axial_sum)
    expected_planes = expected_nz
    expected_voxels_per_plane = expected_nx * expected_ny
    expected_total = expected_nx * expected_ny * expected_nz

    if rows_read != expected_total:
        raise RuntimeError(
            f"Tally {tally_number}: read {rows_read:,} voxel rows, but the configured mesh "
            f"expects {expected_total:,} ({expected_nx} x {expected_ny} x {expected_nz}).\n"
            "Check the tally number, output format, mesh dimensions, and whether the tally "
            "has energy/time bins. If you changed IINTS/JINTS/KINTS, pass the new dimensions "
            "with --nx, --ny, and --nz."
        )
    if len(z_centres) != expected_planes:
        raise RuntimeError(
            f"Found {len(z_centres)} distinct axial planes; expected {expected_planes}."
        )

    bad_planes = [
        (z, axial_count[z])
        for z in z_centres
        if axial_count[z] != expected_voxels_per_plane
    ]
    if bad_planes:
        z, count = bad_planes[0]
        raise RuntimeError(
            f"Axial plane z={z:g} cm has {count:,} voxel rows; expected "
            f"{expected_voxels_per_plane:,}. The tally table may be incomplete or use a different format."
        )

    sums = [axial_sum[z] for z in z_centres]
    counts = [axial_count[z] for z in z_centres]
    return z_centres, sums, counts, rows_read


def linear_interp(x: float, xs: list[float], ys: list[float]) -> float:
    """Linear interpolation with constant values beyond first/last cell centres."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    right = bisect.bisect_right(xs, x)
    left = right - 1
    x0, x1 = xs[left], xs[right]
    y0, y1 = ys[left], ys[right]
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def write_outputs(
    out_path: Path,
    diagnostics_path: Path,
    z_centres_cm: list[float],
    axial_scores: list[float],
    voxels_per_plane: list[int],
    z_min_cm: float | None,
    z_max_cm: float | None,
) -> tuple[float, float, float]:
    # The supplied FMESH is uniform in z. Infer exterior mesh boundaries from
    # the uniformly spaced cell centres: first/last centre +/- half a bin.
    spacings = [b - a for a, b in zip(z_centres_cm[:-1], z_centres_cm[1:])]
    if not spacings:
        raise RuntimeError("Not enough axial planes to construct a profile.")
    dz = sorted(spacings)[len(spacings) // 2]
    max_spacing_deviation = max(abs(delta - dz) for delta in spacings)
    if max_spacing_deviation > max(1e-4, abs(dz) * 1e-4):
        raise RuntimeError(
            "Axial bin centres are not uniformly spaced. This starter script assumes the "
            "uniform KINTS mesh shown in the supplied input deck."
        )

    mesh_min_cm = z_centres_cm[0] - dz / 2.0
    mesh_max_cm = z_centres_cm[-1] + dz / 2.0
    zlo = mesh_min_cm if z_min_cm is None else z_min_cm
    zhi = mesh_max_cm if z_max_cm is None else z_max_cm

    tol = 1e-6
    if zlo < mesh_min_cm - tol or zhi > mesh_max_cm + tol:
        raise RuntimeError(
            f"Requested z range [{zlo:g}, {zhi:g}] cm is outside mesh bounds "
            f"[{mesh_min_cm:g}, {mesh_max_cm:g}] cm."
        )
    if not zlo < zhi:
        raise RuntimeError("The selected axial range must have z-min < z-max.")

    scale = max(abs(value) for value in axial_scores)
    if scale == 0.0:
        raise RuntimeError("All axial tally values are zero; cannot construct a shape function.")
    if any(value < -scale * 1e-10 for value in axial_scores):
        min_score = min(axial_scores)
        raise RuntimeError(
            f"The collapsed tally contains a negative value (minimum {min_score:.6e}). "
            "Do not take absolute values automatically: verify that the MCNP tally and FM "
            "multiplier score positive heat deposition before using it as a heat source."
        )
    # Remove only round-off-sized negative values after the negative-score check.
    scores = [max(0.0, value) for value in axial_scores]

    # Add profile points at the requested domain boundaries so the MOOSE function
    # covers the entire active heat structure. At the physical mesh boundaries,
    # use the nearest bin-centre value; in an interior cut, linearly interpolate.
    z_points_cm = [zlo]
    z_points_cm.extend(z for z in z_centres_cm if zlo + tol < z < zhi - tol)
    z_points_cm.append(zhi)
    z_points_cm = sorted(set(round(z, 9) for z in z_points_cm))
    values_at_points = [linear_interp(z, z_centres_cm, scores) for z in z_points_cm]
    maximum = max(values_at_points)
    if maximum <= 0.0:
        raise RuntimeError("The selected axial range contains no positive heating tally values.")
    normalized = [v / maximum for v in values_at_points]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        # No header: PiecewiseLinear reads x/y numbers as rows by default.
        for z_cm, shape in zip(z_points_cm, normalized):
            writer.writerow((f"{z_cm * 0.01:.10g}", f"{shape:.10g}"))

    diagnostics_path.parent.mkdir(parents=True, exist_ok=True)
    with diagnostics_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("z_center_cm", "z_center_m", "axial_tally_sum_raw", "relative_to_max", "voxel_count"))
        profile_max = max(scores)
        for z_cm, raw, count in zip(z_centres_cm, scores, voxels_per_plane):
            rel = raw / profile_max if profile_max > 0.0 else 0.0
            writer.writerow((f"{z_cm:.9g}", f"{z_cm * 0.01:.9g}", f"{raw:.12e}", f"{rel:.10g}", count))

    return mesh_min_cm, mesh_max_cm, maximum


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collapse an MCNP Cartesian MESHTAL mesh into a MOOSE axial shape CSV."
    )
    parser.add_argument("meshtal", type=Path, help="MCNP text mesh tally output file (often named meshtal).")
    parser.add_argument("--tally", type=int, default=14, help="FMESH tally number (default: 14).")
    parser.add_argument("--nx", type=int, default=200, help="Number of x bins (default: 200).")
    parser.add_argument("--ny", type=int, default=200, help="Number of y bins (default: 200).")
    parser.add_argument("--nz", type=int, default=185, help="Number of z bins (default: 185).")
    parser.add_argument("--z-min-cm", type=float, default=None, help="Optional lower bound of the axial range in MCNP cm.")
    parser.add_argument("--z-max-cm", type=float, default=None, help="Optional upper bound of the axial range in MCNP cm.")
    parser.add_argument("--out", type=Path, default=Path("mcnp_axial_shape.csv"), help="MOOSE-ready CSV output path.")
    parser.add_argument("--diagnostics", type=Path, default=Path("mcnp_axial_profile_diagnostics.csv"), help="Raw collapsed profile for checking/plotting.")
    args = parser.parse_args(argv)

    if min(args.nx, args.ny, args.nz) <= 0:
        parser.error("--nx, --ny and --nz must all be positive integers.")

    try:
        z_centres_cm, axial_scores, counts, rows_read = read_mesh_tally(
            args.meshtal, args.tally, args.nx, args.ny, args.nz
        )
        zmin, zmax, profile_max = write_outputs(
            args.out,
            args.diagnostics,
            z_centres_cm,
            axial_scores,
            counts,
            args.z_min_cm,
            args.z_max_cm,
        )
    except (RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Read tally {args.tally}: {rows_read:,} voxel rows in {len(z_centres_cm)} axial planes.")
    print(f"MCNP mesh extent inferred from bin centres: {zmin:g} to {zmax:g} cm.")
    if args.z_min_cm is not None or args.z_max_cm is not None:
        print("The output shape is restricted to the requested z range.")
    print(f"Wrote MOOSE shape: {args.out}")
    print(f"Wrote raw profile diagnostics: {args.diagnostics}")
    print("Shape values are dimensionless (peak = 1); MOOSE normalizes the function over the heat-source domain.")
    print("Check that the MCNP tally represents the desired fuel-heating distribution before coupling it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
