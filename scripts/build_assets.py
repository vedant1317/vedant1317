#!/usr/bin/env python3
"""Generate the profile's self-hosted SVG assets (banner, stats card, footer).

Stdlib-only so it runs in GitHub Actions. The GitHub stats card is redrawn
from live data (with stats.json as a fallback when the API is unavailable),
so it never depends on the flaky public github-readme-stats service.

Design: monochrome dark, a single restrained accent, editorial typography.
No decorative gradients — language colors are the only chromatic element,
because there they carry meaning.
"""
import html
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
GH_USER = "vedant1317"

# ---- palette: one accent, everything else neutral ----
BG = "#0d1117"       # matches GitHub dark so cards sit flush
CODE_BG = "#010409"
BORDER = "#26303d"
HAIR = "#1b232f"     # faint divider / leader
TEXT = "#e6edf3"
SUBTLE = "#adbac7"
MUTED = "#7d8590"
FAINT = "#4b5563"
ACCENT = "#4c9aff"   # single accent — swap this one value to re-theme
STRING = "#a5d6ff"   # soft blue for code strings (same family as accent)

SANS = "-apple-system,'Segoe UI',Roboto,Ubuntu,sans-serif"
MONO = "'SF Mono','JetBrains Mono','Cascadia Code',Consolas,monospace"

LANG_COLORS = {
    "JavaScript": "#f1e05a", "Python": "#3776ab", "TypeScript": "#3178c6",
    "CSS": "#563d7c", "HTML": "#e34c26", "PowerShell": "#4a7ebb",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#a8b9c0", "Shell": "#89e051",
}

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def fetch(url, headers=None):
    h = dict(UA)
    h.update(headers or {})
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def gather_stats():
    stats_file = ROOT / "stats.json"
    stats = json.loads(stats_file.read_text()) if stats_file.exists() else {}
    token = os.environ.get("GITHUB_TOKEN", "")
    gh = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        u = fetch(f"https://api.github.com/users/{GH_USER}", gh)
        stats["repos"], stats["followers"] = u["public_repos"], u["followers"]
        repos = fetch(f"https://api.github.com/users/{GH_USER}/repos?per_page=100", gh)
        stats["stars"] = sum(r["stargazers_count"] for r in repos)
        lb = {}
        for r in repos:
            if r["fork"]:
                continue
            for k, v in fetch(r["languages_url"], gh).items():
                lb[k] = lb.get(k, 0) + v
        tot = sum(lb.values()) or 1
        stats["langs"] = [[k, round(v * 100 / tot, 1)]
                          for k, v in sorted(lb.items(), key=lambda x: -x[1])[:5]]
        stats["lang_count"] = len(lb)
        c = fetch(f"https://api.github.com/search/commits?q=author:{GH_USER}", gh)
        stats["commits"] = c["total_count"]
        iss = fetch(f"https://api.github.com/search/issues?q=type:issue+author:{GH_USER}", gh)
        stats["issues"] = iss["total_count"]
    except Exception as e:  # noqa: BLE001 keep last-known values
        print("stats fetch failed, using fallback:", e)
    stats_file.write_text(json.dumps(stats, indent=2) + "\n")
    return stats


def esc(s):
    return html.escape(str(s))


def frame(w, h, rx=14):
    """Card background + subtle top highlight + hairline border."""
    return (
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="{BG}"/>'
        f'<rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="{rx-0.5}" '
        f'fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect x="{rx}" y="1.25" width="{w-2*rx}" height="1" fill="#ffffff" opacity="0.05"/>'
    )


def dot_pattern():
    return (f'<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="1" cy="1" r="1" fill="#ffffff" opacity="0.028"/></pattern>')


def caps(x, y, label, anchor="start"):
    """Small-caps letter-spaced section label with a short accent underline."""
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="12" letter-spacing="2.5" '
            f'fill="{MUTED}" text-anchor="{anchor}">{esc(label.upper())}</text>'
            f'<rect x="{x}" y="{y+9}" width="26" height="2" rx="1" fill="{ACCENT}"/>')


