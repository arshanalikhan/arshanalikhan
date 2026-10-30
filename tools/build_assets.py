"""Build the SVG assets used by the profile README.

    python tools/build_assets.py

Plain SVG only (no web fonts, no scripts), so GitHub renders it as-is.
Edit the data near the top and run again.
"""
import base64
import random
import struct
import textwrap
from pathlib import Path
from xml.dom import minidom
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# Palette from the portfolio site
BG, PANEL = "#0a0a12", "#141425"
CYAN, PURPLE, VIOLET, PINK = "#00f0ff", "#7b00ff", "#9e4dff", "#ff2a6d"
TEXT, MUTED, BODY = "#e6f0ff", "#8b9bb4", "#aebbd3"

SANS = "'Segoe UI', 'Helvetica Neue', Ubuntu, Arial, sans-serif"
MONO = "'JetBrains Mono', 'Cascadia Code', 'SF Mono', Consolas, 'DejaVu Sans Mono', monospace"
MONO_EM = 0.6  # advance of one monospace glyph, in em

TYPED = [
    "AI/ML intern @ IIT Roorkee",
    "building AI for the built environment",
    "wrote a 32-bit OS from bare metal",
    "patent-filed inventor of SafeStruct AI",
    "CSE @ AKTU + Data Science @ IIT Madras",
]

NUMBERS = [
    ("1", "PATENT FILED", "SafeStruct AI", PINK),
    ("24", "PUBLICATIONS", "papers + book chapters", VIOLET),
    ("107", "CLOUD BADGES", "on Google Cloud", CYAN),
    ("2", "DEGREES AT ONCE", "AKTU + IIT Madras", VIOLET),
    ("0", "LIBRARIES", "in my from-scratch OS", PINK),
]

PROJECTS = [
    dict(slug="arshan-os", title="Arshan OS", kicker="SYSTEMS · C + x86 ASM", chip="FROM SCRATCH",
         accent=CYAN, accent2=VIOLET, linked=True,
         desc="A 32-bit graphical OS on bare metal: own bootloader, paging, heap allocator, "
              "preemptive scheduler, syscalls, ELF loader and a draggable window manager.",
         tags=["C", "x86 Assembly", "NASM", "QEMU"]),
    dict(slug="safestruct-ai", title="SafeStruct AI", kicker="COMPUTER VISION + RAG", chip="PATENT FILED",
         accent=PINK, accent2=VIOLET, linked=False,
         desc="Audits concrete structures offline: YOLOv8 segments cracks and measures them in mm, "
              "and semantic search over IS 456:2000 returns PASS/FAIL verdicts.",
         tags=["PyTorch", "YOLOv8", "FAISS", "Flask"]),
    dict(slug="ai-learning-tracker", title="AI Learning Tracker Pro", kicker="EDGE AI · CHROME EXTENSION",
         chip="CHROME WEB STORE", accent=VIOLET, accent2=CYAN, linked=False,
         desc="Finds the technical concepts in your Gemini chats with a fine-tuned DistilBERT that runs "
              "in the browser: ONNX Runtime + WASM, under 100 ms, no server.",
         tags=["PyTorch", "DistilBERT", "ONNX Runtime", "Manifest V3"]),
    dict(slug="collabsphere", title="CollabSphere", kicker="FULL STACK · BUILD-A-THON '26", chip="LIVE",
         accent=CYAN, accent2=PINK, linked=True,
         desc="Meetup engine for IIT Madras BS houses: a map of nearby peers, joint events across houses, "
              "and check-in with a rotating signed QR, geofence and face check.",
         tags=["Next.js 15", "MongoDB", "Leaflet", "MediaPipe"]),
    dict(slug="material-passport", title="Material Passport Extractor", kicker="LLM · DOCUMENT AI",
         chip="AMP-GEN", accent=PINK, accent2=CYAN, linked=True,
         desc="Reads a scanned bill of quantities with Gemini vision models and fills an AMP material "
              "passport: 64 of 64 items extracted, with EPD carbon data.",
         tags=["Python", "Gemini", "Streamlit", "OCR"]),
]

