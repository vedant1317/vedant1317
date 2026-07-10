#!/usr/bin/env python3
"""Generate the profile's self-hosted SVG assets (banner, stats card, footer).

Stdlib-only so it runs in GitHub Actions. The GitHub stats card is redrawn
from live data (with stats.json as a fallback when the API is unavailable),
so it never depends on the flaky public github-readme-stats service.
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

# ---- palette (GitHub-dark friendly, vibrant) ----
BG0, BG1 = "#0d1117", "#161b22"
PANEL = "#161b22"
STROKE = "#2b3140"
TEXT = "#e6edf3"
MUTED = "#8b949e"
PURPLE, CYAN, PINK, GREEN, ORANGE = "#a371f7", "#39d0d8", "#f778ba", "#3fb950", "#f0883e"

LANG_COLORS = {
    "JavaScript": "#f1e05a", "Python": "#3776ab", "TypeScript": "#3178c6",
    "CSS": "#563d7c", "HTML": "#e34c26", "PowerShell": "#4a7ebb",
    "Java": "#b07219", "C++": "#f34b7d", "C": "#555555", "Shell": "#89e051",
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


# ============================ BANNER ============================
def build_banner():
    W, H = 1200, 300
    code = [
        [("#8b949e", "const "), ("#79c0ff", "vedant"), ("#8b949e", " = {")],
        [("#8b949e", "  role: "), ("#a5d6ff", '"Backend + Cloud Developer"'), ("#8b949e", ",")],
        [("#8b949e", "  focus: ["), ("#a5d6ff", '"agentic AI"'), ("#8b949e", ", "),
         ("#a5d6ff", '"AWS security"'), ("#8b949e", "],")],
        [("#8b949e", "  currently: "), ("#a5d6ff", '"shipping"'), ("#8b949e", " "), ("#e6edf3", "🚀")],
        [("#8b949e", "}")],
    ]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="\'Segoe UI\',Ubuntu,sans-serif">']
    s.append(f'''<defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#161b22"/></linearGradient>
      <linearGradient id="name" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#a371f7"/><stop offset="0.55" stop-color="#39d0d8"/>
        <stop offset="1" stop-color="#f778ba"/></linearGradient>
      <radialGradient id="g1" cx="0.12" cy="0.15" r="0.5">
        <stop offset="0" stop-color="#a371f7" stop-opacity="0.28"/>
        <stop offset="1" stop-color="#a371f7" stop-opacity="0"/></radialGradient>
      <radialGradient id="g2" cx="0.9" cy="0.9" r="0.55">
        <stop offset="0" stop-color="#39d0d8" stop-opacity="0.22"/>
        <stop offset="1" stop-color="#39d0d8" stop-opacity="0"/></radialGradient>
      <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
        <circle cx="1.5" cy="1.5" r="1.1" fill="#ffffff" opacity="0.05"/></pattern>
    </defs>''')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#bg)"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#dots)"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#g1)"/>')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#g2)"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="#2b3140"/>')
    # left: name + tagline
    s.append(f'<text x="64" y="120" font-size="60" font-weight="800" fill="url(#name)" '
             f'letter-spacing="1">VEDANT WALUNJ</text>')
    s.append(f'<text x="66" y="164" font-size="21" fill="#8b949e" font-family="monospace">'
             f'// backend · cloud security · agentic AI</text>')
    s.append(f'<g font-size="15">'
             f'<rect x="66" y="196" width="150" height="30" rx="15" fill="#a371f71f" stroke="#a371f7"/>'
             f'<text x="141" y="216" fill="#c9a6ff" text-anchor="middle">📍 Mumbai, India</text>'
             f'<rect x="228" y="196" width="215" height="30" rx="15" fill="#39d0d81f" stroke="#39d0d8"/>'
             f'<text x="335" y="216" fill="#8ee7ec" text-anchor="middle">🎓 IT Engineer · Honors in AI</text>'
             f'</g>')
    # right: code card
    cx, cy = 726, 70
    s.append(f'<rect x="{cx}" y="{cy}" width="410" height="168" rx="12" fill="#0d1117cc" stroke="#2b3140"/>')
    for i, col in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        s.append(f'<circle cx="{cx+20+i*20}" cy="{cy+20}" r="6" fill="{col}"/>')
    s.append(f'<text x="{cx+200}" y="{cy+24}" font-size="12" fill="#484f58" text-anchor="middle" '
             f'font-family="monospace">vedant.js</text>')
    ty = cy + 58
    for line in code:
        tx = cx + 22
        spans = "".join(f'<tspan fill="{c}">{esc(t)}</tspan>' for c, t in line)
        s.append(f'<text x="{tx}" y="{ty}" font-size="15" font-family="monospace" '
                 f'xml:space="preserve">{spans}</text>')
        ty += 24
    s.append("</svg>")
    (ASSETS / "banner.svg").write_text("\n".join(s))
    print("wrote assets/banner.svg")


# ========================= STATS CARD =========================
def build_stats_card(st):
    W, H = 860, 250
    PW = 400  # left panel width
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="\'Segoe UI\',Ubuntu,sans-serif">']
    s.append('''<defs>
      <linearGradient id="pg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#161b22"/><stop offset="1" stop-color="#12151c"/></linearGradient>
      <linearGradient id="acc" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#a371f7"/><stop offset="1" stop-color="#39d0d8"/></linearGradient>
    </defs>''')
    # two panels
    s.append(f'<rect x="0" y="0" width="{PW}" height="{H}" rx="14" fill="url(#pg)" stroke="#2b3140"/>')
    s.append(f'<rect x="{W-PW}" y="0" width="{PW}" height="{H}" rx="14" fill="url(#pg)" stroke="#2b3140"/>')
    # -- left: stats --
    s.append(f'<text x="28" y="42" font-size="19" font-weight="700" fill="#e6edf3">'
             f'📊 GitHub Stats</text>')
    s.append(f'<rect x="28" y="54" width="80" height="3" rx="2" fill="url(#acc)"/>')
    rows = [
        (PURPLE, "📦", "Public Repos", st.get("repos", 9)),
        (CYAN, "💾", "Total Commits", st.get("commits", 38)),
        (PINK, "👥", "Followers", st.get("followers", 5)),
        (GREEN, "🐛", "Issues Opened", st.get("issues", 2)),
        (ORANGE, "🔤", "Languages Used", st.get("lang_count", 6)),
    ]
    y = 88
    for col, ic, label, val in rows:
        s.append(f'<text x="30" y="{y}" font-size="15">{ic}</text>')
        s.append(f'<text x="58" y="{y}" font-size="15" fill="#c9d1d9">{esc(label)}</text>')
        s.append(f'<text x="{PW-28}" y="{y}" font-size="16" font-weight="700" fill="{col}" '
                 f'text-anchor="end">{esc(val)}</text>')
        y += 31
    # -- right: languages --
    rx0 = W - PW + 28
    s.append(f'<text x="{rx0}" y="42" font-size="19" font-weight="700" fill="#e6edf3">'
             f'🧬 Most Used Languages</text>')
    s.append(f'<rect x="{rx0}" y="54" width="80" height="3" rx="2" fill="url(#acc)"/>')
    langs = st.get("langs") or [["JavaScript", 38.7], ["Python", 28.6],
                                ["TypeScript", 19.2], ["CSS", 8.5], ["HTML", 4.6]]
    barw = PW - 56
    y = 84
    for name, pct in langs:
        col = LANG_COLORS.get(name, "#8b949e")
        s.append(f'<text x="{rx0}" y="{y}" font-size="13.5" fill="#c9d1d9">{esc(name)}</text>')
        s.append(f'<text x="{rx0+barw}" y="{y}" font-size="13" fill="#8b949e" '
                 f'text-anchor="end">{pct}%</text>')
        s.append(f'<rect x="{rx0}" y="{y+7}" width="{barw}" height="8" rx="4" fill="#21262d"/>')
        s.append(f'<rect x="{rx0}" y="{y+7}" width="{max(6, barw*pct/100):.1f}" height="8" '
                 f'rx="4" fill="{col}"/>')
        y += 32
    s.append("</svg>")
    (ASSETS / "github-stats.svg").write_text("\n".join(s))
    print("wrote assets/github-stats.svg")


# =========================== FOOTER ===========================
def build_footer():
    W, H = 1200, 180
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'font-family="\'Segoe UI\',Ubuntu,sans-serif">']
    s.append('''<defs>
      <linearGradient id="fbg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#161b22"/></linearGradient>
      <linearGradient id="wave" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#a371f7"/><stop offset="0.5" stop-color="#39d0d8"/>
        <stop offset="1" stop-color="#f778ba"/></linearGradient>
    </defs>''')
    s.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#fbg)"/>')
    s.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="none" stroke="#2b3140"/>')
    # skyline silhouette
    bars = "".join(
        f'<rect x="{60+i*58}" y="{H-30-h}" width="34" height="{h}" rx="3" fill="#39d0d8" opacity="0.10"/>'
        for i, h in enumerate([40, 70, 55, 95, 60, 110, 48, 80, 65, 100, 52, 88, 44, 76, 58, 96, 50, 84, 62]))
    s.append(bars)
    s.append(f'<text x="{W/2}" y="72" font-size="30" font-weight="800" fill="url(#wave)" '
             f'text-anchor="middle">⚡ Thanks for stopping by!</text>')
    s.append(f'<text x="{W/2}" y="108" font-size="18" fill="#8b949e" text-anchor="middle" '
             f'font-family="monospace">// let\'s build something that matters</text>')
    s.append("</svg>")
    (ASSETS / "footer.svg").write_text("\n".join(s))
    print("wrote assets/footer.svg")


if __name__ == "__main__":
    st = gather_stats()
    build_banner()
    build_stats_card(st)
    build_footer()
    print("stats:", st)
