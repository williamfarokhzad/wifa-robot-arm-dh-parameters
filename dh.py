"""Forward kinematics with classical Denavit–Hartenberg rows and column vectors."""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

Matrix = tuple[tuple[float, ...], ...]
FIELDS = ("joint", "a_mm", "alpha_deg", "d_mm", "theta_deg")
IDENTITY: Matrix = tuple(tuple(float(i == j) for j in range(4)) for i in range(4))


@dataclass(frozen=True)
class Row:
    joint: str
    a_mm: float
    alpha_deg: float
    d_mm: float
    theta_deg: float

    def __post_init__(self) -> None:
        if self.joint not in {"R", "P"}:
            raise ValueError("joint must be R (degrees) or P (millimetres)")
        if not all(math.isfinite(v) for v in (self.a_mm, self.alpha_deg, self.d_mm, self.theta_deg)):
            raise ValueError("DH values must be finite")


def read_table(path: Path) -> list[Row]:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, strict=True)
        if next(reader, None) != list(FIELDS):
            raise ValueError(f"CSV header must be {','.join(FIELDS)}")
        for line, cells in enumerate(reader, start=2):
            try:
                joint, a, alpha, d, theta = cells
                rows.append(Row(joint.strip(), float(a), float(alpha), float(d), float(theta)))
            except ValueError as exc:
                raise ValueError(f"CSV row {line}: {exc}") from exc
    if not rows:
        raise ValueError("CSV must contain at least one DH row")
    return rows


def row_matrix(row: Row, q: float) -> Matrix:
    if not math.isfinite(q):
        raise ValueError("joint readings must be finite")
    theta = row.theta_deg + (q if row.joint == "R" else 0.0)
    d = row.d_mm + (q if row.joint == "P" else 0.0)
    if not math.isfinite(theta) or not math.isfinite(d):
        raise ValueError("joint reading plus offset is outside the numeric range")
    theta, alpha = math.radians(theta), math.radians(row.alpha_deg)
    ct, st = math.cos(theta), math.sin(theta)
    ca, sa = math.cos(alpha), math.sin(alpha)
    return (
        (ct, -st * ca, st * sa, row.a_mm * ct),
        (st, ct * ca, -ct * sa, row.a_mm * st),
        (0.0, sa, ca, d),
        (0.0, 0.0, 0.0, 1.0),
    )


def multiply(left: Matrix, right: Matrix) -> Matrix:
    result = tuple(
        tuple(math.fsum(left[i][k] * right[k][j] for k in range(4)) for j in range(4))
        for i in range(4)
    )
    if not all(math.isfinite(v) for row in result for v in row):
        raise ValueError("transform is outside the numeric range")
    return result


def forward(rows: list[Row], joints: list[float]) -> list[Matrix]:
    """Return cumulative base-to-frame poses, including the base identity."""
    if not rows or len(rows) != len(joints):
        raise ValueError("provide one joint reading per DH row")
    poses = [IDENTITY]
    for row, q in zip(rows, joints):
        poses.append(multiply(poses[-1], row_matrix(row, q)))
    return poses


def map_point(pose: Matrix, xyz: tuple[float, float, float]) -> tuple[float, ...]:
    """Express a point in the base, including the tool origin translation."""
    if not all(math.isfinite(v) for v in xyz):
        raise ValueError("point coordinates must be finite")
    result = tuple(math.fsum(pose[i][j] * xyz[j] for j in range(3)) + pose[i][3] for i in range(3))
    if not all(math.isfinite(v) for v in result):
        raise ValueError("mapped point is outside the numeric range")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table", type=Path)
    parser.add_argument("--q", nargs="+", type=float, required=True, help="one value per row: R in deg, P in mm")
    parser.add_argument("--point", nargs=3, type=float, metavar=("X", "Y", "Z"), default=(0., 0., 0.),
                        help="point coordinates in the final frame, mm")
    args = parser.parse_args()
    try:
        poses = forward(read_table(args.table), args.q)
        tool = poses[-1]
        point = map_point(tool, tuple(args.point))
    except (OSError, ValueError, OverflowError, csv.Error) as exc:
        parser.error(str(exc))

    def clean(value: float) -> float:
        return round(value, 6) or 0.0

    print(json.dumps({
        "frame_origins_mm": [[clean(p[i][3]) for i in range(3)] for p in poses],
        "tool_rotation": [[clean(tool[i][j]) for j in range(3)] for i in range(3)],
        "point_in_base_mm": list(map(clean, point)),
    }, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
