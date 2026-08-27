#!/usr/bin/env python3
"""Regenerate the 'Used by' table in README.md from users.yml.

Run:  python3 scripts/update-users.py
It edits README.md in place between the USED_BY_START / USED_BY_END markers.
"""
from pathlib import Path
import yaml

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
USERS = ROOT / "users.yml"

START = "<!-- USED_BY_START -->"
END = "<!-- USED_BY_END -->"


def main() -> None:
    data = yaml.safe_load(USERS.read_text()) or {}
    users = data.get("users", [])
    if not users:
        print("No users found in users.yml")
        return

    rows = ["", "| User | Type |", "|------|------|"]
    for u in users:
        name = u.get("name", "?")
        kind = u.get("kind", "")
        link = u.get("link", "")
        label = f"[{name}]({link})" if link else name
        rows.append(f"| {label} | {kind} |")
    rows.append("")

    block = "\n".join(rows)
    text = README.read_text()
    i = text.index(START) + len(START)
    j = text.index(END)
    new_text = text[:i] + block + text[j:]
    README.write_text(new_text)
    print(f"Updated README with {len(users)} user(s).")


if __name__ == "__main__":
    main()
