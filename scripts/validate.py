"""
Comprehensive Validation Script
================================
Validates the entire profile system for production readiness.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
issues = {"errors": [], "warnings": [], "info": []}


def check(category, msg):
    issues[category].append(msg)


def validate_config():
    """Validate config/profile.json."""
    cfg_path = ROOT / "config" / "profile.json"
    if not cfg_path.exists():
        check("errors", "config/profile.json missing")
        return None

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        check("errors", f"config/profile.json invalid JSON: {e}")
        return None

    check("info", "config/profile.json: valid JSON")

    # Check for placeholder values
    cfg_text = cfg_path.read_text(encoding="utf-8")
    placeholders = ["YOUR_GITHUB_USERNAME", "YOUR_PORTFOLIO_URL", "YOUR_LINKEDIN",
                     "YOUR_INSTAGRAM", "YOUR_FACEBOOK", "your.email@example.com"]
    for ph in placeholders:
        if ph in cfg_text:
            check("warnings", f"Config placeholder: {ph}")

    # Check required keys
    required = ["identity", "status", "links", "projects", "tech_stack", "design", "animation"]
    for key in required:
        if key not in config:
            check("errors", f"Config missing key: {key}")

    return config


def validate_data():
    """Validate data/github_profile.json."""
    data_path = ROOT / "data" / "github_profile.json"
    if not data_path.exists():
        check("warnings", "data/github_profile.json missing — run fetch_github_data.py")
        return

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        check("errors", f"data/github_profile.json invalid JSON: {e}")
        return

    check("info", f"data/github_profile.json: valid JSON ({data_path.stat().st_size} bytes)")

    required = ["username", "total_contributions", "repositories", "stars", "languages", "weekly_activity"]
    for key in required:
        if key not in data:
            check("warnings", f"Data missing key: {key}")

    if "generated_at" in data:
        check("info", f"Data generated at: {data['generated_at']}")


def validate_assets():
    """Validate all generated assets exist and are non-empty."""
    gen = ROOT / "assets" / "generated"
    required_gen = [
        "hero.svg", "stack.svg", "footer.svg",
        "header-telemetry.svg", "header-stats.svg", "header-toolkit.svg",
        "header-contribution.svg", "header-projects.svg", "header-connect.svg",
        "github-dashboard.svg", "github-languages.svg",
        "btn-portfolio.svg", "btn-linkedin.svg", "btn-instagram.svg",
        "btn-facebook.svg", "btn-email.svg", "profile-views.svg",
    ]

    for f in required_gen:
        path = gen / f
        if path.exists():
            size = path.stat().st_size
            if size == 0:
                check("errors", f"Empty: assets/generated/{f}")
            elif f.endswith(".svg"):
                content = path.read_text(encoding="utf-8")
                if "<svg" not in content:
                    check("errors", f"Invalid SVG: assets/generated/{f}")
                else:
                    check("info", f"assets/generated/{f}: {size} bytes OK")
            else:
                check("info", f"assets/generated/{f}: {size} bytes")
        else:
            check("errors", f"Missing: assets/generated/{f}")

    # Portrait
    portrait = gen / "portrait-animation.gif"
    if portrait.exists():
        size_kb = portrait.stat().st_size / 1024
        check("info", f"Portrait animation: {size_kb:.0f} KB")
        if size_kb > 5000:
            check("warnings", f"Portrait GIF large: {size_kb:.0f} KB (target < 5000 KB)")
    else:
        check("warnings", "Portrait animation not found")

    # Project cards
    proj_dir = ROOT / "assets" / "projects"
    for card in ["astra.svg", "aerotwin.svg", "saraswati.svg", "portfolio.svg"]:
        path = proj_dir / card
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if "<svg" not in content:
                check("errors", f"Invalid SVG: assets/projects/{card}")
            else:
                check("info", f"assets/projects/{card}: OK")
        else:
            check("errors", f"Missing: assets/projects/{card}")


def validate_readme():
    """Validate README.md references and structure."""
    readme = ROOT / "README.md"
    if not readme.exists():
        check("errors", "README.md missing")
        return

    content = readme.read_text(encoding="utf-8")

    # Check for merge conflict markers
    if "<<<<<<" in content or ">>>>>>>" in content:
        check("errors", "README.md contains merge conflict markers")

    # Check for old external widgets
    if "github-readme-stats" in content:
        check("warnings", "README.md still references github-readme-stats external widget")
    if "streak-stats.demolab.com" in content:
        check("warnings", "README.md still references streak-stats external widget")

    # Check image references
    img_refs = re.findall(r'src=["\']([^"\']+)["\']', content)
    for ref in img_refs:
        if ref.startswith("http"):
            continue
        # Strip query params like ?v=hash
        clean_ref = ref.split("?")[0]
        path = ROOT / clean_ref
        if not path.exists():
            check("errors", f"Broken image ref: {ref}")
        else:
            check("info", f"Image ref OK: {ref}")

    check("info", f"README.md: {len(content)} bytes, {content.count(chr(10))} lines")


def validate_workflows():
    """Validate GitHub Actions workflows."""
    wf_dir = ROOT / ".github" / "workflows"
    if not wf_dir.exists():
        check("errors", ".github/workflows/ missing")
        return

    for yml in wf_dir.glob("*.yml"):
        content = yml.read_text(encoding="utf-8")
        if not content.strip():
            check("errors", f"Empty workflow: {yml.name}")
        elif "name:" not in content:
            check("warnings", f"Workflow missing 'name:': {yml.name}")
        elif "on:" not in content:
            check("warnings", f"Workflow missing 'on:': {yml.name}")
        else:
            # Check for permissions
            if "contents: write" in content:
                check("info", f"Workflow OK (write perms): {yml.name}")
            else:
                check("warnings", f"Workflow may lack write permissions: {yml.name}")


def validate_python():
    """Basic Python syntax check."""
    for py in (ROOT / "scripts").glob("*.py"):
        try:
            with open(py, "r", encoding="utf-8") as f:
                compile(f.read(), py.name, "exec")
            check("info", f"Python syntax OK: {py.name}")
        except SyntaxError as e:
            check("errors", f"Python syntax error in {py.name}: {e}")


def main():
    print()
    print("  VALIDATION SUITE")
    print("  " + "=" * 40)

    validate_config()
    validate_data()
    validate_assets()
    validate_readme()
    validate_workflows()
    validate_python()

    print()

    if issues["errors"]:
        print(f"  ERRORS ({len(issues['errors'])}):")
        for e in issues["errors"]:
            print(f"    x {e}")
        print()

    if issues["warnings"]:
        print(f"  WARNINGS ({len(issues['warnings'])}):")
        for w in issues["warnings"]:
            print(f"    ! {w}")
        print()

    print(f"  INFO ({len(issues['info'])}):")
    for i in issues["info"]:
        print(f"    . {i}")

    print()
    if issues["errors"]:
        print("  RESULT: FAIL")
    elif issues["warnings"]:
        print("  RESULT: PASS (with warnings)")
    else:
        print("  RESULT: PASS")
    print()


if __name__ == "__main__":
    main()
