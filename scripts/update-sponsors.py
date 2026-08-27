#!/usr/bin/env python3
"""Regenerate the Sponsors table in README.md from the FUNDING config.

Run:  python3 scripts/update-sponsors.py
Edits README.md in place between SPONSORS_START / SPONSORS_END markers.
"""
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
START = "<!-- SPONSORS_START -->"
END = "<!-- SPONSORS_END -->"

TIERS = [
    ("☕ Supporter", "$3/mo", "Name in README + warm fuzzies"),
    ("🚀 Pro", "$10/mo", "Priority support + early features"),
    ("💎 Sponsor", "$50/mo", "Logo here + on the docs site"),
]


def main() -> None:
    rows = ["", "| Tier | Price | Perk |", "|------|-------|------|"]
    for name, price, perk in TIERS:
        rows.append(f"| {name} | {price} | {perk} |")
    rows.append("")
    block = "\n".join(rows)

    text = README.read_text()
    i = text.index(START) + len(START)
    j = text.index(END)
    new_text = text[:i] + block + text[j:]
    README.write_text(new_text)
    print("Updated sponsors table in README.md")


if __name__ == "__main__":
    main()
