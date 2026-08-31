"""
GitHub Data Fetcher — Phase 6
==============================
Central data pipeline: fetches GitHub profile data via GraphQL API
and writes normalized JSON to data/github_profile.json.

Modes:
  --ci    CI mode. Real API data is mandatory. No mock fallback.
          Exits non-zero on any failure. Preserves last-known-good files.
  (none)  Local dev mode. Falls back gracefully if GITHUB_TOKEN is unset.

Usage:
    python scripts/fetch_github_data.py          # local dev
    python scripts/fetch_github_data.py --ci      # CI / GitHub Actions
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
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
        stargazerCount
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


def fetch_live_data(username, ci_mode=False):
    """Fetch real GitHub data via GraphQL API."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        if ci_mode:
            print("[FATAL] GITHUB_TOKEN not set. CI mode requires a valid token.")
            sys.exit(1)
        print("[WARN] GITHUB_TOKEN not set — skipping API fetch (local dev mode).")
        return None

    if requests is None:
        if ci_mode:
            print("[FATAL] 'requests' library not installed. CI mode requires it.")
            sys.exit(1)
        print("[WARN] 'requests' not installed — skipping API fetch.")
        return None

    headers = {
        "Authorization": f"bearer {token}",
        "Accept": "application/json",
    }

    try:
        res = requests.post(
            "https://api.github.com/graphql",
            json={"query": GRAPHQL_QUERY, "variables": {"login": username}},
            headers=headers,
            timeout=30,
        )
        if res.status_code != 200:
            print(f"[ERROR] GitHub API HTTP {res.status_code}")
            print(f"        Response: {res.text[:500]}")
            return None

        body = res.json()
        if "errors" in body:
            print(f"[WARN] GraphQL errors returned: {body['errors']}")
            # Proceed to check if partial data is available


        user_data = body.get("data", {}).get("user")
        if not user_data:
            print("[ERROR] GraphQL returned no user data.")
            return None

        return user_data

    except Exception as e:
        print(f"[ERROR] Exception during fetch: {e}")
        return None


def fetch_stars_rest(username, token):
    """Fallback REST API call to fetch aggregate star count if GraphQL fails due to permissions."""
    url = f"https://api.github.com/users/{username}/repos?per_page=100"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        repos = res.json()
        total_stars = sum(r.get("stargazers_count", 0) for r in repos)
        print(f"[INFO] STARS SOURCE: REST repository count ({total_stars})")
        return total_stars
    except Exception as e:
        print(f"[WARN] STARS SOURCE: unavailable. REST fallback failed: {e}")
        return None


def validate_profile_data(profile):
    """Strictly validate normalized GitHub data before saving."""
    if not profile.get("username"):
        raise ValueError("Username is empty or missing")
    if not isinstance(profile.get("total_contributions"), int) or profile["total_contributions"] < 0:
        raise ValueError(f"Invalid total_contributions: {profile.get('total_contributions')}")
    if not isinstance(profile.get("repositories"), int) or profile["repositories"] < 0:
        raise ValueError(f"Invalid repositories count: {profile.get('repositories')}")
    if not isinstance(profile.get("weekly_activity"), list) or len(profile["weekly_activity"]) == 0:
        raise ValueError("weekly_activity is empty or not a list")
    if not isinstance(profile.get("languages"), list):
        raise ValueError("languages is not a list")

    # Check calendar structure basic validity
    for week in profile["weekly_activity"]:
        if "contributions" not in week or "week_start" not in week:
            raise ValueError("Malformed weekly_activity entry")

    # Verify dates are present and parseable
    latest_date = profile["weekly_activity"][-1].get("week_start", "")
    if not latest_date or len(latest_date) < 10:
        raise ValueError(f"Latest week_start is missing or malformed: '{latest_date}'")

    return True


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
    
    stars_available = True
    total_stars = 0
    for r in repos:
        if "stargazerCount" not in r:
            stars_available = False
            total_stars = None
            break
        total_stars += r.get("stargazerCount", 0)
        
    if stars_available:
        print(f"[INFO] STARS SOURCE: GraphQL stargazerCount ({total_stars})")
    else:
        print("[WARN] STARS SOURCE: GraphQL stargazerCount unavailable. Will fallback to REST if possible.")

    total_forks = sum(r.get("forkCount", 0) for r in repos)

    # Find latest contribution date
    latest_date = ""
    for day in reversed(days):
        if day["contributionCount"] > 0:
            latest_date = day["date"]
            break

    return {
        "username": username,
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_contributions": calendar["totalContributions"],
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "latest_contribution_date": latest_date,
        "repositories": user_data["repositories"]["totalCount"],
        "stars": total_stars,
        "stars_available": True,
        "forks": total_forks,
        "followers": user_data["followers"]["totalCount"],
        "pull_requests": user_data["pullRequests"]["totalCount"],
        "issues": user_data["issues"]["totalCount"],
        "weekly_activity": compute_weekly_activity(weeks),
        "languages": compute_languages(repos),
    }


