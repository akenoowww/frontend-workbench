# Flow Architecture for Dense UI

Use this reference when a source screen contains more information than one clear viewport can support, or when the design includes tabs, drawers, modals, detail views, expanded sections, or related states.

## Contents

- Inventory and classify supplied content
- Choose interaction by meaning
- Build the output manifest
- Generate separate states coherently
- Reject impossible density

Complete this architecture before writing any renderer prompt. A dense-screen prompt without an output manifest is invalid.

## Preserve the information, not the crowding

Build a content inventory before choosing a layout. Record:

- content blocks and exact text;
- primary and secondary actions;
- fields and validation states;
- loading, empty, error, success, verified, or warning states;
- dependencies between blocks;
- content that must be compared simultaneously;
- content required only after a user action.

Use a coverage map when the source is dense or ambiguous:

```text
source item | literal meaning | priority | task moment | destination |
trigger | output ID | verbatim required | content available
```

Preserve the semantic priority of the product, not the source screen's visual hierarchy.

Distinguish these source types explicitly:

- **Action**: what the user can request, submit, report, change, or confirm.
- **Trigger**: an entry point whose opened content may or may not be supplied.
- **Opened surface**: the actual drawer, modal, tab, detail, or expanded content.
- **System state**: loading, empty, error, success, disabled, selected, or verified behavior that is directly evidenced by the source or brief.

Do not infer one type from another. An action label is not evidence that the current screen is already in a resulting system state. A closed trigger is not permission to invent the opened surface or its contents.

Classify each item:

- **Primary**: needed immediately to understand the page or complete its central task.
- **Secondary**: useful for evaluation, comparison, provenance, or deeper reading but not continuously required.
- **Contextual**: needed only for one selected item, action, warning, or decision.

Every source item must map to an output destination. It does not need to remain on Output 1.

Classify by task dependency, never by current visibility. A block is not primary merely because the source placed it in the initial viewport.

Apply the independence test to every substantial region:

1. Is it required to begin or complete the central job?
2. Must it be compared simultaneously with the central content?
3. Is it an independent reading or action task with its own heading, controls, or completion moment?
4. Can a concise summary or trigger preserve awareness while the full content moves elsewhere?

Keep a region primary only when the first or second answer is genuinely yes. Treat a complete form as contextual unless completing that form is the page's central job. Treat detailed history, provenance, explanation, or supporting evidence as secondary when a summary can preserve the decision context.

For each planned output, reduce the global coverage map to:

```text
NOW: visible in this output
ELSEWHERE: preserved in another named output or scroll position
UNSUPPORTED: not supplied; do not render or infer
```

Only `NOW` belongs in that output's renderer prompt.

Use `UNSUPPORTED` only for absent content, data, outcomes, or system behavior. Never mark a scroll position, tab, drawer, modal, expandable region, or other presentation container unsupported merely because the source did not use that container.

## Choose interaction by meaning

- **Continuous scroll**: information belongs to one reading or task sequence and benefits from cumulative context.
- **Tabs**: peer categories are mutually exclusive views and users will switch between them repeatedly. Do not use tabs to hide an arbitrary overflow pile.
- **Drawer**: contextual detail should open without losing the current place, comparison, or selection.
- **Modal**: a short focused action, confirmation, warning, or blocking decision requires temporary attention. Do not place long reading or primary navigation in a modal.
- **Expandable section**: supporting detail belongs directly to the surrounding content and occasional reveal is sufficient.
- **Separate screen**: the content has its own deep task, navigation identity, shareable destination, or substantial complexity.
- **Below-fold continuation**: the task is still one page, but the viewport cannot honestly contain it with readable hierarchy.

Do not hide primary information merely to create visual calm. Do not add a new product job, fact, outcome, or system state.

Introduce a presentation-only modal, drawer, tab, expandable region, scroll continuation, or navigation trigger when density requires separation and all of these are true:

- it relocates supplied content without changing its meaning;
- it does not create new data, permissions, workflow stages, or outcomes;
- the interaction type fits the content's task meaning;
- its entry point is discoverable in an earlier output;
- its visible/open state is rendered as a separate output.

This is UX re-architecture, not invented functionality. Prefer wording already present in the supplied content rather than inventing a new CTA label.

Once a complete secondary task, full form, long supporting explanation, or detailed evidence block competes with the central reading or action task, relocate it. Only its unsupported post-action outcomes remain forbidden; the new presentation container itself is allowed.

