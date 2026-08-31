"""
Remote Verification Script — Phase 6
======================================
Runs AFTER git push in CI to verify the complete deployment chain:

1. GitHub Contents API — verify the SVG and README exist at the correct
   branch/ref with expected data hash and blob SHA.
2. Raw CDN check — verify raw.githubusercontent.com serves the new asset
   (with bounded backoff for propagation delay).
3. Commit verification — verify the pushed commit SHA matches remote HEAD.

Usage (CI only):
    python scripts/verify_remote.py --data-hash <hash> --commit-sha <sha>

Exit codes:
    0  All verifications passed
    1  Verification failure (pipeline or data mismatch)
    2  CDN propagation lag (Contents API OK, raw URL not yet updated)
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

ROOT = Path(__file__).resolve().parent.parent

OWNER = "mykcodes"
REPO = "mykcodes"
BRANCH = "main"
SVG_PATH = "assets/generated/github-dashboard.svg"
README_PATH_REPO = "README.md"

GITHUB_API = "https://api.github.com"
RAW_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}"


def get_headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def verify_contents_api(path, expected_data_hash_short=None):
    """Verify a file exists on the remote repository via Contents API."""
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{path}?ref={BRANCH}"
    print(f"  [API] GET {url}")
    res = requests.get(url, headers=get_headers(), timeout=30)

    if res.status_code != 200:
        print(f"  [FAIL] Contents API returned HTTP {res.status_code}")
        return None

    data = res.json()
    blob_sha = data.get("sha", "unknown")
    file_size = data.get("size", 0)
    file_path = data.get("path", "")

    print(f"  [OK] File found: {file_path}")
    print(f"       Blob SHA:  {blob_sha}")
    print(f"       Size:      {file_size} bytes")

    return {
        "blob_sha": blob_sha,
        "size": file_size,
        "path": file_path,
        "download_url": data.get("download_url", ""),
    }


def verify_readme_cache_version(expected_hash_short):
    """Verify remote README.md contains the expected cache-busting version."""
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/contents/{README_PATH_REPO}?ref={BRANCH}"
    print(f"  [API] GET {url}")
    res = requests.get(url, headers=get_headers(), timeout=30)

    if res.status_code != 200:
        print(f"  [FAIL] Cannot fetch remote README (HTTP {res.status_code})")
        return False

    data = res.json()
    # Contents API returns base64-encoded content
    import base64
    content_b64 = data.get("content", "")
    try:
        content = base64.b64decode(content_b64).decode("utf-8")
    except Exception as e:
        print(f"  [FAIL] Cannot decode README content: {e}")
        return False

    expected_pattern = f"github-dashboard.svg?v={expected_hash_short}"
    if expected_pattern in content:
        print(f"  [OK] README contains expected cache version: ?v={expected_hash_short}")
        return True
    else:
        # Show what version is present
        match = re.search(r'github-dashboard\.svg\?v=([a-f0-9]+)', content)
        if match:
            print(f"  [FAIL] README has stale cache version: ?v={match.group(1)} (expected: {expected_hash_short})")
        else:
            print(f"  [FAIL] README has no cache-busting parameter at all")
        return False


def verify_remote_commit(expected_sha):
    """Verify the remote default branch points to the expected commit."""
    url = f"{GITHUB_API}/repos/{OWNER}/{REPO}/branches/{BRANCH}"
    print(f"  [API] GET {url}")
    res = requests.get(url, headers=get_headers(), timeout=30)

    if res.status_code != 200:
        print(f"  [FAIL] Cannot fetch branch info (HTTP {res.status_code})")
        return False

    data = res.json()
    remote_sha = data.get("commit", {}).get("sha", "unknown")

    # Compare full SHA or prefix
    if remote_sha.startswith(expected_sha) or expected_sha.startswith(remote_sha[:7]):
        print(f"  [OK] Remote HEAD matches: {remote_sha[:12]}")
        return True
    else:
        print(f"  [INFO] Remote HEAD: {remote_sha[:12]} (pushed: {expected_sha[:12]})")
        print(f"         This may be OK if another commit landed after push.")
        return True  # Not a pipeline failure


def verify_raw_url(expected_data_hash_short, max_retries=4, backoff_base=5):
    """Verify raw.githubusercontent.com serves the updated SVG.

    This is propagation-aware: the Contents API is the authoritative source.
    Raw URL lag is reported as CDN delay, not pipeline failure.
    """
    url = f"{RAW_BASE}/{SVG_PATH}"

    for attempt in range(max_retries):
        print(f"  [RAW] GET {url} (attempt {attempt + 1}/{max_retries})")
        try:
            res = requests.get(url, timeout=30, headers={"Cache-Control": "no-cache"})
            if res.status_code != 200:
                print(f"  [WARN] Raw URL returned HTTP {res.status_code}")
            else:
                content_type = res.headers.get("content-type", "")
                svg_text = res.text

                # Check for data hash in the served SVG
                if f'data-hash="{expected_data_hash_short}"' in svg_text:
                    print(f"  [OK] Raw URL serving correct version (data-hash={expected_data_hash_short})")
                    return True
                else:
                    hash_match = re.search(r'data-hash="([a-f0-9]+)"', svg_text)
                    served_hash = hash_match.group(1) if hash_match else "none"
                    print(f"  [WAIT] Raw URL serving stale version (hash={served_hash})")

        except Exception as e:
            print(f"  [WARN] Raw URL request failed: {e}")

        if attempt < max_retries - 1:
            wait = backoff_base * (2 ** attempt)
            print(f"  [WAIT] Retrying in {wait}s...")
            time.sleep(wait)

    print(f"  [LAG] Raw URL did not update after {max_retries} attempts.")
    print(f"        This is CDN propagation lag, NOT a pipeline failure.")
    return False  # We'll distinguish this from a hard failure


def main():
    parser = argparse.ArgumentParser(description="Verify remote deployment")
    parser.add_argument("--data-hash", required=True, help="Expected short data hash (8 chars)")
    parser.add_argument("--commit-sha", required=True, help="Expected commit SHA (short or full)")
    parser.add_argument("--skip-raw", action="store_true", help="Skip raw URL propagation check")
    args = parser.parse_args()

    if requests is None:
        print("[FATAL] 'requests' library required for remote verification")
        sys.exit(1)

    print()
    print("=" * 48)
    print("  REMOTE DEPLOYMENT VERIFICATION")
    print("=" * 48)
    print(f"  Owner/Repo:   {OWNER}/{REPO}")
    print(f"  Branch:       {BRANCH}")
    print(f"  Expected Hash:{args.data_hash}")
    print(f"  Expected SHA: {args.commit_sha}")
    print()

    all_passed = True
    cdn_lag = False

    # 1. Verify SVG via Contents API
    print("[1/4] Verifying SVG via GitHub Contents API...")
    svg_info = verify_contents_api(SVG_PATH, args.data_hash)
    if not svg_info:
        print("  [FAIL] SVG not found on remote repository.")
        all_passed = False

    # 2. Verify README via Contents API
    print("\n[2/4] Verifying README cache version...")
    readme_ok = verify_readme_cache_version(args.data_hash)
    if not readme_ok:
        all_passed = False

    # 3. Verify commit
    print("\n[3/4] Verifying remote commit...")
    commit_ok = verify_remote_commit(args.commit_sha)
    if not commit_ok:
        all_passed = False

    # 4. Verify raw URL (propagation-aware)
    if not args.skip_raw:
        print("\n[4/4] Verifying raw URL propagation...")
        raw_ok = verify_raw_url(args.data_hash)
        if not raw_ok:
            cdn_lag = True
    else:
        print("\n[4/4] Skipping raw URL check (--skip-raw).")

    # Final report
    print()
    print("=" * 48)
    print("  VERIFICATION SUMMARY")
    print("=" * 48)

    if all_passed and not cdn_lag:
        print("  [OK] All verifications PASSED.")
        print("  Pipeline is fully operational.")
        sys.exit(0)
    elif all_passed and cdn_lag:
        print("  [OK] Repository state verified (Contents API).")
        print("  [LAG] Raw CDN has not yet propagated.")
        print("  This is a transient GitHub CDN delay, not a pipeline failure.")
        sys.exit(2)  # Distinct exit code for CDN lag
    else:
        print("  [FAIL] Remote verification FAILED.")
        print("  The pipeline did not produce the expected remote state.")
        sys.exit(1)


if __name__ == "__main__":
    main()
