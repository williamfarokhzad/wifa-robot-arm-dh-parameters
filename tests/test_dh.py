import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from dh import Row, forward, map_point, read_table

ROOT = Path(__file__).resolve().parents[1]


class PoseChecks(unittest.TestCase):
    def pose(self, fixture, q):
        return forward(read_table(ROOT / "examples" / (fixture + ".csv")), q)[-1]

    def assertVector(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, places=9)

    def test_planar_against_sum_of_two_geometric_vectors(self):
        for q1, q2 in [(0, 0), (30, -60), (90, 90), (-135, 80)]:
            a, b = math.radians(q1), math.radians(q1 + q2)
            self.assertVector(map_point(self.pose("planar", [q1, q2]), (0, 0, 0)),
                              (300*math.cos(a)+200*math.cos(b), 300*math.sin(a)+200*math.sin(b), 0))

    def test_twisted_chain_against_vertical_and_radial_projection(self):
        for yaw, pitch in [(60, 30), (-90, 25), (30, -35), (0, 90)]:
            a, b = math.radians(yaw), math.radians(pitch)
            self.assertVector(map_point(self.pose("yaw_pitch", [yaw, pitch]), (0, 0, 0)),
                              (250*math.cos(b)*math.cos(a), 250*math.cos(b)*math.sin(a), 120+250*math.sin(b)))

    def test_tool_offset_is_rotated_not_added_in_base_x(self):
        self.assertVector(map_point(self.pose("yaw_pitch", [90, 30]), (50, 0, 0)),
                          (0, 150*math.sqrt(3), 270))

    def test_slide_stroke_and_offset_change_height_only(self):
        for stroke in [-15, 0, 65]:
            self.assertVector(map_point(self.pose("slide", [90, stroke]), (0, 0, 0)), (0, 120, 25+stroke))

    def test_prismatic_keeps_fixed_heading_and_revolute_keeps_fixed_d(self):
        p = forward([Row("P", 4, 0, 7, 90)], [6])[-1]
        self.assertVector(map_point(p, (1, 0, 0)), (0, 5, 13))
        r = forward([Row("R", 4, 0, 7, 90)], [-90])[-1]
        self.assertVector(map_point(r, (1, 0, 0)), (5, 0, 7))

    def test_rotation_columns_form_right_handed_orthonormal_basis(self):
        pose = self.pose("yaw_pitch", [60, 30])
        x, y, z = [tuple(pose[i][j] for i in range(3)) for j in range(3)]
        self.assertVector([sum(a*b for a, b in zip(col, col)) for col in (x, y, z)], [1]*3)
        self.assertVector([sum(a*b for a, b in zip(u, v)) for u, v in ((x, y), (y, z), (z, x))], [0]*3)
        self.assertVector((x[1]*y[2]-x[2]*y[1], x[2]*y[0]-x[0]*y[2], x[0]*y[1]-x[1]*y[0]), z)

    def test_intermediate_frame_shows_base_height_before_pitch(self):
        poses = forward(read_table(ROOT / "examples/yaw_pitch.csv"), [60, 30])
        self.assertEqual(len(poses), 3)
        self.assertVector(map_point(poses[1], (0, 0, 0)), (0, 0, 120))
        self.assertVector(map_point(poses[1], (0, 0, 1)), (math.sqrt(3)/2, -0.5, 120))

    def test_input_validation(self):
        rows = [Row("P", 0, 0, 0, 0)]
        for qs in ([], [1, 2], [math.inf], [math.nan]):
            with self.subTest(qs=qs), self.assertRaises(ValueError):
                forward(rows, qs)
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "bad.csv"
            f.write_text("joint,a_mm,alpha_deg,d_mm,theta_deg\nQ,2,3,4,5\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CSV row 2"):
                read_table(f)
            f.write_text("joint,a_m,alpha_deg,d_mm,theta_deg\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CSV header"):
                read_table(f)

    def test_cli_json_and_bad_count_exit(self):
        cli = [sys.executable, str(ROOT / "dh.py"), str(ROOT / "examples/slide.csv")]
        result = subprocess.run(cli + ["--q", "90", "65"], check=True, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["point_in_base_mm"], [0, 120, 90])
        bad = subprocess.run(cli + ["--q", "90"], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("one joint reading per DH row", bad.stderr)


if __name__ == "__main__":
    unittest.main()
