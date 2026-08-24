# -*- coding: utf-8 -*-
"""Recolor the LordIcon Lottie files to Raz's palette and slim them down.

Source uses two placeholder colours:
  #E8B9BB  the line art  (LordIcon "primary")
  #FF0000  the accent    (LordIcon "secondary")
The timeline section is charcoal, so the line art becomes stone and the
accent becomes the brand red.
"""
import io, json, os, glob, collections

SRC = u"C:/Users/HP/Downloads/\u05e8\u05d6 \u05de\u05d0\u05d9\u05e8 \u05db\u05d4\u05df"
DST = u"C:/Users/HP/raz-landing/assets"

PRIMARY = (0.91, 0.725, 0.733)      # #E8B9BB
ACCENT  = (1.0, 0.0, 0.0)           # #FF0000

# slug per stage, in timeline order
SLUG = {
    u"\u05ea\u05de\u05d7\u05d5\u05e8 \u05d5\u05d0\u05e1\u05d8\u05e8\u05d8\u05d2\u05d9\u05d4": "01-pricing",
    u"\u05d4\u05db\u05e0\u05d4 \u05d5\u05e6\u05d9\u05dc\u05d5\u05dd": "02-prep",
    u"\u05ea\u05d9\u05e7 \u05e0\u05db\u05e1 \u05de\u05e7\u05e6\u05d5\u05e2\u05d9": "03-dossier",
    u"\u05d7\u05e9\u05d9\u05e4\u05d4 \u05e7\u05d5\u05d3\u05dd \u05dc\u05de\u05d0\u05d2\u05e8": "04-database",
    u"\u05e9\u05d9\u05ea\u05d5\u05e3 \u05e4\u05e2\u05d5\u05dc\u05d4 \u05d0\u05d9\u05d6\u05d5\u05e8\u05d9": "05-network",
    u"\u05e1\u05d9\u05e0\u05d5\u05df \u05e7\u05d5\u05e0\u05d9\u05dd": "06-filter",
    u'\u05d1\u05d9\u05e7\u05d5\u05e8\u05d9\u05dd, \u05de\u05d5\u05f4\u05de \u05d5\u05e9\u05e7\u05d9\u05e4\u05d5\u05ea': "07-close",
}


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def near(a, b, tol=0.02):
    return all(abs(x - y) <= tol for x, y in zip(a[:3], b[:3]))


def swap(node, mapping, stats):
    """Walk the animation tree and replace static colour values."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "c" and isinstance(v, dict) and v.get("a") == 0 \
                    and isinstance(v.get("k"), list) and len(v["k"]) >= 3:
                for src, dstc in mapping:
                    if near(v["k"], src):
                        v["k"][0], v["k"][1], v["k"][2] = dstc
                        stats[tuple(dstc)] += 1
                        break
            else:
                swap(v, mapping, stats)
    elif isinstance(node, list):
        for v in node:
            swap(v, mapping, stats)


DROP_KEYS = {"nm", "mn", "cl", "ln", "tt", "hasMask", "sr"}


def strip_cruft(node):
    """Authoring metadata that no player reads. The host serves everything
    uncompressed, so every byte here is a byte on the wire."""
    if isinstance(node, dict):
        for k in list(node.keys()):
            if k in DROP_KEYS:
                del node[k]
            elif k == "hd" and node[k] is False:
                del node[k]
            elif k == "bm" and node[k] == 0:
                del node[k]
            else:
                strip_cruft(node[k])
    elif isinstance(node, list):
        for v in node:
            strip_cruft(v)


def round_floats(node, nd=2):
    """Lottie ships 8+ decimal places. Two is past sub pixel in a 192 box."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, float):
                node[k] = round(v, nd)
            else:
                round_floats(v, nd)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, float):
                node[i] = round(v, nd)
            else:
                round_floats(v, nd)


def build(primary_hex, accent_hex, suffix=""):
    mapping = [(PRIMARY, list(hexrgb(primary_hex))), (ACCENT, list(hexrgb(accent_hex)))]
    total_in = total_out = 0
    rows = []
    for p in sorted(glob.glob(os.path.join(SRC, "*.json"))):
        base = os.path.splitext(os.path.basename(p))[0]
        if base not in SLUG:
            print("  skip (unmapped):", base.encode("utf-8", "replace"))
            continue
        raw = io.open(p, encoding="utf-8").read()
        d = json.loads(raw)
        stats = collections.Counter()
        swap(d, mapping, stats)
        strip_cruft(d)
        round_floats(d)
        out = os.path.join(DST, SLUG[base] + suffix + ".json")
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(d, separators=(",", ":"), ensure_ascii=False))
        a, b = len(raw.encode("utf-8")), os.path.getsize(out)
        total_in += a
        total_out += b
        rows.append((SLUG[base], a / 1024.0, b / 1024.0, sum(stats.values())))
    for s, a, b, n in rows:
        print("  %-12s %6.1f KB -> %6.1f KB   %d colours swapped" % (s, a, b, n))
    print("  TOTAL %.1f KB -> %.1f KB  (%.0f%% smaller)"
          % (total_in / 1024.0, total_out / 1024.0, 100 * (1 - total_out / float(total_in))))


if __name__ == "__main__":
    print("dark-section set: stone line art, brand red accent")
    build("#F1EDE7", "#C2151C")
