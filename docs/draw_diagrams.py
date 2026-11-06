"""Render the two coordinate projections of the yaw/pitch example.

The scale and endpoints are calculated from examples/yaw_pitch.csv. To remake
the images: python3 -m pip install Pillow; python3 docs/draw_diagrams.py
"""
import argparse
import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--font", default="DejaVuSans.ttf")
parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent)
args = parser.parse_args()
with (ROOT / "examples/yaw_pitch.csv").open(encoding="utf-8", newline="") as data:
    base, arm = list(csv.DictReader(data))
height, length = float(base["d_mm"]), float(arm["a_mm"])
yaw, pitch = map(math.radians, (60, 30))
run, rise = length * math.cos(pitch), length * math.sin(pitch)
x, y = run * math.cos(yaw), run * math.sin(yaw)
BLUE, GREEN, INK, MUTE, PAPER = "#095777", "#006553", "#162d39", "#445c66", "#f4faf8"
SIZE = (800, 520)
args.output.mkdir(parents=True, exist_ok=True)


def canvas(title, caption):
    pic = Image.new("RGB", SIZE, PAPER)
    d = ImageDraw.Draw(pic)
    d.text((36, 29), title, fill=INK, font=ImageFont.truetype(args.font, 40))
    d.text((36, 86), caption, fill=MUTE, font=ImageFont.truetype(args.font, 27))
    return pic, d


def label(d, at, message, fill=INK, anchor="la"):
    d.text(at, message, font=ImageFont.truetype(args.font, 26), fill=fill, anchor=anchor,
           stroke_width=2, stroke_fill=PAPER)


def dot(d, pt, color=INK):
    x0, y0 = pt
    d.ellipse((x0-7, y0-7, x0+7, y0+7), fill=color)


def dash(d, a, b):
    dist = math.dist(a, b)
    for i in range(0, int(dist), 15):
        j = min(i+8, dist)
        d.line([tuple(p+(q-p)*v/dist for p, q in zip(a, b)) for v in (i,j)], fill=MUTE, width=3)


def arrow(d, a, b):
    d.line((a,b), fill=MUTE, width=3)
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    sides = [(b[0]-13*math.cos(angle+k), b[1]-13*math.sin(angle+k)) for k in (-0.5, 0.5)]
    d.polygon([b,*sides], fill=MUTE)


def save(pic, name):
    pic.save(args.output / f"dh-{name}.webp", format="WEBP", quality=87, method=6)


pic, d = canvas("Elevation: look along the pitch axis", "This plane turns with the base.")
s = 1.14
o = (145, 443)
shoulder = (o[0], o[1]-height*s)
tip = (o[0]+run*s, shoulder[1]-rise*s)
projection = (tip[0], shoulder[1])
arrow(d,o,(700,o[1]))
arrow(d,o,(o[0],145))
d.line((o,shoulder), fill=GREEN, width=7)
d.line((shoulder,tip), fill=BLUE, width=9)
dash(d,shoulder,projection)
dash(d,tip,projection)
for pt in (o,shoulder,tip):
    dot(d,pt)
d.arc((shoulder[0]-125,shoulder[1]-125,shoulder[0]+125,shoulder[1]+125),330,360,fill=BLUE,width=3)
label(d,(173,365),"120 mm base height",GREEN)
label(d,(290,262),"30°",BLUE)
label(d,(170,157),"250 mm link",BLUE)
label(d,(415,181),"Tip")
label(d,(414,253),f"{rise:.0f} mm rise")
label(d,(162,318),f"{run:.1f} mm horizontal")
label(d,(109,154),"z₀")
label(d,(473,453),"Horizontal distance")
save(pic, "elevation")

pic, d = canvas("Top view: split reach into x and y", "Same pose, viewed down from above the base.")
s = 1.32
o = (203, 425)
tip = (o[0]+x*s, o[1]-y*s)
arrow(d,o,(670,o[1]))
arrow(d,o,(o[0],141))
dash(d,tip,(tip[0],o[1]))
dash(d,tip,(o[0],tip[1]))
d.line((o,tip), fill=BLUE, width=8)
d.arc((o[0]-94,o[1]-94,o[0]+94,o[1]+94),300,360,fill=BLUE,width=3)
dot(d,o)
dot(d,tip)
label(d,(242,371),"60°",BLUE)
label(d,(366,286),f"{run:.1f} mm",BLUE)
label(d,(360,163),"Tip projection")
label(d,(191,165),f"y = {y:.1f} mm",anchor="ra")
label(d,(358,435),f"x = {x:.1f} mm")
label(d,(645,385),"x₀")
label(d,(153,137),"y₀")
label(d,(67,439),"Base")
save(pic, "top-view")
