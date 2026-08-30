"""
SVG Asset Generator — v3
=========================
Produces all visual assets for the GitHub profile.
Generates a fully self-contained hero SVG with embedded GIF,
refined project cards, and premium SVG buttons.
"""

import json
import html
import base64
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


def get_base64_gif(path):
    if not path.exists():
        return None
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/gif;base64,{b64}"


# ===========================================================================
# HERO SVG — Full-width application window with info panel & embedded GIF
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
    
    info_x = 340
    info_w = W - info_x - 32
    
    # Check for GIF
    gif_path = GEN_DIR / "portrait-animation.gif"
    gif_b64 = get_base64_gif(gif_path)
    
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
  
  <!-- LEFT: portrait zone -->
  <g transform="translate(24, 50)">
    <text x="0" y="10" fill="{t3}" font-family="'SF Mono',monospace" font-size="8" letter-spacing="2">VISUAL.MAP</text>
    <rect x="0" y="18" width="280" height="258" rx="4" fill="none" stroke="{border}" stroke-width="0.4" stroke-dasharray="3,5" opacity="0.5"/>
'''
    if gif_b64:
        # Embed GIF
        svg += f'''    <image href="{gif_b64}" x="0" y="18" width="280" height="258" preserveAspectRatio="xMidYMid slice" clip-path="url(#portrait-clip)"/>
    <defs>
      <clipPath id="portrait-clip">
        <rect x="0" y="18" width="280" height="258" rx="4"/>
      </clipPath>
    </defs>
'''
    else:
        svg += f'''    <text x="140" y="147" text-anchor="middle" fill="{t3}" font-family="'SF Mono',monospace" font-size="10" opacity="0.5">[ PORTRAIT ]</text>
'''
    
    svg += f'''  </g>
  
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
# PROJECT CARDS SVG (Refined with mesh, visual area)
# ===========================================================================
def generate_project_cards(config):
    d = config["design"]
    projects = config["projects"]
    card_w = (d["content_width"] - 16) // 2
    card_h = 240
    r = d["card_radius"]
    
    for proj in projects:
        pid = proj["id"]
        color = proj["color_accent"]
        
        # Determine abstract visual shape based on ID
        if pid == "astra":
            visual = f'''
            <g stroke="{color}" opacity="0.3" stroke-width="0.5">
                <circle cx="340" cy="90" r="40" fill="none" stroke-dasharray="2 4"/>
                <circle cx="340" cy="90" r="20" fill="none"/>
                <path d="M 280 90 L 320 90 M 360 90 L 400 90 M 340 30 L 340 70 M 340 110 L 340 150"/>
                <circle cx="340" cy="90" r="4" fill="{color}" opacity="0.8"/>
            </g>'''
        elif pid == "aerotwin":
            visual = f'''
            <g stroke="{color}" opacity="0.3" stroke-width="0.5">
                <path d="M 290 120 L 320 60 L 360 60 L 390 120 Z" fill="none"/>
                <line x1="290" y1="100" x2="390" y2="100"/>
                <line x1="305" y1="80" x2="375" y2="80"/>
                <circle cx="340" cy="120" r="15" fill="none" stroke-dasharray="2 2"/>
            </g>'''
        elif pid == "saraswati":
            visual = f'''
            <g stroke="{color}" opacity="0.3" stroke-width="0.5">
                <rect x="300" y="50" width="60" height="80" rx="2" fill="none"/>
                <line x1="310" y1="65" x2="350" y2="65"/>
                <line x1="310" y1="80" x2="350" y2="80"/>
                <line x1="310" y1="95" x2="340" y2="95"/>
                <rect x="320" y="60" width="60" height="80" rx="2" fill="none" stroke-dasharray="1 3"/>
            </g>'''
        else:
            visual = f'''
            <g stroke="{color}" opacity="0.3" stroke-width="0.5">
                <rect x="290" y="60" width="90" height="60" rx="4" fill="none"/>
                <circle cx="305" cy="75" r="3" fill="none"/>
                <circle cx="315" cy="75" r="3" fill="none"/>
                <line x1="290" y1="90" x2="380" y2="90"/>
            </g>'''
            
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{card_w}" height="{card_h}" viewBox="0 0 {card_w} {card_h}">
  <defs>
    <linearGradient id="cg-{pid}" x1="0" y1="0" x2="{card_w}" y2="{card_h}">
      <stop offset="0%" stop-color="{d['bg_secondary']}"/>
      <stop offset="100%" stop-color="{d['bg_card']}"/>
    </linearGradient>
    <linearGradient id="ca-{pid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{color}" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="grid-{pid}" width="20" height="20" patternUnits="userSpaceOnUse">
      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="{d['border_subtle']}" stroke-width="0.5" opacity="0.1"/>
    </pattern>
  </defs>
  
  <rect width="{card_w}" height="{card_h}" rx="{r}" fill="url(#cg-{pid})" stroke="{d['border']}" stroke-width="0.5"/>
  <rect width="{card_w}" height="{card_h}" rx="{r}" fill="url(#grid-{pid})"/>
  <rect x="0" y="0" width="{card_w}" height="1.5" rx="{r}" fill="{d['border']}" opacity="0.4"/>
  
  {visual}
  
  <text x="24" y="32" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="2" opacity="0.6">{esc(proj['number'])}</text>
  <text x="52" y="32" fill="{color}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="1.5" opacity="0.75">{esc(proj['category'])}</text>
  
  <circle cx="{card_w - 24}" cy="26" r="3" fill="{color}" opacity="0.6"/>
  <text x="{card_w - 36}" y="30" text-anchor="end" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="8" letter-spacing="0.5">{esc(proj['status'].upper())}</text>
  
  <text x="24" y="72" fill="{d['text_primary']}" font-family="'Inter','Segoe UI',sans-serif" font-size="22" font-weight="600" letter-spacing="0.2">{esc(proj['name'])}</text>
  <line x1="24" y1="88" x2="{card_w - 24}" y2="88" stroke="{d['border_subtle']}" stroke-width="0.4"/>
