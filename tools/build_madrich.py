# -*- coding: utf-8 -*-
"""Port the printed guide to a scrolling web page.

The guide was authored as HTML at 720x1280 per page and only then printed to
PDF, so this is a port and not a rebuild: same markup, same copy, same colours.
What changes is the page model. Fixed-height pages become sections of natural
height, dark divider pages become full-bleed bands, and the fonts come from the
CDN rather than 600 KB of embedded base64.
"""
import io, os, re

SRC_DIR = ("C:/Users/HP/AppData/Local/Temp/claude/C--Users-HP/"
           "8c8bcb44-a1c9-4131-99c1-b850f0a87bb9/scratchpad/raz")
ROOT = "C:/Users/HP/raz-landing"
OUT = os.path.join(ROOT, "madrich", "index.html")

IMAGES = {
    "M_DARK":    "../assets/guide/m_dark.jpg",
    "M_CREAM":   "../assets/guide/m_cream.jpg",
    "M_GREY":    "../assets/guide/m_grey.jpg",
    "M_WASH":    "../assets/guide/m_wash.jpg",
    "RAZ_BEIGE": "../assets/guide/raz_beige.png",
    "RAZ_NAVY":  "../assets/guide/raz_navy.png",
}

HEAD = u"""<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#14161A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@200;300;400;500;700;900&family=Cormorant+Garamond:wght@600&display=swap" rel="stylesheet">"""

# Everything that turns a print sheet into a web page.
WEB_CSS = u"""
/* ============ web overrides ============ */
html{scroll-behavior:smooth}
html,body{overflow-x:hidden;max-width:100%}
body{background:var(--bone);font-size:17px}
img{max-width:100%}

.pg{width:100%;height:auto;min-height:0;overflow:hidden;
    page-break-after:auto;break-after:auto;justify-content:flex-start}
.pad{max-width:760px;margin:0 auto;padding:78px 46px}
.grow{flex:0}

/* dark bands run edge to edge, their content stays in the column */
.pg.dk{background:var(--ink)}
.bgi{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}

/* the cover becomes a real hero */
#cover{min-height:min(100svh,900px);justify-content:flex-end}

/* Raz was cut out for a 720x1280 sheet and pinned by absolute offsets, which on
   a fluid page drop him straight onto the copy. Reserving space with padding is
   fragile here, so he leaves the overlay entirely and joins the page flow. The
   page is already a flex column, so order puts him last whatever the markup says. */
/* Some pages pin their whole copy block with an inline absolute style, which
   is fine on a fixed sheet and useless on a fluid page: nothing else can flow
   around it. Put those blocks back in the flow. */
.pg .pad[style*="absolute"]{position:static !important;inset:auto !important}

.pg img[src*="raz_"]{
  /* relative, not static: the marble .bgi is positioned, and a static element
     paints underneath every positioned one in the same stacking context. */
  position:relative !important;z-index:2;
  align-self:center;flex:0 0 auto;
  display:block;margin:26px auto 0;
  inset:auto !important;transform:none !important;
  height:auto !important;width:auto;
  max-height:min(52vh,500px);max-width:78%}

/* a thin progress rail, the only new element on the page */
#rail{position:fixed;top:0;right:0;left:0;height:3px;background:transparent;z-index:60}
#rail i{display:block;height:100%;width:0;background:var(--red);transition:width .12s linear}

.tease{max-width:min(402px,100%)}

/* the personal greeting */
#hello{background:var(--ink);color:var(--bone);text-align:center;padding:30px 24px 34px}
#hello .k{font-family:"Cormorant Garamond",Georgia,serif;direction:ltr;font-size:13px;
    letter-spacing:.34em;color:var(--red);display:block;margin-bottom:12px}
#hello h2{font-size:26px;font-weight:200;line-height:1.35;color:var(--bone);margin:0}
#hello h2 b{font-weight:500}
#hello p{font-size:14.5px;color:#9A9AA0;margin:10px 0 0;font-weight:300}

/* closing action back to Raz */
#back{background:var(--ink);text-align:center;padding:64px 24px 78px}
#back .k{font-family:"Cormorant Garamond",Georgia,serif;direction:ltr;font-size:13px;
    letter-spacing:.34em;color:var(--red);display:block;margin-bottom:14px}
#back h2{font-size:28px;font-weight:200;color:var(--bone);line-height:1.4;margin:0 0 10px}
#back h2 b{font-weight:500}
#back p{font-size:15px;color:#9A9AA0;font-weight:300;margin:0 auto 26px;max-width:420px}
#back a{display:inline-flex;align-items:center;justify-content:center;gap:12px;
    min-width:300px;padding:17px 30px;border-radius:18px;text-decoration:none;
    color:#fff;font-size:16.5px;font-weight:500;
    background:linear-gradient(135deg,#D82127 0%,#C2151C 52%,#8F081B 100%);
    box-shadow:0 12px 30px rgba(194,21,28,.32),0 2px 0 rgba(255,255,255,.16) inset}
#back svg{flex:none}

@media (max-width:820px){
  body{font-size:16px}
  .pad{padding:56px 24px}
  /* the guide was drawn on a 720 sheet, so a few blocks carry inline widths
     up to 470px. max-width always beats an inline width. */
  .pad *{max-width:100%}
  /* and a print type scale is not a phone type scale */
  .cvtitle{font-size:104px}
  .cvhe{font-size:31px}
  h1{font-size:29px;line-height:1.28}
  h2{font-size:23px;line-height:1.34}
  h3{font-size:18px}
  .stats .n{font-size:25px}
  .vs .big,.quote{font-size:19.5px;line-height:1.6}
  [style*="font-size:52px"]{font-size:31px !important}
  [style*="font-size:27px"]{font-size:20px !important}
  .tease{margin-top:24px}
  #cover{min-height:0}
  .pg img[src*="raz_"]{max-height:min(44vh,400px);max-width:90%}
  #hello h2{font-size:22px}
  #back h2{font-size:23px}
  #back a{min-width:0;width:100%}
}
"""

