# -*- coding: utf-8 -*-
"""Render the live guide to a static PDF for Raz to send.

    python tools/render_guide_pdf.py
    python tools/render_guide_pdf.py --out "C:\\path\\to\\file.pdf"

The guide's source of truth is `madrich/index.html`, the same file that serves
the web version, so the PDF can never drift from what a lead actually reads.
The page geometry comes from the `@media print` block in that file: on screen
the guide is one continuous scroll, on paper every `.pg` is one sheet.

Three things this has to get right, each of which has failed before:

**The font.** Chrome's headless print silently falls back to Segoe UI when the
webfont has not finished loading, and Hebrew in the wrong face is the first
thing anyone notices. So we wait on `document.fonts.ready` and then assert the
family is actually embedded in the output bytes.

**The path.** Chrome's own `--print-to-pdf` will not open a Hebrew filename and
writes an error page with exit code 0. Playwright does not have that problem,
which is the main reason it is used here rather than the Chrome CLI.

**The proof.** A PDF that opens is not a PDF that is right. The run ends by
rasterising a few pages so they can be looked at, because page count and font
name together still cannot tell you the layout held.
"""
import argparse, io, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "madrich", "index.html")
DEFAULT_OUT = os.path.join(
    os.path.expanduser("~"), "Downloads", u"\u05e8\u05d6 \u05de\u05d0\u05d9\u05e8 \u05db\u05d4\u05df",
    u"\u05e7\u05d1\u05e6\u05d9\u05dd \u05e0\u05d5\u05e1\u05e4\u05d9\u05dd",
    u"\u05de\u05d3\u05e8\u05d9\u05da 90 \u05d4\u05d9\u05de\u05d9\u05dd \u05d4\u05e8\u05d0\u05e9\u05d5\u05e0\u05d9\u05dd.pdf")


def expected_pages():
    return io.open(SRC, encoding="utf-8").read().count('class="pg')


def render(out, scale):
    from playwright.sync_api import sync_playwright
    url = "file:///" + SRC.replace("\\", "/")
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 760, "height": 1280}).new_page()
        pg.goto(url, wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1500)
        fams = pg.evaluate("[...document.fonts].map(f => f.family + ' ' + f.weight).sort()")
        print("  fonts loaded:", ", ".join(sorted(set(f.split()[0] for f in fams))) or "none")
        pg.emulate_media(media="print")
        pg.pdf(path=out, width="190.5mm", height="338.6mm",
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
               print_background=True, prefer_css_page_size=True, scale=scale)
        br.close()



def shrink(path):
    """Chrome re-encodes every image to PNG when it prints, which triples the
    file. Put the opaque ones back as JPEG.

    The stream has to go in UNCOMPRESSED (`compress=False`): JPEG carries its
    own compression, and letting PyMuPDF deflate it again while the dictionary
    says DCTDecode produces a file that opens, reports the right page count and
    renders nothing. That exact mistake cost a round here, so the function
    rasterises a page at the end and refuses to keep a result it cannot draw.
    """
    import fitz, io as _io
    from PIL import Image
    before = os.path.getsize(path)
    doc = fitz.open(path)
    n = 0
    for xref in sorted({i[0] for p in range(doc.page_count) for i in doc[p].get_images(full=True)}):
        info = doc.extract_image(xref)
        im = Image.open(_io.BytesIO(info["image"]))
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            continue
        buf = _io.BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=80, optimize=True, progressive=True)
        if buf.tell() >= len(info["image"]) * 0.85:
            continue
        doc.update_stream(xref, buf.getvalue(), new=True, compress=False)
        doc.xref_set_key(xref, "Filter", "/DCTDecode")
        doc.xref_set_key(xref, "ColorSpace", "/DeviceRGB")
        doc.xref_set_key(xref, "BitsPerComponent", "8")
        n += 1
    tmp = path + ".small"
    doc.save(tmp, garbage=4, deflate=True, clean=True)
    doc.close()

    probe = fitz.open(tmp)                      # draw it, or throw the result away
    try:
        for i in (0, probe.page_count // 2, probe.page_count - 1):
            probe[i].get_pixmap(dpi=36)
        good = True
    except Exception as e:
        print("  shrink produced an unreadable file, keeping the original:", e)
        good = False
    probe.close()
    if not good:
        os.remove(tmp)
        return
    os.replace(tmp, path)
    print("  shrink: %d images to JPEG, %.1f MB -> %.1f MB"
          % (n, before / 1048576.0, os.path.getsize(path) / 1048576.0))


def verify(out, want_pages):
    raw = open(out, "rb").read()
    ok = True
    print("  size: %.1f MB" % (len(raw) / 1048576.0))
    if b"Heebo" not in raw:
        print("  FAIL  Heebo is not embedded, the PDF fell back to a system font")
        ok = False
    else:
        print("  ok    Heebo embedded")
    try:
        import fitz
        doc = fitz.open(out)
        print("  pages: %d (expected %d)" % (doc.page_count, want_pages))
        if doc.page_count != want_pages:
            print("  FAIL  page count does not match the number of .pg blocks")
            ok = False
        shots = os.path.join(ROOT, "tools", "_pdf_check")
        os.makedirs(shots, exist_ok=True)
        for i in sorted({0, 1, want_pages // 2, doc.page_count - 1}):
            if i < doc.page_count:
                doc[i].get_pixmap(dpi=72).save(os.path.join(shots, "p%02d.png" % (i + 1)))
        print("  rasters for eyeballing: %s" % shots)
        doc.close()
    except ImportError:
        print("  note  PyMuPDF not installed, page count and rasters skipped")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    want = expected_pages()
    print("rendering %d pages from %s" % (want, SRC))
    render(a.out, a.scale)
    shrink(a.out)
    print("checking %s" % a.out)
    sys.exit(0 if verify(a.out, want) else 1)


if __name__ == "__main__":
    main()
