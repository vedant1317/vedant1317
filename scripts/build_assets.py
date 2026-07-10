#!/usr/bin/env python3
"""Generate the profile's self-hosted SVG assets (banner, stats card, footer).

Stdlib-only so it runs in GitHub Actions. The GitHub stats card is redrawn
from live data (with stats.json as a fallback when the API is unavailable),
so it never depends on the flaky public github-readme-stats service.

Theme: Claude Code — warm near-black, Anthropic cream text, and the Claude
coral accent (#D97757), styled like a terminal / CLI session.
"""
import html
import json
import math
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
GH_USER = "vedant1317"

# ---- Claude Code palette: warm dark + coral ----
BG = "#1f1d1a"        # warm near-black card
CODE_BG = "#17150f"   # terminal inner
BORDER = "#3a352d"    # warm hairline border
BORDER_ACC = "#5a4636"  # coral-tinted border
HAIR = "#2b261f"      # faint divider / leader / track
TRACK = "#2b261f"
TEXT = "#ece7dd"      # warm off-white (Anthropic paper on dark)
SUBTLE = "#cabfb0"
MUTED = "#8a8377"
FAINT = "#5c5347"
ACCENT = "#d97757"    # Claude coral — the one accent
STRING = "#cc9b7a"    # warm tan for code strings

SANS = "-apple-system,'Segoe UI',Roboto,Ubuntu,sans-serif"
MONO = "'SF Mono','JetBrains Mono','Cascadia Code',Consolas,monospace"
CW = 0.6  # monospace char-width / font-size ratio

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


def frame(w, h, rx=14, bg=BG, border=BORDER):
    return (
        f'<rect width="{w}" height="{h}" rx="{rx}" fill="{bg}"/>'
        f'<rect x="0.75" y="0.75" width="{w-1.5}" height="{h-1.5}" rx="{rx-0.5}" '
        f'fill="none" stroke="{border}" stroke-width="1"/>'
        f'<rect x="{rx}" y="1.25" width="{w-2*rx}" height="1" fill="#fff" opacity="0.045"/>'
    )


def dot_pattern():
    return ('<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            '<circle cx="1" cy="1" r="1" fill="#fff" opacity="0.03"/></pattern>')


def spark(cx, cy, r, color=ACCENT, w=2.2):
    """The Claude coral spark — an 8-ray asterisk."""
    lines = []
    for ang in (0, 45, 90, 135):
        a = math.radians(ang)
        dx, dy = math.cos(a) * r, math.sin(a) * r
        lines.append(f'<line x1="{cx-dx:.1f}" y1="{cy-dy:.1f}" x2="{cx+dx:.1f}" y2="{cy+dy:.1f}"/>')
    return (f'<g stroke="{color}" stroke-width="{w}" stroke-linecap="round">'
            + "".join(lines) + '</g>')


def caps(x, y, label, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="12" letter-spacing="2.5" '
            f'fill="{MUTED}" text-anchor="{anchor}">{esc(label.upper())}</text>'
            f'<rect x="{x}" y="{y+9}" width="26" height="2" rx="1" fill="{ACCENT}"/>')


# ============================ BANNER ============================
def build_banner(st):
    W, H = 1200, 300
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{SANS}">',
         f'<defs>{dot_pattern()}</defs>',
         frame(W, H, 16),
         f'<rect width="{W}" height="{H}" rx="16" fill="url(#dots)"/>']

    # --- window titlebar ---
    s.append(f'<rect x="1" y="1" width="{W-2}" height="38" rx="16" fill="#191712"/>')
    s.append(f'<rect x="1" y="22" width="{W-2}" height="17" fill="#191712"/>')
    for i, c in enumerate(("#c1613f", "#c99a4e", "#5b7a4a")):
        s.append(f'<circle cx="{24+i*18}" cy="20" r="5" fill="{c}" opacity="0.85"/>')
    s.append(f'<text x="{W/2}" y="24" font-family="{MONO}" font-size="12.5" fill="{FAINT}" '
             f'text-anchor="middle">vedant-walunj — claude-code — zsh</text>')
    s.append(f'<line x1="1" y1="39" x2="{W-1}" y2="39" stroke="{BORDER}"/>')

    # --- left: identity ---
    x0 = 64
    s.append(spark(x0 + 12, 92, 11))
    s.append(f'<text x="{x0+34}" y="98" font-family="{MONO}" font-size="15" fill="{SUBTLE}">'
             f'Welcome to Vedant Walunj’s GitHub</text>')
    s.append(f'<text x="{x0}" y="168" font-size="52" font-weight="800" fill="{TEXT}" '
             f'letter-spacing="-0.5">VEDANT WALUNJ</text>')
    s.append(f'<text x="{x0+2}" y="200" font-family="{MONO}" font-size="17" fill="{MUTED}">'
             f'Backend Engineer &#183; Cloud Security &#183; Agentic AI</text>')
    # slash-command hints (Claude Code style dim hints)
    hy = 244
    s.append(f'<text x="{x0+2}" y="{hy}" font-family="{MONO}" font-size="14" '
             f'xml:space="preserve"><tspan fill="{FAINT}">&gt; </tspan>'
             f'<tspan fill="{ACCENT}">/projects</tspan><tspan fill="{FAINT}">   </tspan>'
             f'<tspan fill="{ACCENT}">/skills</tspan><tspan fill="{FAINT}">   </tspan>'
             f'<tspan fill="{ACCENT}">/contact</tspan>'
             f'<tspan fill="{MUTED}">   · always shipping</tspan></text>')

    # --- right: Claude Code welcome box ---
    bx, by, bw, bh = 748, 68, 388, 176
    s.append(f'<g transform="translate({bx},{by})">{frame(bw, bh, 12, CODE_BG, BORDER_ACC)}</g>')
    s.append(spark(bx + 26, by + 32, 8))
    s.append(f'<text x="{bx+44}" y="{by+37}" font-family="{MONO}" font-size="13.5" '
             f'fill="{TEXT}">Session started</text>')
    s.append(f'<line x1="{bx+22}" y1="{by+52}" x2="{bx+bw-22}" y2="{by+52}" stroke="{HAIR}"/>')
    rows = [
        f'cwd: ~/vedant-walunj',
        f'{st.get("repos", 9)} repos · {st.get("commits", 39)} commits',
        f'IT · Honors in AI · Mumbai',
    ]
    ry = by + 78
    for r in rows:
        s.append(f'<text x="{bx+24}" y="{ry}" font-family="{MONO}" font-size="13" '
                 f'xml:space="preserve"><tspan fill="{ACCENT}">→ </tspan>'
                 f'<tspan fill="{MUTED}">{esc(r)}</tspan></text>')
        ry += 26
    # prompt + cursor
    cur_x = bx + 24 + (len("> ready ")) * 13 * CW
    s.append(f'<text x="{bx+24}" y="{by+bh-20}" font-family="{MONO}" font-size="13" '
             f'xml:space="preserve"><tspan fill="{FAINT}">&gt; </tspan>'
             f'<tspan fill="{SUBTLE}">ready</tspan></text>')
    s.append(f'<rect x="{cur_x:.0f}" y="{by+bh-31}" width="8" height="15" fill="{ACCENT}"/>')
    s.append("</svg>")
    (ASSETS / "banner.svg").write_text("\n".join(s))
    print("wrote assets/banner.svg")


