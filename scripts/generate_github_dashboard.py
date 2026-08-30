"""
GitHub Dashboard Generator
============================
Generates a full-width (880px) premium activity visualization SVG.
Reads data from data/github_profile.json.

Features:
- Top metrics row (contributions, repos, stars, streak, followers)
- Smooth area chart from 52-week contribution calendar
- Month labels, gridlines, gradient fill, peak markers
- Premium dark-theme design language

Usage:
    python scripts/generate_github_dashboard.py
"""

import json
import html
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
DATA_PATH = ROOT / "data" / "github_profile.json"
OUTPUT_PATH = ROOT / "assets" / "generated" / "github-dashboard.svg"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def esc(text):
    return html.escape(str(text))


def fmt_number(n):
    """Format number with comma separator."""
    return f"{n:,}"


def smooth_points(points, window=3):
    """Apply simple moving average smoothing to y-values."""
    smoothed = []
    for i in range(len(points)):
        start = max(0, i - window)
        end = min(len(points), i + window + 1)
        avg_y = sum(p[1] for p in points[start:end]) / (end - start)
        smoothed.append((points[i][0], avg_y))
    return smoothed


def build_smooth_path(points):
    """Build a smooth SVG path using cubic bezier curves."""
    if len(points) < 2:
        return ""

    parts = [f"M {points[0][0]:.1f},{points[0][1]:.1f}"]
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        # Control points for smooth curve
        cx = (x0 + x1) / 2
        parts.append(f"C {cx:.1f},{y0:.1f} {cx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")

    return " ".join(parts)


