import os
import vtracer
from PIL import Image, ImageFilter

src = r"C:\Users\Daniel Yepez Garces\Downloads\ChatGPT Image 28 sept 2026, 06_59_51 p.m. (1).png"
im = Image.open(src).convert("RGBA")

# 1. Clean alpha to crisp silhouette
r, g, b, a = im.split()
a = a.point(lambda p: 0 if p < 30 else 255 if p > 220 else p)

# 2. Smooth color transitions to make spline tracing continuous and free of staircasing
rgb = Image.merge("RGB", (r, g, b))
rgb_smooth = rgb.filter(ImageFilter.MedianFilter(size=3)).filter(ImageFilter.SMOOTH_MORE)
r_s, g_s, b_s = rgb_smooth.split()
polished_im = Image.merge("RGBA", (r_s, g_s, b_s, a))

polished_png = r"C:\thorium\polished_temp.png"
polished_im.save(polished_png)

out_svg = r"C:\thorium\selenium_v3_polished.svg"
vtracer.convert_image_to_svg_py(
    polished_png,
    out_svg,
    "color",
    "stacked",
    "spline",
    20,   # filter_speckle (removes all small speckles)
    5,    # color_precision
    26,   # layer_difference
    75,   # corner_threshold (smoother transitions)
    7.0,  # length_threshold (longer, continuous curves)
    30,   # max_iterations (deep spline optimization for polished lines)
    40,   # splice_threshold
    3     # path_precision
)

with open(out_svg, "r", encoding="utf-8") as f:
    s = f.read()

width, height = im.size
if "viewBox" not in s:
    s = s.replace(f'width="{width}" height="{height}">', f'viewBox="0 0 {width} {height}" width="100%" height="100%">')
with open(out_svg, "w", encoding="utf-8") as f:
    f.write(s)

print(f"Polished SVG generated: {os.path.getsize(out_svg)} bytes")