# ========================= STATS CARD =========================
def build_stats_card(st):
    W, H = 860, 236
    PW = 400
    RX = W - PW
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
         f'viewBox="0 0 {W} {H}" font-family="{SANS}">']
    for px in (0, RX):
        s.append(f'<g transform="translate({px},0)">{frame(PW, H, 12)}</g>')

    # left: stats with dotted leaders
    s.append(f'<g transform="translate(28,0)">{caps(0, 40, "GitHub / Stats")}</g>')
    rows = [
        ("Public Repos", st.get("repos", 9)),
        ("Total Commits", st.get("commits", 39)),
        ("Followers", st.get("followers", 5)),
        ("Issues Opened", st.get("issues", 2)),
        ("Languages Used", st.get("lang_count", 6)),
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

    # right: languages
    s.append(f'<g transform="translate({RX+28},0)">{caps(0, 40, "Most Used Languages")}</g>')
    langs = st.get("langs") or [["JavaScript", 38.7], ["Python", 28.7],
                                ["TypeScript", 19.2], ["CSS", 8.5], ["HTML", 4.6]]
    barw = PW - 56
    y = 74
    for name, pct in langs:
        col = LANG_COLORS.get(name, MUTED)
        s.append(f'<text x="{RX+28}" y="{y}" font-family="{MONO}" font-size="12.5" '
                 f'fill="{SUBTLE}">{esc(name)}</text>')
        s.append(f'<text x="{RX+28+barw}" y="{y}" font-family="{MONO}" font-size="12" '
                 f'fill="{MUTED}" text-anchor="end">{pct}%</text>')
        s.append(f'<rect x="{RX+28}" y="{y+8}" width="{barw}" height="6" rx="3" fill="{TRACK}"/>')
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
    # spark mark in a box
    s.append(f'<g transform="translate({cx-22},30)">{frame(44, 44, 10, CODE_BG, BORDER_ACC)}</g>')
    s.append(spark(cx, 52, 11))
    s.append(f'<rect x="{cx-16}" y="86" width="32" height="2" rx="1" fill="{ACCENT}"/>')
    s.append(f'<text x="{cx}" y="108" font-size="17" font-weight="600" fill="{TEXT}" '
             f'text-anchor="middle" letter-spacing="0.3">Thanks for stopping by</text>')
    s.append(f'<text x="{cx}" y="130" font-family="{MONO}" font-size="12.5" fill="{MUTED}" '
             f'text-anchor="middle" xml:space="preserve">'
             f'<tspan fill="{FAINT}">&gt; </tspan>let’s build something that matters</text>')
    s.append("</svg>")
    (ASSETS / "footer.svg").write_text("\n".join(s))
    print("wrote assets/footer.svg")


if __name__ == "__main__":
    st = gather_stats()
    build_banner(st)
    build_stats_card(st)
    build_footer()
    print("stats:", st)
