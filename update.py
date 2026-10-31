"""Regenerate card-dark.svg, card-light.svg and the README activity section.

Stdlib only. Run from the repo root: python update.py  (or --selftest).
Any failed fetch exits non-zero before anything is written.
The card copies the portfolio site's look: Schibsted Grotesk + IBM Plex Mono
(embedded from fonts/, both OFL), forest and sage colours, and the home page's
network map. If photo.jpg exists it sits in the middle of the map.
"""
import base64
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

USER = "noahrohlinger40-commits"
PROFILE = USER  # the profile repo shares the user name
START, END = "<!-- activity:start -->", "<!-- activity:end -->"
SANS, MONO = "'Schibsted Grotesk', 'Segoe UI', Arial, sans-serif", "'IBM Plex Mono', Consolas, monospace"
FONTS = [("Schibsted Grotesk", 800, "grotesk-800"), ("Schibsted Grotesk", 500, "grotesk-500"),
         ("IBM Plex Mono", 400, "plexmono-400"), ("IBM Plex Mono", 500, "plexmono-500")]

THEMES = {  # from the site's tokens; dark is the same palette at night
    "light": dict(bg="#F5F6F1", dot="#D3DACE", border="#D3DACE", ink="#13201A",
                  mute="#4D5A52", wire="#6F7F73", acc="#1E6B47"),
    "dark": dict(bg="#0F1A14", dot="#22342A", border="#2A3B31", ink="#E9EDE2",
                 mute="#9AA89F", wire="#6B7E72", acc="#7CC39B"),
}
# (name, what it is, angle around the hub in degrees, 0 = right, clockwise)
NODES = [("Jarvis", "desktop AI assistant", 215), ("Matchob", "Chrome extension", 165),
         ("Help Desk Sim", "backend API", 115), ("LanSentinel", "network scanner", 50),
         ("AI Usage Rings", "usage widget", 310), ("Now Playing", "Spotify widget", 265)]


def rel(then, now):
    d = (now.date() - then.date()).days
    if d <= 0:
        return "today"
    if d == 1:
        return "yesterday"
    if d < 7:
        return f"{d} days ago"
    if d < 30:
        w = d // 7
        return f"{w} week{'s' * (w != 1)} ago"
    m = d // 30
    return f"{m} month{'s' * (m != 1)} ago"


def replace_between(text, body):
    a, b = text.index(START) + len(START), text.index(END)
    if a > b:
        raise ValueError("markers out of order")
    return text[:a] + "\n" + body + "\n" + text[b:]


def get(path):
    h = {"Accept": "application/vnd.github+json", "User-Agent": USER}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    url = "https://api.github.com" + path
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        return json.load(r)


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)  # same clock as now


def title(name, tag):
    """Release title without the leading tag or any em dash."""
    name = (name or "").strip()
    if name.startswith(tag):
        name = name[len(tag):].lstrip(" —-:")
    return name.replace("—", "-")


def fetch():
    repos = [r["name"] for r in get(f"/users/{USER}/repos?per_page=100&type=owner")
             if not r["fork"] and r["name"] != PROFILE]
    releases = []
    for n in repos:
        for r in get(f"/repos/{USER}/{n}/releases?per_page=3"):
            if not r["draft"] and r.get("published_at"):
                releases.append(dict(repo=n, tag=r["tag_name"], name=title(r["name"], r["tag_name"]),
                                     url=r["html_url"], when=ts(r["published_at"])))
    releases.sort(key=lambda r: r["when"], reverse=True)
    # Commit search covers every public repo he commits to (Matchob included), newest first.
    found = get(f"/search/commits?q=author:{USER}&sort=author-date&order=desc&per_page=30")
    commits = []
    for c in found["items"]:
        msg = c["commit"]["message"].split("\n")[0].strip().replace("—", "-")
        if not msg.startswith("Merge") and c["repository"]["name"] != PROFILE:
            commits.append(dict(msg=msg, repo=c["repository"]["name"], url=c["html_url"],
                                when=ts(c["commit"]["author"]["date"])))
    return dict(repos=len(repos), releases=releases, commits=commits[:5], total=found["total_count"])


def activity(d, now):
    out = [f"- **[{r['repo']}]({r['url']}) {r['tag']}**{': ' + r['name'] if r['name'] else ''} · {rel(r['when'], now)}"
           for r in d["releases"][:3]]
    out += [f"- {c['msg']} · [{c['repo']}]({c['url']}) · {rel(c['when'], now)}" for c in d["commits"]]
    return "\n".join(out + ["", "_Updated daily by a GitHub Action._"])


def fontface(fonts):
    return "".join(f"@font-face{{font-family:'{fam}';font-weight:{w};"
                   f"src:url(data:font/woff2;base64,{base64.b64encode(fonts[f]).decode()}) format('woff2')}}"
                   for fam, w, f in FONTS if f in fonts)


