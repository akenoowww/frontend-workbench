# Visual synthesis and art-direction handoff

Use this reference only after product, UX, interaction, and state decisions are stable enough to test visually.

## Contents

1. Visual specification
2. Art-direction handoff
3. Master and derived states
4. Visual review
5. Client fallback

## 1. Visual specification

Combine:

```text
PROJECT UI DNA
+ FEATURE MODEL
+ UX DECISIONS
+ INTERACTION MODEL
+ STATE MODEL
+ CURRENT STATE
```

Specify hierarchy, layout relationships, component roles, relative emphasis, density, spacing behavior, affordances, reused project components, overlays, responsive transformations, and state-specific changes.

Use existing tokens and primitives. Avoid arbitrary pixel values, colors, typography, radii, shadows, gradients, card styles, or navigation patterns when project evidence already defines them.

## 2. Art-direction handoff

For a full-track design task, invoke the bundled `$art-direct-imagegen` skill after completing the visual specification. Do not use image generation as a substitute for repository archaeology, product logic, UX research, or state modeling.

Provide the art-direction stage with:

```text
PROJECT_UI_DNA
FEATURE_BLUEPRINT
INTERACTION_MODEL
STATE_MODEL
PARENT_VISUAL_STATE
CURRENT_STATE
STATE_CHANGE
SUPPORTED_CONTENT_AND_ACTIONS
```

Preserve product semantics and project identity while leaving enough visual freedom for a genuine concept. Never invent metrics, copy, controls, data, permissions, confirmations, or outcomes to make an image look complete.

For a focused nonvisual decision, skip rendering only when a visual artifact cannot test the decision. Record the reason in the working report.

If the user explicitly forbids or defers image generation, prepare the renderer-ready handoff without invoking it. Treat full-track rendering and visual review as deferred, not completed; do not cross into production implementation later until that gate is resolved.

## 3. Master and derived states

Generate the primary or default state first. Treat the first accepted output as the visual-system anchor for later states.

Generate separate derived outputs only when a state materially changes the interface, such as an overlay, drawer, selection, editing mode, confirmation, error, empty state, or mobile transformation.

Across outputs preserve:

- layout and hierarchy language;
- typography and spacing character;
- surfaces, controls, and iconography;
- navigation and proportions;
- branding and density;
- shared data and action semantics.

Do not request a collage of final screens unless the user explicitly asks for a comparison board.

## 4. Visual review

Inspect the generated artifacts before implementation. Verify:

- fit with `PROJECT UI DNA`;
- hierarchy, clarity, density, and discoverability;
- preservation of the primary user goal and necessary context;
- consistency between default and derived states;
- truthful controls, content, and system states;
- sensible overlays, dismissal, focus, and responsive behavior;
- feasibility with the current architecture and reusable primitives.

When an output reveals a UX problem, revise the decision or state model and regenerate the affected state. Do not blindly implement a visually attractive contradiction.

Treat generated UI as high-fidelity visual direction, not production proof. Bitmap text can be inaccurate; preserve exact copy and behavior in implementation artifacts.

## 5. Client fallback

Agent Plugins clients may discover both bundled skills without supporting skill-to-skill invocation in the same way. If `$art-direct-imagegen` cannot be invoked:

1. finish the visual specification and per-state handoff;
2. identify the missing client capability;
3. do not substitute an unreviewed generic image generation call;
4. for a full-track task, stop before production implementation until the required rendering and visual-review stage can run;
5. report the blocked rendering/review stage explicitly.