def compute_data_hash(profile_dict):
    """Compute deterministic SHA256 hash of normalized profile data."""
    canonical = json.dumps(profile_dict, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub profile data")
    parser.add_argument("--ci", action="store_true", help="CI mode: require real API data, fail on error")
    parser.add_argument("--debug", action="store_true", help="Print detailed diagnostic info")
    args = parser.parse_args()

    ci_mode = args.ci or os.environ.get("GITHUB_ACTIONS") == "true"

    config = load_config()
    username = config["identity"]["username"]

    print("=" * 48)
    print(f"  Fetching GitHub data for: {username}")
    print(f"  Mode: {'CI' if ci_mode else 'LOCAL DEV'}")
    print("=" * 48)

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    user_data = fetch_live_data(username, ci_mode=ci_mode)

    if not user_data:
        print("[ERROR] Failed to fetch live data from GitHub API.")
        if ci_mode:
            print("[FATAL] CI mode — cannot proceed without live data.")
            if DATA_PATH.exists():
                print("[INFO] Last-known-good data file preserved (NOT overwritten).")
            sys.exit(1)
        else:
            if DATA_PATH.exists():
                print("[INFO] Preserving existing data file (local dev mode).")
            return

    try:
        print("[INFO] Normalizing API response...")
        profile = normalize(username, raw_data)
        
        if not profile["stars_available"]:
            print("[INFO] STARS SOURCE: Attempting REST fallback for stars.")
            rest_stars = fetch_stars_rest(username, token)
            if rest_stars is not None:
                profile["stars"] = rest_stars
                profile["stars_available"] = True
            else:
                profile["stars"] = None
                profile["stars_available"] = False
        validate_profile_data(profile)
        print("[OK] Data validation passed.")
    except Exception as e:
        print(f"[ERROR] Data normalization/validation failed: {e}")
        if ci_mode:
            print("[FATAL] CI mode — invalid data. Preserving last-known-good.")
            sys.exit(1)
        else:
            if DATA_PATH.exists():
                print("[INFO] Preserving existing data file.")
            return

    data_hash = compute_data_hash(profile)

    # Atomic write: write to temp file, then move
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json", dir=str(DATA_DIR))
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
            json.dump(profile, tmp_f, indent=2, ensure_ascii=False)

        # Validate the temp file is valid JSON
        with open(tmp_path, "r", encoding="utf-8") as check_f:
            json.load(check_f)

        # Atomic replace
        tmp_path_obj = Path(tmp_path)
        tmp_path_obj.replace(DATA_PATH)
    except Exception as e:
        print(f"[ERROR] Atomic write failed: {e}")
        if ci_mode:
            sys.exit(1)
        return

    print(f"[OK] Data written: {DATA_PATH}")
    print(f"  -> Contributions: {profile['total_contributions']}")
    print(f"  -> Repos:         {profile['repositories']}")
    print(f"  -> Stars:         {profile['stars'] if profile['stars_available'] else 'unavailable'}")
    print(f"  -> Streak:        {profile['current_streak']}d (longest: {profile['longest_streak']}d)")
    print(f"  -> Languages:     {len(profile['languages'])}")
    print(f"  -> Latest Date:   {profile.get('latest_contribution_date', 'N/A')}")
    print(f"  -> Data Hash:     {data_hash[:8]}")
    print(f"  -> Generated At:  {profile['generated_at']}")

    if args.debug:
        print()
        print("=" * 48)
        print("  DEBUG DIAGNOSTICS")
        print("=" * 48)
        print(f"  USERNAME:               {profile['username']}")
        print(f"  FETCH TIME:             {profile['generated_at']}")
        print(f"  TOTAL CONTRIBUTIONS:    {profile['total_contributions']}")
        print(f"  LATEST CONTRIBUTION:    {profile.get('latest_contribution_date', 'N/A')}")
        print(f"  CURRENT STREAK:         {profile['current_streak']}d")
        print(f"  LONGEST STREAK:         {profile['longest_streak']}d")
        print(f"  REPOSITORIES:           {profile['repositories']}")
        print(f"  STARS:                  {profile['stars'] if profile['stars_available'] else 'unavailable'}")
        print(f"  FOLLOWERS:              {profile['followers']}")
        print(f"  LANGUAGES:              {len(profile['languages'])}")
        print(f"  WEEKLY ACTIVITY WEEKS:  {len(profile['weekly_activity'])}")
        print(f"  DATA HASH (full):       {data_hash}")
        print(f"  DATA HASH (short):      {data_hash[:8]}")


if __name__ == "__main__":
    main()