def card(theme, d, fonts=None, photo=None):
    t = THEMES[theme]
    W, H, HX, HY = 1000, 340, 755, 178  # card size and the hub's centre
    hub = 74 if photo else 7            # wires start at the photo's edge, or at the dot
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         "<title>Noah Rohlinger: IT student at Florida State</title>",
         f"<style>{fontface(fonts or {})}"
         f".s{{font-family:{SANS}}}.m{{font-family:{MONO}}}"
         # Each project's link lights up in turn, like the site's network map.
         f"@keyframes lit{{0%,14%{{stroke:{t['acc']};stroke-width:2}}22%,100%{{stroke:{t['wire']};stroke-width:1}}}}"
         f"@keyframes dot{{0%,14%{{fill:{t['acc']}}}22%,100%{{fill:{t['ink']}}}}}"
         f".w{{animation:lit {len(NODES) * 2.5}s infinite}}.n{{animation:dot {len(NODES) * 2.5}s infinite}}"
         "@media (prefers-reduced-motion:reduce){.w,.n{animation:none}}</style>",
         f'<defs><pattern id="g" width="18" height="18" patternUnits="userSpaceOnUse">'
         f'<circle cx="9" cy="9" r="1" fill="{t["dot"]}"/></pattern>'
         '<radialGradient id="f"><stop offset="0.55" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
         f'<mask id="fade"><circle cx="{HX}" cy="{HY}" r="96" fill="url(#f)"/></mask></defs>',
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="url(#g)"/>']
    for r in (118, 158):
        o.append(f'<circle cx="{HX}" cy="{HY}" r="{r}" fill="none" stroke="{t["wire"]}" '
                 f'stroke-width="1" stroke-dasharray="1 6" opacity=".7"/>')
    for i, (name, what, deg) in enumerate(NODES):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        x, y = HX + 165 * c, HY + 128 * s
        delay = f'style="animation-delay:{i * 2.5}s"'
        o.append(f'<line class="w" {delay} x1="{HX + hub * c:.1f}" y1="{HY + hub * s:.1f}" '
                 f'x2="{x:.1f}" y2="{y:.1f}" stroke="{t["wire"]}" stroke-width="1"/>')
        o.append(f'<circle class="n" {delay} cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{t["ink"]}"/>')
        side, lx = ("end", x - 14) if c < 0 else ("start", x + 14)
        o.append(f'<text class="s" x="{lx:.1f}" y="{y + 1:.1f}" text-anchor="{side}" font-size="16" '
                 f'font-weight="800" fill="{t["ink"]}">{escape(name)}</text>')
        o.append(f'<text class="m" x="{lx:.1f}" y="{y + 18:.1f}" text-anchor="{side}" font-size="11.5" '
                 f'fill="{t["mute"]}">{escape(what)}</text>')
    if photo:
        o.append(f'<image href="data:image/jpeg;base64,{base64.b64encode(photo).decode()}" x="{HX - 96}" '
                 f'y="{HY - 96}" width="192" height="192" mask="url(#fade)"/>')
    else:
        o.append(f'<circle cx="{HX}" cy="{HY}" r="{hub}" fill="{t["acc"]}"/>')
    # Under the photo like the site; without it, in the free gap right of the dot (no wire crosses it).
    lx, ly, anchor = (HX, HY + 112, "middle") if photo else (HX + 16, HY + 4, "start")
    o.append(f'<text class="m" x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="12" '
             f'fill="{t["mute"]}">noah_rohlinger</text>')
    o += [f'<text class="m" x="44" y="76" font-size="12.5" font-weight="500" letter-spacing="1.2" '
          f'fill="{t["acc"]}">NOAH_ROHLINGER / GITHUB</text>',
          f'<text class="s" font-size="33" font-weight="800" letter-spacing="-0.5" fill="{t["ink"]}">'
          '<tspan x="44" y="122">I\'m Noah, and this is</tspan><tspan x="44" y="160">what I\'ve built so far.</tspan></text>',
          f'<text class="s" font-size="17" font-weight="500" fill="{t["ink"]}">'
          '<tspan x="44" y="206">IT student at Florida State, seeking a 2027</tspan>'
          '<tspan x="44" y="231">internship in IT support or infrastructure.</tspan></text>',
          f'<text class="m" x="44" y="280" font-size="12.5" fill="{t["mute"]}">'
          f'{d["repos"]} public repos · {d["total"]:,} commits · refreshed daily</text>',
          "</svg>"]
    return "\n".join(o) + "\n"


def selftest():
    now = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)
    for days, want in [(0, "today"), (1, "yesterday"), (3, "3 days ago"), (7, "1 week ago"),
                       (15, "2 weeks ago"), (30, "1 month ago"), (95, "3 months ago")]:
        got = rel(now - timedelta(days=days), now)
        assert got == want, (days, got)
    assert rel(ts("2026-10-28T22:30:00-04:00"), now) == "today"  # an evening commit in Florida is the 29th in UTC
    src = f"a\n{START}\nold\n{END}\nb\n"
    assert replace_between(src, "new") == f"a\n{START}\nnew\n{END}\nb\n"
    assert replace_between(replace_between(src, "x"), "YYY").count("YYY") == 1
    assert title("v1.2.0 — A guard", "v1.2.0") == "A guard" and title("v1.0", "v1.0") == ""
    assert title("Notes from 2014", "v2") == "Notes from 2014"
    try:
        replace_between("no markers", "x")
        raise AssertionError("missing markers must raise")
    except ValueError:
        pass
    for photo in (None, b"jpg"):
        s = card("dark", dict(repos=5, total=1234), photo=photo)
        assert s.startswith("<svg") and "5 public repos · 1,234 commits" in s
        assert s.count('class="w"') == len(NODES) and ("<image" in s) == bool(photo)
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    now = datetime.now(timezone.utc)
    d = fetch()  # raises on any failure, before anything is written
    fonts = {f: open(f"fonts/{f}.woff2", "rb").read() for _, _, f in FONTS}
    photo = open("photo.jpg", "rb").read() if os.path.exists("photo.jpg") else None
    readme = replace_between(open("README.md", encoding="utf-8").read(), activity(d, now))
    for name in THEMES:
        with open(f"card-{name}.svg", "w", encoding="utf-8", newline="\n") as f:
            f.write(card(name, d, fonts, photo))
    with open("README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
