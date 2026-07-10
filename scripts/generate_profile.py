#!/usr/bin/env python3
"""Regenerate profile-dark.svg / profile-light.svg.

Stdlib-only so it runs in GitHub Actions with no dependencies:
  * Uptime  -> computed from DOB (Asia/Kolkata)
  * GitHub  -> repos/followers/commits via the REST API
  * LeetCode-> solved counts via the public GraphQL endpoint
Falls back to the last known values in stats.json when an API is down.
ASCII art comes from ascii_art.txt (generated locally by ascii_from_photo.py
so the source photo never needs to be committed).
"""
import html
import json
import os
import urllib.request
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DOB = date(2005, 5, 10)
GH_USER = "vedant1317"
LC_USER = "vedantvw"

# ---------------- uptime ----------------
def add_months(d: date, n: int) -> date:
    y, m = d.year + (d.month - 1 + n) // 12, (d.month - 1 + n) % 12 + 1
    return date(y, m, d.day)  # DOB day (10) exists in every month

today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
total_months = (today.year - DOB.year) * 12 + today.month - DOB.month - (today.day < DOB.day)
years, months = divmod(total_months, 12)
days = (today - add_months(DOB, total_months)).days
uptime = f"{years} years, {months} months, {days} days"

# ---------------- live stats (with fallback) ----------------
stats_file = ROOT / "stats.json"
stats = json.loads(stats_file.read_text()) if stats_file.exists() else {
    "repos": 9, "followers": 4, "commits": 33,
    "lc_total": 51, "lc_easy": 30, "lc_medium": 21,
}

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

def fetch(url, data=None, headers=None):
    h = {"User-Agent": UA}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())

token = os.environ.get("GITHUB_TOKEN", "")
gh_headers = {"Authorization": f"Bearer {token}"} if token else {}
try:
    u = fetch(f"https://api.github.com/users/{GH_USER}", headers=gh_headers)
    stats["repos"], stats["followers"] = u["public_repos"], u["followers"]
    c = fetch(f"https://api.github.com/search/commits?q=author:{GH_USER}", headers=gh_headers)
    stats["commits"] = c["total_count"]
except Exception as e:  # noqa: BLE001 - keep last known values
    print("github fetch failed:", e)

