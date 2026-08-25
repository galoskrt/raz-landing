# -*- coding: utf-8 -*-
"""The lead notification Raz gets on his phone.

Text first and table based on purpose: it has to render with images off, in
Gmail on a phone, and it has to be actionable in one tap. The whole point is
that Raz never needs to open a dashboard to send the guide.
"""
import io, json, os, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(io.open(os.path.join(ROOT, "tools", ".resend.json"), encoding="utf-8"))

SITE = "https://tom-harush.co.il/raz-meir-cohen"
INK, RED, BONE, STONE, LINE, MUTED = "#14161A", "#C2151C", "#FAF8F5", "#F1EDE7", "#E2DCD3", "#71757C"
FONT = "Heebo, 'Segoe UI', Arial, sans-serif"


def wa_link(phone, first_name, token):
    """Raz taps this and WhatsApp opens with the message already written."""
    intl = "972" + phone.lstrip("0").replace("-", "").replace(" ", "")
    msg = (u"היי %s, הנה המדריך שלך.\n"
           u"%s/madrich/%s\n"
           u"אם עולה שאלה תוך כדי הקריאה, אפשר פשוט לכתוב לי. אני קורא הכל בעצמי."
           % (first_name, SITE, token))
    return "https://wa.me/%s?text=%s" % (intl, urllib.parse.quote(msg))


def row(label, value, href=None):
    v = u'<a href="%s" style="color:%s;text-decoration:none">%s</a>' % (href, INK, value) if href else value
    return (u'<tr>'
            u'<td style="padding:11px 0;border-bottom:1px solid %s;color:%s;font-size:14px;width:96px">%s</td>'
            u'<td style="padding:11px 0;border-bottom:1px solid %s;color:%s;font-size:15px;font-weight:500">%s</td>'
            u'</tr>' % (LINE, MUTED, label, LINE, INK, v))


def build(lead):
    first = lead["name"].split(" ")[0]
    wa = wa_link(lead["phone"], first, lead["token"])
    guide = "%s/madrich/%s" % (SITE, lead["token"]) if lead.get("token") else "%s/madrich/" % SITE

    return u"""<!doctype html>
<html dir="rtl" lang="he"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:%(bone)s">
<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" style="background:%(bone)s;padding:20px 12px">
<tr><td align="center">
<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#fff;border:1px solid %(line)s;border-radius:16px;overflow:hidden;font-family:%(font)s">

  <tr><td style="background:%(ink)s;padding:20px 24px">
    <div style="color:%(red)s;font-size:12px;letter-spacing:.08em;font-weight:700;line-height:1.5">ליד חדש מהדף של רז מאיר כהן</div>
    <div style="color:%(bone)s;font-size:22px;font-weight:300;padding-top:6px">%(name)s</div>
    <div style="color:#9A9AA0;font-size:13px;padding-top:5px">%(when)s</div>
  </td></tr>

  <tr><td style="padding:24px">
    <a href="%(wa)s" style="display:block;background:%(red)s;color:#ffffff;text-decoration:none;
       text-align:center;padding:17px 20px;border-radius:14px;font-size:16px;font-weight:700">
       שלח ל%(first)s את המדריך בוואטסאפ
    </a>
    <div style="color:%(muted)s;font-size:12.5px;text-align:center;padding-top:10px;line-height:1.6">
      ההודעה כבר כתובה, כולל הקישור האישי. רק ללחוץ שלח.
    </div>
  </td></tr>

  <tr><td style="padding:0 24px 8px">
    <table role="presentation" width="100%%" cellpadding="0" cellspacing="0">
      %(rows)s
    </table>
  </td></tr>

  <tr><td style="padding:18px 24px 24px">
    <a href="%(guide)s" style="display:block;background:%(stone)s;border-radius:12px;padding:14px 16px;text-decoration:none">
      <div style="color:%(muted)s;font-size:12px;padding-bottom:6px">הקישור האישי של %(first)s</div>
      <div style="direction:ltr;text-align:left;font-size:12.5px;color:%(red)s;word-break:break-all;text-decoration:underline">%(guide)s</div>
    </a>
  </td></tr>

  <tr><td style="background:%(stone)s;padding:14px 24px;text-align:center;color:%(muted)s;font-size:12px">
    <a href="%(site)s" style="color:%(muted)s;text-decoration:underline">הדשבורד</a>
    &nbsp;·&nbsp; רז מאיר כהן &nbsp;·&nbsp; מקבוצת תום הרוש
  </td></tr>

</table>
</td></tr></table>
</body></html>""" % {
        "bone": BONE, "ink": INK, "red": RED, "stone": STONE, "line": LINE,
        "muted": MUTED, "font": FONT, "site": SITE,
        "name": lead["name"], "first": first, "when": lead["when"],
        "wa": wa, "guide": guide,
        "rows": (row(u"טלפון", lead["phone"], "tel:" + lead["phone"])
                 + row(u"אימייל", lead["email"], "mailto:" + lead["email"])
                 + row(u"כתובת הנכס", lead.get("address") or u"לא צוינה")),
    }


TO_PRIMARY   = "raz@tom-harush.co.il"
TO_SECONDARY = "office@tom-harush.co.il"


def send(lead, to=None, cc=None):
    import urllib.request
    payload = {
        "from": u"%s <%s>" % (CFG["from_name"], CFG["from"]),
        "to": [to or TO_PRIMARY],
        "cc": [cc] if cc else ([TO_SECONDARY] if to is None else []),
        "reply_to": lead["email"],
        "subject": u"ליד חדש · %s · %s" % (lead["name"], lead["phone"]),
        "html": build(lead),
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + CFG["api_key"],
                 "Content-Type": "application/json",
                 # Cloudflare fronts the API and rejects the default urllib
                 # signature with error 1010. Any normal agent string passes.
                 "User-Agent": "raz-landing/1.0"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


if __name__ == "__main__":
    import sys
    demo = {"name": u"דנה כהן", "phone": "0541234567", "email": "dana.demo@gmail.com",
            "address": u"כצנלסון 41, גבעתיים", "token": "a7f3c9e2b41d",
            "when": u"היום, 14:32"}
    print(send(demo, sys.argv[1] if len(sys.argv) > 1 else "galharush46@gmail.com"))
