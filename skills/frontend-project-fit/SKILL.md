---
name: frontend-project-fit
description: "Fit frontend changes to the host project's established architecture and reusable UI. Use whenever planning or implementing frontend code in an existing repository, including work performed alongside design, UX, or user-facing copy changes. Before editing, inspect module boundaries, similar surfaces, components and widgets, styles and tokens, data and state patterns, utilities, localization, accessibility conventions, and tests; reuse or coherently extend every compatible existing solution instead of creating a parallel implementation. Permit a new component, style, pattern, or dependency only after an evidence-backed search shows that reuse would not fit. Do not use for tasks with no frontend implementation or claim project fit when the repository is unavailable."
---

# Frontend Project Fit

Make each frontend change look and behave as though it belongs to the existing product and codebase. Project architecture and reusable UI are implementation constraints, not optional inspiration.

## Apply the guard to every frontend implementation

Use this skill for any authorized change to frontend production code in an existing project, whether the task is a bug fix, feature, refactor, design implementation, or copy-related change.

Preserve the request boundary:

- For a read-only review, report architecture or reuse findings without editing.
- For an implementation request, inspect before editing and reuse before creating.
- Do not expand into a repository-wide architecture migration unless requested.
- Preserve unrelated user changes and existing ownership boundaries.
- If the relevant repository or source is unavailable, state the evidence gap and do not invent project conventions.

## Load the references

- Read [references/project-discovery-and-reuse.md](references/project-discovery-and-reuse.md) before planning or creating frontend code.
- Read [references/architecture-and-validation.md](references/architecture-and-validation.md) before choosing integration boundaries and before handoff.

## Follow the project-fit workflow

### 1. Map the affected path

Trace the requested behavior from route or entry point through layout, components, state, data fetching, API adapters, styling, localization, accessibility semantics, and tests. Inspect the actual path rather than inferring architecture from filenames.

Identify one or two existing surfaces closest in responsibility, interaction, and visual hierarchy. Treat them as internal reference implementations, not merely screenshots.

### 2. Build a reuse inventory

Before designing or coding, search for existing:

- pages, layouts, panels, widgets, fields, tables, lists, cards, dialogs, navigation, and feedback components;
- primitives, variants, slots, composition APIs, hooks, utilities, and formatters;
- tokens, typography, spacing, color, elevation, radius, breakpoints, motion, icons, and style helpers;
- routing, state, caching, forms, validation, permissions, errors, telemetry, and data-access patterns;
- localization, accessibility, testing, story, fixture, and mock conventions.

Search by behavior and API shape as well as by visual name. A reusable solution may have a project-specific name.

### 3. Decide reuse explicitly

For each needed element, compare existing candidates against:

- semantic responsibility;
- required behavior and states;
- accessibility and keyboard behavior;
- responsive and theming support;
- data and ownership boundaries;
- extension cost and regression risk.

If an existing candidate fits directly or through a small coherent extension, reuse it. This is mandatory. Do not create a local copy, parallel primitive, one-off style system, or second state/data pattern for convenience.

Extend an existing solution only when the added capability belongs to its responsibility and does not turn its API into unrelated conditional branches.

### 4. Justify any new solution

Create a new component, widget, style abstraction, architectural pattern, or dependency only when the search found no compatible solution or reuse would violate semantics, boundaries, accessibility, or maintainability.

Record:

- what was searched;
- the closest candidates;
- why direct reuse or extension would not fit;
- where the new solution belongs in the existing architecture;
- how it avoids becoming a competing primitive.

“Faster to write,” “cleaner from scratch,” or personal framework preference is not sufficient justification.

### 5. Keep design inside the project language

When the task also includes UI/UX design, derive the visual and interaction direction from existing project evidence first. Use the project's components, variants, tokens, icons, layout rhythm, content density, responsive transformations, and motion conventions in the design specification.

Do not design an unavailable bespoke widget when an existing project component can satisfy the same user need. If the user explicitly requests a design-system change, show how existing surfaces migrate and obtain the required implementation authority before broadening scope.

### 6. Implement through established boundaries

Place code where the project expects the responsibility to live. Follow existing conventions for component APIs, state ownership, server/client boundaries, data access, forms, errors, localization, permissions, telemetry, and tests.

Prefer composition and supported variants over duplication. Avoid new dependencies when the project already provides the needed capability.

When user-visible copy is created, changed, or encountered, also apply the bundled `$frontend-copy-guard`.

### 7. Validate project fit

Run checks proportional to the change and compare the result with the internal reference surfaces. Verify:

- no duplicate primitive or competing pattern was introduced;
- reused components use their public API rather than private internals;
- extensions preserve existing consumers;
- tokens and style utilities replace arbitrary parallel values where applicable;
- behavior, states, accessibility, responsiveness, localization, and tests match project conventions;
- the exact affected flow works with real integration when available.

### 8. Report evidence, not assurance

In the final handoff, state concisely:

- existing components, styles, utilities, and architecture patterns reused;
- existing primitives extended and how compatibility was checked;
- any new solution and its evidence-backed justification;
- validation actually performed and remaining uncertainty.

Do not claim architectural consistency merely because the build passes.

## Keep these non-negotiable rules

- Inspect the host project before designing or implementing when access exists.
- Reuse a compatible existing solution whenever one exists.
- Search for behavioral and project-specific equivalents before concluding none exist.
- Do not duplicate a component to avoid understanding its API.
- Do not introduce a second styling, state, fetching, form, or validation system for a local task.
- Do not force reuse when semantics or ownership are wrong; explain the mismatch and add the smallest coherent solution.
- Do not replace stable project architecture as an incidental part of feature work.
- Do not confuse visual similarity with architectural compatibility.
