"""
Profile Builder
===============
Orchestrates the complete build pipeline:
1. Generate SVG assets
2. Generate portrait animation (if source images exist)
3. Build README.md from config + assets
4. Validate all references

Run: python scripts/build_profile.py
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "profile.json"

sys.path.insert(0, str(ROOT / "scripts"))


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_readme(config):
    """Generate README.md from config, replacing placeholders in a template."""
    identity = config["identity"]
    status = config["status"]
    links = config["links"]
    projects = config["projects"]
    
    username = identity["username"]
    
    # Read the README template/current README
    readme_path = ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
    else:
        print("[WARN] README.md not found. Run generate_assets.py first.")
        return
    
    # Replace all username placeholders
    content = content.replace("YOUR_GITHUB_USERNAME", username)
    content = content.replace("YOUR_PORTFOLIO_URL", links.get("portfolio", "").replace("https://", ""))
    content = content.replace("https://linkedin.com/in/YOUR_LINKEDIN", links.get("linkedin", "#"))
    content = content.replace("https://instagram.com/YOUR_INSTAGRAM", links.get("instagram", "#"))
    content = content.replace("https://facebook.com/YOUR_FACEBOOK", links.get("facebook", "#"))
    content = content.replace("your.email@example.com", links.get("email", ""))
    
    # Update project repo links
    for proj in projects:
        old_link = f'{username}/{proj["id"]}'
        new_repo = proj.get("repo", f'{username}/{proj["id"]}')
        content = content.replace(old_link, new_repo)
    
    readme_path.write_text(content, encoding="utf-8")
    print(f"[OK] README.md updated with config values: {readme_path}")


def validate():
    """Validate the project for common issues."""
    config = load_config()
    errors = []
    warnings = []
    
    # Check generated assets
    gen_files = [
        "hero.svg", "stack.svg", "contact.svg", "footer.svg",
        "header-telemetry.svg", "header-stats.svg", "header-toolkit.svg",
        "header-contribution.svg", "header-projects.svg", "header-connect.svg",
    ]
    for f in gen_files:
        if not (ROOT / "assets" / "generated" / f).exists():
            errors.append(f"Missing: assets/generated/{f}")
    
    # Portrait
    if not (ROOT / "assets" / "generated" / "portrait-animation.gif").exists():
        warnings.append("Portrait animation not generated")
        warnings.append("  -> Place portrait.png + logo.png in assets/source/ and run generate_portrait.py")
    
    # Project cards
    for proj in config["projects"]:
        if not (ROOT / "assets" / "projects" / f"{proj['id']}.svg").exists():
            errors.append(f"Missing project card: assets/projects/{proj['id']}.svg")
    
    # README placeholders
    readme = ROOT / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        placeholders = [
            "YOUR_GITHUB_USERNAME", "YOUR_PORTFOLIO_URL", "YOUR_LINKEDIN",
            "YOUR_INSTAGRAM", "YOUR_FACEBOOK",
        ]
        for ph in placeholders:
            if ph in text:
                warnings.append(f"README placeholder: {ph} -> update config/profile.json and rebuild")
    
    # Config placeholders
    cfg_text = CONFIG_PATH.read_text(encoding="utf-8")
    if "YOUR_GITHUB_USERNAME" in cfg_text:
        warnings.append("Config: username not set -> edit config/profile.json")
    
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
    print("  MAYANK.SYSTEM -- Profile Builder")
    print("  " + "-" * 38)
    print()
    
    # Step 1: Portrait (Generate first so it can be embedded in SVG)
    print("[1/4] Portrait animation...")
    portrait_src = ROOT / "assets" / "source" / "portrait.png"
    logo_src = ROOT / "assets" / "source" / "logo.png"
    
    if portrait_src.exists() or logo_src.exists():
        print("       Source images found. Generating...")
        from generate_portrait import generate_portrait_animation
        generate_portrait_animation()
    else:
        print("       No source images. Skipping.")
        print(f"       Place images in: assets/source/")

    # Step 2: Generate SVG assets
    print("\n[2/4] Generating SVG assets...")
    from generate_assets import generate_all
    generate_all()
    
    # Step 3: Fetch GitHub Stats
    print("\n[3/5] Fetching GitHub Stats...")
    from generate_github_stats import main as generate_stats
    generate_stats()
    
    # Step 4: Build README
    print("\n[4/5] Building README.md...")
    config = load_config()
    build_readme(config)
    
    # Step 5: Validate
    print("\n[5/5] Validating...")
    validate()
    
    print("\n  Build complete.\n")


if __name__ == "__main__":
    main()
