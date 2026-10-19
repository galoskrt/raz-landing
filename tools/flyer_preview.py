# -*- coding: utf-8 -*-
"""Build the preview Raz opens, on Gal's own domain.

    python tools/flyer_preview.py

The sketch page `flyer/index.html` is for us: it carries the reasoning behind
each direction, what each one risks, and the press spec. A client opens a page
to look at his flyer, not to read our strategy, so this page is generated from
the same four faces with all of that stripped out.

Generated rather than written, so the preview cannot drift from the artwork.
It is built mobile first, because he will open it on his phone, and each face
opens full screen on a tap for reading the small print.
"""
import io, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "flyer", "index.html")
OUT = os.path.join(ROOT, "flyer", "preview")
IMG = os.path.join(OUT, "img")
FACES = [("a-front", u"כיוון א", u"צד קדמי"), ("a-back", u"כיוון א", u"צד אחורי"),
         ("b-front", u"כיוון ב", u"צד קדמי"), ("b-back", u"כיוון ב", u"צד אחורי")]

PAGE = u"""<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<title>הפלאייר שלך · רז מאיר כהן</title>
<meta property="og:title" content="הפלאייר שלך · רז מאיר כהן">
<meta property="og:description" content="שני כיוונים לפלאייר, שני צדדים לכל אחד.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@200;300;400;500;700&display=swap" rel="stylesheet">
<style>
:root{--ink:#14161A;--ink2:#3A3F46;--muted:#6E737A;--bone:#FAF8F5;--stone:#F1EDE7;
  --line:#E2DCD3;--line2:#CFC7BC;--red:#C2151C}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Heebo,Arial,sans-serif;direction:rtl;background:var(--stone);
  color:var(--ink);line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1000px;margin:0 auto;padding:0 18px 70px}
header{padding:38px 0 6px}
header h1{font-size:clamp(25px,6.4vw,34px);font-weight:700;letter-spacing:-.015em;text-wrap:balance}
header p{color:var(--ink2);margin-top:11px;font-size:16px;max-width:58ch}
header p b{font-weight:700;color:var(--ink)}

.how{display:flex;gap:16px;align-items:center;margin-top:24px;padding:16px 18px;
  background:#fff;border:1px solid var(--line);border-radius:14px}
.how .dia{flex:none;width:46px}
.how .strip{width:38px;margin:0 auto;border:2px solid var(--ink2);border-radius:4px;overflow:hidden}
.how .tabp{height:22px;background:var(--red)}
.how .bodyp{height:60px;background:var(--bone);border-top:2px dashed var(--ink2)}
.how p{font-size:14.5px;color:var(--ink2)}
.how p b{color:var(--ink);font-weight:700}

h2{font-size:21px;font-weight:700;margin:38px 0 14px;padding-top:22px;
  border-top:1px solid var(--line2);display:flex;align-items:center;gap:9px}
.dot{width:12px;height:12px;border-radius:4px;flex:none}
.dot.a{background:linear-gradient(135deg,#D82127,#7F0224)}
.dot.b{background:#14161A}
.faces{display:grid;grid-template-columns:1fr 1fr;gap:16px}
figure{margin:0;display:flex;flex-direction:column;gap:7px}
figure button{padding:0;border:0;background:none;cursor:zoom-in;display:block;border-radius:10px}
figure img{width:100%;display:block;border-radius:10px;background:#fff;
  box-shadow:0 2px 6px rgba(20,22,26,.07),0 14px 34px rgba(20,22,26,.12)}
figcaption{font-size:12.5px;color:var(--muted);text-align:center}

.foot{margin-top:40px;padding:18px;background:#fff;border:1px solid var(--line);
  border-radius:14px;font-size:14.5px;color:var(--ink2)}
.foot b{color:var(--ink);font-weight:700}
.foot a{display:inline-flex;align-items:center;gap:8px;margin-top:12px;
  color:var(--red);font-weight:500;text-decoration:none;border-bottom:1px solid currentColor;
  padding-bottom:1px}

/* tap to read the small print */
#lb{position:fixed;inset:0;z-index:50;background:rgba(10,11,13,.92);display:none;
  align-items:center;justify-content:center;padding:16px;cursor:zoom-out}
#lb.on{display:flex}
#lb img{max-width:100%;max-height:100%;height:100%;width:auto;object-fit:contain;
  border-radius:6px}
#lb .x{position:absolute;top:14px;left:16px;width:40px;height:40px;border-radius:50%;
  border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.1);color:#fff;
  font-size:20px;line-height:1;cursor:pointer}
@media (max-width:620px){
  .faces{grid-template-columns:1fr 1fr;gap:11px}
  header{padding-top:28px}
}
@media (prefers-reduced-motion:reduce){*{transition:none !important}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>הפלאייר שלך</h1>
  <p>שני כיוונים, לכל אחד שני צדדים. <b>אפשר ללחוץ על כל תמונה כדי לפתוח אותה גדול</b>
  ולקרוא את הטקסט הקטן. הטקסטים עדיין פתוחים לשינוי.</p>
  <div class="how">
    <div class="dia"><div class="strip"><div class="tabp"></div><div class="bodyp"></div></div></div>
    <p><b>הפלאייר מקופל בראש.</b> הגוף נכנס לתיבת הדואר והראש המקופל נתפס על השפה
    ובולט החוצה, כך שרואים אותו בלי לפתוח את התיבה. לכן ההצעה וקוד הסריקה יושבים שם.</p>
  </div>
</header>
<!--FACES-->
<div class="foot">
  <b>מידות:</b> 10 על 30 סנטימטר, הדפסה בשני הצדדים, קיפול אחד 6 סנטימטר מהראש.
  קוד הסריקה זהה בכל המופעים ומוביל לדף שלך.
  <br><a href="flyer-print.pdf" download>הקובץ המוכן לבית הדפוס</a>
</div>
</div>

<div id="lb" role="dialog" aria-modal="true" aria-label="תצוגה מוגדלת">
  <button class="x" id="lbx" aria-label="סגירה">&#215;</button><img id="lbi" alt="">
</div>

<script>
(function(){
  var lb=document.getElementById("lb"), im=document.getElementById("lbi");
  function open(src,alt){ im.src=src; im.alt=alt; lb.classList.add("on");
    document.body.style.overflow="hidden"; }
  function shut(){ lb.classList.remove("on"); im.src=""; document.body.style.overflow=""; }
  [].slice.call(document.querySelectorAll("figure button")).forEach(function(b){
    b.addEventListener("click", function(){
      var i=b.querySelector("img"); open(i.src, i.alt);
    });
  });
  lb.addEventListener("click", shut);
  document.getElementById("lbx").addEventListener("click", shut);
  document.addEventListener("keydown", function(e){ if(e.key==="Escape") shut(); });
})();
</script>
</body>
</html>
"""


