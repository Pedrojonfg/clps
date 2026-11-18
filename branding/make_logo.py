#!/usr/bin/env python3
"""Generate the Moonpark logo assets. Run from the repo root: python3 branding/make_logo.py

Mark: a circle (the Moon) crossed by one continuous diagonal stroke with three
crossing strokes, so the three X marks read as a single band with no seams.
"""
from pathlib import Path

OUT = Path(__file__).parent
AMBER = "#F2A100"        # accent, for graphics and on dark backgrounds
AMBER_TEXT = "#9A5E00"   # darker amber for text/links on light backgrounds (>= 4.5:1 on white)
INK = "#14171C"          # logo ink on light backgrounds
PAPER = "#F2F4F7"        # logo ink on dark backgrounds
NIGHT = "#0E1116"        # dark background / app icon tile

A = 8                    # half-size of each X on each axis
SW = 6                   # stroke width
CENTERS = [(34, 66), (50, 50), (66, 34)]   # touching X centres along the diagonal


def marks(color: str) -> str:
    x0, y0 = CENTERS[0]
    x1, y1 = CENTERS[-1]
    # One diagonal from the outer tip of the first X to the outer tip of the last,
    # drawn as a single path so there is no seam between X marks.
    d = f"M{x0 - A} {y0 + A}L{x1 + A} {y1 - A}"
    for cx, cy in CENTERS:
        d += f"M{cx - A} {cy - A}L{cx + A} {cy + A}"
    return f'<path d="{d}" stroke="{color}" stroke-width="{SW}" stroke-linecap="butt" fill="none"/>'


def mark_svg(ring: str, accent: str, size: int | None = None, tile: str | None = None) -> str:
    wh = f' width="{size}" height="{size}"' if size else ""
    body = f'<circle cx="50" cy="50" r="45" fill="none" stroke="{ring}" stroke-width="5"/>{marks(accent)}'
    if tile:  # app icon: rounded tile, mark scaled down to leave padding
        body = (f'<rect width="100" height="100" rx="22" fill="{tile}"/>'
                f'<g transform="translate(9 9) scale(.82)">{body}</g>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"{wh}>{body}</svg>\n'


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text)


write("moonpark-mark.svg", mark_svg(INK, AMBER))                     # on light backgrounds
write("moonpark-mark-dark.svg", mark_svg(PAPER, AMBER))              # on dark backgrounds
write("moonpark-mark-mono.svg", mark_svg("currentColor", "currentColor"))  # single colour
write("moonpark-icon.svg", mark_svg(PAPER, AMBER, tile=NIGHT))       # app icon / favicon

# Social preview 1280x640 (GitHub): mark, wordmark and tagline on the night background.
social = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 640" width="1280" height="640">
<rect width="1280" height="640" fill="{NIGHT}"/>
<g transform="translate(120 195) scale(3)">{mark_svg(PAPER, AMBER).split(">",1)[1].rsplit("</svg>",1)[0]}</g>
<text x="470" y="320" fill="{PAPER}" font-family="Inter, 'Helvetica Neue', Arial, sans-serif" font-size="112" font-weight="600" letter-spacing="-2">Moonpark</text>
<text x="474" y="392" fill="{AMBER}" font-family="Inter, 'Helvetica Neue', Arial, sans-serif" font-size="40" font-weight="500">Park where the Sun is.</text>
<text x="474" y="450" fill="#9AA3AF" font-family="Inter, 'Helvetica Neue', Arial, sans-serif" font-size="30">Landing-site light and Earth-link planner</text>
<text x="474" y="490" fill="#9AA3AF" font-family="Inter, 'Helvetica Neue', Arial, sans-serif" font-size="30">for the lunar south pole</text>
</svg>
'''
write("social-preview.svg", social)
