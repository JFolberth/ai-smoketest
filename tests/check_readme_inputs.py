#!/usr/bin/env python3
"""CI guard: every input declared in action.yml must be documented in README.md.

Parses action.yml, extracts the top-level `inputs.*` keys, and asserts each one
appears at least once in README.md (verbatim, backtick-wrapped so it counts as
the inputs-table row rather than an incidental prose mention).

Exits 0 on sync, 1 on drift. Run standalone: `python3 tests/check_readme_inputs.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_YML = REPO_ROOT / "action.yml"
README = REPO_ROOT / "README.md"


def main() -> int:
    action = yaml.safe_load(ACTION_YML.read_text())
    inputs = list((action.get("inputs") or {}).keys())
    if not inputs:
        print("ERROR: action.yml declares no inputs — nothing to check.", file=sys.stderr)
        return 1

    readme = README.read_text()
    missing: list[str] = []
    for name in inputs:
        # Require the input name in backticks so we don't confuse a prose
        # mention (e.g. "the agent name") with a real inputs-table entry.
        needle = f"`{name}`"
        if needle not in readme:
            missing.append(name)

    if missing:
        print("ERROR: the following action.yml inputs are missing from README.md:", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 1

    print(f"OK: all {len(inputs)} inputs documented ({', '.join(inputs)}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
