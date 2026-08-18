---
name: frontend-information-architecture
description: "Use for sitemap, routes, page families, navigation, content ownership, and state or viewport coverage of a multi-page site, app, or flow. Produce a frozen structure contract before visual design or implementation. Do not use for styling, component code, copy, ImageGen, runtime QA, or a fully specified single page."
---

# Frontend Information Architecture

Turn product requirements and project evidence into a complete, typed frontend structure before visual design or implementation begins.

## Scope and authority

- Use for a new multi-page site or app, an explicit sitemap/navigation request, a multi-step flow, or a redesign that may change page boundaries or route relationships.
- Do not activate for a fully specified single page, a local component change, or a visual-only refresh whose structure is locked.
- For existing products, preserve routes, deep links, navigation semantics, permissions, and page-specific user jobs unless the user authorized structural change.
- Produce structure and coverage only. Do not select visual style, render images, write production code, or polish interface copy.

This skill owns sitemap and route structure, page families, navigation edges, surface ownership, and required structural coverage. `frontend-product-design` consumes the frozen structure for interaction and visual decisions; `frontend-project-fit` consumes it for implementation.

## Load the contract

Read [references/structure-contract.md](references/structure-contract.md) before creating or changing a sitemap, route graph, page family, or multi-surface flow.

## Workflow

### 1. Establish the structural request

Record the product objective, users, in-scope surfaces, explicit exclusions, known routes, content sources, required actions, permissions, and whether existing structure may change. Separate confirmed facts, project evidence, reasonable assumptions, and unresolved requirements.

Treat “design a website” as a full-site request unless the user explicitly asks for a homepage, one-page landing, sample, or visual concept only. If the sitemap is absent, infer the smallest coherent provisional structure from the product jobs and state the assumption. Ask one concise question only when different structures would materially change scope or cost and cannot be inferred safely.

### 2. Inspect current structure when available

Trace the real router, layouts, navigation, deep links, selected-item flows, overlays, permissions, and responsive transformations. Identify which surfaces have independent URLs or user jobs and which are states of a parent surface.

Do not inspect `.frontend-workbench/` as product evidence. It contains private workflow state and may describe superseded ideas.

### 3. Model user jobs and ownership

For every required surface, identify:

- the primary user job;
- necessary information and actions;
- entry and exit paths;
- content and action ownership;
- dependencies, permissions, persistence, failure, and recovery;
- what must remain visible or shareable.

A shareable destination, independent task, different permission boundary, or materially different hierarchy usually deserves a page or flow step. A temporary contextual action or state usually belongs to an overlay, drawer, modal, or derived state. Do not choose containers to hide density.

### 4. Build the typed structure contract

Create stable IDs for the site or flow, surfaces, pages, page families, states, viewports, navigation edges, and required outputs. Keep these axes separate:

```text
page != state != viewport != scroll position != evidence output
```

Map every named page and surface. Group structurally equivalent dynamic routes into page families, but give a page independent coverage when its user job, hierarchy, composition, permission, or interaction is materially unique. If the user requests every page separately, representative collapse is forbidden.

### 5. Audit coverage and navigation

Verify that:

- every page has an entry path and required return or onward path;
- every visible navigation control has a supported destination;
- every hidden surface has a discoverable trigger;
- page-specific content and actions have one owner;
- no required surface disappears into the homepage or another representative page;
- default, safety, failure, recovery, and responsive transformations are accounted for proportionally;
- mobile transformations preserve the same user jobs even when containers change.

Do not manufacture variants for trivial visual differences.

### 6. Freeze and store the handoff

When another skill or later turn must consume the structure, require the exact root `.gitignore` entry `/.frontend-workbench/` and verify it with `git check-ignore`. Prepare rich `structure.json` and minimal `coverage.json` in allowed task-scoped staging, validate the coverage adapter, then call the bundled runtime helper `init --structure <structure.json> --contract <coverage.json>`. The helper atomically installs both canonical files with `state.json`; do not pre-create or hand-edit the final session directory. Do not create sitemap reports, diagrams, or screenshots in the repository root or product source.

For a read-only answer that needs no durable artifact, keep the contract concise in the conversation and write nothing. If the hidden workspace cannot be kept out of version control, use an allowed task-scoped temporary directory or report the blocker.

Freeze structural authority as `locked` or `revisable`, name authorized cross-page content moves, and list unresolved or deferred surfaces. Visual design may change presentation inside that authority but must not silently rewrite the sitemap or route graph. Pass both workspace-relative files: `structure.json` for product reasoning and `coverage.json` for machine state.

## Completion contract

Finish only when:

- every named page, surface, and flow step has a stable destination and user job;
- page families and unique pages are distinguished with reasons;
- navigation edges, deep-link/back semantics, content ownership, states, and material viewports are accounted for;
- required coverage outputs are declared without collapsing unique pages;
- structural authority, assumptions, deferred items, and unsupported behavior are explicit;
- the handoff is stored only in the hidden workspace or conversation, never as stray project documentation.