def main():
    os.makedirs(IMG, exist_ok=True)
    from playwright.sync_api import sync_playwright
    from PIL import Image
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_context(viewport={"width": 1400, "height": 1200},
                            device_scale_factor=3).new_page()
        pg.goto("file:///" + SRC.replace("\\", "/"), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(1600)
        pg.add_style_tag(content=".panel::after{display:none !important}")
        pg.wait_for_timeout(300)
        panels = pg.query_selector_all(".panel")
        assert len(panels) == 4, "expected four faces, found %d" % len(panels)
        for el, (slug, _, _) in zip(panels, FACES):
            el.screenshot(path=os.path.join(IMG, slug + ".png"))
        br.close()
    for slug, _, _ in FACES:
        p_ = os.path.join(IMG, slug + ".png")
        im = Image.open(p_).convert("RGB")
        im = im.resize((900, int(900 * im.height / im.width)), Image.LANCZOS)
        im.save(os.path.join(IMG, slug + ".jpg"), "JPEG", quality=86,
                optimize=True, progressive=True)
        os.remove(p_)
        print("  %-9s %sx%s  %.0f KB" % (slug, im.width, im.height,
              os.path.getsize(os.path.join(IMG, slug + ".jpg")) / 1024.0))

    body = []
    for con, dot in ((u"כיוון א", "a"), (u"כיוון ב", "b")):
        rows = "".join(
            u'<figure><button type="button"><img src="img/%s.jpg" alt="%s %s" loading="lazy">'
            u'</button><figcaption>%s</figcaption></figure>' % (s, c, side, side)
            for s, c, side in FACES if c == con)
        body.append(u'<h2><span class="dot %s"></span>%s</h2><div class="faces">%s</div>'
                    % (dot, con, rows))
    html = PAGE.replace("<!--FACES-->", chr(10).join(body))
    io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
    print("  page written, %d chars" % len(html))


if __name__ == "__main__":
    main()
