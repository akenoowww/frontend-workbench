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

- framework, routing, project and component architecture;
- styling system, CSS methodology, design tokens, themes, typography, icons;
- responsive and motion systems;
- state management, data fetching, caching, forms, and validation;
- visualization, upload, editor, and other specialized libraries;
- localization, permissions, feature flags, and role handling;
- testing conventions and accessibility helpers.

For redesign work, inspect the actual definitions and usage of the current component library, themes, tokens, typography, spacing, color, radius, elevation, icons, motion, and breakpoints. Do not infer the design system from one screenshot or from generated CSS alone.

Trace the feature's likely data and state path as well as its visible components. Record constraints that can change the design, such as server pagination, role limitations, persisted filters, optimistic updates, or unavailable data.

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

Search before proposing a new primitive. Include buttons, inputs, selects, date controls, tabs, cards, dialogs, drawers, popovers, menus, tooltips, lists, tables, pagination, notifications, status indicators, skeletons, empty states, filters, navigation, forms, charts, editors, and uploaders as relevant.

For each likely reuse candidate, record:

- path and public API;
- existing variants and states;
- accessibility and responsive behavior;
- whether composition, extension, or a new primitive is justified.

Prefer composition or extension. Introduce a new primitive only when existing ones cannot support the required behavior cleanly.

## 4. Project UI DNA

Produce a concise evidence-backed model:

```text
PROJECT UI DNA

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

Primary internal references
- ...

Technical constraints
- ...
```

Attach file paths, component names, screenshots, or runtime observations to material claims. Do not use generic defaults where project evidence exists.

For a redesign, add a concise current-state baseline: the exact target surface, its included states and breakpoints, existing component composition, visual hierarchy, and protected functional behavior. This baseline feeds [redesign-calibration.md](redesign-calibration.md).

## 5. Evidence gaps

When repository access, runtime access, representative data, or a relevant surface is missing:

1. state what is unavailable;
2. distinguish confirmed facts from assumptions;
3. use supplied screenshots or requirements only within their evidentiary limits;
4. avoid claiming project fit that has not been verified;
5. ask for input only when the missing choice would materially change the result.