# ============================ BANNER ============================
def build_banner():
    W, H = 1200, 290
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{SANS}">',
         f'<defs>{dot_pattern()}</defs>',
         frame(W, H, 16),
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#dots)"/>']

    # name block with accent rule
    nx = 76
    s.append(f'<rect x="{nx}" y="70" width="4" height="96" rx="2" fill="{ACCENT}"/>')
    s.append(f'<text x="{nx+24}" y="122" font-size="54" font-weight="800" fill="{TEXT}" '
             f'letter-spacing="-0.5">VEDANT WALUNJ</text>')
    s.append(f'<text x="{nx+26}" y="154" font-family="{MONO}" font-size="18" fill="{MUTED}">'
             f'Backend Engineer &#183; Cloud Security &#183; Agentic AI</text>')
    # meta line with accent middots
    meta = ["MUMBAI, INDIA", "IT · HONORS IN AI", "@VEDANT1317"]
    mx = nx + 26
    s.append(f'<g font-family="{MONO}" font-size="11.5" letter-spacing="1.5">')
    for i, part in enumerate(meta):
        if i:
            s.append(f'<text x="{mx}" y="196" fill="{ACCENT}">&#9679;</text>')
            mx += 22
        s.append(f'<text x="{mx}" y="196" fill="{MUTED}">{esc(part)}</text>')
        mx += len(part) * 8.1 + 10
    s.append('</g>')

    # terminal card
    cx, cy, cw, ch = 724, 58, 404, 174
    s.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="10" fill="{CODE_BG}" '
             f'stroke="{BORDER}"/>')
    s.append(f'<rect x="{cx}" y="{cy}" width="{cw}" height="34" rx="10" fill="#0d131c"/>')
    s.append(f'<rect x="{cx}" y="{cy+24}" width="{cw}" height="10" fill="#0d131c"/>')
    for i in range(3):
        s.append(f'<circle cx="{cx+20+i*18}" cy="{cy+17}" r="5" fill="#2b333d"/>')
    s.append(f'<text x="{cx+cw-18}" y="{cy+21}" font-family="{MONO}" font-size="11.5" '
             f'fill="{FAINT}" text-anchor="end">vedant.ts</text>')
    code = [
        [(FAINT, "const"), (SUBTLE, " vedant"), (FAINT, " = {")],
        [(SUBTLE, "  role:   "), (STRING, '"Backend + Cloud Dev"'), (FAINT, ",")],
        [(SUBTLE, "  stack:  "), (FAINT, "["), (STRING, '"Python"'), (FAINT, ", "),
         (STRING, '"TS"'), (FAINT, ", "), (STRING, '"AWS"'), (FAINT, "],")],
        [(SUBTLE, "  focus:  "), (STRING, '"agentic AI · security"'), (FAINT, ",")],
        [(SUBTLE, "  status: "), (STRING, '"always shipping"'), (FAINT, ",")],
        [(FAINT, "}")],
    ]
    ty = cy + 60
    for line in code:
        spans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for c, t in line)
        s.append(f'<text x="{cx+22}" y="{ty}" font-family="{MONO}" font-size="14" '
                 f'xml:space="preserve">{spans}</text>')
        ty += 20
    s.append("</svg>")
    (ASSETS / "banner.svg").write_text("\n".join(s))
    print("wrote assets/banner.svg")


