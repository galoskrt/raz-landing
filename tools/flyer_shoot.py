# -*- coding: utf-8 -*-
"""Render the flyer faces and report whether anything runs off its sheet.

    python tools/flyer_shoot.py [scale]

Lives in the project rather than the scratchpad, which has been wiped three
times in this project and taken the check with it each time.
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "tools", "_faces")
NAMES = ["A-front", "A-back", "B-front", "B-back"]


def main():
    from playwright.sync_api import sync_playwright
    scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1.65
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 1400, "height": 1200},
                            device_scale_factor=scale).new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file:///" + os.path.join(ROOT, "flyer", "index.html").replace("\\", "/"),
                wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1500)
        print("page errors:", errs or "none")
        over = pg.evaluate("""()=>[...document.querySelectorAll('.panel')].map(p=>{
          const pr=p.getBoundingClientRect(); let w=0, who='';
          p.querySelectorAll('*').forEach(e=>{const r=e.getBoundingClientRect();
            const d=Math.max(r.bottom-pr.bottom, pr.top-r.top, r.right-pr.right, pr.left-r.left);
            if(d>w){w=d; who=String(e.className).slice(0,30);}});
          return {over:+(w/3.7795).toFixed(2), who};})""")
        for el, name in zip(pg.query_selector_all(".panel"), NAMES):
            el.screenshot(path=os.path.join(OUT, name + ".png"))
        br.close()
    bad = False
    for o, n in zip(over, NAMES):
        print("  %-8s overflow %5.2f mm  %s" % (n, o["over"], o["who"]))
        if o["over"] > 0.1:
            bad = True
    print("  faces written to %s" % OUT)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