ANIMATION_CSS = (
    ".flow{stroke-dasharray:4 7;animation:flow 1.2s linear infinite}"
    ".pulse{animation:pulse 2.4s ease-in-out infinite}"
    "@keyframes flow{to{stroke-dashoffset:-22}}"
    "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}"
    "@media (prefers-reduced-motion:reduce){.flow,.pulse{animation:none}}"
)


def attr(s):
    return escape(s, {'"': "&quot;"})


def svg(w, h, body, title, css=""):
    style = f"<style>{css}</style>" if css else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{attr(title)}">'
            f"<title>{escape(title)}</title>{style}{body}</svg>\n")


def panel(w, h, accent, rx=14, grid=22, glow=(1, 0)):
    """Dark panel with a faint grid, a corner glow and a thin accent border."""
    return (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#13132b"/>'
            f'<stop offset="1" stop-color="{BG}"/></linearGradient>'
            f'<radialGradient id="glow" cx="{glow[0]}" cy="{glow[1]}" r="0.8"><stop offset="0" stop-color="{accent}" '
            f'stop-opacity="0.2"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>'
            f'<pattern id="grid" width="{grid}" height="{grid}" patternUnits="userSpaceOnUse"><path d="M{grid} 0H0V{grid}" '
            f'fill="none" stroke="{accent}" stroke-opacity="0.06"/></pattern>'
            f'<clipPath id="frame"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath></defs>'
            f'<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="url(#bg)"/>'
            f'<rect width="{w}" height="{h}" fill="url(#grid)"/><rect width="{w}" height="{h}" fill="url(#glow)"/></g>'
            f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{accent}" '
            f'stroke-opacity="0.3"/>')


def mono_text(x, y, s, size, color, per_char, extra=""):
    """Monospace text with a fixed total width, so layout holds whatever font the viewer has."""
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{color}" '
            f'textLength="{len(s) * per_char:.1f}" {extra}>{escape(s)}</text>')


def stack_icon(kind, x, y, c):
    if kind == "DATA":
        nodes = [(8, 21), (21, 9), (21, 33), (34, 21)]
        edges = [(0, 1), (0, 2), (1, 3), (2, 3), (1, 2)]
        lines = "".join(
            f'<line x1="{x + nodes[a][0]}" y1="{y + nodes[a][1]}" x2="{x + nodes[b][0]}" y2="{y + nodes[b][1]}" '
            f'stroke="{c}" stroke-opacity="0.6" stroke-width="1.4"/>' for a, b in edges)
        dots = "".join(
            f'<circle class="pulse" style="animation-delay:{i * 0.6:.1f}s" cx="{x + nx}" cy="{y + ny}" r="3.6" fill="{c}"/>'
            for i, (nx, ny) in enumerate(nodes))
        return lines + dots
    if kind == "CODE":
        return (f'<path d="M{x + 14} {y + 12}L{x + 6} {y + 21}L{x + 14} {y + 30}M{x + 28} {y + 12}L{x + 36} {y + 21}'
                f'L{x + 28} {y + 30}M{x + 24} {y + 10}L{x + 18} {y + 32}" fill="none" stroke="{c}" stroke-width="2.4" '
                f'stroke-linecap="round" stroke-linejoin="round"/>')
    # CIVIL: an I-beam cross-section
    return (f'<path d="M{x + 8} {y + 9}H{x + 34}V{y + 14}H{x + 24}V{y + 28}H{x + 34}V{y + 33}H{x + 8}V{y + 28}'
            f'H{x + 18}V{y + 14}H{x + 8}Z" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="1.6" '
            f'stroke-linejoin="round"/>')


