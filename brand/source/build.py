"""Build Vialactea Works' vector originals and PNG exports.

Requires Python 3.11+, fonttools[woff], and rsvg-convert.
Run from any directory: python brand/source/build.py
All production art loads galaxy-master.svg, traced from the approved concept.
"""

from pathlib import Path
import html
import json
import subprocess
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

COLORS = {
    "ink": "#101116", "paper": "#F4F1EB", "violet": "#A89BFF",
    "muted": "#9899A6", "surface": "#1C1D25",
}

# Use the approved silhouette for every export. Hand-approximated curves
# previously pinched the lower arm into a disconnected, hairline tail.
MASTER = ET.parse(ROOT / "source" / "galaxy-master.svg").getroot()
MASTER_PATHS = tuple(path.attrib["d"] for path in MASTER.findall("{http://www.w3.org/2000/svg}path"))
if MASTER.attrib.get("viewBox") != "0 0 1254 1254" or len(MASTER_PATHS) != 3:
    raise ValueError("The master logo must contain its two arms and core on the original 1254px canvas.")


def symbol(color, x=0, y=0, size=1254):
    paths = ''.join(f'<path d="{path}"/>' for path in MASTER_PATHS)
    return (f'<g transform="translate({x} {y}) scale({size / 1254:.8f})" fill="{color}">'
            f'{paths}</g>')


def svg(width, height, content, title, desc=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">'
            f'<title id="title">{html.escape(title)}</title>'
            f'<desc id="desc">{html.escape(desc)}</desc>{content}</svg>\n')


FONTS = {}
for family, weight in [("SpaceGrotesk", 500), ("Inter", 400), ("JetBrainsMono", 400)]:
    font = TTFont(ROOT / "fonts" / f"{family}.ttf")
    font = instantiateVariableFont(font, {"wght": weight}, inplace=False)
    FONTS[family] = font


def lettering(text, x, baseline, size, color, family="SpaceGrotesk", tracking=0):
    """Outline letters so SVG assets render independently of installed fonts."""
    font = FONTS[family]
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    advance = 0
    paths = []
    for ch in text:
        name = cmap.get(ord(ch), ".notdef")
        glyph = glyphs[name]
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        if pen.getCommands():
            paths.append(f'<path transform="translate({x + advance:.3f} {baseline}) scale({scale:.7f} {-scale:.7f})" d="{pen.getCommands()}"/>')
        advance += glyph.width * scale + tracking
    return f'<g fill="{color}">{"".join(paths)}</g>'


def rect(x, y, width, height, fill, rx=0):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{rx}" fill="{fill}"/>'


def save(name, data):
    (ASSETS / name).write_text(data)


def render(name, size=None, output=None):
    source = ASSETS / name
    cmd = ["rsvg-convert", str(source), "-o", str(ASSETS / (output or source.with_suffix(".png").name))]
    if size:
        cmd += ["-w", str(size), "-h", str(size)]
    subprocess.run(cmd, check=True)


ink, paper, violet, muted, surface = (COLORS[k] for k in ("ink", "paper", "violet", "muted", "surface"))
description = "Two tapered spiral arms around an oval core, an abstract Milky Way galaxy."

for label, color in [("light", paper), ("dark", ink), ("violet", violet), ("black", "#000000")]:
    save(f"mark-{label}.svg", svg(1254, 1254, symbol(color), "Vialactea Works galaxy symbol", description))
    render(f"mark-{label}.svg", 1024)

for suffix, bg, fg in [("", ink, paper), ("-light", paper, ink), ("-violet", violet, ink)]:
    name = f"github-avatar{suffix}.svg"
    save(name, svg(512, 512, rect(0, 0, 512, 512, bg) + symbol(fg, size=512), "Vialactea Works", description))
    render(name)
    render(name, 1024, f"github-avatar{suffix}-1024.png")

for label, fg in [("light", paper), ("dark", ink)]:
    content = symbol(fg, -14, -34, 208)
    content += lettering("vialactea", 171, 82, 68, fg, tracking=-1.3)
    content += lettering("WORKS", 175, 116, 15, fg, "JetBrainsMono", tracking=4)
    save(f"lockup-{label}.svg", svg(510, 148, content, "Vialactea Works", "Primary horizontal wordmark with galaxy symbol. Lettering is outlined."))
    render(f"lockup-{label}.svg")

header = rect(0, 0, 1280, 400, ink)
header += symbol(paper, 834, -37, 468)
header += lettering("VIALACTEA WORKS", 68, 64, 13, violet, "JetBrainsMono", tracking=2.1)
header += lettering("A constellation", 64, 183, 65, paper, tracking=-1.8)
header += lettering("of software tools.", 64, 255, 65, paper, tracking=-1.8)
header += lettering("Knowledge. Engineering. Navigation. Automation.", 68, 343, 17, muted, "Inter")
save("github-header.svg", svg(1280, 400, header, "Vialactea Works — A constellation of software tools", "Knowledge. Engineering. Navigation. Automation."))
render("github-header.svg")

