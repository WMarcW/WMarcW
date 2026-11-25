"""Erzeugt assets/header.svg – das animierte Banner oben im Profil.

Texte und Farben oben anpassen, dann:  python scripts/build_header.py
"""
import random
from xml.sax.saxutils import escape
from pathlib import Path

TITLE = "[Überschrift]"
TAGLINE = "// [Tagline]"
# Zeilen, die nacheinander "getippt" werden (max. ~34 Zeichen, sonst Breite anpassen)
LINES = [
    "[Zeile 1]",
    "[Zeile 2]",
    "[Zeile 3]",
]
SUBLINE = "[Unterzeile]"

BG, GRID, TEXT, MUTED = "#0D1320", "#18223A", "#EEF2F8", "#8B97AD"
AMBER, MINT = "#FFB547", "#4FD1A5"
W, H = 1200, 320
CYCLE = 3.2  # Sekunden pro Zeile

random.seed(7)


def typing_lines() -> str:
    """Tipp-Effekt per SMIL (läuft in <img>-SVGs auf GitHub in allen gängigen Browsern)."""
    total = CYCLE * len(LINES)
    out = []
    for i, line in enumerate(LINES):
        s = i / len(LINES)
        e = (i + 1) / len(LINES)
        t_end = s + (e - s) * 0.45
        h_end = s + (e - s) * 0.85
        width = len(line) * 15.65 + 4  # Monospace 26px ≈ 15,6px pro Zeichen
        times = [0, s, t_end, h_end, e, 1]
        vals = [0, 0, width, width, 0, 0]
        # doppelte keyTimes vermeiden (erste/letzte Zeile)
        pairs = []
        for t, v in zip(times, vals):
            if pairs and abs(pairs[-1][0] - t) < 1e-9:
                pairs[-1] = (t, v)
            else:
                pairs.append((t, v))
        kt = ";".join(f"{t:.4f}" for t, _ in pairs)
        vv = ";".join(f"{v:.0f}" for _, v in pairs)
        out.append(
            f'<clipPath id="c{i}"><rect x="96" y="196" height="40" width="0">'
            f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" keyTimes="{kt}" values="{vv}"/>'
            f"</rect></clipPath>"
            f'<text x="96" y="226" class="mono typed" clip-path="url(#c{i})">{escape(line)}</text>'
        )
    return "", "\n".join(out)


def dot_grid() -> str:
    cols, rows, size, gap = 13, 7, 22, 7
    x0 = W - 70 - cols * (size + gap) + gap
    y0 = (H - rows * (size + gap) + gap) / 2
    cells = []
    for c in range(cols):
        for r in range(rows):
            level = random.choices([0, 1, 2, 3, 4], weights=[30, 25, 20, 15, 10])[0]
            op = [0.08, 0.28, 0.5, 0.75, 1][level]
            fill = MINT if level else TEXT
            delay = (c * 0.12 + r * 0.04)
            cells.append(
                f'<rect x="{x0 + c * (size + gap):.0f}" y="{y0 + r * (size + gap):.0f}" width="{size}" height="{size}" '
                f'rx="5" fill="{fill}" opacity="{op}" class="cell" style="animation-delay:{delay:.2f}s"/>'
            )
    return "\n".join(cells)


def build() -> str:
    type_css, type_svg = typing_lines()
    grid_lines = "".join(
        f'<path d="M{x} 0V{H}" />' for x in range(0, W, 40)
    ) + "".join(f'<path d="M0 {y}H{W}" />' for y in range(0, H, 40))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{escape(TITLE)}">
<style>
.sans{{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif}}
.mono{{font-family:ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace}}
.typed{{font-size:26px;fill:{TEXT}}}
.cell{{animation:pulse 4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
.caret{{animation:blink 1s steps(1) infinite}}
@keyframes blink{{50%{{opacity:0}}}}
.fade{{animation:in .9s ease-out both}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
{type_css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
<linearGradient id="glow" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="{AMBER}" stop-opacity=".18"/><stop offset=".55" stop-color="{BG}" stop-opacity="0"/>
</linearGradient>
</defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<g stroke="{GRID}" stroke-width="1">{grid_lines}</g>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<rect x="44" y="70" width="6" height="170" rx="3" fill="{AMBER}"/>
<text x="96" y="92" class="mono fade" font-size="18" fill="{AMBER}" letter-spacing="1">{escape(TAGLINE)}</text>
<text x="92" y="164" class="sans fade" font-size="68" font-weight="700" fill="{TEXT}" style="animation-delay:.15s">{escape(TITLE)}<tspan fill="{AMBER}">.</tspan></text>
<text x="70" y="226" class="mono" font-size="26" fill="{MINT}" dx="0">&gt;</text>
{type_svg}
<text x="96" y="276" class="mono" font-size="15" fill="{MUTED}">{escape(SUBLINE)}</text>
{dot_grid()}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="#25304A"/>
</svg>
"""


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "header.svg"
    out.write_text(build(), encoding="utf-8")
    print("geschrieben:", out)
