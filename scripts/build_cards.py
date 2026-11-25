"""Erzeugt eigene Stats- und Sprachen-Karten als SVG (hell + dunkel).

Läuft täglich per GitHub Action (.github/workflows/profile.yml).
Lokal testen:  GITHUB_TOKEN=... GH_USER=deinname python scripts/build_cards.py
Ohne Token:    python scripts/build_cards.py --demo   (Beispieldaten)
"""
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "generated"

THEMES = {
    "dark": dict(bg="#0D1320", border="#25304A", text="#EEF2F8", muted="#8B97AD", accent="#FFB547", bar="#18223A"),
    "light": dict(bg="#FFFFFF", border="#D8DEE8", text="#1B2233", muted="#5B6678", accent="#C27A00", bar="#EEF1F6"),
}
FONT = "'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif"
MONO = "ui-monospace,'SF Mono',Menlo,Consolas,monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar { totalContributions }
    }
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
"""

EXCLUDE_LANGS = {"Jupyter Notebook"}  # hier Sprachen ausblenden, die die Statistik verzerren


def fetch(user: str, token: str) -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GitHub API Fehler: {data['errors']}")
    return data["data"]["user"]


def summarize(u: dict) -> dict:
    cc = u["contributionsCollection"]
    langs: dict[str, list] = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            if n in EXCLUDE_LANGS:
                continue
            langs.setdefault(n, [0, e["node"]["color"] or "#8B97AD"])[0] += e["size"]
    return {
        "contributions": cc["contributionCalendar"]["totalContributions"],
        "commits": cc["totalCommitContributions"],
        "prs": cc["totalPullRequestContributions"],
        "issues": cc["totalIssueContributions"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "langs": sorted(langs.items(), key=lambda kv: -kv[1][0])[:6],
    }


def demo() -> dict:
    return {
        "contributions": 214, "commits": 168, "prs": 9, "issues": 4, "repos": 7, "stars": 3,
        "langs": [("Python", [52000, "#3572A5"]), ("C", [31000, "#555555"]), ("HTML", [18000, "#e34c26"]),
                  ("CSS", [9000, "#663399"]), ("PHP", [4000, "#4F5D95"]), ("CMake", [1500, "#DA3434"])],
    }


def card(t: dict, title: str, body: str, h: int) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{h}" viewBox="0 0 420 {h}" role="img" aria-label="{title}">
<style>.f{{font-family:{FONT}}}.m{{font-family:{MONO}}}
.r{{animation:in .6s ease-out both}}@keyframes in{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<rect x=".5" y=".5" width="419" height="{h - 1}" rx="14" fill="{t['bg']}" stroke="{t['border']}"/>
<rect x="24" y="26" width="4" height="18" rx="2" fill="{t['accent']}"/>
<text x="38" y="41" class="f" font-size="17" font-weight="700" fill="{t['text']}">{title}</text>
{body}
</svg>"""


def stats_svg(s: dict, t: dict) -> str:
    rows = [
        ("Contributions (last year)", s["contributions"]),
        ("Commits", s["commits"]),
        ("Pull Requests", s["prs"]),
        ("Issues", s["issues"]),
        ("Public Repos", s["repos"]),
        ("Stars", s["stars"]),
    ]
    body = []
    for i, (label, val) in enumerate(rows):
        y = 82 + i * 28
        body.append(
            f'<g class="r" style="animation-delay:{i * .08:.2f}s">'
            f'<text x="24" y="{y}" class="f" font-size="14" fill="{t["muted"]}">{label}</text>'
            f'<text x="396" y="{y}" class="m" font-size="15" font-weight="700" fill="{t["text"]}" text-anchor="end">{val}</text>'
            f'<path d="M24 {y + 9}H396" stroke="{t["bar"]}"/></g>'
        )
    stamp = datetime.now(timezone.utc).strftime("%b %d, %Y")
    body.append(f'<text x="24" y="262" class="m" font-size="11" fill="{t["muted"]}">updated {stamp}</text>')
    return card(t, "GitHub Stats", "\n".join(body), 280)


def langs_svg(s: dict, t: dict) -> str:
    total = sum(v[0] for _, v in s["langs"]) or 1
    body, x = [], 24.0
    width = 372
    body.append(f'<clipPath id="bar"><rect x="24" y="64" width="{width}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
    for name, (size, color) in s["langs"]:
        w = size / total * width
        body.append(f'<rect x="{x:.1f}" y="64" width="{w + .5:.1f}" height="10" fill="{color}"/>')
        x += w
    body.append("</g>")
    for i, (name, (size, color)) in enumerate(s["langs"]):
        col, row = i % 2, i // 2
        cx, cy = 24 + col * 190, 108 + row * 30
        body.append(
            f'<g class="r" style="animation-delay:{i * .08:.2f}s"><circle cx="{cx + 5}" cy="{cy - 5}" r="5" fill="{color}"/>'
            f'<text x="{cx + 18}" y="{cy}" class="f" font-size="14" fill="{t["text"]}">{escape(name)}</text>'
            f'<text x="{cx + 172}" y="{cy}" class="m" font-size="13" fill="{t["muted"]}" text-anchor="end">{size / total * 100:.1f}%</text></g>'
        )
    rows = (len(s["langs"]) + 1) // 2
    h = max(280, 108 + rows * 30 + 34)
    body.append(f'<text x="24" y="{h - 18}" class="m" font-size="11" fill="{t["muted"]}">by code size · own public repos</text>')
    return card(t, "Top Languages", "\n".join(body), h)


def main() -> None:
    if "--demo" in sys.argv:
        s = demo()
    else:
        user = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER")
        token = os.environ.get("GITHUB_TOKEN")
        if not (user and token):
            raise SystemExit("GH_USER und GITHUB_TOKEN setzen – oder --demo verwenden.")
        s = summarize(fetch(user, token))
    OUT.mkdir(parents=True, exist_ok=True)
    for mode, t in THEMES.items():
        (OUT / f"stats-{mode}.svg").write_text(stats_svg(s, t), encoding="utf-8")
        (OUT / f"langs-{mode}.svg").write_text(langs_svg(s, t), encoding="utf-8")
    print("Karten geschrieben nach", OUT)


if __name__ == "__main__":
    main()
