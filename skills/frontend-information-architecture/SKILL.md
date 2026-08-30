---
name: frontend-information-architecture
description: "Define routes, navigation, page families, and state coverage for multi-page products or flows. Not for styling, code, or a locked single page."
---

# Frontend Information Architecture

Turn product requirements and project evidence into a complete frontend structure before visual design or implementation.

## Choose the workflow profile

- **MICRO** — a read-only route/navigation diagnosis or one bounded structural decision with a locked surrounding product. Return the decision in conversation; do not initialize runtime state or invoke downstream design.
- **STANDARD** — a scoped multi-step flow, new product section, or several related surfaces. Produce a compact frozen structure handoff and persist it only when another stage must consume it.
- **FULL** — a new multi-page product, broad navigation model, or redesign that may change page boundaries. Produce typed structure and coverage contracts with explicit checkpoints and durable runtime state.

Do not activate this skill for a fully specified single page, local component change, or visual refresh with locked structure. Preserve an existing contract's workflowProfile; use full for a new full-flow contract.

## Scope

- Preserve existing routes, deep links, navigation semantics, permissions, and page-specific jobs unless structural change is authorized.
- Produce structure and coverage only: no visual style, ImageGen, production code, or copy polish.
- Do not invoke Product Design merely because a structure was analyzed; hand it off only when the user also requested design.

This skill owns sitemap/route structure, page families, navigation edges, surface ownership, and structural coverage.

## Load the contract conditionally

Read [references/structure-contract.md](references/structure-contract.md) for STANDARD/FULL work or when a MICRO decision changes a typed route or coverage contract.

For FULL, also read [the lifecycle contract](../frontend-product-design/references/full-lifecycle.md) before modeling structure. It owns intent confirmation, visual-direction/artifact policy, lineage, quality gates, and the eventual delivery checkpoint.

## Model the structure

### Establish authority

Record the objective, users, in-scope surfaces, exclusions, known routes, content sources, actions, permissions, and whether structure may change. Separate confirmed facts, project evidence, assumptions, and unresolved requirements.

For FULL v3, start from the confirmed product-object hierarchy rather than the most visible scenario. Read the root, primary work objects, supporting objects, downstream evidence, and implementation details from `productModel`; preserve confirmed protected capabilities monotonically. A later scenario, reference, artifact, or implementation convenience may add detail but may not demote, replace, or remove a protected capability without the lifecycle's explicit change-control authority.

Treat product truth, available backend metadata, and workflow evidence as non-visible by default. Do not elevate verification, freshness, provenance, sync/processing, confidence, or service-health facts into required information or state changes from agent judgment.

Treat “design a website” as a full-site request unless the user explicitly asks for one page, landing page, sample, or concept. Infer the smallest coherent provisional structure when safe; ask only when materially different structures cannot be resolved from evidence.

### Inspect and assign ownership

For existing products, trace the real router, layouts, navigation, deep links, overlays, permissions, and responsive transformations. Ignore .frontend-workbench/ as product evidence.

For each required surface, identify its user job, information/actions, entry and exit paths, owner, dependencies, permissions, persistence, failure, and recovery. A shareable destination, independent job, distinct permission boundary, or different hierarchy usually deserves a page or flow step; temporary contextual state usually belongs to an overlay or derived state.

Model nested shells as ownership, not decoration. A child shell fills a declared parent slot and inherits the parent navigation, identity, and persistent regions unless the confirmed contract explicitly replaces them. Bind every surface to its shell and primary product object; do not let a supporting, downstream-evidence, or implementation-detail object become the dominant object of a surface whose job belongs to a primary work object.

### Build and audit coverage

Keep page, state, viewport, scroll position, and evidence output as separate axes. Give stable IDs to surfaces, page families, states, viewports, and required outputs. Treat a navigation edge's stable identity as its exact `(from, trigger, to)` tuple because the compact v3 edge shape has no separate ID.

For FULL v3, trace every required domain and product object through at least one representative scenario to its required surfaces, then to meaningful states, material viewports, and runtime evidence. A scenario is one end-to-end job, not the definition of the whole product. Preserve scenarios that exercise different primary objects or capabilities even when one scenario is more visually prominent.

Group only structurally equivalent dynamic routes. Preserve separate coverage when job, hierarchy, composition, permission, or interaction is materially unique; never collapse pages the user requested separately.

Verify entry/onward paths, visible destinations, hidden-surface triggers, one owner for page-specific content/actions, failure and recovery, and material mobile transformations. Do not manufacture variants for trivial visual differences.

### Freeze the handoff

MICRO stays in conversation unless a file was requested. STANDARD may produce a compact structure handoff for the next authorized stage. FULL sets workflowProfile to full, creates rich structure.json plus minimal coverage.json, and initializes them through the bundled runtime helper; do not hand-edit canonical runtime state. In v3, the pair binds `productModel`, domain/scenario traceability, nested `shells`, surface ownership, and separate design-evidence from runtime-evidence requirements per output. Include `operationalMetadataPolicy` with `defaultVisibility: hidden-unless-required`. Populate `requiredClaims` only from an explicit user request, approved product requirement/design, or legal/safety requirement, and bind each claim to covered surface/state IDs; otherwise leave it empty. Existing source is evidence to inspect, not approval to propagate operational copy. Continue that session through later FULL stages instead of creating skill-specific sessions. A design-only FULL contract keeps `implementationTargets` empty. If implementation is already authorized and exact project owners are known, it may predeclare safe repository-relative targets for the later gate.

Freeze structure as locked or revisable, name permitted cross-page moves, and list unresolved/deferred surfaces. Persist deferred/unsupported outcomes through the helper-owned runtime output status plus reason; do not invent unsupported coverage fields. Downstream design may change presentation within that authority but may not silently rewrite routes or ownership.

For read-only work, write nothing. Durable STANDARD/FULL state belongs only in the ignored /.frontend-workbench/ session, never in product source or repository-root reports.

## Completion

Finish when every in-scope surface has a stable destination and user job, page families and unique pages are distinguished, navigation/ownership/states/material viewports are covered, and authority, assumptions, deferred items, and unsupported behavior are explicit.
