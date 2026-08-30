"""
SVG Asset Generator — v2
=========================
Produces all visual assets for the GitHub profile.
This version generates a fully self-contained hero SVG with embedded
composition, plus all supporting section assets.
"""

import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
GEN_DIR = ROOT / "assets" / "generated"
PROJ_DIR = ROOT / "assets" / "projects"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def esc(text):
    return html.escape(str(text))


# ===========================================================================
# HERO SVG — Full-width application window with info panel
# ===========================================================================
def generate_hero(config):
    d = config["design"]
    identity = config["identity"]
    status = config["status"]
    
    W = d["content_width"]
    H = 340
    r = d["card_radius"]
    
    bg = d["bg_secondary"]
    bg_card = d["bg_card"]
    border = d["border"]
    border_s = d["border_subtle"]
    t1 = d["text_primary"]
    t2 = d["text_secondary"]
    t3 = d["text_muted"]
    cyan = d["accent_cyan"]
    blue = d["accent_blue"]
    violet = d["accent_violet"]
    
    # Portrait area on left (will be overlaid with GIF in README)
    # Info panel on right
    info_x = 340
    info_w = W - info_x - 32
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">
  <defs>
    <linearGradient id="bg-grad" x1="0" y1="0" x2="{W}" y2="{H}">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="#111820"/>
    </linearGradient>
    <linearGradient id="accent-bar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{cyan}" stop-opacity="0.5"/>
      <stop offset="50%" stop-color="{blue}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{violet}" stop-opacity="0.08"/>
    </linearGradient>
  </defs>
  
  <!-- Shell -->
  <rect width="{W}" height="{H}" rx="{r}" fill="url(#bg-grad)"/>
  <rect width="{W}" height="{H}" rx="{r}" fill="none" stroke="{border}" stroke-width="0.8"/>
  
  <!-- Subtle grid -->
  <g opacity="0.025">
    {"".join(f'<line x1="{x}" y1="40" x2="{x}" y2="{H}" stroke="{t2}" stroke-width="0.5"/>' for x in range(0, W, 44))}
    {"".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{t2}" stroke-width="0.5"/>' for y in range(40, H, 44))}
  </g>
  
  <!-- Title bar -->
  <rect x="0.5" y="0.5" width="{W - 1}" height="36" rx="{r}" fill="{bg_card}" opacity="0.85"/>
  <rect x="0" y="28" width="{W}" height="9" fill="{bg_card}" opacity="0.85"/>
  <line x1="0" y1="36.5" x2="{W}" y2="36.5" stroke="{border}" stroke-width="0.5"/>
  
  <!-- Dots -->
  <circle cx="20" cy="18" r="5" fill="#FF5F56"/>
  <circle cx="37" cy="18" r="5" fill="#FFBD2E"/>
  <circle cx="54" cy="18" r="5" fill="#27C93F"/>
  
  <!-- Title -->
  <text x="{W // 2}" y="22" text-anchor="middle" fill="{t2}" font-family="'SF Mono','Cascadia Code','Fira Code',monospace" font-size="10.5" letter-spacing="1.8">MAYANK.SYSTEM — ./profile --live</text>
  
  <!-- Accent bar -->
  <rect x="0" y="36" width="{W}" height="1.5" fill="url(#accent-bar)"/>
  
  <!-- LEFT: portrait zone (empty — GIF overlays this in README) -->
  <g transform="translate(24, 50)">
    <text x="0" y="10" fill="{t3}" font-family="'SF Mono',monospace" font-size="8" letter-spacing="2">VISUAL.MAP</text>
    <rect x="0" y="18" width="280" height="258" rx="4" fill="none" stroke="{border}" stroke-width="0.4" stroke-dasharray="3,5" opacity="0.5"/>
  </g>
  
  <!-- RIGHT: System info -->
  <g transform="translate({info_x}, 50)">
    <text x="0" y="12" fill="{cyan}" font-family="'SF Mono',monospace" font-size="12" font-weight="600" letter-spacing="1.2">SYSTEM.INFO</text>
    <circle cx="{info_w - 4}" cy="8" r="3" fill="#27C93F" opacity="0.8"/>
    <text x="{info_w - 14}" y="12" text-anchor="end" fill="#27C93F" font-family="'SF Mono',monospace" font-size="7.5" letter-spacing="1">LIVE</text>
    
    <line x1="0" y1="22" x2="{info_w}" y2="22" stroke="{border_s}" stroke-width="0.4"/>
'''

    rows = [
        ("Subject", identity["name"], cyan, t1),
        ("Role", identity["headline"], cyan, t1),
        ("Origin", identity["location"], cyan, t1),
        ("Status", status["current"], cyan, t1),
    ]
    
    y = 40
    for label, value, lc, vc in rows:
        svg += f'''    <text x="0" y="{y}" fill="{lc}" font-family="'SF Mono',monospace" font-size="10.5" letter-spacing="0.5">{esc(label)}</text>
    <text x="{info_w}" y="{y}" text-anchor="end" fill="{vc}" font-family="'SF Mono',monospace" font-size="10.5">{esc(value)}</text>
'''
        y += 20
    
    # Separator
    svg += f'''    <line x1="0" y1="{y - 6}" x2="{info_w}" y2="{y - 6}" stroke="{border_s}" stroke-width="0.4" stroke-dasharray="2,3"/>
'''
    y += 8
    
    tech_rows = [
        ("Focus", status["focus"]),
        ("Building", status["currently_building"]),
        ("Learning", status["currently_learning"]),
        ("Open To", status["open_to"]),
    ]
    
    for label, value in tech_rows:
        svg += f'''    <text x="0" y="{y}" fill="{blue}" font-family="'SF Mono',monospace" font-size="10" letter-spacing="0.5">{esc(label)}</text>
    <text x="{info_w}" y="{y}" text-anchor="end" fill="{t2}" font-family="'SF Mono',monospace" font-size="10">{esc(value)}</text>
'''
        y += 18
    
    # Separator
    svg += f'''    <line x1="0" y1="{y - 4}" x2="{info_w}" y2="{y - 4}" stroke="{border_s}" stroke-width="0.4" stroke-dasharray="2,3"/>
'''
    y += 10
    
    # Bio
    bio = identity["short_bio"]
    words = bio.split()
    lines = []
    current = ""
    max_c = int(info_w / 5.8)
    for word in words:
        if len(current) + len(word) + 1 <= max_c:
            current += (" " if current else "") + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    
    for line in lines[:3]:
        svg += f'''    <text x="0" y="{y}" fill="{t2}" font-family="'Inter','Segoe UI',sans-serif" font-size="10.5" opacity="0.75">{esc(line)}</text>
'''
        y += 15
    
    y += 6
    svg += f'''    <text x="0" y="{y}" fill="{t3}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="1.2" opacity="0.5">— {esc(identity["design_principle"])}</text>
'''
    
    svg += '''  </g>
</svg>'''
    
    output = GEN_DIR / "hero.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"[OK] Hero SVG: {output}")


# ===========================================================================
# TECH STACK SVG
# ===========================================================================
def generate_stack(config):
    d = config["design"]
    stack = config["tech_stack"]
    W = d["content_width"]
    
    category_colors = {
        "Languages": d["accent_cyan"],
        "Interface": d["accent_blue"],
        "Backend & Systems": d["accent_violet"],
        "AI & Intelligence": "#F78C6C",
        "Cloud & DevOps": d["accent_ice"],
        "Security": "#FF5370",
        "Design": d["accent_violet"],
    }
    
    row_height = 50
    header_h = 46
    padding = 16
    H = header_h + len(stack) * row_height + padding
    r = d["card_radius"]
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" rx="{r}" fill="{d['bg_secondary']}" stroke="{d['border_subtle']}" stroke-width="0.5"/>
  <text x="24" y="26" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="2">TOOLKIT.MAP</text>
  <line x1="24" y1="36" x2="{W - 24}" y2="36" stroke="{d['border_subtle']}" stroke-width="0.4"/>
'''
    
    y_pos = header_h
    for i, (cat_name, techs) in enumerate(stack.items()):
        color = category_colors.get(cat_name, d["accent_cyan"])
        
        svg += f'''  <circle cx="32" cy="{y_pos + 12}" r="2.5" fill="{color}" opacity="0.8"/>
  <text x="44" y="{y_pos + 16}" fill="{color}" font-family="'SF Mono',monospace" font-size="9.5" letter-spacing="1.5" font-weight="600">{esc(cat_name.upper())}</text>
'''
        tag_x = 44
        tag_y = y_pos + 32
        for tech in techs:
            tw = len(tech) * 6.2 + 16
            if tag_x + tw > W - 30:
                tag_x = 44
                tag_y += 20
            svg += f'''  <rect x="{tag_x}" y="{tag_y - 11}" width="{tw}" height="17" rx="3" fill="{color}" opacity="0.07" stroke="{color}" stroke-width="0.4" stroke-opacity="0.2"/>
  <text x="{tag_x + 8}" y="{tag_y + 1}" fill="{d['text_secondary']}" font-family="'SF Mono',monospace" font-size="9">{esc(tech)}</text>
'''
            tag_x += tw + 5
        
        y_pos += row_height
        if i < len(stack) - 1:
            svg += f'''  <line x1="44" y1="{y_pos - 4}" x2="{W - 24}" y2="{y_pos - 4}" stroke="{d['border_subtle']}" stroke-width="0.3"/>
'''
    
    svg += '</svg>'
    output = GEN_DIR / "stack.svg"
    output.write_text(svg, encoding="utf-8")
    print(f"[OK] Stack SVG: {output}")


# ===========================================================================
# PROJECT CARDS SVG
# ===========================================================================
def generate_project_cards(config):
    d = config["design"]
    projects = config["projects"]
    card_w = (d["content_width"] - 16) // 2  # Account for gap
    card_h = 200
    r = d["card_radius"]
    
    for proj in projects:
        pid = proj["id"]
        color = proj["color_accent"]
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}">
  <defs>
    <linearGradient id="cg-{pid}" x1="0" y1="0" x2="{card_w}" y2="{card_h}">
      <stop offset="0%" stop-color="{d['bg_secondary']}"/>
      <stop offset="100%" stop-color="{d['bg_card']}"/>
    </linearGradient>
    <linearGradient id="ca-{pid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="{card_w}" height="{card_h}" rx="{r}" fill="url(#cg-{pid})" stroke="{d['border']}" stroke-width="0.5"/>
  <rect x="0" y="0" width="{card_w}" height="2" rx="{r}" fill="url(#ca-{pid})"/>
  
  <text x="20" y="30" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="2" opacity="0.4">{esc(proj['number'])}</text>
  <text x="46" y="30" fill="{color}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="1.5" opacity="0.65">{esc(proj['category'])}</text>
  
  <circle cx="{card_w - 20}" cy="24" r="2.5" fill="{color}" opacity="0.55"/>
  <text x="{card_w - 30}" y="28" text-anchor="end" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="7.5" letter-spacing="0.5">{esc(proj['status'].upper())}</text>
  
  <text x="20" y="62" fill="{d['text_primary']}" font-family="'Inter','Segoe UI',sans-serif" font-size="20" font-weight="600" letter-spacing="0.3">{esc(proj['name'])}</text>
  <line x1="20" y1="72" x2="{card_w - 20}" y2="72" stroke="{d['border_subtle']}" stroke-width="0.4"/>
'''
        desc = proj["description"]
        words = desc.split()
        lines = []
        current = ""
        max_c = int((card_w - 40) / 6.0)
        for w in words:
            if len(current) + len(w) + 1 <= max_c:
                current += (" " if current else "") + w
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        
        dy = 90
        for line in lines[:3]:
            svg += f'''  <text x="20" y="{dy}" fill="{d['text_secondary']}" font-family="'Inter','Segoe UI',sans-serif" font-size="10.5" opacity="0.8">{esc(line)}</text>
'''
            dy += 15
        
        # Tech tags at bottom
        ty = card_h - 30
        tx = 20
        for tech in proj["technologies"]:
            tw = len(tech) * 5.8 + 14
            svg += f'''  <rect x="{tx}" y="{ty}" width="{tw}" height="16" rx="3" fill="{color}" opacity="0.08" stroke="{color}" stroke-width="0.35" stroke-opacity="0.25"/>
  <text x="{tx + 7}" y="{ty + 11}" fill="{d['text_secondary']}" font-family="'SF Mono',monospace" font-size="8.5">{esc(tech)}</text>
'''
            tx += tw + 5
        
        svg += '</svg>'
        output = PROJ_DIR / f"{pid}.svg"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(svg, encoding="utf-8")
        print(f"[OK] Project: {output}")


# ===========================================================================
# SECTION HEADERS
# ===========================================================================
def generate_section_header(config, title, subtitle, filename):
    d = config["design"]
    W = d["content_width"]
    H = 40
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <text x="0" y="16" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="2">{esc(title)}</text>
  <text x="{len(title) * 7 + 14}" y="16" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="1" opacity="0.35">{esc(subtitle)}</text>
  <line x1="0" y1="26" x2="{W}" y2="26" stroke="{d['border_subtle']}" stroke-width="0.4"/>
</svg>'''
    output = GEN_DIR / filename
    output.write_text(svg, encoding="utf-8")
    print(f"[OK] Header: {output}")


# ===========================================================================
# FOOTER SVG
# ===========================================================================
def generate_footer(config):
    d = config["design"]
    W = d["content_width"]
    H = 52
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="fl" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{d['accent_cyan']}" stop-opacity="0"/>
      <stop offset="20%" stop-color="{d['accent_cyan']}" stop-opacity="0.25"/>
      <stop offset="50%" stop-color="{d['accent_blue']}" stop-opacity="0.15"/>
      <stop offset="80%" stop-color="{d['accent_violet']}" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="{d['accent_violet']}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <line x1="0" y1="6" x2="{W}" y2="6" stroke="url(#fl)" stroke-width="0.5"/>
  <text x="{W // 2}" y="28" text-anchor="middle" fill="{d['text_muted']}" font-family="'Inter','Segoe UI',sans-serif" font-size="10.5" letter-spacing="0.3" opacity="0.55">Built quietly. Refined deliberately.</text>
  <text x="{W // 2}" y="44" text-anchor="middle" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="7.5" letter-spacing="2" opacity="0.25">MAYANK.SYSTEM v1.0</text>
</svg>'''
    output = GEN_DIR / "footer.svg"
    output.write_text(svg, encoding="utf-8")
    print(f"[OK] Footer: {output}")


# ===========================================================================
# CONTACT SVG
# ===========================================================================
def generate_contact(config):
    d = config["design"]
    W = d["content_width"]
    H = 50
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <text x="{W // 2}" y="20" text-anchor="middle" fill="{d['accent_cyan']}" font-family="'SF Mono',monospace" font-size="10.5" letter-spacing="1.5" font-weight="600">◆  OPEN PORTFOLIO</text>
  <text x="{W // 2}" y="40" text-anchor="middle" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="1">LinkedIn  ·  Instagram  ·  Facebook  ·  Email</text>
</svg>'''
    output = GEN_DIR / "contact.svg"
    output.write_text(svg, encoding="utf-8")
    print(f"[OK] Contact: {output}")


# ===========================================================================
# MAIN
# ===========================================================================
def generate_all():
    config = load_config()
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    PROJ_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 48)
    print(" Generating SVG assets...")
    print("=" * 48)
    
    generate_hero(config)
    generate_stack(config)
    generate_project_cards(config)
    generate_contact(config)
    generate_footer(config)
    
    headers = [
        ("GITHUB.TELEMETRY", "real-time metrics", "header-telemetry.svg"),
        ("GITHUB.STATISTICS", "performance overview", "header-stats.svg"),
        ("TOOLKIT.MAP", "active technologies", "header-toolkit.svg"),
        ("CONTRIBUTION.FLOW", "activity visualization", "header-contribution.svg"),
        ("PROJECTS.ACTIVE", "selected work", "header-projects.svg"),
        ("CONNECT", "reach out", "header-connect.svg"),
    ]
    for title, sub, fn in headers:
        generate_section_header(config, title, f"— {sub}", fn)
    
    print("=" * 48)
    print(" All assets generated.")
    print("=" * 48)


if __name__ == "__main__":
    generate_all()