social = rect(0, 0, 1280, 640, ink)
social += lettering("VIALACTEA WORKS", 72, 88, 16, violet, "JetBrainsMono", tracking=2.6)
social += symbol(paper, 717, 80, 600)
social += lettering("A constellation", 65, 287, 72, paper, tracking=-2.2)
social += lettering("of software tools.", 65, 368, 72, paper, tracking=-2.2)
social += lettering("Knowledge. Engineering.", 72, 468, 21, muted, "Inter")
social += lettering("Navigation. Automation.", 72, 500, 21, muted, "Inter")
social += rect(72, 568, 48, 3, violet)
social += lettering("vialactea-works", 138, 577, 15, paper, "JetBrainsMono")
save("social-card.svg", svg(1280, 640, social, "Vialactea Works", "A constellation of software tools. Organization social preview artwork."))
render("social-card.svg")

# Compact presentation image for the completed identity.
board = rect(0, 0, 1600, 1080, paper)
board += rect(0, 0, 1600, 650, ink)
board += lettering("VIALACTEA WORKS", 70, 78, 15, violet, "JetBrainsMono", tracking=2.5)
board += lettering("Visual identity / 01", 1260, 78, 12, muted, "JetBrainsMono")
board += symbol(paper, 955, 50, 605)
board += lettering("A constellation", 64, 270, 82, paper, tracking=-2.7)
board += lettering("of software tools.", 64, 360, 82, paper, tracking=-2.7)
board += lettering("Precision, curiosity, and room to explore.", 70, 425, 22, muted, "Inter")
board += rect(70, 538, 54, 3, violet)
board += lettering("ONE GALAXY. MANY PROJECTS.", 145, 546, 13, paper, "JetBrainsMono", tracking=1.9)
board += lettering("01 / PALETTE", 70, 718, 12, ink, "JetBrainsMono", tracking=1.5)
for i, (name, color) in enumerate([("Deep Space", ink), ("Starlight", paper), ("Orbit Violet", violet), ("Dust", muted), ("Observatory", surface)]):
    x = 70 + i * 149
    board += rect(x, 751, 129, 83, ink)
    board += rect(x + 1, 752, 127, 81, color)
    board += lettering(name, x, 862, 13, ink, "Inter")
    board += lettering(color.upper(), x, 885, 11, ink, "JetBrainsMono")
board += lettering("02 / TYPOGRAPHY", 895, 718, 12, ink, "JetBrainsMono", tracking=1.5)
board += lettering("Space Grotesk", 890, 785, 46, ink, tracking=-1.1)
board += lettering("Inter for readable interfaces and prose.", 895, 836, 20, ink, "Inter")
board += lettering("JetBrains Mono / 0123456789", 895, 878, 16, ink, "JetBrainsMono")
board += rect(70, 949, 1460, 1, "#D3D0CC")
board += lettering("PRIMARY AVATAR", 70, 1010, 11, ink, "JetBrainsMono", tracking=1.4)
for x, bg, fg in [(263, ink, paper), (351, paper, ink), (439, violet, ink)]:
    board += rect(x, 965, 70, 70, bg, 12) + symbol(fg, x, 965, 70)
board += lettering("Pleiades / Kepler / Polaris / Asimov", 895, 1010, 16, ink, "JetBrainsMono")
save("identity-board.svg", svg(1600, 1080, board, "Vialactea Works visual identity", "Logo, five-color palette, typography, and avatar applications."))
render("identity-board.svg")

# Actual-size optical check: square and circular avatar crops.
checks = rect(0, 0, 1000, 520, paper)
checks += lettering("Avatar size checks", 36, 48, 26, ink)
checks += lettering("24 / 32 px stress tests; 48 px and above recommended", 36, 81, 14, ink, "Inter")
for index, size in enumerate([24, 32, 48, 64, 96, 160]):
    x = 36 + index * 149
    checks += lettering(str(size) + " px", x, 126, 12, ink, "JetBrainsMono")
    checks += rect(x, 145, size, size, ink)
    checks += symbol(paper, x, 145, size)
    checks += f'<defs><clipPath id="round-{size}"><circle cx="{x + size / 2}" cy="{333 + size / 2}" r="{size / 2}"/></clipPath></defs>'
    checks += f'<g clip-path="url(#round-{size})">' + rect(x, 333, size, size, ink) + symbol(paper, x, 333, size) + '</g>'
save("size-checks.svg", svg(1000, 520, checks, "Vialactea Works avatar size checks", "Square and round crops from 24 to 160 pixels."))
render("size-checks.svg")

for family in FONTS:
    font = TTFont(ROOT / "fonts" / f"{family}.ttf")
    font.flavor = "woff2"
    font.save(ROOT / "fonts" / f"{family}.woff2")

(ROOT / "tokens.json").write_text(json.dumps({
    "name": "Vialactea Works", "version": "1.0", "colors": COLORS,
    "type": {"display": "Space Grotesk", "body": "Inter", "code": "JetBrains Mono"},
    "spacing": [4, 8, 12, 16, 24, 32, 48, 64, 96],
    "logo": {"clearspace": "One eighth of visible symbol width", "avatarFill": "Approximately 68% of canvas width", "minimumAvatarPx": 48},
}, indent=2) + "\n")
print(f"Built {len(list(ASSETS.iterdir()))} production assets in {ASSETS}")
