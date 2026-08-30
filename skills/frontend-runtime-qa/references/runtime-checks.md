# Runtime verification checks

Use this reference to select proportional rendered checks and produce evidence that can be repeated after a fix.

## Required baseline

For every rendered flow, confirm:

1. **Identity** — URL and title match the intended page.
2. **Meaningful render** — the app shows real interface content rather than an empty shell, skeleton-only state, login redirect, framework overlay, or stale fallback.
3. **Runtime health** — relevant console errors, rejected requests, and failed assets are absent or explained.
4. **Interaction proof** — at least one target action is followed by an observable state assertion.
5. **Visual evidence** — a screenshot supports any hierarchy, layout, clipping, or fidelity claim.

For durable evidence, these observations must come from the canonical browser probe, not a prose summary. Put a v1 spec under the active session `qa/`, run:

```bash
python3 <plugin-root>/scripts/runtime_state.py run-runtime-qa \
  --root <project-root> \
  --session-id <session-id> \
  --output-id <output-id> \
  --expected-revision <revision> \
  --accepted-artifact-sha256 <accepted-sha-or-omit-for-direction-only> \
  --probe-spec qa/<output-id>.runtime-probe-spec.json
```

The lifecycle helper invokes the already-installed `agent-browser`, opens only the spec URL, and never installs dependencies. The spec binds the current `implementationSnapshotSha256`; names the output/route/state/viewport/scroll position; provides explicit state setup plus a state assertion; selects a non-document app root; and declares at least one target interaction with a postcondition that must change from before to after. It then writes and validates the screenshot, trace, and manifest in one operation. If the browser adapter or selected library is unavailable, the result is `BLOCKED`; do not use a search engine, `file://`, direct Chrome scripting, a static screenshot, or hand-built SVG as a substitute.

Probe specs are durable evidence: use only synthetic non-secret form values. Reuse an already-authenticated browser/session boundary when the route needs login; never place passwords, tokens, cookies, or private production data in the spec, trace, screenshot, or HAR.

For human trace inspection, reuse an available viewer: the installed agent-browser observability dashboard for its sessions, the project's existing Playwright trace viewer for Playwright traces, or another project-native runner UI. A request to “show the trace/graph” means select the mature viewer that owns that trace format; do not build a bespoke SVG trace graph unless the user explicitly asks for a new visualization product.

## Capability-control checks

When the implementation plan selects a library, framework, platform facility, internal primitive, or project-owned control for a complex/foundational capability, verify behavior against the relevant plan constraints and `validation` obligations. Import presence, a rendered shell, or a toolbar screenshot is insufficient.

Select the smallest meaningful checks for the capability:

- overlays: trigger, focus entry, keyboard traversal, Escape/outside dismissal when supported, focus restoration, and nested/scroll behavior;
- forms and validation: input, submit, pending, server/client error mapping, error focus, correction, resubmit, and data preservation;
- graphs, charts, tables, and trees: selection, keyboard alternative, zoom/pan/filter/sort/expand as applicable, accessible interpretation, empty/error data, and meaningful density;
- editors: input, selection, undo/redo, validation or serialization, focus, paste/IME when material, and recovery from malformed content;
- drag and drop or reordering: pointer path, keyboard or equivalent accessible path, cancellation, invalid target, and persisted result;
- virtualization or large data: boundary scrolling, stable identity, focus retention, loading/error transitions, and no inaccessible off-screen-only action.

Do not run irrelevant generic gestures to inflate coverage. Each check should prove a selected capability or a documented difficult edge case.

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

### Direction-only runtime outputs

When an accepted artifact is explicitly direction-only, separate authorities:

- product and implementation contracts own real data, states, actions, permissions, errors, and capability behavior;
- the visual-direction contract owns hierarchy, density, typography/color roles, surface/component language, imagery, and motion tone;
- the bitmap does not authorize sample data, decorative controls, operational claims, or new interactions.

Exercise the real route and state through its planned typed contract and capability owner, then compare only the visual invariants the artifact is allowed to express. Mark the check FAIL or BLOCKED when the real state cannot be reached; do not substitute fixture markup or a static recreation to obtain a screenshot.

For STANDARD/FULL evidence, store a distinct rendered PNG screenshot of at least 320x200 pixels under `qa/`. Its structured manifest binds `outputId`, `acceptedArtifactSha256`, `result`, `route`, `state`, `viewport`, `scrollPosition`, `pixelWidth`, `pixelHeight`, screenshot path/SHA, and canonical `runtimeProbe.path`/`sha256`. The trace also binds the probe spec, current implementation-target snapshot, direct URL, explicit state assertion, verified scroll/full-page capture, non-document app-root mount, semantic counts, before/after interaction fingerprints and changing postconditions, console/page/network health, axe result, and the same screenshot bytes. Source changes after capture invalidate completion. Two outputs may share bytes only when the confirmed coverage contract declares the exact `evidenceEquivalentTo` pair and the same specific `equivalenceJustification`; an unvisited state, reused capture, or manifest-only explanation is not evidence. FAIL/BLOCKED may omit a screenshot only with an explicit reason.

After all required checks pass, assemble the final runtime gallery from these receipts. Show every required output with those labels and the delivery digest so design approval cannot be mistaken for acceptance of the implementation.

## Evidence shape

Keep one concise record per check:

```text
CHECK
- Route, state, and viewport:
- Scroll position and pixel dimensions:
- Implementation-plan slice and capability owner:
- Action:
- Expected:
- Observed:
- Evidence:
- Result: PASS / FAIL / BLOCKED
- Remaining uncertainty:
```

For a partial tool failure, mark the specific check `BLOCKED`; do not convert it to `PASS` because other checks succeeded.
