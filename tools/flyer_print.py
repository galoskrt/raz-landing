# -*- coding: utf-8 -*-
"""Build the press-ready PDF for Raz's flyer.

    python tools/flyer_print.py

The sketch page `flyer/index.html` is the single source: the panels and the
stylesheet are lifted out of it, so the file that goes to the printer can never
drift from the file Gal and Raz approved on screen.

What a print shop needs, and what this produces:

**Vector, not pixels.** The pages are written by the browser's own PDF writer,
so every line of Hebrew stays as embedded type and the QR stays as paths. A
300 dpi PNG of the same page would look soft on press and the code would
depend on the printer's resampling. Photographs are the only raster content,
and each one is checked against its printed size.

**Bleed.** Ink must run 3 mm past every trim edge or a half millimetre of
guillotine drift leaves a white hairline. The panel is re-declared 6 mm wider
and taller with its padding grown to match, so the artwork genuinely extends
into the bleed instead of being scaled into it: the trim size stays exactly
100x300 and the fold stays exactly 60 mm from the head.

**Crop marks**, in their own 3 mm zone outside the bleed, which is why each
page is 112x312 mm.

**Colour is RGB and that is deliberate.** Ghostscript is not installed here,
and converting with a generic profile is worse than letting the press convert
with the profile of the machine the job actually runs on. Every Israeli press
expects that. Say so when handing the file over.
"""
import io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "flyer", "index.html")
OUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads",
                       u"רז מאיר כהן", u"פלאייר")
NAMES = [u"א-קדמי", u"א-אחורי",
         u"ב-קדמי", u"ב-אחורי"]

TRIM_W, TRIM_H, BLEED, MARK = 100.0, 300.0, 3.0, 3.0
# The finished flyer is folded at the crease, so the tab hangs the other way up.
# Printed as drawn it would read upside down in the hand; printed rotated it
# reads correctly folded and upside down flat, which is how press sheets for
# folded work normally look. Pass "flat" to export the unfolded reading order.
FOLD = "flat" not in sys.argv
PAGE_W = TRIM_W + 2 * (BLEED + MARK)      # 112
PAGE_H = TRIM_H + 2 * (BLEED + MARK)      # 312

PRINT_CSS = u"""
@page{size:%(pw)smm %(ph)smm;margin:0}
html,body{background:#fff;margin:0;padding:0}
.sheet{position:relative;width:%(pw)smm;height:%(ph)smm;page-break-after:always;
  break-after:page;overflow:hidden}
.sheet:last-child{page-break-after:auto;break-after:auto}
/* the artwork, grown by the bleed on every side */
.sheet .panel{position:absolute;top:%(mark)smm;left:%(mark)smm;
  --W:%(bw)smm; --H:%(bh)smm; --TAB:%(tab)smm; --PAD:%(pad)smm;
  box-shadow:none !important}
.sheet .panel::after{display:none !important}   /* the fold guide is screen only */
.sheet .panel .body{padding:9mm %(pad)smm %(pad)smm}
.sheet .panel .tab{transform:rotate(180deg)}   /* set FOLD=False to disable */
/* crop marks: hairlines in the mark zone, never touching the bleed.
   The class is deliberately not ".cm": that is the card's own text block in
   the artwork, and the collision gave every card a black absolute box. */
.cropmark{position:absolute;background:#000}
""" % {"pw": PAGE_W, "ph": PAGE_H, "mark": MARK,
       "bw": TRIM_W + 2 * BLEED, "bh": TRIM_H + 2 * BLEED,
       "tab": 60 + BLEED, "pad": 9 + BLEED}
if not FOLD:
    PRINT_CSS = PRINT_CSS.replace(".sheet .panel .tab{transform:rotate(180deg)}", "")


def marks():
    """Eight hairlines at the four trim corners, in the outer 3 mm."""
    t = MARK + BLEED                      # distance from page edge to trim
    out = []
    for y in (t, PAGE_H - t):
        for x0 in (0, PAGE_W - MARK):
            out.append('<i class="cropmark" style="left:%smm;top:%smm;width:%smm;height:.08mm"></i>'
                       % (x0, y, MARK))
    for x in (t, PAGE_W - t):
        for y0 in (0, PAGE_H - MARK):
            out.append('<i class="cropmark" style="left:%smm;top:%smm;width:.08mm;height:%smm"></i>'
                       % (x, y0, MARK))
    return "".join(out)


def build():
    from playwright.sync_api import sync_playwright
    url = "file:///" + SRC.replace("\\", "/")
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 1400, "height": 1200}).new_page()
        pg.goto(url, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1500)

        style = pg.evaluate("[...document.querySelectorAll('style')].map(s=>s.textContent).join('\\n')")
        panels = pg.evaluate("[...document.querySelectorAll('.panel')].map(e=>e.outerHTML)")
        head = pg.evaluate("[...document.querySelectorAll('link[rel=stylesheet]')].map(e=>e.outerHTML).join('')")
        br.close()

    assert len(panels) == 4, "expected four faces, found %d" % len(panels)
    body = "".join('<div class="sheet">%s%s</div>' % (marks(), html) for html in panels)
    doc = (u'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">'
           + head + u"<style>" + style + PRINT_CSS + u"</style></head><body>"
           + body + u"</body></html>")
    tmp = os.path.join(ROOT, "flyer", "_print.html")
    io.open(tmp, "w", encoding="utf-8").write(doc)
    return tmp