HELLO = u"""<div id="rail"><i></i></div>
<section id="hello">
  <span class="k">YOUR COPY</span>
  <h2>היי <b data-lead-name>דנה</b>, זה המדריך שלך.</h2>
  <p>שבעה פרקים קצרים. אפשר לקרוא ברצף או לחזור אליו מתי שנוח.</p>
</section>
"""

BACK = u"""<section id="back">
  <span class="k">ONE MORE THING</span>
  <h2>עלתה לך שאלה תוך כדי?<br><b>פשוט תכתוב לי.</b></h2>
  <p>אני קורא הכל בעצמי.</p>
  <a href="https://wa.me/972544263355" target="_blank" rel="noopener">
    <svg width="30" height="12" viewBox="0 0 34 12" fill="none" aria-hidden="true">
      <path d="M33 6H2M2 6L7 1M2 6L7 11" stroke="#fff" stroke-width="1.25"
            stroke-linecap="round" stroke-linejoin="round"/></svg>
    לכתוב לרז בוואטסאפ
  </a>
</section>
"""

SCRIPT = u"""<script>
(function () {
  var API   = "https://raz-leads.tom-harush.workers.dev";
  var seg   = location.pathname.replace(/\/+$/, "").split("/").pop();
  var TOKEN = /^[a-f0-9]{8,}$/.test(seg) ? seg : null;
  var VISIT = Math.random().toString(36).slice(2) + Date.now().toString(36);

  var bar = document.querySelector("#rail i");
  var deepest = 0, active = 0, idle = 0, sent = "";

  function onScroll() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    var p = h > 0 ? window.scrollY / h : 0;
    bar.style.width = (p * 100).toFixed(1) + "%";
    var pct = Math.round(p * 100);
    if (pct > deepest) deepest = pct;
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Greet by name. The link is personal, so the page should say so.
  if (TOKEN) {
    fetch(API + "/guide/" + TOKEN).then(function (r) { return r.json(); }).then(function (d) {
      if (!d || !d.first_name) return;
      var el = document.querySelector("[data-lead-name]");
      if (el) el.textContent = d.first_name;
    }).catch(function () {});
  }

  // Depth alone lies: a reader can flick to the bottom in two seconds just to
  // see how long it is. Count only seconds where the tab is visible AND the
  // person is doing something, so the number means attention, not elapsed time.
  ["scroll", "touchstart", "mousemove", "keydown", "click"].forEach(function (e) {
    window.addEventListener(e, function () { idle = 0; }, { passive: true });
  });
  setInterval(function () {
    if (document.hidden) return;
    idle += 1;
    if (idle <= 20) active += 1;
  }, 1000);

  function beat() {
    if (!TOKEN) return;
    var body = JSON.stringify({ t: TOKEN, v: VISIT, depth: deepest, secs: active });
    if (body === sent) return;          // nothing changed, do not chatter
    sent = body;
    if (navigator.sendBeacon) navigator.sendBeacon(API + "/read", body);
    else fetch(API + "/read", { method: "POST", body: body, keepalive: true });
  }
  setInterval(beat, 15000);
  document.addEventListener("visibilitychange", function () { if (document.hidden) beat(); });
  window.addEventListener("pagehide", beat);
})();
</script>
"""


def move_cutouts_to_page_end(html):
    """Each Raz cutout is authored near the top of its page and pinned by
    absolute offsets. Put it last in the markup instead, so it simply follows
    the copy no matter how the page reflows."""
    parts = html.split('<div class="pg')
    out = [parts[0]]
    for chunk in parts[1:]:
        m = re.search(r'<img[^>]*raz_[^>]*>', chunk)
        if m:
            tag = m.group(0)
            chunk = chunk[:m.start()] + chunk[m.end():]
            close = chunk.rfind('</div>')
            if close != -1:
                chunk = chunk[:close] + tag + chunk[close:]
        out.append(chunk)
    return '<div class="pg'.join(out)


def build():
    src = io.open(os.path.join(SRC_DIR, "guide.html"), encoding="utf-8").read()
    style = io.open(os.path.join(SRC_DIR, "guidestyle.css"), encoding="utf-8").read()

    # fonts come from the CDN now, so the two embed tokens simply go away
    src = src.replace("/*FONT*/", "").replace("/*CORM*/", "")
    src = src.replace("/*STYLE*/", style + WEB_CSS)
    src = src.replace("<head>", "<head>\n" + HEAD, 1)

    for token, path in IMAGES.items():
        src = src.replace(token, path)

    # first page becomes the hero, and Raz on the cover gets a class to steer
    src = src.replace('<div class="pg dk">', '<div class="pg dk" id="cover">', 1)
    src = re.sub(r'(<img src="\.\./assets/guide/raz_beige\.png")([^>]*)>',
                 r'<img class="cvraz" src="../assets/guide/raz_beige.png">', src, count=1)

    src = move_cutouts_to_page_end(src)

    src = src.replace("<body>", "<body>\n" + HELLO, 1)
    src = src.replace("</body>", BACK + SCRIPT + "\n</body>", 1)

    io.open(OUT, "w", encoding="utf-8").write(src)
    kb = os.path.getsize(OUT) / 1024.0
    print("wrote %s  %.1f KB" % (OUT, kb))
    print("sections: %d" % src.count('class="pg'))
    for t in IMAGES:
        if t in src:
            print("  !! token left unreplaced:", t)


if __name__ == "__main__":
    build()
