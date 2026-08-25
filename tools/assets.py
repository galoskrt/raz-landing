# -*- coding: utf-8 -*-
"""Prepare the landing page images.

The host serves everything uncompressed (see the Evolution ticket), so image
weight is the page weight. Everything becomes WebP at the size it is actually
displayed, cutouts keep their alpha, and the two testimonial videos are copied
untouched because they never load until someone taps play.
"""
import io, os, glob, shutil
from PIL import Image

SP = ("C:/Users/HP/AppData/Local/Temp/claude/C--Users-HP/"
      "8c8bcb44-a1c9-4131-99c1-b850f0a87bb9/scratchpad/raz")
DL = u"C:/Users/HP/Downloads/\u05e8\u05d6 \u05de\u05d0\u05d9\u05e8 \u05db\u05d4\u05df"
OUT = "C:/Users/HP/raz-landing/assets/img"

# source, output name, target width, quality, keep alpha
JOBS = [
    ("_sky1.png",         "hero-bg",      1254, 72, False),
    ("hero_win_img1.jpg", "hero-window",   900, 82, False),
    ("raz_navy.png",      "raz-navy",      760, 86, True),
    ("raz_beige.png",     "raz-beige",     760, 86, True),
    ("guide_cover.jpg",   "guide-cover",   720, 84, False),
    ("tom_logo_light.png","th-logo",       320, 88, True),
    ("vid1.jpg",          "video-1",       560, 78, False),
    ("vid2.jpg",          "video-2",       560, 78, False),
    ("m_dark.jpg",        "marble-dark",  1400, 68, False),
    ("m_wash.jpg",        "marble-wash",  1400, 68, False),
]


def convert(src, name, width, q, alpha):
    im = Image.open(src)
    if im.width > width:
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
    im = im.convert("RGBA" if alpha else "RGB")
    dst = os.path.join(OUT, name + ".webp")
    im.save(dst, "WEBP", quality=q, method=6)
    return os.path.getsize(src), os.path.getsize(dst), im.size


def main():
    os.makedirs(OUT, exist_ok=True)
    before = after = 0
    for src, name, w, q, a in JOBS:
        p = os.path.join(SP, src)
        if not os.path.exists(p):
            print("  MISSING", src); continue
        b, t, size = convert(p, name, w, q, a)
        before += b; after += t
        print("  %-14s %5dx%-4d %6.0f -> %5.0f KB" % (name, size[0], size[1], b / 1024., t / 1024.))

    # the thirteen real Google reviews, as they look in Google
    shots = sorted(glob.glob(os.path.join(DL, u"\u05d4\u05de\u05dc\u05e6\u05d5\u05ea \u05d2\u05d5\u05d2\u05dc", "*.png")))
    for i, p in enumerate(shots, 1):
        b, t, size = convert(p, "review-%02d" % i, 620, 80, False)
        before += b; after += t
    print("  %-14s %d files  %6.0f -> %5.0f KB total"
          % ("reviews", len(shots), sum(os.path.getsize(p) for p in shots) / 1024.,
             sum(os.path.getsize(os.path.join(OUT, "review-%02d.webp" % i))
                 for i in range(1, len(shots) + 1)) / 1024.))

    # videos stay as they are: preload none means they cost nothing until tapped
    for i, p in enumerate(sorted(glob.glob(os.path.join(DL, "AQ*.mp4"))), 1):
        dst = os.path.join(OUT, "video-%d.mp4" % i)
        if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(p):
            shutil.copy2(p, dst)
        print("  %-14s %6.1f MB (copied, preload none)" % ("video-%d.mp4" % i, os.path.getsize(dst) / 1048576.))

    print("  ---")
    print("  images %.0f KB -> %.0f KB  (%.0f%% lighter)"
          % (before / 1024., after / 1024., 100 * (1 - after / float(before))))


if __name__ == "__main__":
    main()
