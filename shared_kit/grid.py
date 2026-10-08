"""Measuring aid: crop a reference drawing, enlarge it and draw a labelled pixel grid.

    python3 grid.py refs/t64.png x0 y0 x1 y1 out.png [step=10] [scale=3]
Grid labels are ORIGINAL drawing pixel coordinates, so you can read positions straight off it.
"""
import sys
from PIL import Image, ImageDraw

src, x0, y0, x1, y1, out = sys.argv[1], *map(int, sys.argv[2:6]), sys.argv[6]
step = int(sys.argv[7]) if len(sys.argv) > 7 else 10
k = int(sys.argv[8]) if len(sys.argv) > 8 else 3
im = Image.open(src).convert('RGB').crop((x0, y0, x1, y1))
im = im.resize((im.width*k, im.height*k), Image.NEAREST)
d = ImageDraw.Draw(im)
for x in range((x0//step+1)*step, x1, step):
    major = x % (step*5) == 0
    d.line([((x-x0)*k, 0), ((x-x0)*k, im.height)], fill=(255, 0, 0) if major else (255, 180, 180), width=1)
    if major: d.text(((x-x0)*k+2, 2), str(x), fill=(200, 0, 0))
for y in range((y0//step+1)*step, y1, step):
    major = y % (step*5) == 0
    d.line([(0, (y-y0)*k), (im.width, (y-y0)*k)], fill=(0, 0, 255) if major else (180, 180, 255), width=1)
    if major: d.text((2, (y-y0)*k+2), str(y), fill=(0, 0, 200))
im.save(out)
print(out, im.size)