## Output manifest

Define the minimum complete set before invoking image generation:

```text
Output 1 — main/default state
Purpose:
Primary content:
Visible triggers to later states:
Exact text required here:

Output 2 — named secondary/open state
Opened from:
Content moved here:
What stays visually unchanged:
Exact text required here:
```

Add outputs only when they communicate a materially different state. Do not generate arbitrary variants for coverage.

Do not compile Output 1 until every row in the coverage map has a destination and Output 1 contains only the information required for its immediate user job plus discoverable entry points to later outputs.

Do not accept `NOW: everything` merely because the source fits everything on a large canvas. Simultaneous visibility must be justified by real comparison or task dependency, not available pixels.

Require multiple outputs when a viewport combines long primary content with a complete independent form and one or more detailed supporting regions. A single output is allowed only when the content forms one continuous task, must remain simultaneously visible, and stays legible without shrinking or flattening hierarchy. State that justification per region, not as a blanket claim.

If a trigger's inner content is unavailable, do not invent it. Ask for the missing state, use explicitly marked placeholders only when the user permits them, or omit that opened output and state the limitation.

When wording is genuinely ambiguous and does not block the base screen, preserve it as an action or trigger and omit the speculative opened state. Ask only when the distinction materially changes the requested deliverables.

## Separate calls, shared visual system

Generate final states separately. Multi-panel boards are useful for comparison or early storyboarding, not for readable final UI.

Sequence:

1. Generate and inspect Output 1.
2. Accept or revise its visual system.
3. Use the accepted Output 1 as a visual-system anchor for Output 2 and later states.
4. In every later prompt, name what changes and repeat what must remain invariant.

Later-state invariant example:

```text
Use the accepted main screen as the visual-system and shell reference.
Keep navigation, viewport, typography, palette relationships, spacing character,
component language, and custom symbols consistent. Change only the requested state.
```

Do not refer vaguely to "same style" when exact continuity matters. Name the stable qualities without re-specifying every pixel.

## Source-role language

For a radical redesign:

```text
The source screenshot is a functional and content reference only.
Do not preserve its layout, styling, geometry, grouping, or page boundaries.
Preserve every supplied user job, action, state, and exact content item across the output set.
```

For a later state:

```text
The accepted main output is the visual-system anchor, not an edit target whose content must remain closed.
Preserve its shell and authored language while rendering the named open state.
```

## Density sanity check

Before generating a viewport, test for contradictions:

- long exact copy plus large display type;
- dense secondary rails plus generous negative space;
- multiple languages plus small labels;
- complete content plus a fixed short canvas;
- several interaction states requested in one final image.

Resolve the conflict through the output architecture. Do not hope the image model will solve impossible density by making text tiny.

Reject a single-viewport plan when it requires several independent reading or action regions to be fully visible at once, especially any combination of long-form copy, a complete form, detailed provenance or history, contextual warnings, and secondary actions. The exact categories vary; the contradiction is simultaneous completeness, readability, and spaciousness.

Hard contradictions:

- `default`, `closed`, or `unopened` while inner fields of the closed surface are also required;
- `one complete viewport` while all long copy and all secondary/contextual regions are required;
- `generous negative space` while nothing may move below the fold or into another state;
- a later-state trigger is visible but the corresponding supplied content has no output destination;
- hidden content appears with no discoverable trigger.
- all source regions are classified as primary without dependency evidence;
- a complete secondary form is kept on the main screen although form completion is not the central job;
- presentation containers or scroll positions are marked `UNSUPPORTED` while their supplied content remains crowded into Output 1.

Treat another scroll position as another generated output but the same product screen. Treat a relocated supplied section as a new presentation state, not a new product capability.

## Additional edge cases

- Treat content below the fold as the same screen at another scroll position, not as a new design system.
- Split a long form only when real cognitive stages exist, not merely to manufacture whitespace.
- Keep task-critical status, constraints, blocking warnings, and the primary action out of secondary tabs or drawers.
- Preserve repeated rows through readable scrolling or pagination; do not silently summarize them.
- Plan responsive flows separately. A desktop drawer may need to become a mobile sheet or screen, but the semantic destination must remain the same.
- In a modal or drawer output, keep the background shell visually consistent with the accepted base screen rather than regenerating it as a new composition.
