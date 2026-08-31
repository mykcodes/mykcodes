"""
Profile Builder — Phase 6
===========================
Orchestrates the complete build pipeline:
1. Fetch GitHub data
2. Generate portrait animation (if source images exist)
3. Generate SVG assets (hero, stack, project cards, buttons)
4. Generate GitHub dashboard (with freshness + hash metadata)
5. Generate language visualization
6. Validate all references
7. Update README cache-busting version (deterministic, data-hash based)

Run: python scripts/build_profile.py
"""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"
DATA_PATH = ROOT / "data" / "github_profile.json"
README_PATH = ROOT / "README.md"
DASHBOARD_PATH = ROOT / "assets" / "generated" / "github-dashboard.svg"

sys.path.insert(0, str(ROOT / "scripts"))


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_data_hash():
    """Compute deterministic SHA256 hash of normalized profile data."""
    content = DATA_PATH.read_text(encoding="utf-8")
    data = json.loads(content)
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_svg_hash():
    """Compute SHA256 hash of the generated dashboard SVG."""
    content = DASHBOARD_PATH.read_bytes()
    return hashlib.sha256(content).hexdigest()


def update_readme_cache_version(data_hash_short):
    """Update README.md dashboard image reference with cache-busting version.

    Uses the data hash (not timestamp) so:
    - same data = same version = no commit churn
    - new data  = new version  = forces GitHub CDN refresh
    """
    if not README_PATH.exists():
        print("[WARN] README.md not found — skipping cache-bust update.")
        return False

    readme_text = README_PATH.read_text(encoding="utf-8")

    # Match: github-dashboard.svg or github-dashboard.svg?v=ANYTHING
    pattern = r'(github-dashboard\.svg)(\?v=[a-f0-9]+)?'
    replacement = rf'\1?v={data_hash_short}'

    new_text, count = re.subn(pattern, replacement, readme_text)

    if count == 0:
        print("[WARN] No github-dashboard.svg reference found in README.md.")
        return False

    if new_text == readme_text:
        print("[INFO] README cache version unchanged (data hash identical).")
        return False

    README_PATH.write_text(new_text, encoding="utf-8")
    print(f"[OK] README cache version updated: ?v={data_hash_short}")
    return True


def validate():
    """Validate the project for common issues."""
    config = load_config()
    errors = []
    warnings = []

    # Check generated assets
    gen_files = [
        "hero.svg", "stack.svg", "footer.svg",
        "header-telemetry.svg", "header-stats.svg", "header-toolkit.svg",
        "header-contribution.svg", "header-projects.svg", "header-connect.svg",
        "github-dashboard.svg", "github-languages.svg",
        "btn-portfolio.svg", "btn-linkedin.svg", "btn-instagram.svg",
        "btn-facebook.svg", "btn-email.svg", "profile-views.svg",
    ]
    for f in gen_files:
        path = ROOT / "assets" / "generated" / f
        if not path.exists():
            errors.append(f"Missing: assets/generated/{f}")
        elif path.stat().st_size == 0:
            errors.append(f"Empty: assets/generated/{f}")

    # Portrait
    if not (ROOT / "assets" / "generated" / "portrait-animation.gif").exists():
        warnings.append("Portrait animation not generated")
        warnings.append("  -> Place portrait.png + logo.png in assets/source/ and run generate_portrait.py")

    # Project cards
    for proj in config["projects"]:
        path = ROOT / "assets" / "projects" / f"{proj['id']}.svg"
        if not path.exists():
            errors.append(f"Missing project card: assets/projects/{proj['id']}.svg")

    # Data file
    if not DATA_PATH.exists():
        warnings.append("data/github_profile.json not found — run fetch_github_data.py")
    else:
        try:
            data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            if "username" not in data:
                warnings.append("data/github_profile.json missing 'username'")
        except json.JSONDecodeError:
            errors.append("data/github_profile.json is invalid JSON")

    # Dashboard SVG metadata validation
    if DASHBOARD_PATH.exists():
        svg_text = DASHBOARD_PATH.read_text(encoding="utf-8")
        if "data-hash" not in svg_text:
            warnings.append("Dashboard SVG missing data-hash attribute")
        if "SYNCED" not in svg_text:
            warnings.append("Dashboard SVG missing SYNCED freshness marker")

    # README checks
    if README_PATH.exists():
        text = README_PATH.read_text(encoding="utf-8")
        if "<<<<<<" in text or ">>>>>>>" in text:
            errors.append("README.md contains merge conflict markers")
        if "github-readme-stats" in text:
            warnings.append("README.md still references github-readme-stats external widget")
        if "streak-stats.demolab.com" in text:
            warnings.append("README.md still references streak-stats external widget")
        # Check cache-busting is present
        if "github-dashboard.svg?v=" not in text:
            warnings.append("README.md dashboard reference missing cache-busting ?v= parameter")

    # YAML syntax check
    for yml in (ROOT / ".github" / "workflows").glob("*.yml"):
        try:
            content = yml.read_text(encoding="utf-8")
            if not content.strip():
                errors.append(f"Empty workflow: {yml.name}")
        except Exception as e:
            errors.append(f"Cannot read {yml.name}: {e}")

    # Report
    print("\n" + "=" * 48)
    print(" VALIDATION REPORT")
    print("=" * 48)

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    x {e}")

    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"    ! {w}")

    if not errors and not warnings:
        print("\n  All checks passed.")

    return len(errors) == 0


