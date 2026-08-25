# -*- coding: utf-8 -*-
"""Assemble the landing page.

Icons are inlined rather than linked, because an external SVG cannot inherit
currentColor and these change colour between the light and dark sections. The
seven timeline glyphs and five leak glyphs are the exact vectors exported from
the approved Figma file, not redrawn.
"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "page.html")
OUT = os.path.join(ROOT, "index.html")
ICONS = os.path.join(ROOT, "assets", "icons")

# the long thin arrow Gal specced: a 1.25 shaft with a small chevron, pointing
# left because left is forward in Hebrew
ARROW = ('<svg width="30" height="12" viewBox="0 0 34 12" fill="none" aria-hidden="true">'
         '<path d="M33 6H2M2 6L7 1M2 6L7 11" stroke="currentColor" stroke-width="1.25" '
         'stroke-linecap="round" stroke-linejoin="round"/></svg>')

# the logo arch, shrunk to a tick beside a heading
TICK = ('<i><svg viewBox="0 0 15 18" fill="none" aria-hidden="true">'
        '<path d="M1.2 16.6V7.6a6.3 6.3 0 0 1 12.6 0v9" stroke="currentColor" '
        'stroke-width="1.4" stroke-linecap="round"/>'
        '<path d="M.5 17.4h14" stroke="#C2151C" stroke-width="1.6" stroke-linecap="round"/>'
        '</svg></i>')

STAR = ('<svg width="14" height="13" viewBox="0 0 14 13" fill="none" aria-hidden="true">'
        '<path d="M7 .8l1.85 3.75 4.14.6-3 2.92.71 4.12L7 10.24l-3.7 1.95.7-4.12-3-2.92 '
        '4.15-.6L7 .8z" fill="#E0B15C"/></svg>')
STARS = STAR * 5

CHEV_L = ('<svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">'
          '<path d="M11 4L6 9l5 5" stroke="currentColor" stroke-width="1.5" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>')
CHEV_R = ('<svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">'
          '<path d="M7 4l5 5-5 5" stroke="currentColor" stroke-width="1.5" '
          'stroke-linecap="round" stroke-linejoin="round"/></svg>')

MARK_LIGHT = ('<svg width="30" height="36" viewBox="0 0 70 82" fill="none" aria-hidden="true">'
              '<path d="M5 74 L5 33 A30 30 0 0 1 65 33 L65 74" stroke="#FAF8F5" '
              'stroke-width="2.8" stroke-linecap="round"/>'
              '<path d="M2 79 L68 79" stroke="#C2151C" stroke-width="3.2" '
              'stroke-linecap="round"/></svg>')


def build():
    s = io.open(SRC, encoding="utf-8").read()

    for name in ("ARROW", "TICK", "STARS", "CHEV_L", "CHEV_R", "MARK_LIGHT"):
        s = s.replace("{{%s}}" % name, globals()[name])

    missing = []
    for m in set(re.findall(r"\{\{([a-z0-9-]+)\}\}", s)):
        p = os.path.join(ICONS, m + ".svg")
        if not os.path.exists(p):
            missing.append(m); continue
        s = s.replace("{{%s}}" % m, io.open(p, encoding="utf-8").read().strip())

    left = re.findall(r"\{\{[^}]+\}\}", s)
    io.open(OUT, "w", encoding="utf-8").write(s)
    print("wrote index.html  %.1f KB" % (os.path.getsize(OUT) / 1024.0))
    if missing: print("  !! icon files missing:", ", ".join(missing))
    if left:    print("  !! placeholders left:", ", ".join(sorted(set(left))))
    if not missing and not left: print("  every placeholder resolved")


if __name__ == "__main__":
    build()
