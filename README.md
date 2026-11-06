# Robot arm DH parameters in Python

Read the [full WIFA Robotics tutorial](https://wifarobotics.com/learn/robot-arm-dh-parameters/) for the frame drawings, worked geometry and troubleshooting.

This offline lab reads a standard Denavit–Hartenberg table and reports each frame origin, the final rotation matrix and the base coordinates of a point specified in the tool frame. It uses Python's standard library. No robot, controller or calibration file is needed.

## Run from zero

1. Install [Python 3.12](https://www.python.org/downloads/).
2. Use **Code → Download ZIP** on GitHub, extract it and open a terminal in the folder containing `dh.py`.
3. On macOS or Linux run `python3 --version`, then use the commands below. On Windows use `py -3.12 --version` and replace `python3` with `py -3.12`. No pip install is required.

```sh
python3 dh.py examples/planar.csv --q 30 -60
python3 dh.py examples/yaw_pitch.csv --q 60 30
python3 dh.py examples/slide.csv --q 90 65
python3 dh.py examples/yaw_pitch.csv --q 60 30 --point 50 0 0
python3 -m unittest discover -s tests -v
```

| File or change | Expected `point_in_base_mm` |
| --- | --- |
| Planar arm | `[433.012702, 50.0, 0.0]` |
| Yaw and pitch | `[108.253175, 187.5, 245.0]` |
| Revolute plus prismatic | `[0.0, 120.0, 90.0]` |
| Point 50 mm along tool x | `[129.903811, 225.0, 270.0]` |

The first frame origin is the base. The last origin and the reported point differ only when a nonzero tool point is provided. Rotation columns are the tool x, y and z directions expressed in the base. The display rounds to six decimals for readability.

## Enter a new table

Copy one file in `examples/` and retain the header `joint,a_mm,alpha_deg,d_mm,theta_deg`. Use one CSV row per joint from base to tool. Give one reading per row after `--q`. For an R row the reading is in degrees and adds to the `theta_deg` offset. For a P row it is in millimetres and adds to the `d_mm` offset. Every `a_mm` and `d_mm` value uses millimetres, including offsets. This tool implements classical DH, using column vectors and the order Rz(theta) Tz(d) Tx(a) Rx(alpha).

If coordinates appear in the wrong quadrant, check the positive rotation direction about the previous frame's z axis and whether the joint offset was counted twice. If the arm stays flat when you expect pitch, check the twist on the row **before** the pitching joint. If a point offset moves in the wrong direction, check that you entered it in tool axes. A rejected CSV often has a renamed header, a missing value, or a decimal comma. Use decimal points.

The tests check the matrix results against independent geometric formulas, frame direction, orthogonality, prismatic offset, error handling and the CLI. `docs/draw_diagrams.py` recreates both WebPs if you install Pillow separately. All diagrams describe the supplied models. No hardware tests were performed. This project does not model joint limits, calibration, uncertainty, collisions, loads or safe motion. Do not send its outputs to a robot controller.

Reference: [Czech Technical University DH lecture](https://cw.fel.cvut.cz/b231/_media/courses/pkr/pro-lecture-dh.pdf) and [MathWorks DH example](https://www.mathworks.com/help/robotics/ug/build-manipulator-robot-using-kinematic-dh-parameters.html).
