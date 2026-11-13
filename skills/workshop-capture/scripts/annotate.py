#!/usr/bin/env python3
"""Annotate a screenshot: frames, arrows, spotlight, redaction, crop. Never text.

    annotate.py shot.png -o shot.png --box 40,60,300,120
    annotate.py shot.png -o shot.png --arrow 500,300,360,180
    annotate.py shot.png -o shot.png --spotlight 40,60,300,120

**This script never draws text, and must not be taught to.** Text painted onto a finished
capture uses a font the app does not use, and never matches it. A label that is really needed is
drawn by the runtime itself, before the capture: the `label` step of capture.py for a web page,
or the runtime's own text function (TIC-80 `print`, for example) in an illustration program.
Sentences go in the caption underneath.

Coordinates are pixels in the image. When called from capture.py you give **selectors** instead
and the boxes are computed for you, which is the only sane way to do this on a page you did not
lay out yourself.

Used by capture.py; also usable on any PNG you already have.
"""
import argparse, math, sys
from PIL import Image, ImageDraw, ImageFilter

RED = (230, 60, 50)
PAD = 6


def box(img, rect, color=RED, width=4, radius=10, pad=PAD):
    x, y, w, h = rect
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x - pad, y - pad, x + w + pad, y + h + pad],
                        radius=radius, outline=color, width=width)
    return img


def spotlight(img, rect, dim=0.55, pad=PAD, color=RED, width=4):
    """Darken everything outside the rect — the strongest way to say 'look here'."""
    x, y, w, h = rect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, int(255 * dim)))
    hole = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
    overlay.paste(hole, (int(x - pad), int(y - pad)))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return box(img, rect, color=color, width=width, pad=pad)


def arrow(img, x1, y1, x2, y2, color=RED, width=None, head=None):
    """From (x1,y1) towards (x2,y2); a solid head lands on the target.

    Sizes default to the image width so an arrow reads the same on a 400px crop and a 2000px
    full page — a screenshot set looks amateur the moment the annotations are inconsistent.
    """
    scale = max(1.0, img.size[0] / 900)
    width = int(width or 5 * scale)
    head = int(head or 26 * scale)
    ang = math.atan2(y2 - y1, x2 - x1)
    # stop the shaft short so it does not stick out of the head
    sx, sy = x2 - head * 0.85 * math.cos(ang), y2 - head * 0.85 * math.sin(ang)
    d = ImageDraw.Draw(img)
    tri = [(x2, y2),
           (x2 - head * math.cos(ang - 0.42), y2 - head * math.sin(ang - 0.42)),
           (x2 - head * math.cos(ang + 0.42), y2 - head * math.sin(ang + 0.42))]
    # halo clair d'abord : une flèche rouge sur un objet rouge est invisible
    halo = (255, 255, 255)
    d.line([x1, y1, sx, sy], fill=halo, width=width + 4)
    d.polygon([(p[0] + math.cos(ang) * 3, p[1] + math.sin(ang) * 3) for p in tri], fill=halo)
    d.polygon(tri, fill=halo, outline=halo, width=4)
    d.line([x1, y1, sx, sy], fill=color, width=width)
    d.polygon(tri, fill=color)
    return img


def blur(img, rect, radius=14):
    x, y, w, h = [int(v) for v in rect]
    region = img.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(radius))
    img.paste(region, (x, y))
    return img


def crop(img, rect):
    x, y, w, h = [int(v) for v in rect]
    return img.crop((x, y, x + w, y + h))


def apply_ops(img, ops):
    """ops: list of dicts, as produced by capture.py from selectors."""
    for op in ops:
        k = op["op"]
        if k == "box":
            img = box(img, op["rect"], color=tuple(op.get("color", RED)), width=op.get("width", 4))
        elif k == "spotlight":
            img = spotlight(img, op["rect"], dim=op.get("dim", 0.55))
        elif k == "arrow":
            img = arrow(img, *op["from"], *op["to"], width=op.get("width"))
        elif k == "blur":
            img = blur(img, op["rect"], radius=op.get("radius", 14))
        elif k == "crop":
            img = crop(img, op["rect"])
    return img


def _rect(s):
    return [float(v) for v in s.split(",")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--box", action="append", type=_rect, default=[])
    ap.add_argument("--spotlight", type=_rect)
    ap.add_argument("--arrow", action="append", type=_rect, default=[])
    ap.add_argument("--blur", action="append", type=_rect, default=[])
    ap.add_argument("--crop", type=_rect)
    a = ap.parse_args()

    img = Image.open(a.image).convert("RGB")
    for r in a.box:
        img = box(img, r)
    if a.spotlight:
        img = spotlight(img, a.spotlight)
    for r in a.arrow:
        img = arrow(img, *r)
    for r in a.blur:
        img = blur(img, r)
    if a.crop:
        img = crop(img, a.crop)
    img.save(a.out)
    print(f"  {a.out}  ({img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