def header():
    w, h = 1000, 330
    body = [
        panel(w, h, CYAN, rx=18, grid=40, glow=(0.1, 0.15)),
        f'<defs><linearGradient id="ink" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset="0.55" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>'
        f'<radialGradient id="glow2" cx="0.9" cy="0.9" r="0.6"><stop offset="0" stop-color="{PURPLE}" stop-opacity="0.25"/>'
        f'<stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="18" fill="url(#glow2)"/>',
        f'<text x="56" y="74" font-family="{MONO}" font-size="17" letter-spacing="1" fill="{CYAN}">&gt; hello, world. I\'m</text>',
        f'<text x="54" y="140" font-family="{SANS}" font-size="60" font-weight="800" fill="url(#ink)" '
        f'textLength="470" lengthAdjust="spacingAndGlyphs">Arshan Ali Khan</text>',
        f'<text x="56" y="190" font-family="{MONO}" font-size="20" fill="{PINK}">$</text>',
    ]
    # Typing effect: each line sits on a path that grows, then shrinks; the lines run in a loop.
    n = len(TYPED)
    for i, line in enumerate(TYPED):
        begin = f"0s;t{n - 1}.end" if i == 0 else f"t{i - 1}.end"
        body.append(
            f'<path id="p{i}" d="m84,190 h0" fill="none"><animate id="t{i}" attributeName="d" begin="{begin}" '
            f'dur="4.5s" fill="remove" values="m84,190 h0;m84,190 h520;m84,190 h520;m84,190 h0" '
            f'keyTimes="0;0.45;0.88;1"/></path>'
            f'<text font-family="{MONO}" font-size="20" fill="{TEXT}"><textPath xlink:href="#p{i}">{escape(line)}'
            f'</textPath></text>')

    def kw(word, color):
        return f'<tspan fill="{color}" font-weight="700">{word}</tspan>'

    body.append(
        f'<text font-family="{SANS}" font-size="16.5" fill="{MUTED}">'
        f'<tspan x="56" y="238">I laid foundations with {kw("Civil", PINK)}, built logic with {kw("Code", CYAN)},</tspan>'
        f'<tspan x="56" y="262">and found insight through {kw("Data", VIOLET)}, from the ground to the cloud.</tspan></text>')
    body.append(
        f'<path d="M62 307C62 307 56 300.5 56 296.5A6 6 0 0 1 68 296.5C68 300.5 62 307 62 307Z" fill="none" '
        f'stroke="{PINK}" stroke-width="1.6"/><circle cx="62" cy="296.5" r="2" fill="{PINK}"/>'
        f'<text x="76" y="302" font-family="{MONO}" font-size="13" fill="{MUTED}">Uttar Pradesh, India</text>')

    # Ground-to-cloud stack on the right
    body.append(
        f'<path class="flow" d="M652 270V66" stroke="{CYAN}" stroke-width="2" fill="none" stroke-linecap="round"/>'
        f'<path d="M646 72L652 63L658 72" fill="none" stroke="{CYAN}" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round"/>')
    tiles = [("DATA", "LLMs · RAG · computer vision", VIOLET, 52),
             ("CODE", "C · Python · JS · the cloud", CYAN, 133),
             ("CIVIL", "structures · materials · codes", PINK, 214)]
    for label, sub, color, y in tiles:
        cy, ix, iy = y + 32, 690, y + 11
        body.append(
            f'<line x1="656" y1="{cy}" x2="676" y2="{cy}" stroke="{color}" stroke-opacity="0.6" stroke-width="1.5"/>'
            f'<circle cx="652" cy="{cy}" r="4.5" fill="{BG}" stroke="{color}" stroke-width="2"/>'
            f'<rect x="676" y="{y}" width="280" height="64" rx="12" fill="{PANEL}" fill-opacity="0.9" '
            f'stroke="{color}" stroke-opacity="0.55"/>'
            f'<rect x="{ix}" y="{iy}" width="42" height="42" rx="10" fill="{color}" fill-opacity="0.1" '
            f'stroke="{color}" stroke-opacity="0.4"/>'
            + stack_icon(label, ix, iy, color)
            + mono_text(746, y + 28, label, 13, color, 10.4, 'font-weight="700"')
            + f'<text x="746" y="{y + 48}" font-family="{SANS}" font-size="13" fill="{MUTED}">{escape(sub)}</text>')

    return svg(w, h, "".join(body), "Arshan Ali Khan: building AI for the built environment", ANIMATION_CSS)


