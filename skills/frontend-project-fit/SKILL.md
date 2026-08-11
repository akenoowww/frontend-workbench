---
name: frontend-project-fit
description: "Fit frontend changes to the host project's established architecture and reusable UI, then choose implementation mechanisms and dependencies from capability-specific evidence instead of defaulting either to hand-written code or to a library. Use whenever planning or implementing frontend code in an existing repository, including work performed alongside design, UX, or user-facing copy changes. Before editing, inspect module boundaries, similar surfaces, components and widgets, styles and tokens, installed dependencies, framework and platform capabilities, data and state patterns, utilities, localization, accessibility conventions, and tests; reuse or coherently extend every compatible existing solution instead of creating a parallel implementation. Permit a new component, style, pattern, tool, or dependency only after an evidence-backed search and a project-specific lifetime-cost decision. Do not use for tasks with no frontend implementation or claim project fit when the repository is unavailable."
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
- Read [references/capability-and-dependency-selection.md](references/capability-and-dependency-selection.md) before selecting how to implement a capability or whether to add a tool or dependency.
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
- installed libraries, framework and platform primitives, generated clients, build tooling, and internal abstractions;
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

### 4. Select the implementation mechanism dynamically

Define the needed capability without naming a technology. Derive its constraints from the requested behavior, the affected runtime, and project evidence. Then generate only the plausible options for this task. Depending on context, these may include:

- reuse or coherent extension of the established project solution;
- a platform-native or framework-native primitive;
- a small project-owned abstraction;
- a mature external library;
- an official SDK, generated client, compiler, or specialized tool.

This is not a fixed checklist and not every category must appear. Search dynamically by capability, risks, and stack. Always consider a library when standardized behavior, difficult edge cases, repeated manual work, or security and correctness concerns make it a credible way to reduce lifetime cost. Never prefer hand-written code merely to avoid a dependency, and never add a dependency merely to avoid understanding a bounded problem.

If the project already has a compatible way to provide the capability, use that style. Do not introduce a competing mechanism for one feature. If the established solution cannot meet a concrete requirement safely or maintainably, document the limitation and keep the change compatible, or obtain authority for an explicit migration.

### 5. Justify the selected solution

Choose the option with the smallest justified lifetime cost and risk for this project, not the smallest initial diff. Consider only criteria material to the task, including correctness, edge cases, realistic reuse, security, accessibility, runtime compatibility, bundle and performance impact, maintenance, maturity, API stability, license and supply-chain exposure, testability, observability, lock-in, and migration cost.

Create a new component, widget, style abstraction, architectural pattern, tool, or dependency only when no compatible established solution owns the capability and the evidence shows the new solution fits better than the remaining feasible options. If an established solution exists but must be replaced, treat that as an explicit migration rather than a local implementation choice.

Record:

- the technology-neutral capability and relevant constraints;
- what was searched;
- the plausible candidates generated for this project;
- why the selected option has the best lifetime trade-off;
- why direct reuse or extension would not fit, when adding something new;
- where the new solution belongs in the existing architecture;
- how it avoids becoming a competing primitive or hidden parallel system;
- any maintenance, security, bundle, license, or migration obligation introduced.

“Faster to write,” “cleaner from scratch,” “fewer dependencies,” package popularity, or personal framework preference is not sufficient justification by itself.

### 6. Keep design inside the project language

When the task also includes UI/UX design, derive the visual and interaction direction from existing project evidence first. Use the project's components, variants, tokens, icons, layout rhythm, content density, responsive transformations, and motion conventions in the design specification.

Do not design an unavailable bespoke widget when an existing project component can satisfy the same user need. If the user explicitly requests a design-system change, show how existing surfaces migrate and obtain the required implementation authority before broadening scope.

### 7. Implement through established boundaries

Place code where the project expects the responsibility to live. Follow existing conventions for component APIs, state ownership, server/client boundaries, data access, forms, errors, localization, permissions, telemetry, and tests.

Prefer composition and supported variants over duplication. Implement the selected capability through the project's established boundary and dependency-management conventions. Audit important defaults instead of assuming that either a platform primitive or a library is safe merely because it is familiar.

When user-visible copy is created, changed, or encountered, also apply the bundled `$frontend-copy-guard`.

### 8. Validate project fit

Run checks proportional to the change and compare the result with the internal reference surfaces. Verify:

- no duplicate primitive or competing pattern was introduced;
- reused components use their public API rather than private internals;
- extensions preserve existing consumers;
- the capability decision still holds against the implemented behavior and discovered edge cases;
- any new dependency or tool is compatible with the runtime, build, project policy, and ownership model;
- tokens and style utilities replace arbitrary parallel values where applicable;
- behavior, states, accessibility, responsiveness, localization, and tests match project conventions;
- the exact affected flow works with real integration when available.

### 9. Report evidence, not assurance

In the final handoff, state concisely:

- existing components, styles, utilities, and architecture patterns reused;
- existing primitives extended and how compatibility was checked;
- the selected implementation mechanism and its capability-specific justification;
- any new solution or dependency and the obligations it introduces;
- validation actually performed and remaining uncertainty.

Do not claim architectural consistency merely because the build passes.

## Keep these non-negotiable rules

- Inspect the host project before designing or implementing when access exists.
- Reuse a compatible existing solution whenever one exists.
- Search for behavioral and project-specific equivalents before concluding none exist.
- Do not duplicate a component to avoid understanding its API.
- Do not introduce a second styling, state, fetching, form, or validation system for a local task.
- Do not reject a justified library in favor of hand-written standardized behavior merely to keep the dependency count low.
- Do not install a library automatically when a bounded native or project-owned solution is clearer and cheaper to maintain.
- Do not build speculative infrastructure for hypothetical future reuse; use realistic expected reuse and current requirements.
- Do not force reuse when semantics or ownership are wrong; explain the mismatch and add the smallest coherent solution.
- Do not replace stable project architecture as an incidental part of feature work.
- Do not confuse visual similarity with architectural compatibility.
