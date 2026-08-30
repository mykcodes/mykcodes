"""
Language Visualization Generator
==================================
Generates a full-width (880px) premium language distribution SVG.
Reads data from data/github_profile.json.

Features:
- Horizontal segmented proportion bar with GitHub language colors
- Ranked language list with percentages
- Premium dark-theme design language

Usage:
    python scripts/generate_languages.py
"""

import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
DATA_PATH = ROOT / "data" / "github_profile.json"
OUTPUT_PATH = ROOT / "assets" / "generated" / "github-languages.svg"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def esc(text):
    return html.escape(str(text))


def generate_languages():
    config = load_config()
    d = config["design"]
    data = load_data()

    W = 880
    H = 200
    r = d["card_radius"]

    bg = d["bg_secondary"]
    bg_card = d["bg_card"]
    border = d["border"]
    border_s = d["border_subtle"]
    t1 = d["text_primary"]
    t2 = d["text_secondary"]
    t3 = d["text_muted"]
    cyan = d["accent_cyan"]

    languages = data.get("languages", [])
    if not languages:
        languages = [{"name": "Unknown", "color": "#8B949E", "percent": 100}]

    # Segmented bar dimensions
    bar_x = 24
    bar_y = 58
    bar_w = W - 48
    bar_h = 12

    # Build the segmented bar with clip-path for rounded corners
    bar_segments = ""
    curr_x = bar_x
    for i, lang in enumerate(languages):
        seg_w = max(1, (lang["percent"] / 100.0) * bar_w)
        bar_segments += f'  <rect x="{curr_x:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{bar_h}" fill="{lang["color"]}"/>\n'
        curr_x += seg_w

    # Language legend — two columns
    legend_svg = ""
    col_w = (W - 48) / 2
    per_col = (len(languages) + 1) // 2

    for i, lang in enumerate(languages):
        col = 0 if i < per_col else 1
        row = i if col == 0 else i - per_col
        lx = 24 + col * col_w
        ly = 100 + row * 26

        legend_svg += f'  <circle cx="{lx + 6}" cy="{ly + 1}" r="4.5" fill="{lang["color"]}"/>\n'
        legend_svg += f'  <text x="{lx + 18}" y="{ly + 5}" fill="{t2}" font-family="\'SF Mono\',monospace" font-size="10.5">{esc(lang["name"])}</text>\n'
        legend_svg += f'  <text x="{lx + col_w - 24}" y="{ly + 5}" text-anchor="end" fill="{t3}" font-family="\'SF Mono\',monospace" font-size="10">{lang["percent"]:.1f}%</text>\n'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <clipPath id="bar-clip">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6"/>
    </clipPath>
  </defs>

  <!-- Shell -->
  <rect width="{W}" height="{H}" rx="{r}" fill="{bg}" stroke="{border}" stroke-width="0.5"/>

  <!-- Header -->
  <text x="24" y="28" fill="{t3}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="2">LANGUAGE.SIGNAL</text>
  <text x="180" y="28" fill="{t3}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="1" opacity="0.35">— code distribution</text>
  <line x1="24" y1="38" x2="{W - 24}" y2="38" stroke="{border_s}" stroke-width="0.4"/>

  <!-- Segmented bar -->
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6" fill="{bg_card}"/>
  <g clip-path="url(#bar-clip)">
{bar_segments}  </g>

  <!-- Bar border -->
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="6" fill="none" stroke="{border_s}" stroke-width="0.4"/>

  <!-- Language list -->
{legend_svg}
</svg>'''

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")

    size = OUTPUT_PATH.stat().st_size
    print(f"[OK] Languages SVG: {OUTPUT_PATH} ({size} bytes)")
    return OUTPUT_PATH


if __name__ == "__main__":
    generate_languages()