'''
        desc = proj["description"]
        words = desc.split()
        lines = []
        current = ""
        max_c = int((card_w - 48) / 6.0)
        for w in words:
            if len(current) + len(w) + 1 <= max_c:
                current += (" " if current else "") + w
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        
        dy = 112
        for line in lines[:3]:
            svg += f'''  <text x="24" y="{dy}" fill="{d['text_secondary']}" font-family="'Inter','Segoe UI',sans-serif" font-size="11" opacity="0.85">{esc(line)}</text>
'''
            dy += 18
        
        # Tech tags at bottom
        ty = card_h - 36
        tx = 24
        for tech in proj["technologies"]:
            tw = len(tech) * 5.8 + 16
            svg += f'''  <rect x="{tx}" y="{ty}" width="{tw}" height="18" rx="4" fill="{color}" opacity="0.08" stroke="{color}" stroke-width="0.5" stroke-opacity="0.3"/>
  <text x="{tx + 8}" y="{ty + 12}" fill="{d['text_secondary']}" font-family="'SF Mono',monospace" font-size="8.5">{esc(tech)}</text>
'''
            tx += tw + 8
        
        # View Project Link
        svg += f'''  <text x="{card_w - 24}" y="{card_h - 22}" text-anchor="end" fill="{color}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="1">VIEW PROJECT →</text>
