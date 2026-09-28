# -*- coding: utf-8 -*-
"""Find every place the copy commits to a gender.

    python tools/gender_audit.py

Hebrew forces a gender on most verbs and adjectives, and the reader of these
pages is a property owner of either one. The rule the project settled on:
address the reader in SINGULAR neutral forms, describe them from outside in
PLURAL, and let the client speak about himself in the masculine.

Two things this learned the hard way. A word list misses what it was not told
about, so the reliable pass is the second one: **collect every word that starts
with tav**, which is where every second person future and imperative hides, and
read that closed list. And most hits are false: the accusative particle is not
the feminine pronoun, a property can be masculine, and a real testimonial is
never edited whatever it says.
"""
import io, re, urllib.request

D = r"C:\Users\HP\AppData\Local\Temp\claude\C--Users-HP\8c8bcb44-a1c9-4131-99c1-b850f0a87bb9\scratchpad"


def get(u):
    return urllib.request.urlopen(
        urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8")


def txt(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", h, flags=re.S)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", h.replace("&nbsp;", " ").replace("\u00a0", " ").replace("&#8211;", "-"))


HE = u"\u05d0-\u05ea"

GROUPS = [
 (u"גוף שני זכר, יחיד", u"""אתה תוכל תבחר תמכור תקרא תדע תצטרך תרצה תגלה תקבל תשלם
    תחשוב תבין תמצא תשאל תוריד תחתום תתחיל תבדוק תעשה תיקח תראה תזכור תסכים
    תיכנס תשב תלחץ תשים קרא בדוק בחר שאל תן קח חשוב זכור""".split()),
 (u"גוף שני נקבה, יחיד", u"את תוכלי תבחרי תמכרי תקראי תדעי תצטרכי תרצי תקבלי תביני".split()),
 (u"גוף שני רבים", u"""אתם שלכם לכם אתכם תבחרו תקראו תמכרו תוכלו תדעו תרצו תקבלו
    תבינו תעשו תשאלו תסמנו תלחצו תעברו תרגישו תשאירו""".split()),
 (u"בינוני זכר בגוף ראשון", [u"אני צריך", u"אני יודע", u"אני חושב", u"אני בטוח",
                              u"אני מוכן", u"אני רואה", u"אני מרגיש", u"אני מבין",
                              u"אני עושה", u"אני מכיר", u"אני שולח", u"אני זמין",
                              u"אני גר", u"אני נמצא", u"אני מלווה", u"אני אומר"]),
 (u"תיאור בעל הנכס ביחיד", [u"בעל נכס", u"בעל הנכס", u"בעל דירה", u"בעל הדירה",
                             u"בעל בית", u"מוכר פרטי", u"המוכר"]),
 (u"תואר זכר", u"בטוח מוכן מרוצה עסוק מודאג חייב זכאי".split()),
]

rows = []
for name, url in ((u"דף הנחיתה", "https://tom-harush.co.il/raz-meir-cohen/?s=11"),
                  (u"המדריך", "https://tom-harush.co.il/raz-meir-cohen/madrich/?s=11"),
                  (u"דף התודה", "https://tom-harush.co.il/raz-meir-cohen/thanks/?s=11")):
    t = txt(get(url))
    rows.append(u"\n########## %s ##########" % name)
    for label, words in GROUPS:
        hits = []
        for w in words:
            pat = re.escape(w) if u" " in w else u"(?<![%s])%s(?![%s])" % (HE, re.escape(w), HE)
            for m in re.finditer(pat, t):
                hits.append((w, t[max(0, m.start() - 75):m.start() + 65].strip()))
        if not hits:
            continue
        rows.append(u"\n--- %s : %d ---" % (label, len(hits)))
        for w, c in hits:
            rows.append(u"  [%s]  %s" % (w, c))

io.open(D + r"\gender_all.txt", "w", encoding="utf-8", newline="\n").write(u"\n".join(rows))
print("written", sum(1 for r in rows if r.startswith("  [")), "hits")
