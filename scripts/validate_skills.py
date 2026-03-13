#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
PATH_RE = re.compile(r"`((?:agents|assets|references|scripts)/[^`]+)`")


def list_skill_dirs(selected: Optional[List[str]]) -> List[Path]:
    if selected:
        return [SKILLS_DIR / name for name in selected]
    return sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir() and (path / "SKILL.md").exists())


def require_contains(text: str, needle: str, label: str, errors: List[str]) -> None:
    if needle not in text:
        errors.append(f"missing {label}: {needle}")


def validate_skill(skill_dir: Path) -> List[str]:
    errors: List[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"]

    skill_text = skill_md.read_text()
    require_contains(skill_text, "name:", "frontmatter name", errors)
    require_contains(skill_text, "description:", "frontmatter description", errors)

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        errors.append("missing agents/openai.yaml")
    else:
        openai_text = openai_yaml.read_text()
        for key in ["display_name:", "short_description:", "default_prompt:", "allow_implicit_invocation:"]:
            require_contains(openai_text, key, f"openai.yaml field", errors)

    for rel in PATH_RE.findall(skill_text):
        target = skill_dir / rel
        if not target.exists():
            errors.append(f"broken SKILL.md link: {rel}")

    for subdir in ["references", "assets", "scripts"]:
        path = skill_dir / subdir
        if path.exists() and not path.is_dir():
            errors.append(f"{subdir} exists but is not a directory")

    for script in (skill_dir / "scripts").glob("*.py") if (skill_dir / "scripts").exists() else []:
        try:
            subprocess.run([sys.executable, "-m", "py_compile", str(script)], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            errors.append(f"python syntax error in {script.name}: {exc.stderr.strip()}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local private skills.")
    parser.add_argument("skills", nargs="*", help="Optional skill directory names under skills/")
    args = parser.parse_args()

    skill_dirs = list_skill_dirs(args.skills)
    if not skill_dirs:
        print("No skill directories found.")
        return 1

    failed = False
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        rel = skill_dir.relative_to(ROOT)
        if errors:
            failed = True
            print(f"FAIL {rel}")
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"PASS {rel}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
