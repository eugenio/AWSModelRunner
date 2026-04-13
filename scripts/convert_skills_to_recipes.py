#!/usr/bin/env python3
"""Convert OpenCode SKILL.md files to Goose recipe YAML files.

Usage:
    python convert_skills_to_recipes.py <skills_dir> <recipes_dir> [--limit N]

Converts SKILL.md files (with YAML frontmatter) into Goose-compatible
recipe YAML files. The SKILL.md body becomes the recipe's `instructions`.
"""

import argparse
import re
from pathlib import Path

import yaml


def parse_skill_md(path: Path) -> dict | None:
    """Parse a SKILL.md file into frontmatter dict + body string."""
    text = path.read_text(encoding="utf-8", errors="replace")

    # Split YAML frontmatter from body
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not m:
        return None

    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return None

    body = m.group(2).strip()
    if not body or not meta.get("name"):
        return None

    meta["_body"] = body
    return meta


def skill_to_recipe(meta: dict, skill_path: Path, skills_root: Path) -> dict:
    """Convert parsed skill metadata + body to a Goose recipe dict."""
    name = meta.get("name", skill_path.parent.name)
    desc = meta.get("description", "")
    body = meta.get("_body", "")

    recipe = {
        "version": "1.0.0",
        "title": str(name),
        "description": desc[:200] if desc else f"Skill: {name}",
        "instructions": body,
        "prompt": "{{ input }}",
        "parameters": [
            {
                "key": "input",
                "input_type": "string",
                "title": "What would you like to work on?",
                "description": desc[:100] if desc else "Describe your task",
                "requirement": "required",
            }
        ],
    }
    return recipe


def sanitize_filename(name: str) -> str:
    """Convert a skill name to a safe filename."""
    return re.sub(r"[^a-zA-Z0-9_-]", "-", str(name)).strip("-").lower()


def main():
    """CLI entry point: parse args and convert skill files to recipe YAML."""
    parser = argparse.ArgumentParser(
        description="Convert OpenCode skills to Goose recipes"
    )
    parser.add_argument("skills_dir", help="Path to OpenCode skills directory")
    parser.add_argument("recipes_dir", help="Output directory for Goose recipes")
    parser.add_argument(
        "--limit", type=int, default=0, help="Max skills to convert (0=all)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print stats without writing"
    )
    args = parser.parse_args()

    skills_root = Path(args.skills_dir)
    recipes_dir = Path(args.recipes_dir)

    skill_files = sorted(skills_root.rglob("SKILL.md"))
    print(f"Found {len(skill_files)} SKILL.md files")

    converted = 0
    skipped = 0
    for skill_path in skill_files:
        if args.limit and converted >= args.limit:
            break

        meta = parse_skill_md(skill_path)
        if not meta:
            skipped += 1
            continue

        recipe = skill_to_recipe(meta, skill_path, skills_root)
        fname = sanitize_filename(meta.get("name", "unknown")) + ".yaml"

        if args.dry_run:
            print(f"  {fname}: {recipe['title']} ({len(recipe['instructions'])} chars)")
        else:
            recipes_dir.mkdir(parents=True, exist_ok=True)
            out_path = recipes_dir / fname
            with open(out_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    recipe,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                    width=120,
                )

        converted += 1

    print(f"\nConverted: {converted}, Skipped: {skipped}")
    if not args.dry_run and converted:
        print(f"Recipes written to: {recipes_dir}")


if __name__ == "__main__":
    main()