try:
    q = json.dumps({
        "query": "query($u:String!){matchedUser(username:$u){submitStatsGlobal{acSubmissionNum{difficulty count}}}}",
        "variables": {"u": LC_USER},
    }).encode()
    lc = fetch("https://leetcode.com/graphql", data=q,
               headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"})
    nums = {d["difficulty"]: d["count"]
            for d in lc["data"]["matchedUser"]["submitStatsGlobal"]["acSubmissionNum"]}
    stats.update(lc_total=nums["All"], lc_easy=nums["Easy"], lc_medium=nums["Medium"])
except Exception as e:  # noqa: BLE001
    print("leetcode fetch failed:", e)

stats_file.write_text(json.dumps(stats, indent=2) + "\n")

# ---------------- layout ----------------
art_lines = (ROOT / "ascii_art.txt").read_text().splitlines()
COLS = max(len(l) for l in art_lines)
ROWS = len(art_lines)
W = 56

def kv(key, val, key2=None, val2=None):
    tail = (3 + len(key2) + 2 + len(val2)) if key2 else 0
    dots = W - len(key) - len(val) - 6 - tail
    spans = [("k", f" {key}:"), ("d", " " + "." * max(dots, 2) + " "), ("v", val)]
    if key2:
        spans += [("d", " | "), ("k", f"{key2}:"), ("v", f" {val2}")]
    return spans

def rule(label=""):
    if label:
        return [("h", f"─ {label} "), ("d", "─" * (W - len(label) - 4))]
    return [("d", "─" * W)]

def blank():
    return [("d", "")]

INFO = [
    [("t", "vedant@walunj "), ("d", "─" * (W - 14))],
    kv("OS", "macOS, Windows 11"),
    kv("Uptime", uptime),
    kv("Host", "KJ Somaiya College of Engineering"),
    kv("Kernel", "B.Tech IT, Honors in AI"),
    kv("Shell", "zsh + VS Code"),
    blank(),
    kv("Languages.Programming", "Python, TypeScript, C++, Java"),
    kv("Languages.Computer", "HTML, CSS, JSON, LaTeX, YAML"),
    kv("Languages.Real", "English, Marathi, Hindi, German"),
    blank(),
    kv("Hobbies.Software", "Agentic AI, LeetCode, Benchmarking"),
    kv("Hobbies.Offline", "Film logging, Playlist curation"),
    blank(),
    rule("Contact"),
    kv("Email", "vedantwalunj1317@gmail.com"),
    kv("LinkedIn", "vedantwalunj"),
    kv("Portfolio", "vedant-walunj-portfolio.vercel.app"),
    kv("LeetCode", LC_USER),
    blank(),
    rule("GitHub Stats"),
    kv("Repos", str(stats["repos"]), "Followers", str(stats["followers"])),
    kv("Commits", str(stats["commits"]), "Stack", "Py/TS/JS"),
    kv("LeetCode.Solved",
       f"{stats['lc_total']} ({stats['lc_easy']} Easy, {stats['lc_medium']} Medium)"),
]

THEMES = {
    "dark": dict(bg="#0d1117", art="#8b949e", t="#e6edf3", k="#ffa657",
                 v="#79c0ff", d="#484f58", h="#e6edf3"),
    "light": dict(bg="#ffffff", art="#57606a", t="#1f2328", k="#953800",
                  v="#0969da", d="#8c959f", h="#1f2328"),
}

INFO_FS, INFO_LH = 15.5, 24.0
PAD = 34
# scale art font so the art block stays ~<= info block height and ~<= 470px wide
ART_LH = min(13.6, (len(INFO) * INFO_LH) / ROWS, 470 / (COLS * 0.63))
ART_FS = ART_LH * 0.955
ART_CW = ART_FS * 0.6
ART_W = COLS * ART_CW + 24
SVG_W = 1060
SVG_H = int(max(ROWS * ART_LH, len(INFO) * INFO_LH) + PAD * 2)

FONT = "&apos;SF Mono&apos;,&apos;Fira Code&apos;,&apos;Cascadia Code&apos;,Consolas,Menlo,monospace"

for theme, C in THEMES.items():
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" font-family="{FONT}">',
        f'<rect width="{SVG_W}" height="{SVG_H}" rx="10" fill="{C["bg"]}"/>',
    ]
    art_y0 = PAD + (SVG_H - 2 * PAD - ROWS * ART_LH) / 2 + ART_FS
    out.append(f'<g font-size="{ART_FS}" fill="{C["art"]}">')
    for i, line in enumerate(art_lines):
        if line:
            out.append(f'<text x="{PAD}" y="{art_y0 + i * ART_LH:.1f}" '
                       f'xml:space="preserve">{html.escape(line)}</text>')
    out.append("</g>")
    info_x = PAD + ART_W
    info_y0 = PAD + (SVG_H - 2 * PAD - len(INFO) * INFO_LH) / 2 + INFO_FS
    out.append(f'<g font-size="{INFO_FS}">')
    for i, spans in enumerate(INFO):
        parts = []
        for cls, txt in spans:
            if not txt:
                continue
            bold = ' font-weight="bold"' if cls in ("t", "h") else ""
            parts.append(f'<tspan fill="{C[cls]}"{bold}>{html.escape(txt)}</tspan>')
        if parts:
            out.append(f'<text x="{info_x}" y="{info_y0 + i * INFO_LH:.1f}" '
                       f'xml:space="preserve">{"".join(parts)}</text>')
    out.append("</g></svg>")
    (ROOT / f"profile-{theme}.svg").write_text("\n".join(out))
    print(f"wrote profile-{theme}.svg")

print("uptime:", uptime, "| stats:", stats)
