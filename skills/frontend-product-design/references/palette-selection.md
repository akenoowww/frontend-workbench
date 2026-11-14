# Site palette selection

Use the bundled [Refactoring UI Color Palettes catalog](refactoring-ui-palettes.json) for new site UI colors and for roles explicitly open to change. It records seven scales of ten printed HEX values from the [publisher's public previews](https://refactoringui.com/#color-palettes), with source links. The local step IDs identify colors within those scales. Describe a combination selected for the task as the project's palette.

Keep exact brand and project tokens in roles the scope already fixes. Reuse a verified selection for a matching direction, theme, or inherited shell. Run this workflow once per new or materially changed palette. A palette shared across pages, bands, or responsive outputs stays shared.

## Delegate the choice

Product Design identifies the visible color roles, their backgrounds, the user job, themes, and any fixed project colors after scoping the design. Ask one subagent to read this reference and the bundled catalog and choose the palette. Give it those scoped inputs and the catalog path. The subagent selects colors and explains which role each serves; the caller still owns layout, hierarchy, behavior, and final verification. Keep the subagent's work read-only and limited to the supplied non-secret context and bundled reference.

Have the subagent compare eligible treatments when hue or emphasis can change the design. Ask for one selected set of catalog step IDs, the rationale and a compact account of the trade-off. Use only registered steps for open UI roles. A fixed project color can remain as a contrast neighbor. Photos, illustration, and antialiased edges are outside the UI token set. When the host lacks delegation, apply the same selection rules and identify the selecting agent accurately.

## Verify and carry the result

Use the following JSON shape for the selected open roles and their required foreground/background pairings. Add pairs for all applicable roles and states, including body text, labels on actions, status text, and focus/control boundaries that carry meaning.

```json
{
  "roles": {
    "canvas": "refactoring-ui.blue-grey.10",
    "text": "refactoring-ui.blue-grey.01"
  },
  "pairs": [
    {"foreground": "text", "background": "canvas", "use": "text"}
  ]
}
```

Run [check_palette.py](../../../scripts/check_palette.py) with the selection on standard input. It resolves IDs to their exact HEX values and checks the named WCAG pairs. Use `text`, `large-text`, or `non-text` according to the actual usage. For a contrast neighbor already fixed by the project, include its role and exact HEX under optional `fixedRoles`. For gradients or transparency, verify contrast on the actual rendered or composited background. Use an empty `pairs` array only when the selected roles carry no contrast obligation, and record why. [WCAG 2.2](https://www.w3.org/TR/WCAG22/#contrast-minimum)

```bash
python3 "<plugin-root>/scripts/check_palette.py" < "<selection-json>"
```

Verify the selected roles cover the visible job and states. If a pair fails, use another catalog step and recheck. If the catalog cannot satisfy a material requirement, record the affected role and reconcile it with the user or project constraint. Keep the selected IDs, rationale and contrast evidence in the existing direction record. Include the verified role and HEX in the design specification or `colorRoles`, and use those values in any in-scope prototype.