def numbers():
    w, h, gap = 900, 112, 14
    tw = (w - gap * (len(NUMBERS) - 1)) / len(NUMBERS)
    body = [f'<defs><linearGradient id="ink" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/>'
            f'<stop offset="1" stop-color="{VIOLET}"/></linearGradient>'
            f'<linearGradient id="tile" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#13132b"/>'
            f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>']
    for i, (num, label, sub, color) in enumerate(NUMBERS):
        body.append(
            f'<g transform="translate({i * (tw + gap):.1f},0)">'
            f'<rect x="0.5" y="0.5" width="{tw - 1:.1f}" height="{h - 1}" rx="14" fill="url(#tile)" '
            f'stroke="{color}" stroke-opacity="0.35"/>'
            f'<rect x="16" y="0.5" width="36" height="3" rx="1.5" fill="{color}"/>'
            f'<text x="16" y="56" font-family="{SANS}" font-size="40" font-weight="800" fill="url(#ink)">{num}</text>'
            + mono_text(16, 80, label, 11, color, 7.8, 'font-weight="700"')
            + f'<text x="16" y="99" font-family="{SANS}" font-size="12.5" fill="{MUTED}">{escape(sub)}</text></g>')
    title = " · ".join(f"{n} {label.lower()}" for n, label, _, _ in NUMBERS)
    return svg(w, h, "".join(body), title)


def card(p):
    w, h = 440, 200
    a, a2 = p["accent"], p["accent2"]
    lines = textwrap.wrap(p["desc"], 54)
    assert len(lines) <= 3, f"{p['title']}: description needs {len(lines)} lines"

    chip, live = p["chip"], p["chip"] == "LIVE"
    chip_w = len(chip) * 7 + 20 + (12 if live else 0)
    chip_x = w - 22 - chip_w
    body = [
        panel(w, h, a),
        f'<defs><linearGradient id="bar" x1="0" x2="1"><stop offset="0" stop-color="{a}"/>'
        f'<stop offset="1" stop-color="{a2}"/></linearGradient></defs>',
        f'<path d="M14 0H{w - 14}A14 14 0 0 1 {w} 14V0Z" fill="none"/>',
        f'<rect x="22" y="0" width="{w - 44}" height="3" rx="1.5" fill="url(#bar)"/>',
        mono_text(22, 34, p["kicker"], 11, a, 8.2),
        f'<g transform="translate({chip_x},20)"><rect width="{chip_w}" height="20" rx="10" fill="{a}" '
        f'fill-opacity="0.12" stroke="{a}" stroke-opacity="0.55"/>'
        + (f'<circle class="pulse" cx="12" cy="10" r="3.2" fill="{a}"/>' if live else "")
        + mono_text(22 if live else 10, 14, chip, 10, a, 7, 'font-weight="700"') + "</g>",
        f'<text x="22" y="68" font-family="{SANS}" font-size="22" font-weight="700" fill="{TEXT}">{escape(p["title"])}</text>',
    ]
    if p["linked"]:
        body.append(f'<path d="M405 63L416 52M408 52H416V60" fill="none" stroke="{MUTED}" stroke-width="1.8" '
                    f'stroke-linecap="round" stroke-linejoin="round"/>')
    body.append(f'<text font-family="{SANS}" font-size="13.5" fill="{BODY}">'
                + "".join(f'<tspan x="22" y="{96 + 20 * i}">{escape(t)}</tspan>' for i, t in enumerate(lines))
                + "</text>")
    x = 22
    for tag in p["tags"]:
        pw = round(len(tag) * 11 * MONO_EM + 18)
        body.append(f'<rect x="{x}" y="156" width="{pw}" height="22" rx="11" fill="#ffffff" fill-opacity="0.04" '
                    f'stroke="{a}" stroke-opacity="0.35"/>'
                    + mono_text(x + 9, 171, tag, 11, "#cfe3ff", 11 * MONO_EM))
        x += pw + 8
    assert x - 8 <= w - 22, f"{p['title']}: tags overflow"
    return svg(w, h, "".join(body), f"{p['title']}: {p['desc']}", ANIMATION_CSS if live else "")


def button(label, kind, color):
    w, h = 150, 40
    if kind == "globe":
        icon = (f'<circle cx="28" cy="20" r="8" fill="none" stroke="{color}" stroke-width="1.6"/>'
                f'<ellipse cx="28" cy="20" rx="3.6" ry="8" fill="none" stroke="{color}" stroke-width="1.4"/>'
                f'<path d="M20 20H36" stroke="{color}" stroke-width="1.4"/>')
    elif kind == "in":
        icon = (f'<rect x="20" y="12" width="16" height="16" rx="3.5" fill="{color}"/>'
                f'<text x="28" y="24.5" text-anchor="middle" font-family="{SANS}" font-size="11.5" font-weight="800" '
                f'fill="{BG}">in</text>')
    else:
        icon = (f'<rect x="19" y="13.5" width="18" height="13" rx="2.5" fill="none" stroke="{color}" stroke-width="1.6"/>'
                f'<path d="M19.8 14.5L28 21L36.2 14.5" fill="none" stroke="{color}" stroke-width="1.6" '
                f'stroke-linejoin="round"/>')
    body = (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#16163a"/>'
            f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>'
            f'<rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="{(h - 1.5) / 2}" fill="url(#bg)" '
            f'stroke="{color}" stroke-opacity="0.7" stroke-width="1.5"/>{icon}'
            f'<text x="46" y="25.5" font-family="{SANS}" font-size="15" font-weight="700" fill="{TEXT}">{label}</text>')
    return svg(w, h, body, label)


def footer():
    w, h = 1000, 120
    rnd = random.Random(7)
    path, windows, x = [f"M0 {h}"], [], 0
    while x < w:
        bw, bh = rnd.randint(26, 62), rnd.randint(16, 52)
        top, right = h - bh, min(x + bw, w)
        path.append(f"V{top}H{right}")
        for wy in range(top + 7, h - 6, 9):
            for wx in range(x + 6, right - 6, 9):
                if rnd.random() < 0.18:
                    windows.append((wx, wy, rnd.choice([CYAN, PINK, VIOLET]), rnd.random() < 0.3))
        x = right
    path.append(f"V{h}Z")
    nodes = [(70, 40), (150, 22), (240, 48), (320, 28), (680, 30), (760, 50), (850, 24), (930, 44)]
    links = "".join(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{VIOLET}" stroke-opacity="0.35"/>'
                    for (x1, y1), (x2, y2) in zip(nodes, nodes[1:]) if abs(x2 - x1) < 200)
    dots = "".join(f'<circle class="pulse" style="animation-delay:{i * 0.4:.1f}s" cx="{nx}" cy="{ny}" r="3" '
                   f'fill="{CYAN if i % 2 else VIOLET}"/>' for i, (nx, ny) in enumerate(nodes))
    lit = "".join(f'<rect{" class=" + chr(34) + "pulse" + chr(34) if blink else ""} x="{wx}" y="{wy}" width="3" '
                  f'height="4" fill="{c}" fill-opacity="0.75"/>' for wx, wy, c, blink in windows)
    tagline = "from the ground to the cloud"
    body = (panel(w, h, CYAN, rx=18, grid=40, glow=(0.5, 1.2))
            + f'<defs><linearGradient id="city" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{VIOLET}" '
              f'stop-opacity="0.28"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></linearGradient>'
              f'<clipPath id="inner"><rect width="{w}" height="{h}" rx="18"/></clipPath></defs>'
            + f'<g clip-path="url(#inner)"><path d="{"".join(path)}" fill="url(#city)" stroke="{CYAN}" '
              f'stroke-opacity="0.55" stroke-width="1.2"/>{lit}</g>'
            + links + dots
            + mono_text(w / 2, 42, tagline, 13, CYAN, 9.4, 'text-anchor="middle"'))
    return svg(w, h, body, "From the ground to the cloud", ANIMATION_CSS)


def os_window():
    """The Arshan OS screenshot in a QEMU-style window. The PNG is embedded because
    GitHub shows SVGs as images, and images inside an SVG cannot load other files."""
    png = (ROOT / "tools" / "arshan-os-gui.png").read_bytes()
    pw, ph = struct.unpack(">II", png[16:24])
    w, sx, sy, sw = 1000, 20, 56, 960
    sh = round(sw * ph / pw)
    chips = ["32-bit protected mode", "VGA mode 13h", "8x8 bitmap font", "PS/2 mouse + keyboard", "draggable windows"]
    widths = [round(len(c) * 7.2 + 22) for c in chips]
    cy = sy + sh + 22
    h = cy + 24 + 22
    x = (w - sum(widths) - 10 * (len(chips) - 1)) / 2
    pills = []
    for chip, cw in zip(chips, widths):
        pills.append(f'<rect x="{x:.1f}" y="{cy}" width="{cw}" height="24" rx="12" fill="#ffffff" fill-opacity="0.04" '
                     f'stroke="{CYAN}" stroke-opacity="0.35"/>'
                     + mono_text(round(x + 11, 1), cy + 16, chip, 12, "#cfe3ff", 7.2))
        x += cw + 10
    body = (panel(w, h, VIOLET, rx=18, grid=40, glow=(0.5, 0))
            + f'<defs><clipPath id="screen"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="10"/></clipPath>'
              f'<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" '
              f'fill="#000000" fill-opacity="0.14"/></pattern></defs>'
            + "".join(f'<circle cx="{28 + 18 * i}" cy="26" r="5.5" fill="{c}"/>' for i, c in enumerate((PINK, VIOLET, CYAN)))
            + f'<text x="{w / 2}" y="31" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">'
              f'qemu-system-i386 · Arshan OS</text>'
            + f'<line x1="0" y1="46" x2="{w}" y2="46" stroke="{CYAN}" stroke-opacity="0.15"/>'
            + f'<g clip-path="url(#screen)"><image x="{sx}" y="{sy}" width="{sw}" height="{sh}" '
              f'preserveAspectRatio="xMidYMid slice" xlink:href="data:image/png;base64,{base64.b64encode(png).decode()}"/>'
              f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" fill="url(#scan)"/></g>'
            + f'<rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="10" fill="none" stroke="{CYAN}" stroke-opacity="0.35"/>'
            + "".join(pills))
    return svg(w, h, body, "Arshan OS running in QEMU: a draggable window on a VGA desktop")


def main():
    out = {
        "header.svg": header(),
        "arshan-os-window.svg": os_window(),
        "numbers.svg": numbers(),
        "footer.svg": footer(),
        "connect-portfolio.svg": button("Portfolio", "globe", CYAN),
        "connect-linkedin.svg": button("LinkedIn", "in", VIOLET),
        "connect-email.svg": button("Email", "mail", PINK),
    }
    out.update({f"cards/{p['slug']}.svg": card(p) for p in PROJECTS})
    for name, content in out.items():
        minidom.parseString(content)  # fail loudly on malformed XML
        target = ASSETS / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