def render(tmp, out):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 1400, "height": 1200}).new_page()
        pg.goto("file:///" + tmp.replace("\\", "/"), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1800)
        over = pg.evaluate("""()=>[...document.querySelectorAll('.panel')].map(p=>{
          const pr=p.getBoundingClientRect(); let w=0;
          p.querySelectorAll('*').forEach(e=>{const r=e.getBoundingClientRect();
            w=Math.max(w, r.bottom-pr.bottom, pr.top-r.top, r.right-pr.right, pr.left-r.left);});
          return +(w/3.7795).toFixed(2);})""")
        print("  overflow per face (mm):", over)
        if max(over) > 0.1:
            sys.exit("  FAIL  artwork runs outside its own face")

        # A rule added for the press pages can collide with a class name in the
        # artwork, and every numeric check still passes while the page is
        # ruined. This is the check that catches it: nothing in the artwork may
        # be positioned by the print stylesheet, and a card's text must sit
        # below its photo rather than on top of it.
        bad = pg.evaluate("""()=>{
          const hits=[...document.querySelectorAll('.panel *')].filter(e=>
            getComputedStyle(e).position==='absolute').map(e=>e.className);
          const cards=[...document.querySelectorAll('.card')].filter(c=>{
            const ph=c.querySelector('.ph'), cm=c.querySelector('.cm');
            return !ph||!cm||cm.getBoundingClientRect().top < ph.getBoundingClientRect().bottom-1;});
          return {positioned:hits.slice(0,4), overlapping:cards.length};}""")
        if bad["positioned"] or bad["overlapping"]:
            sys.exit("  FAIL  the print stylesheet is colliding with the artwork: %s" % bad)
        print("  artwork untouched by the print stylesheet: ok")
        pg.emulate_media(media="print")
        pg.pdf(path=out, width="%smm" % PAGE_W, height="%smm" % PAGE_H,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
               print_background=True, prefer_css_page_size=True)
        br.close()


def verify(out):
    """A PDF that opens is not a PDF that prints. Check the four things a
    press job actually fails on: wrong page size, missing font, a photograph
    below 300 dpi, and type that came out as pixels."""
    import fitz
    ok = True
    doc = fitz.open(out)
    print("  pages: %d" % doc.page_count)
    if doc.page_count != 4:
        print("  FAIL  expected 4 pages"); ok = False
    for i, page in enumerate(doc):
        w, h = page.rect.width / 72 * 25.4, page.rect.height / 72 * 25.4
        size_ok = abs(w - PAGE_W) < .6 and abs(h - PAGE_H) < .6
        words = len(page.get_text("words"))
        print("    %-10s %.1f x %.1f mm %s  type objects: %d"
              % (NAMES[i], w, h, "ok" if size_ok else "WRONG SIZE", words))
        if not size_ok or words < 20:
            print("    FAIL  page %d" % (i + 1)); ok = False
        for info in page.get_images(full=True):
            xref = info[0]
            px = info[2]
            for r in page.get_image_rects(xref):
                dpi = px / (r.width / 72.0)
                if dpi < 300:
                    print("    FAIL  image %d renders at %d dpi" % (xref, dpi)); ok = False
    raw = open(out, "rb").read()
    for fam in (b"Heebo", b"Cormorant"):
        if fam in raw:
            print("  ok    %s embedded" % fam.decode())
        else:
            print("  FAIL  %s is not embedded" % fam.decode()); ok = False
    print("  size: %.1f MB" % (len(raw) / 1048576.0))
    shots = os.path.join(ROOT, "tools", "_print_check")
    os.makedirs(shots, exist_ok=True)
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=70).save(os.path.join(shots, "p%d.png" % (i + 1)))
    print("  rasters for eyeballing: %s" % shots)
    doc.close()
    return ok


def main():
    out = os.path.join(OUT_DIR, u"פלאייר-לדפוס.pdf"
                       if FOLD else u"פלאייר-שטוח.pdf")
    os.makedirs(OUT_DIR, exist_ok=True)
    print("trim %gx%g mm, bleed %g, marks %g, page %gx%g"
          % (TRIM_W, TRIM_H, BLEED, MARK, PAGE_W, PAGE_H))
    print("tab: %s" % ("rotated 180 for the fold" if FOLD else "flat, reading order"))
    tmp = build()
    render(tmp, out)
    os.remove(tmp)
    print("checking %s" % out)
    sys.exit(0 if verify(out) else 1)


if __name__ == "__main__":
    main()
