#!/usr/bin/env python3
"""Resolve bundled Refactoring UI steps and verify declared WCAG contrast pairs."""

import json
from pathlib import Path
import re
import sys


CATALOG = (
    Path(__file__).resolve().parents[1]
    / "skills/frontend-product-design/references/refactoring-ui-palettes.json"
)
MINIMUM_CONTRAST = {"text": 4.5, "large-text": 3.0, "non-text": 3.0}
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def luminance(hex_color):
    channels = [int(hex_color[start:start + 2], 16) / 255 for start in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def check_selection(selection, catalog):
    if not isinstance(selection, dict) or set(selection) - {"roles", "fixedRoles", "pairs"}:
        raise ValueError("selection must contain roles, pairs, and optionally fixedRoles")
    roles = selection.get("roles")
    fixed = selection.get("fixedRoles", {})
    pairs = selection.get("pairs")
    if not isinstance(roles, dict) or not roles:
        raise ValueError("roles must be a non-empty object of role names and catalog step IDs")
    if not isinstance(fixed, dict) or set(roles) & set(fixed):
        raise ValueError("fixedRoles must be an object with names distinct from selected roles")
    if not isinstance(pairs, list):
        raise ValueError("pairs must be an array")

    steps = {
        step["id"]: step["hex"]
        for scale in catalog["scales"]
        for step in scale["steps"]
    }
    resolved = {}
    for role, step_id in roles.items():
        if not role.strip() or not isinstance(step_id, str) or step_id not in steps:
            raise ValueError(f"invalid role or unknown catalog step for {role!r}")
        resolved[role] = {"stepId": step_id, "hex": steps[step_id]}
    for role, color in fixed.items():
        if not role.strip() or not isinstance(color, str) or not HEX_COLOR.fullmatch(color):
            raise ValueError(f"fixed role {role!r} must have a #RRGGBB value")

    colors = {role: color["hex"] for role, color in resolved.items()}
    colors.update(fixed)
    results = []
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != {"foreground", "background", "use"}:
            raise ValueError("each pair must contain foreground, background, and use")
        foreground, background, usage = pair["foreground"], pair["background"], pair["use"]
        if any(not isinstance(role, str) or role not in colors for role in (foreground, background)):
            raise ValueError("pair must refer to two declared roles")
        if not isinstance(usage, str) or usage not in MINIMUM_CONTRAST:
            raise ValueError("pair use must be text, large-text, or non-text")
        darker, lighter = sorted((luminance(colors[foreground]), luminance(colors[background])))
        ratio = (lighter + 0.05) / (darker + 0.05)
        minimum = MINIMUM_CONTRAST[usage]
        results.append({**pair, "ratio": round(ratio, 6), "minimum": minimum, "pass": ratio >= minimum})

    return {
        "catalogId": catalog["id"],
        "roles": resolved,
        "fixedRoles": fixed,
        "pairs": results,
        "pass": all(pair["pass"] for pair in results),
    }


def main():
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        report = check_selection(json.load(sys.stdin), catalog)
    except (KeyError, OSError, ValueError) as error:
        print(f"Palette selection error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