'''
        
        svg += '</svg>'
        output = PROJ_DIR / f"{pid}.svg"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(svg, encoding="utf-8")
        print(f"[OK] Project: {output}")


# ===========================================================================
# CONNECT BUTTONS SVG — Premium dark-theme controls with icons
# ===========================================================================
def generate_buttons(config):
    d = config["design"]
    cyan = d['accent_cyan']
    bg = d['bg_secondary']
    bg_card = d['bg_card']
    border = d['border']
    border_s = d['border_subtle']
    t1 = d['text_primary']
    t2 = d['text_secondary']
    t3 = d['text_muted']
    
    # ─── Portfolio CTA (full-width premium panel) ───
    pw, ph = 880, 72
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{pw}" height="{ph}" viewBox="0 0 {pw} {ph}">
  <defs>
    <linearGradient id="cta-bg" x1="0" y1="0" x2="{pw}" y2="{ph}">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{bg_card}"/>
    </linearGradient>
    <linearGradient id="cta-accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{cyan}" stop-opacity="0.6"/>
      <stop offset="50%" stop-color="{d['accent_blue']}" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="{cyan}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="{pw}" height="{ph}" rx="8" fill="url(#cta-bg)" stroke="{cyan}" stroke-width="0.6" stroke-opacity="0.35"/>
  <rect x="0" y="0" width="{pw}" height="1.5" rx="8" fill="url(#cta-accent)"/>
  <g opacity="0.015">
    {chr(10).join(f"<line x1='{x}' y1='0' x2='{x}' y2='{ph}' stroke='{t2}' stroke-width='0.5'/>" for x in range(0, pw, 32))}
  </g>
  <text x="32" y="30" fill="{cyan}" font-family="'SF Mono',monospace" font-size="13" font-weight="600" letter-spacing="2">◇  OPEN PORTFOLIO</text>
  <text x="32" y="52" fill="{t2}" font-family="'Inter','Segoe UI',sans-serif" font-size="10.5" opacity="0.7">Work · Interfaces · Experiments</text>
  <text x="{pw - 32}" y="42" text-anchor="end" fill="{cyan}" font-family="'SF Mono',monospace" font-size="16" opacity="0.6">→</text>
  <circle cx="{pw - 60}" cy="38" r="3" fill="#27C93F" opacity="0.5"/>
  <text x="{pw - 72}" y="42" text-anchor="end" fill="{t3}" font-family="'SF Mono',monospace" font-size="7" letter-spacing="1" opacity="0.4">LIVE</text>
</svg>'''
    (GEN_DIR / "btn-portfolio.svg").write_text(svg, encoding="utf-8")
    
    # ─── Social Buttons (with inline SVG icons) ───
    icon_paths = {
        "linkedin": "M4.98 3.5C4.98 4.88 3.87 6 2.5 6S.02 4.88.02 3.5 1.13 1 2.5 1 4.98 2.12 4.98 3.5zM.5 8h4v12h-4V8zm7.09.01C7.85 8.01 8.07 8 8.5 8h3.5v1.75h.05c.5-.95 1.72-1.95 3.54-1.95 3.78 0 4.48 2.49 4.48 5.73V20h-4v-5.66c0-1.35-.02-3.09-1.88-3.09-1.88 0-2.17 1.47-2.17 2.99V20h-4V8.01z",
        "instagram": "M7 2C4.24 2 2 4.24 2 7v10c0 2.76 2.24 5 5 5h10c2.76 0 5-2.24 5-5V7c0-2.76-2.24-5-5-5H7zm0 2h10c1.65 0 3 1.35 3 3v10c0 1.65-1.35 3-3 3H7c-1.65 0-3-1.35-3-3V7c0-1.65 1.35-3 3-3zm5 3a5 5 0 100 10 5 5 0 000-10zm0 2a3 3 0 110 6 3 3 0 010-6zm5.5-2.5a1 1 0 100 2 1 1 0 000-2z",
        "facebook": "M22 12c0-5.52-4.48-10-10-10S2 6.48 2 12c0 4.84 3.44 8.87 8 9.8V15h-2v-3h2V9.5C10 7.57 11.57 6 13.5 6H16v3h-2c-.55 0-1 .45-1 1v2h3l-.5 3H13v6.95c5.05-.5 9-4.76 9-9.95z",
        "email": "M2 4h20v16H2V4zm2 2v.01L12 12l8-5.99V6L12 12 4 6zm0 2.5V18h16V8.5l-8 5.5-8-5.5z"
    }
    
    labels = {
        "linkedin": "LINKEDIN",
        "instagram": "INSTAGRAM",
        "facebook": "FACEBOOK",
        "email": "EMAIL"
    }
    
    sw, sh = 180, 44
    
    for social in ["linkedin", "instagram", "facebook", "email"]:
        icon = icon_paths.get(social, "")
        label = labels[social]
        
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{sw}" height="{sh}" viewBox="0 0 {sw} {sh}">
  <rect width="{sw}" height="{sh}" rx="6" fill="{bg}" stroke="{border_s}" stroke-width="0.5"/>
  <rect x="0" y="{sh - 1}" width="{sw}" height="1" rx="0" fill="{t3}" opacity="0.15"/>
  <g transform="translate(14, {sh // 2 - 8}) scale(0.66)" fill="{t2}" opacity="0.7">
    <path d="{icon}"/>
  </g>
  <text x="38" y="{sh // 2 + 4}" fill="{t2}" font-family="'SF Mono',monospace" font-size="10" letter-spacing="1.2">{label}</text>
  <text x="{sw - 14}" y="{sh // 2 + 3}" text-anchor="end" fill="{t3}" font-family="'SF Mono',monospace" font-size="10" opacity="0.4">→</text>
</svg>'''
        (GEN_DIR / f"btn-{social}.svg").write_text(svg, encoding="utf-8")
    
    # ─── Profile Views Counter SVG wrapper ───
    generate_profile_views(config)
    
    print("[OK] Connect buttons generated.")


def generate_profile_views(config):
    d = config["design"]
    username = config["identity"]["username"]
    
    vw, vh = 280, 36
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" viewBox="0 0 {vw} {vh}">
  <rect width="{vw}" height="{vh}" rx="4" fill="{d['bg_secondary']}" stroke="{d['border_subtle']}" stroke-width="0.4"/>
  <circle cx="14" cy="{vh // 2}" r="3" fill="#27C93F" opacity="0.5"/>
  <text x="24" y="{vh // 2 + 4}" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="8.5" letter-spacing="1">PROFILE.VIEWS</text>
  <image href="https://komarev.com/ghpvc/?username={username}&amp;style=flat-square&amp;color=161B22&amp;label=" x="128" y="6" width="140" height="24"/>
</svg>'''
    (GEN_DIR / "profile-views.svg").write_text(svg, encoding="utf-8")
    print(f"[OK] Profile views SVG: assets/generated/profile-views.svg")


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
    generate_buttons(config)
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
