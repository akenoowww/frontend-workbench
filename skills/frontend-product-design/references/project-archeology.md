# Project archaeology and UI DNA

Use this reference before making design decisions in an existing repository.

## Contents

1. Technical inspection
2. Internal reference surfaces
3. Reusable primitives
4. Project UI DNA
5. Evidence gaps

## 1. Technical inspection

Inspect how this repository actually builds frontend behavior. Do not infer conventions from the framework name alone.

Determine when applicable:

- product objects expressed by routes, domain types, navigation, persistence, and user language; distinguish primary work, supporting objects, downstream evidence, and implementation details;
- framework, routing, project and component architecture;
- styling system, CSS methodology, design tokens, themes, typography, icons;
- responsive and motion systems;
- state management, data fetching, caching, forms, and validation;
- visualization, upload, editor, and other specialized libraries;
- localization, permissions, feature flags, and role handling;
- testing conventions and accessibility helpers.

For redesign work, inspect the actual definitions and usage of the current component library, themes, tokens, typography, spacing, color, radius, elevation, icons, motion, and breakpoints. Do not infer the design system from one screenshot or from generated CSS alone. When supplied websites, screenshots, brand guidance, or visual anchors materially affect the direction, normalize them separately through [visual-reference-extraction.md](visual-reference-extraction.md).

Trace the feature's likely data and state path as well as its visible components. Record constraints that can change the design, such as server pagination, role limitations, persisted filters, optimistic updates, or unavailable data.

For FULL v3, compare the confirmed `productModel` and nested shells with repository truth. A technical model, analytics view, or evidence surface must not become the primary product object merely because it is easiest to inspect. Return a structure conflict when the confirmed hierarchy cannot be supported honestly.

## 2. Internal reference surfaces

Search for pages and components that are structurally or behaviorally similar to the requested feature. Select one or two as primary references when possible.

Inspect their:

- layout hierarchy, page headers, navigation, and action placement;
- spacing, density, typography, surfaces, and dividers;
- tabs, filters, forms, lists, tables, charts, dialogs, drawers, and popovers;
- loading, empty, partial, permission, error, success, and destructive states;
- desktop, tablet, and mobile behavior;
- focus, keyboard, dismissal, feedback, and recovery patterns.

Use them as evidence, not templates. State explicitly when no relevant internal reference exists.

## 3. Reusable primitives

Search before proposing a new primitive. Include buttons, inputs, selects, date controls, tabs, cards, dialogs, drawers, popovers, menus, tooltips, lists, tables, pagination, notifications, status indicators, skeletons, empty states, filters, navigation, forms, charts, editors, graphs, and uploaders as relevant. Also inspect installed/workspace libraries and platform/framework capabilities that already own complex behavior.

For each likely reuse candidate, record:

- path and public API;
- existing variants and states;
- accessibility and responsive behavior;
- whether composition, extension, or a new primitive is justified.

Prefer composition or extension. Product-specific direction is not evidence for bespoke implementation; mature project/internal/framework/library capability owners remain valid ways to realize unique hierarchy and relationships. Introduce a new primitive only when current evidence shows a concrete product-driven gap.

## 4. Project UI DNA

Produce a concise evidence-backed model:

```text
PROJECT UI DNA

Product objects and nested shells
- ...

Layout
- ...

Spacing
- ...

Typography
- ...

Surfaces
- ...

Controls
- ...

Navigation
- ...

Overlays
- ...

Feedback
- ...

Interaction density
- ...

Responsive behavior
- ...

Motion
- ...

Reusable primitives
- ...

Complex capability owners
- ...

Primary internal references and their scoped surface/aspect roles
- ...

Technical constraints
- ...
```

Attach stable source references plus file paths, component names, screenshots, or runtime observations to material claims. Mark direct observations and inferences separately. Do not use generic defaults where project evidence exists.

For a redesign, add a concise current-state baseline: the exact target surface, its included states and viewports, existing component composition, visual hierarchy, and protected functional behavior. This baseline feeds [redesign-boundaries.md](redesign-boundaries.md); its verified visual claims feed `preserveFromProjectDNA` and `evidence` in [visual-direction.md](visual-direction.md).

## 5. Evidence gaps

When repository access, runtime access, representative data, or a relevant surface is missing:

1. state what is unavailable;
2. distinguish confirmed facts from assumptions;
3. use supplied screenshots or requirements only within their evidentiary limits;
4. avoid claiming project fit that has not been verified;
5. ask for input only when the missing choice would materially change the result.