def generate_dashboard():
    config = load_config()
    d = config["design"]
    data = load_data()

    W = 880
    H = 380
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
    ice = d["accent_ice"]

    # Chart area dimensions
    chart_left = 56
    chart_right = W - 32
    chart_top = 160
    chart_bottom = 320
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top

    # Weekly activity data
    weekly = data.get("weekly_activity", [])
    if not weekly:
        weekly = [{"week_start": "", "contributions": 0}] * 52

    values = [w["contributions"] for w in weekly]
    max_val = max(values) if values else 1
    if max_val == 0:
        max_val = 1

    # Build chart points
    n = len(values)
    raw_points = []
    for i, val in enumerate(values):
        x = chart_left + (i / max(n - 1, 1)) * chart_w
        y = chart_bottom - (val / max_val) * chart_h
        raw_points.append((x, y))

    points = smooth_points(raw_points, window=2)

    # Build paths
    line_path = build_smooth_path(points)
    # Area fill path — close to bottom
    area_path = line_path + f" L {points[-1][0]:.1f},{chart_bottom} L {points[0][0]:.1f},{chart_bottom} Z"

    # Find peak
    peak_idx = values.index(max(values))
    peak_x, peak_y = points[peak_idx]

    # Month labels
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_labels_svg = ""
    for i, week in enumerate(weekly):
        ds = week.get("week_start", "")
        if ds and len(ds) >= 7:
            try:
                month = int(ds[5:7])
                day = int(ds[8:10]) if len(ds) >= 10 else 1
                if day <= 7 and i < n:
                    x = chart_left + (i / max(n - 1, 1)) * chart_w
                    month_labels_svg += f'  <text x="{x:.1f}" y="{chart_bottom + 18}" text-anchor="middle" fill="{t3}" font-family="\'SF Mono\',monospace" font-size="8" opacity="0.6">{month_names[month - 1]}</text>\n'
            except (ValueError, IndexError):
                pass

    # Metrics
    metrics = [
        ("CONTRIBUTIONS", fmt_number(data.get("total_contributions", 0)), cyan),
        ("REPOSITORIES", fmt_number(data.get("repositories", 0)), t1),
        ("STARS", fmt_number(data.get("stars", 0)), t1),
        ("STREAK", f"{data.get('current_streak', 0)}d", ice),
        ("FOLLOWERS", fmt_number(data.get("followers", 0)), t1),
    ]

    # Horizontal gridlines
    grid_lines = ""
    for i in range(5):
        y = chart_top + (i / 4) * chart_h
        val = int(max_val * (1 - i / 4))
        grid_lines += f'  <line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="{border_s}" stroke-width="0.4" opacity="0.5"/>\n'
        grid_lines += f'  <text x="{chart_left - 8}" y="{y + 3:.1f}" text-anchor="end" fill="{t3}" font-family="\'SF Mono\',monospace" font-size="7.5" opacity="0.5">{val}</text>\n'

    # Build data point dots for peaks and significant values
    data_dots = ""
    threshold = max_val * 0.7
    for i, val in enumerate(values):
        if val >= threshold and i < len(points):
            x, y = points[i]
            data_dots += f'  <circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="{cyan}" opacity="0.6"/>\n'

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="dash-bg" x1="0" y1="0" x2="{W}" y2="{H}">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="{bg_card}"/>
    </linearGradient>
    <linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{cyan}" stop-opacity="0.25"/>
      <stop offset="50%" stop-color="{blue}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{blue}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="chart-stroke" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{cyan}" stop-opacity="0.9"/>
      <stop offset="50%" stop-color="{ice}" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="{blue}" stop-opacity="0.6"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Shell -->
  <rect width="{W}" height="{H}" rx="{r}" fill="url(#dash-bg)" stroke="{border}" stroke-width="0.5"/>

  <!-- Accent bar -->
  <rect x="0" y="0" width="{W}" height="1.5" rx="{r}" fill="{cyan}" opacity="0.3"/>

  <!-- Subtle grid pattern -->
  <g opacity="0.02">
    {"".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{t2}" stroke-width="0.5"/>' for x in range(0, W, 44))}
  </g>

  <!-- Header -->
  <text x="24" y="28" fill="{t3}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="2">GITHUB.ACTIVITY</text>
  <text x="185" y="28" fill="{t3}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="1" opacity="0.35">— a year of building</text>
  <circle cx="{W - 24}" cy="22" r="3" fill="#27C93F" opacity="0.7"/>
  <text x="{W - 36}" y="26" text-anchor="end" fill="#27C93F" font-family="'SF Mono',monospace" font-size="7.5" letter-spacing="1" opacity="0.7">LIVE</text>

  <line x1="24" y1="38" x2="{W - 24}" y2="38" stroke="{border_s}" stroke-width="0.4"/>

  <!-- Metrics row -->
'''

    metric_w = (W - 48) / len(metrics)
    for i, (label, value, color) in enumerate(metrics):
        mx = 24 + i * metric_w + metric_w / 2
        svg += f'  <text x="{mx:.0f}" y="62" text-anchor="middle" fill="{t3}" font-family="\'SF Mono\',monospace" font-size="8" letter-spacing="1.5">{label}</text>\n'
        svg += f'  <text x="{mx:.0f}" y="92" text-anchor="middle" fill="{color}" font-family="\'Inter\',\'Segoe UI\',sans-serif" font-size="26" font-weight="600">{value}</text>\n'
        if i < len(metrics) - 1:
            sep_x = 24 + (i + 1) * metric_w
            svg += f'  <line x1="{sep_x:.0f}" y1="52" x2="{sep_x:.0f}" y2="96" stroke="{border_s}" stroke-width="0.4"/>\n'

    svg += f'''
  <!-- Metrics / chart separator -->
  <line x1="24" y1="110" x2="{W - 24}" y2="110" stroke="{border_s}" stroke-width="0.4"/>
  <text x="24" y="130" fill="{t3}" font-family="'SF Mono',monospace" font-size="7.5" letter-spacing="1.5" opacity="0.5">WEEKLY CONTRIBUTION ACTIVITY</text>
  <text x="{W - 24}" y="130" text-anchor="end" fill="{t3}" font-family="'SF Mono',monospace" font-size="7.5" letter-spacing="1" opacity="0.35">52 WEEKS</text>

  <!-- Gridlines -->
{grid_lines}

  <!-- Area fill -->
  <path d="{area_path}" fill="url(#chart-fill)" opacity="0.9"/>

  <!-- Line -->
  <path d="{line_path}" fill="none" stroke="url(#chart-stroke)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>

  <!-- Data point highlights -->
{data_dots}

  <!-- Peak marker -->
  <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="3.5" fill="{cyan}" filter="url(#glow)" opacity="0.9"/>
  <circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="1.5" fill="#fff"/>
  <text x="{peak_x:.1f}" y="{peak_y - 10:.1f}" text-anchor="middle" fill="{cyan}" font-family="'SF Mono',monospace" font-size="8" font-weight="600">{max(values)}</text>

  <!-- Month labels -->
{month_labels_svg}

  <!-- Bottom axis line -->
  <line x1="{chart_left}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="{border_s}" stroke-width="0.4"/>

  <!-- Chart frame accent -->
  <line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_bottom}" stroke="{border_s}" stroke-width="0.4" opacity="0.3"/>

  <!-- Footer micro-label -->
  <text x="{W / 2}" y="{H - 16}" text-anchor="middle" fill="{t3}" font-family="'SF Mono',monospace" font-size="7" letter-spacing="2" opacity="0.25">BUILD · COMMIT · REPEAT</text>

</svg>'''

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")

    size = OUTPUT_PATH.stat().st_size
    print(f"[OK] Dashboard SVG: {OUTPUT_PATH} ({size} bytes)")
    return OUTPUT_PATH


if __name__ == "__main__":
    generate_dashboard()
