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


def validate_assets():
    """Validate all generated assets exist."""
    gen = ROOT / "assets" / "generated"
    required_gen = [
        "hero.svg", "stack.svg", "contact.svg", "footer.svg",
        "header-telemetry.svg", "header-stats.svg", "header-toolkit.svg",
        "header-contribution.svg", "header-projects.svg", "header-connect.svg",
        "github-telemetry.svg", "github-stats.svg", "github-languages.svg",
        "btn-portfolio.svg", "btn-linkedin.svg", "btn-instagram.svg", 
        "btn-facebook.svg", "btn-email.svg"
    ]
    
    for f in required_gen:
        if (gen / f).exists():
            size = (gen / f).stat().st_size
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
        if (proj_dir / card).exists():
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
    
    # Check image references
    img_refs = re.findall(r'src=["\']([^"\']+)["\']', content)
    for ref in img_refs:
        if ref.startswith("http"):
            continue
        path = ROOT / ref
        if not path.exists():
            check("errors", f"Broken image ref: {ref}")
        else:
            check("info", f"Image ref OK: {ref}")
    
    # Check for common issues
    if content.count("<br/>") > 20:
        check("warnings", f"Excessive <br/> tags: {content.count('<br/>')}")
    
    # Check alt text
    imgs_without_alt = re.findall(r'<img[^>]*(?<!alt=")[^>]*/>', content)
    for img in imgs_without_alt:
        if 'alt=' not in img:
            check("warnings", f"Image without alt text: {img[:60]}...")
    
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
            check("info", f"Workflow OK: {yml.name}")


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