def main():
    print()
    print("  MAYANK.SYSTEM -- Profile Builder v3")
    print("  " + "-" * 38)
    print()

    # Step 1: Fetch GitHub data
    print("[1/7] Fetching GitHub data...")
    try:
        from fetch_github_data import main as fetch_data
        fetch_data()
    except SystemExit:
        print("  [WARN] Data fetch exited (expected in local dev without token).")
        print("  Continuing with existing data if available...")
    except Exception as e:
        print(f"  [WARN] Data fetch failed: {e}")
        print("  Continuing with existing data if available...")

    # Step 2: Portrait
    print("\n[2/7] Portrait animation...")
    portrait_src = ROOT / "assets" / "source" / "portrait.png"
    logo_src = ROOT / "assets" / "source" / "logo.png"

    if portrait_src.exists() or logo_src.exists():
        print("       Source images found. Generating...")
        from generate_portrait import generate_portrait_animation
        generate_portrait_animation()
    else:
        print("       No source images. Skipping.")
        print(f"       Place images in: assets/source/")

    # Step 3: Generate SVG assets
    print("\n[3/7] Generating SVG assets...")
    from generate_assets import generate_all
    generate_all()

    # Step 4: Generate GitHub Dashboard
    print("\n[4/7] Generating GitHub Dashboard...")
    try:
        from generate_github_dashboard import generate_dashboard
        generate_dashboard()
    except Exception as e:
        print(f"  [ERROR] Dashboard generation failed: {e}")

    # Step 5: Generate Language Visualization
    print("\n[5/7] Generating Language Visualization...")
    try:
        from generate_languages import generate_languages
        generate_languages()
    except Exception as e:
        print(f"  [WARN] Language generation failed: {e}")

    # Step 6: Validate
    print("\n[6/7] Validating...")
    validate()

    # Step 7: Update README cache-busting version
    print("\n[7/7] Updating README cache version...")
    if DATA_PATH.exists() and DASHBOARD_PATH.exists():
        data_hash = compute_data_hash()
        svg_hash = compute_svg_hash()
        data_hash_short = data_hash[:8]

        print(f"  Data Hash:  {data_hash_short}")
        print(f"  SVG Hash:   {svg_hash[:8]}")

        updated = update_readme_cache_version(data_hash_short)
        if updated:
            print("  README.md updated with new cache version.")
        else:
            print("  README.md cache version unchanged.")
    else:
        print("  [SKIP] Data or dashboard not available.")

    print("\n  Build complete.\n")


if __name__ == "__main__":
    main()
