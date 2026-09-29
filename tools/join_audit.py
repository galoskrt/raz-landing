# -*- coding: utf-8 -*-
import io, sys, json
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const out = {hidden: [], longtok: []};
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
  const txt = n => (n && n.nodeType === 3) ? n.nodeValue : null;
  let el;
  while ((el = walk.nextNode())) {
    const cs = getComputedStyle(el);
    if (cs.display !== 'none' && cs.visibility !== 'hidden') continue;
    // find the nearest preceding / following sibling text
    let p = el.previousSibling, n = el.nextSibling;
    while (p && p.nodeType === 8) p = p.previousSibling;
    while (n && n.nodeType === 8) n = n.nextSibling;
    const pt = txt(p), nt = txt(n);
    if (pt === null || nt === null) continue;
    const a = pt.replace(/\s+$/, '') , b = nt.replace(/^\s+/, '');
    if (!a || !b) continue;
    const joinsHere = /\S$/.test(pt) && /^\S/.test(nt);
    if (joinsHere) out.hidden.push({
      tag: el.tagName, cls: el.className, disp: cs.display,
      before: a.slice(-25), after: b.slice(0, 25),
      parent: el.parentElement ? el.parentElement.tagName + '.' + el.parentElement.className : ''
    });
  }
  const t = document.body.innerText || '';
  const seen = {};
  t.split(/[\s ]+/).forEach(w => {
    const clean = w.replace(/[^֐-׿]/g, '');
    if (clean.length >= 13 && !seen[clean]) { seen[clean] = 1; out.longtok.push(clean); }
  });
  return out;
}
"""

PAGES = [
    ("landing", "https://tom-harush.co.il/raz-meir-cohen/"),
    ("thanks",  "https://tom-harush.co.il/raz-meir-cohen/thanks/"),
    ("madrich", "https://tom-harush.co.il/raz-meir-cohen/madrich/"),
    ("meeting", "https://tom-harush.co.il/raz-meir-cohen/meeting/"),
]
WIDTHS = [(390, 844), (900, 1000), (1440, 900)]

res = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")
    for name, url in PAGES:
        for w, h in WIDTHS:
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.goto(url, wait_until="networkidle", timeout=60000)
            pg.wait_for_timeout(700)
            r = pg.evaluate(JS)
            res.append({"page": name, "w": w, "hidden": r["hidden"], "longtok": r["longtok"]})
            pg.close()
    b.close()

io.open(sys.argv[1], "w", encoding="utf-8").write(json.dumps(res, ensure_ascii=False, indent=1))
print("done")
