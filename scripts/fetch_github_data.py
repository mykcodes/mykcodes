"""
GitHub Data Fetcher
====================
Central data pipeline: fetches GitHub profile data via GraphQL API
and writes normalized JSON to data/github_profile.json.

Falls back gracefully to mock data if GITHUB_TOKEN is unavailable.
Preserves the last known data file on API failure.

Usage:
    python scripts/fetch_github_data.py
"""

import os
import json
import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
DATA_DIR = ROOT / "data"
DATA_PATH = DATA_DIR / "github_profile.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, orderBy: {field: STARGAZERS, direction: DESC}) {
      totalCount
      nodes {
        stargazers { totalCount }
        forkCount
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


def fetch_live_data(username):
    """Fetch real GitHub data via GraphQL API."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[WARN] GITHUB_TOKEN not set -- using mock data.")
        return None

    if requests is None:
        print("[WARN] 'requests' not installed -- using mock data.")
        return None

    headers = {"Authorization": f"bearer {token}"}

    try:
        res = requests.post(
            "https://api.github.com/graphql",
            json={"query": GRAPHQL_QUERY, "variables": {"login": username}},
            headers=headers,
            timeout=30,
        )
        if res.status_code != 200:
            print(f"[ERROR] GitHub API HTTP {res.status_code}")
            return None

        body = res.json()
        if "errors" in body:
            print(f"[ERROR] GraphQL errors: {body['errors']}")
            return None

        return body["data"]["user"]

    except Exception as e:
        print(f"[ERROR] Exception during fetch: {e}")
        return None


def compute_streaks(days):
    """Calculate current and longest contribution streaks."""
    current_streak = 0
    longest_streak = 0
    temp = 0

    for day in days:
        if day["contributionCount"] > 0:
            temp += 1
            longest_streak = max(longest_streak, temp)
        else:
            temp = 0

    # Current streak — walk backwards from today
    for day in reversed(days):
        if day["contributionCount"] > 0:
            current_streak += 1
        else:
            break

    return current_streak, longest_streak


def compute_weekly_activity(weeks):
    """Compute weekly contribution totals for the activity chart."""
    weekly = []
    for week in weeks:
        total = sum(d["contributionCount"] for d in week["contributionDays"])
        start_date = week["contributionDays"][0]["date"] if week["contributionDays"] else ""
        weekly.append({"week_start": start_date, "contributions": total})
    return weekly


def compute_languages(repos):
    """Aggregate language usage across all repos."""
    langs = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            color = edge["node"]["color"] or "#8B949E"
            size = edge["size"]
            if name not in langs:
                langs[name] = {"size": 0, "color": color}
            langs[name]["size"] += size

    sorted_langs = sorted(langs.items(), key=lambda x: x[1]["size"], reverse=True)[:8]
    total = sum(x[1]["size"] for x in sorted_langs) or 1

    return [
        {"name": name, "color": data["color"], "percent": round((data["size"] / total) * 100, 1)}
        for name, data in sorted_langs
    ]


def normalize(username, user_data):
    """Normalize raw GitHub API data into the profile JSON schema."""
    calendar = user_data["contributionsCollection"]["contributionCalendar"]
    weeks = calendar["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    repos = user_data["repositories"]["nodes"]

    current_streak, longest_streak = compute_streaks(days)
    total_stars = sum(r["stargazers"]["totalCount"] for r in repos)
    total_forks = sum(r.get("forkCount", 0) for r in repos)

    return {
        "username": username,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total_contributions": calendar["totalContributions"],
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "repositories": user_data["repositories"]["totalCount"],
        "stars": total_stars,
        "forks": total_forks,
        "followers": user_data["followers"]["totalCount"],
        "pull_requests": user_data["pullRequests"]["totalCount"],
        "issues": user_data["issues"]["totalCount"],
        "weekly_activity": compute_weekly_activity(weeks),
        "languages": compute_languages(repos),
    }


def get_mock_data(username):
    """Generate realistic mock data for local development."""
    import math

    # Generate a plausible weekly activity curve
    weekly = []
    for i in range(52):
        # Simulate natural contribution rhythm
        base = 8 + 6 * math.sin(i * 0.12) + 4 * math.cos(i * 0.25)
        val = max(0, int(base + (i % 7) * 0.5))
        weekly.append({"week_start": f"2025-{1 + (i // 4) % 12:02d}-{1 + (i % 4) * 7:02d}", "contributions": val})

    return {
        "username": username,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total_contributions": sum(w["contributions"] for w in weekly),
        "current_streak": 12,
        "longest_streak": 45,
        "repositories": 34,
        "stars": 128,
        "forks": 18,
        "followers": 89,
        "pull_requests": 56,
        "issues": 24,
        "weekly_activity": weekly,
        "languages": [
            {"name": "Python", "color": "#3572A5", "percent": 42.1},
            {"name": "TypeScript", "color": "#3178C6", "percent": 22.8},
            {"name": "C++", "color": "#f34b7d", "percent": 14.5},
            {"name": "Dart", "color": "#00B4AB", "percent": 9.2},
            {"name": "JavaScript", "color": "#f1e05a", "percent": 6.1},
            {"name": "HTML", "color": "#e34c26", "percent": 3.4},
            {"name": "CSS", "color": "#563d7c", "percent": 1.9},
        ],
    }


def main():
    config = load_config()
    username = config["identity"]["username"]

    print("=" * 48)
    print(f"  Fetching GitHub data for: {username}")
    print("=" * 48)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    user_data = fetch_live_data(username)

    if user_data:
        profile = normalize(username, user_data)
        print("[OK] Live GitHub data fetched successfully.")
    else:
        # Check if we have a cached version
        if DATA_PATH.exists():
            print("[INFO] Retaining last known data file.")
            try:
                existing = json.loads(DATA_PATH.read_text(encoding="utf-8"))
                print(f"  -> Last generated: {existing.get('generated_at', 'unknown')}")
                return DATA_PATH
            except Exception:
                pass

        print("[INFO] Using mock data for local development.")
        profile = get_mock_data(username)

    DATA_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Data written: {DATA_PATH}")
    print(f"  -> Contributions: {profile['total_contributions']}")
    print(f"  -> Repos: {profile['repositories']}")
    print(f"  -> Stars: {profile['stars']}")
    print(f"  -> Languages: {len(profile['languages'])}")

    return DATA_PATH


if __name__ == "__main__":
    main()
