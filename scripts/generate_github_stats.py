"""
Local GitHub Telemetry Generator
=================================
Fetches GitHub stats via GraphQL/REST API and generates matching SVG dashboards.
Falls back to mock data if GITHUB_TOKEN is not available.
"""

import os
import json
import requests
import html
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
GEN_DIR = ROOT / "assets" / "generated"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def esc(text):
    return html.escape(str(text))

def fetch_github_data(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[WARN] GITHUB_TOKEN not found. Using mock telemetry data.")
        return get_mock_data()
    
    headers = {"Authorization": f"bearer {token}"}
    
    # 1. Fetch user stats (repos, stars, followers)
    query = """
    query($login: String!) {
      user(login: $login) {
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        pullRequests(first: 1) { totalCount }
        issues(first: 1) { totalCount }
        followers { totalCount }
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    
    try:
        res = requests.post("https://api.github.com/graphql", json={"query": query, "variables": {"login": username}}, headers=headers)
        if res.status_code != 200:
            print(f"[ERROR] GitHub API failed: {res.status_code}")
            return get_mock_data()
            
        data = res.json()
        if "errors" in data:
            print(f"[ERROR] GitHub GraphQL Error: {data['errors']}")
            return get_mock_data()
            
        user = data["data"]["user"]
        
        # Calculate streak
        calendar = user["contributionsCollection"]["contributionCalendar"]
        total_contribs = calendar["totalContributions"]
        
        days = []
        for week in calendar["weeks"]:
            days.extend(week["contributionDays"])
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        
        # Historical longest streak
        for day in days:
            if day["contributionCount"] > 0:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0
                
        # Current streak logic (provisional today)
        if days:
            today_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
            days_dict = {day["date"]: day["contributionCount"] for day in days}
            
            if today_str not in days_dict:
                max_date = max(days_dict.keys())
                if max_date < today_str:
                    print(f"[WARN] GitHub calendar is stale. Expected today ({today_str}) but ends at {max_date}")
                    today_str = max_date
                else:
                    today_str = max_date
                    print(f"[WARN] Calendar missing today ({today_str}), using max_date {max_date}")
            
            today_count = days_dict[today_str]
            today_dt = datetime.datetime.strptime(today_str, "%Y-%m-%d")
            
            if today_count > 0:
                streak_end = today_dt
            else:
                streak_end = today_dt - datetime.timedelta(days=1)
                
            curr_dt = streak_end
            while True:
                d_str = curr_dt.strftime("%Y-%m-%d")
                if d_str not in days_dict:
                    break
                if days_dict[d_str] > 0:
                    current_streak += 1
                    curr_dt -= datetime.timedelta(days=1)
                else:
                    break
                
        # Calculate stars
        repos = user["repositories"]["nodes"]
        total_stars = sum(r.get("stargazerCount", 0) for r in repos)
        total_repos = user["repositories"]["totalCount"]
        
        # Calculate languages
        langs = {}
        for r in repos:
            for edge in r["languages"]["edges"]:
                name = edge["node"]["name"]
                color = edge["node"]["color"] or "#8B949E"
                size = edge["size"]
                if name not in langs:
                    langs[name] = {"size": 0, "color": color}
                langs[name]["size"] += size
        
        sorted_langs = sorted(langs.items(), key=lambda x: x[1]["size"], reverse=True)[:5]
        total_lang_size = sum(x[1]["size"] for x in sorted_langs) or 1
        
        lang_stats = []
        for name, data in sorted_langs:
            lang_stats.append({
                "name": name,
                "color": data["color"],
                "percent": (data["size"] / total_lang_size) * 100
            })
            
        return {
            "total_contribs": total_contribs,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "stars": total_stars,
            "repos": total_repos,
            "prs": user["pullRequests"]["totalCount"],
            "issues": user["issues"]["totalCount"],
            "followers": user["followers"]["totalCount"],
            "languages": lang_stats
        }
        
    except Exception as e:
        print(f"[ERROR] Exception fetching data: {e}")
        return get_mock_data()


def get_mock_data():
    return {
        "total_contribs": 1452,
        "current_streak": 12,
        "longest_streak": 45,
        "stars": 128,
        "repos": 34,
        "prs": 56,
        "issues": 24,
        "followers": 89,
        "languages": [
            {"name": "Python", "color": "#3572A5", "percent": 45.2},
            {"name": "TypeScript", "color": "#3178C6", "percent": 28.5},
            {"name": "C++", "color": "#f34b7d", "percent": 15.0},
            {"name": "Dart", "color": "#00B4AB", "percent": 8.3},
            {"name": "Shell", "color": "#89e051", "percent": 3.0}
        ]
    }


def generate_telemetry_svg(config, data):
    d = config["design"]
    W = 880
    H = 120
    r = d["card_radius"]
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="{W}" y2="{H}">
      <stop offset="0%" stop-color="{d['bg_secondary']}"/>
      <stop offset="100%" stop-color="{d['bg_card']}"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="{r}" fill="url(#bg)" stroke="{d['border']}" stroke-width="0.5"/>
  <rect width="{W}" height="2" rx="{r}" fill="{d['accent_cyan']}" opacity="0.4"/>
  
  <g transform="translate(0, 0)">
    <!-- Contribs -->
    <text x="{W/6}" y="45" text-anchor="middle" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="10" letter-spacing="1.5">TOTAL CONTRIBUTIONS</text>
    <text x="{W/6}" y="85" text-anchor="middle" fill="{d['text_primary']}" font-family="'Inter','Segoe UI',sans-serif" font-size="32" font-weight="600">{data['total_contribs']:,}</text>
    
    <!-- Sep 1 -->
    <line x1="{W/3}" y1="30" x2="{W/3}" y2="90" stroke="{d['border_subtle']}" stroke-width="0.5"/>
    
    <!-- Current Streak -->
    <text x="{W/2}" y="45" text-anchor="middle" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="10" letter-spacing="1.5">CURRENT STREAK</text>
    <text x="{W/2}" y="85" text-anchor="middle" fill="{d['accent_cyan']}" font-family="'Inter','Segoe UI',sans-serif" font-size="32" font-weight="600">{data['current_streak']} days</text>
    
    <!-- Sep 2 -->
    <line x1="{W*2/3}" y1="30" x2="{W*2/3}" y2="90" stroke="{d['border_subtle']}" stroke-width="0.5"/>
    
    <!-- Longest Streak -->
    <text x="{W*5/6}" y="45" text-anchor="middle" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="10" letter-spacing="1.5">LONGEST STREAK</text>
    <text x="{W*5/6}" y="85" text-anchor="middle" fill="{d['text_primary']}" font-family="'Inter','Segoe UI',sans-serif" font-size="32" font-weight="600">{data['longest_streak']} days</text>
  </g>
</svg>'''
    (GEN_DIR / "github-telemetry.svg").write_text(svg, encoding="utf-8")


def generate_stats_svg(config, data):
    d = config["design"]
    W, H = 432, 200
    r = d["card_radius"]
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" rx="{r}" fill="{d['bg_secondary']}" stroke="{d['border']}" stroke-width="0.5"/>
  <text x="24" y="32" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="2">GITHUB.STATISTICS</text>
  <line x1="24" y1="44" x2="{W-24}" y2="44" stroke="{d['border_subtle']}" stroke-width="0.5"/>
'''
    
    items = [
        ("Total Stars", data["stars"], d["accent_cyan"]),
        ("Total Commits", data["total_contribs"], d["accent_blue"]),
        ("Pull Requests", data["prs"], d["accent_violet"]),
        ("Issues", data["issues"], "#F78C6C"),
        ("Repositories", data["repos"], d["text_secondary"]),
    ]
    
    y = 75
    for label, value, color in items:
        svg += f'''  <circle cx="32" cy="{y-4}" r="3" fill="{color}" opacity="0.8"/>
  <text x="48" y="{y}" fill="{d['text_secondary']}" font-family="'SF Mono',monospace" font-size="11" letter-spacing="0.5">{esc(label)}</text>
  <text x="{W-24}" y="{y}" text-anchor="end" fill="{d['text_primary']}" font-family="'SF Mono',monospace" font-size="11" font-weight="600">{value:,}</text>
'''
        y += 28

    svg += '</svg>'
    (GEN_DIR / "github-stats.svg").write_text(svg, encoding="utf-8")


def generate_languages_svg(config, data):
    d = config["design"]
    W, H = 432, 200
    r = d["card_radius"]
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" rx="{r}" fill="{d['bg_secondary']}" stroke="{d['border']}" stroke-width="0.5"/>
  <text x="24" y="32" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="9" letter-spacing="2">LANGUAGE.DISTRIBUTION</text>
  <line x1="24" y1="44" x2="{W-24}" y2="44" stroke="{d['border_subtle']}" stroke-width="0.5"/>
'''
    
    # Draw progress bar
    bar_y = 70
    bar_h = 10
    bar_w = W - 48
    svg += f'''  <rect x="24" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5" fill="{d['bg_card']}"/>
'''
    
    curr_x = 24
    for idx, lang in enumerate(data["languages"]):
        width = (lang["percent"] / 100.0) * bar_w
        if width > 0:
            rad = "5" if idx == 0 else ("5" if idx == len(data["languages"])-1 else "0")
            # Simple SVG doesn't do distinct corner radius easily on rects, so we clip path it
            svg += f'''  <rect x="{curr_x}" y="{bar_y}" width="{width}" height="{bar_h}" fill="{lang['color']}"/>
'''
            curr_x += width
            
    # Add a clip path over the bar to round it
    svg += f'''  <rect x="24" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5" fill="none" stroke="{d['bg_secondary']}" stroke-width="2"/>
'''
    
    # Draw legend
    y = 110
    x = 24
    for idx, lang in enumerate(data["languages"]):
        if idx == 3: # new column
            x = W / 2 + 10
            y = 110
            
        svg += f'''  <circle cx="{x + 4}" cy="{y - 3}" r="4" fill="{lang['color']}"/>
  <text x="{x + 14}" y="{y + 1}" fill="{d['text_secondary']}" font-family="'SF Mono',monospace" font-size="10">{esc(lang['name'])}</text>
  <text x="{x + 110}" y="{y + 1}" text-anchor="end" fill="{d['text_muted']}" font-family="'SF Mono',monospace" font-size="10">{lang['percent']:.1f}%</text>
'''
        y += 24

    svg += '</svg>'
    (GEN_DIR / "github-languages.svg").write_text(svg, encoding="utf-8")


def main():
    config = load_config()
    username = config["identity"]["username"]
    
    print("=" * 48)
    print(f" Fetching GitHub data for {username}...")
    print("=" * 48)
    
    data = fetch_github_data(username)
    
    generate_telemetry_svg(config, data)
    print(f"[OK] Telemetry SVG: assets/generated/github-telemetry.svg")
    
    generate_stats_svg(config, data)
    print(f"[OK] Stats SVG: assets/generated/github-stats.svg")
    
    generate_languages_svg(config, data)
    print(f"[OK] Languages SVG: assets/generated/github-languages.svg")
    
if __name__ == "__main__":
    main()
