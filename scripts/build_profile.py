"""
Profile Builder
===============
Orchestrates the complete build pipeline:
1. Fetch GitHub data (or use mock)
2. Generate portrait animation (if source images exist)
3. Generate SVG assets (hero, stack, project cards, buttons)
4. Generate GitHub dashboard
5. Generate language visualization
6. Validate all references

Run: python scripts/build_profile.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"

sys.path.insert(0, str(ROOT / "scripts"))


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


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
    data_path = ROOT / "data" / "github_profile.json"
    if not data_path.exists():
        warnings.append("data/github_profile.json not found — run fetch_github_data.py")
    else:
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
            if "username" not in data:
                warnings.append("data/github_profile.json missing 'username'")
        except json.JSONDecodeError:
            errors.append("data/github_profile.json is invalid JSON")

    # README checks
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        # Check for merge conflict markers
        if "<<<<<<" in text or ">>>>>>>" in text:
            errors.append("README.md contains merge conflict markers")
        # Check for old external widgets
        if "github-readme-stats" in text:
            warnings.append("README.md still references github-readme-stats external widget")
        if "streak-stats.demolab.com" in text:
            warnings.append("README.md still references streak-stats external widget")

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
    print("  MAYANK.SYSTEM -- Profile Builder v2")
    print("  " + "-" * 38)
    print()

    # Step 1: Fetch GitHub data
    print("[1/6] Fetching GitHub data...")
    try:
        from fetch_github_data import main as fetch_data
        fetch_data()
    except Exception as e:
        print(f"  [WARN] Data fetch failed: {e}")
        print("  Continuing with existing data if available...")

    # Step 2: Portrait (Generate first so it can be embedded in hero SVG)
    print("\n[2/6] Portrait animation...")
    portrait_src = ROOT / "assets" / "source" / "portrait.png"
    logo_src = ROOT / "assets" / "source" / "logo.png"

    if portrait_src.exists() or logo_src.exists():
        print("       Source images found. Generating...")
        from generate_portrait import generate_portrait_animation
        generate_portrait_animation()
    else:
        print("       No source images. Skipping.")
        print(f"       Place images in: assets/source/")

    # Step 3: Generate SVG assets (hero, stack, projects, buttons, headers)
    print("\n[3/6] Generating SVG assets...")
    from generate_assets import generate_all
    generate_all()

    # Step 4: Generate GitHub Dashboard
    print("\n[4/6] Generating GitHub Dashboard...")
    try:
        from generate_github_dashboard import generate_dashboard
        generate_dashboard()
    except Exception as e:
        print(f"  [WARN] Dashboard generation failed: {e}")

    # Step 5: Generate Language Visualization
    print("\n[5/6] Generating Language Visualization...")
    try:
        from generate_languages import generate_languages
        generate_languages()
    except Exception as e:
        print(f"  [WARN] Language generation failed: {e}")

    # Step 6: Validate
    print("\n[6/7] Validating...")
    validate()
    
    # Step 7: Dynamic Data Test (Part K)
    print("\n[7/7] Running Dynamic Data Change Test...")
    import shutil
    import subprocess
    data_path = ROOT / "data" / "github_profile.json"
    backup_path = ROOT / "data" / "github_profile_backup.json"
    chart_path = ROOT / "assets" / "generated" / "github-dashboard.svg"
    chart_backup = ROOT / "assets" / "generated" / "github-dashboard_backup.svg"
    
    if data_path.exists() and chart_path.exists():
        shutil.copy2(data_path, backup_path)
        shutil.copy2(chart_path, chart_backup)
        try:
            # Modify data temporarily
            with open(data_path, "r", encoding="utf-8") as f:
                test_data = json.load(f)
            # Dramatically alter the activity curve to prove dynamic nature
            if "weekly_activity" in test_data:
                for i in range(len(test_data["weekly_activity"])):
                    test_data["weekly_activity"][i]["contributions"] = 100 if i % 2 == 0 else 0
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(test_data, f)
                
            # Regenerate chart
            from generate_github_dashboard import generate_dashboard
            generate_dashboard()
            
            # Compare output sizes or hashes to prove it changed
            if chart_path.stat().st_size != chart_backup.stat().st_size:
                print("  [OK] Dynamic Data Change Test Passed: SVG geometry successfully altered when underlying dataset changes.")
            else:
                print("  [ERROR] SVG did not appear to change when data changed.")
        finally:
            # Restore
            shutil.copy2(backup_path, data_path)
            shutil.copy2(chart_backup, chart_path)
            backup_path.unlink()
            chart_backup.unlink()

    print("\n  Build complete.\n")



if __name__ == "__main__":
    main()
