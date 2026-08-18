---
name: frontend-project-fit
description: "Use for an authorized frontend code change in an existing repository. Trace the affected path, reuse compatible project patterns, and evaluate a new primitive or dependency only when required. Do not use for design-only work, backend-only work, or claims of project fit without repository evidence."
---

# Frontend Project Fit

Make an authorized frontend change through the host project's existing architecture instead of creating a parallel implementation.

## Scope and authority

- For review or diagnosis, inspect and report without editing.
- For implementation, inspect the affected path before editing and preserve unrelated user changes.
- Consume approved information-architecture and product-design handoffs when they exist; do not manufacture a design phase for fully specified work.
- Do not turn a local change into a design-system or architecture migration unless the user authorized that migration.
- If the repository or affected source is unavailable, state the evidence gap and do not invent project conventions.

This skill owns implementation fit, reuse, capability choice, integration, and source/automated validation. It does not own product direction, ImageGen rendering, rendered QA evidence, or unrelated backend contracts.

## Load references conditionally

- Read [references/project-discovery-and-reuse.md](references/project-discovery-and-reuse.md) before planning or editing frontend code.
- Read [references/capability-and-dependency-selection.md](references/capability-and-dependency-selection.md) only when introducing or replacing a component, mechanism, tool, dependency, SDK, generated client, or other capability owner.
- Read [references/architecture-and-validation.md](references/architecture-and-validation.md) before choosing integration boundaries and before handoff.

## Workflow

### 1. Trace the affected path

Follow the requested behavior from route or entry point through layout, components, state, data access, errors, localization, accessibility, styling, and tests. Inspect one or two current surfaces with the closest responsibility and interaction model.

Ignore `.frontend-workbench/` when inferring product architecture, content, or assets. It contains private workflow state, prompts, renders, and QA evidence rather than product source.

### 2. Reuse before creating

Inventory compatible components, variants, tokens, icons, hooks, utilities, form and validation patterns, data clients, state owners, and testing conventions. Search by behavior and API shape as well as visual name.

Reuse directly, compose existing primitives, or extend a public API when the responsibility belongs there. Do not duplicate a component or introduce a second styling, state, fetching, form, validation, error, or localization system for convenience.

Reuse is the default, not a veto on an explicitly authorized redesign or migration. When replacement is authorized, record the concrete product or technical reason, affected consumers, and migration impact. Never create a silent parallel owner.

### 3. Choose a new mechanism only when necessary

If no established solution owns the required capability, define the behavior and material constraints without naming a preferred technology. Compare only plausible candidates from the actual stack. Select the option with the smallest justified lifetime cost and risk, not merely the shortest initial diff.

For a trivial bounded choice, keep the rationale to one sentence. Preserve a fuller capability decision only for a new dependency, foundational primitive, security-sensitive behavior, or deviation from project practice.

### 4. Implement through established boundaries

Place code where the project owns the responsibility. Follow current conventions for component APIs, route and server/client boundaries, state, data access, permissions, errors, localization, telemetry, and tests. Prefer composition and supported variants over copies and one-off abstractions.

When the task changes user-visible text, apply the bundled `frontend-copy-guard` workflow if available. This is a one-way handoff; copy work must not invoke this skill back. If the host cannot compose bundled skills, preserve the same minimum fallback: use existing localization and error paths, keep product language truthful, and do not expose raw implementation details.

### 5. Keep working artifacts out of product source

Do not create `ANALYSIS.md`, design reports, prompts, generated mockups, screenshots, or QA folders in the project tree. When task-owned working artifacts are needed and filesystem access is available, require and verify the exact `/.frontend-workbench/` ignore rule, then use the current runtime session. Promote a final asset outside that directory only when it has an approved project-native destination and a real code, build, or test consumer.

For a read-only task with no requested artifact, do not create the runtime workspace.

### 6. Validate and hand off rendered QA

Run checks proportional to the change:

- focused unit, integration, localization, and accessibility tests;
- project-standard type, lint, and build checks when relevant;
- integration contracts and affected consumers.

A passing build is not proof of visual or interaction correctness. For a visible implementation, apply the bundled `frontend-runtime-qa` workflow when available and pass it the exact route, state, viewports, accepted design evidence, and expected behavior. That workflow owns screenshots, console evidence, interaction proof, and responsive fidelity. If the host cannot compose it, perform the smallest equivalent rendered check and report the fallback.

## Completion contract

Finish only when:

- the affected architecture path and reused project assets are identified;
- every new primitive or dependency has a proportional evidence-backed reason;
- no competing project system or stray workflow artifact was introduced;
- source and automated validation passed, and visible work received rendered QA or an explicit blocker;
- source inspection, automated checks, rendered proof, and production proof are reported separately;
- any remaining uncertainty is explicit.
