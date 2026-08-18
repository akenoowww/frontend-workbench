# Runtime verification checks

Use this reference to select proportional rendered checks and produce evidence that can be repeated after a fix.

## Required baseline

For every rendered flow, confirm:

1. **Identity** — URL and title match the intended page.
2. **Meaningful render** — the app shows real interface content rather than an empty shell, skeleton-only state, login redirect, framework overlay, or stale fallback.
3. **Runtime health** — relevant console errors, rejected requests, and failed assets are absent or explained.
4. **Interaction proof** — at least one target action is followed by an observable state assertion.
5. **Visual evidence** — a screenshot supports any hierarchy, layout, clipping, or fidelity claim.

## Responsive checks

Use the project's breakpoints or the viewports required by the frozen design handoff. Check:

- horizontal overflow, clipping, overlap, and scroll traps;
- readable wrapping and content density;
- navigation and overlay transformations;
- fixed and sticky regions inside the visible viewport;
- touch target and focus access on narrow layouts;
- layout shift and missing assets.

Do not generate arbitrary viewport variants. Add one when navigation, hierarchy, composition, or interaction changes materially.

## Accessibility checks

Inspect semantics and accessible names, keyboard order, visible focus, modal or drawer focus containment and restoration, labels and validation relationships, non-color communication, and zoom or reduced-motion behavior when relevant. Automated accessibility output is evidence, not a substitute for exercising the affected interaction.

## Design fidelity

When an accepted design artifact exists, compare:

- page and state identity;
- primary user job and required information;
- hierarchy and grouping;
- shared shell, navigation, and proportions;
- typography and spacing character;
- component, icon, surface, and motion language;
- responsive transformation;
- exact product copy from source rather than unreliable bitmap text.

Prioritize product truth, accessibility, and project architecture over decorative bitmap details. Record intentional adaptations rather than treating every pixel difference as a defect.

## Evidence shape

Keep one concise record per check:

```text
CHECK
- Route and viewport:
- Action or state:
- Expected:
- Observed:
- Evidence:
- Result: PASS / FAIL / BLOCKED
- Remaining uncertainty:
```

For a partial tool failure, mark the specific check `BLOCKED`; do not convert it to `PASS` because other checks succeeded.