# ========================= STATS CARD =========================
def build_stats_card(st):
    W, H = 860, 236
    PW = 400
    RX = W - PW  # right panel start
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{SANS}">']
    # panels
    for px in (0, RX):
        s.append(f'<g transform="translate({px},0)">{frame(PW, H, 12)}</g>')

    # -- left: stats with dotted leaders --
    s.append(f'<g transform="translate(28,0)">{caps(0, 40, "GitHub / Stats")}</g>')
    rows = [
        ("Public Repos", st.get("repos", 9)),
        ("Total Commits", st.get("commits", 38)),
        ("Followers", st.get("followers", 5)),
        ("Issues Opened", st.get("issues", 2)),
        ("Languages Used", st.get("lang_count", 7)),
    ]
    y = 82
    for label, val in rows:
        s.append(f'<text x="28" y="{y}" font-family="{MONO}" font-size="12.5" letter-spacing="1" '
                 f'fill="{MUTED}">{esc(label.upper())}</text>')
        lx = 28 + len(label) * 8.0 + 12
        s.append(f'<line x1="{lx}" y1="{y-4}" x2="{PW-58}" y2="{y-4}" stroke="{HAIR}" '
                 f'stroke-width="1.4" stroke-dasharray="0.5 5" stroke-linecap="round"/>')
        s.append(f'<text x="{PW-28}" y="{y}" font-size="19" font-weight="700" fill="{TEXT}" '
                 f'text-anchor="end">{esc(val)}</text>')
        y += 29

    # -- right: languages --
    s.append(f'<g transform="translate({RX+28},0)">{caps(0, 40, "Most Used Languages")}</g>')
    langs = st.get("langs") or [["JavaScript", 38.7], ["Python", 28.6],
                                ["TypeScript", 19.2], ["CSS", 8.5], ["HTML", 4.6]]
    barw = PW - 56
    y = 74
    for name, pct in langs:
        col = LANG_COLORS.get(name, MUTED)
        s.append(f'<text x="{RX+28}" y="{y}" font-family="{MONO}" font-size="12.5" '
                 f'fill="{SUBTLE}">{esc(name)}</text>')
        s.append(f'<text x="{RX+28+barw}" y="{y}" font-family="{MONO}" font-size="12" '
                 f'fill="{MUTED}" text-anchor="end">{pct}%</text>')
        s.append(f'<rect x="{RX+28}" y="{y+8}" width="{barw}" height="6" rx="3" fill="#161b22"/>')
        s.append(f'<rect x="{RX+28}" y="{y+8}" width="{max(5, barw*pct/100):.1f}" height="6" '
                 f'rx="3" fill="{col}"/>')
        y += 31
    s.append("</svg>")
    (ASSETS / "github-stats.svg").write_text("\n".join(s))
    print("wrote assets/github-stats.svg")


# =========================== FOOTER ===========================
def build_footer():
    W, H = 1200, 150
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{SANS}">',
         f'<defs>{dot_pattern()}</defs>',
         frame(W, H, 16),
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#dots)"/>']
    cx = W / 2
    # monogram
    s.append(f'<rect x="{cx-22}" y="30" width="44" height="44" rx="10" fill="none" '
             f'stroke="{BORDER}"/>')
    s.append(f'<text x="{cx}" y="60" font-family="{MONO}" font-size="18" font-weight="700" '
             f'fill="{ACCENT}" text-anchor="middle">VW</text>')
    s.append(f'<text x="{cx}" y="105" font-size="17" font-weight="600" fill="{TEXT}" '
             f'text-anchor="middle" letter-spacing="0.3">Thanks for stopping by</text>')
    s.append(f'<text x="{cx}" y="128" font-family="{MONO}" font-size="12.5" fill="{MUTED}" '
             f'text-anchor="middle">// let\'s build something that matters</text>')
    # short accent underline
    s.append(f'<rect x="{cx-16}" y="84" width="32" height="2" rx="1" fill="{ACCENT}"/>')
    s.append("</svg>")
    (ASSETS / "footer.svg").write_text("\n".join(s))
    print("wrote assets/footer.svg")


if __name__ == "__main__":
    st = gather_stats()
    build_banner()
    build_stats_card(st)
    build_footer()
    print("stats:", st)
