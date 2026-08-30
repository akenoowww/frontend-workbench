---
name: frontend-product-design
description: "Design or critique UI/UX and own renderer-neutral visual direction after structure is known. Not for specified implementation, small styling/copy fixes, tests, performance, or backend work."
---

# Frontend Product Design

Resolve material UI/UX decisions and the renderer-neutral visual direction from user and project evidence, then hand off only what the authorized next stage needs.

## Choose the workflow profile

- **MICRO** — a critique or one bounded interaction/visual decision on a structurally locked surface. Inspect the supplied evidence and answer directly; do not invoke IA, ImageGen, implementation, or Runtime QA automatically.
- **STANDARD** — design one surface or a scoped flow whose structure is known. Resolve material behavior and hierarchy, and create only the lightest artifact that tests those decisions. An explicitly preview-only, non-promotable redesign evaluation may remain STANDARD when the target, preserve/replace boundary, scoped references, named outputs, and fixed artifact budget are supplied and no implementation or durable acceptance follows.
- **FULL** — a multi-page product/redesign, a complete/material rethink intended for implementation or durable acceptance, a staged approval process, a coherent rendered set with dependent acceptance, or a design-and-implementation handoff. Consume typed structure/coverage, persist checkpoints, and require accepted-design fidelity receipts.

Escalate only when the requested scope or discovered product decision requires it. Preserve an existing contract's workflowProfile.

## Freeze scope and authority

Record the target zone, confirmed facts, constraints, exclusions, evidence gaps, and authority: design-only, critique-only, or design-and-implementation.

For FULL, read [references/full-lifecycle.md](references/full-lifecycle.md) first and consume its confirmed product intent, v3 `productModel`, protected capabilities, nested shells, operational-metadata, visual-direction, artifact, checkpoint, reference-binding, and render-budget policy. Do not let the most visible scenario, reference, or downstream evidence redefine the product or silently switch artifact strategy.

For STANDARD/FULL, record checkpointMode as continuous, review-before-artifact, review-each-stage, or review-before-implementation. A material redesign defaults to review-before-implementation. An explicitly non-promotable STANDARD preview with no downstream implementation may use continuous while still reviewing every saved artifact truthfully. Use review-each-stage only when the user requests stepwise/page-by-page approval or later work depends on an accepted visual anchor. Stop at the named checkpoint rather than treating silence as approval.

For redesigns, read [references/redesign-boundaries.md](references/redesign-boundaries.md). Never silently remove required capabilities, states, accessibility, or data contracts. When the user preserves only a named region, encode `redesignBoundary.mode: preserve-only`: that region and its exact invariants are the entire preserve allowlist. Everything else belongs in `replaceRegions` with material `mustChange` dimensions and forbidden carryover. Do not broaden “keep the main sidebar” into “keep the recognizable shell/top bar/dashboard composition.”

Do not equate product-truth preservation with simultaneous first-viewport visibility. For a dense page, choose a `contentDistribution` strategy: prioritize the first viewport, move secondary material into a deliberate scroll continuation or on-demand state, and keep every protected capability reachable across the complete surface. When the user grants composition freedom, Product Design owns that allocation; do not force every current widget into one screenshot merely because it exists today.

## Inspect evidence and structure

For STANDARD/FULL repository work, read [references/project-archeology.md](references/project-archeology.md). Inspect the affected surface, closest internal examples, tokens, shared components, responsive behavior, localization, accessibility, state/data constraints, and tests. When supplied websites, screenshots, brand guidance, or visual anchors can materially affect the direction, also read [references/visual-reference-extraction.md](references/visual-reference-extraction.md). MICRO may inspect only the supplied or bounded source. If the project is unavailable, use supplied evidence and state the limitation.

Use frontend-information-architecture first only when a multi-page structure, navigation model, page ownership, or multi-step flow is genuinely unresolved and the user authorized that design scope. A locked single surface does not need an IA contract.

Consume frozen product objects, shells, surfaces, routes, families, scenarios, states, viewports, outputs, scoped reference bindings, and authority without silently changing them. Preserve protected capabilities monotonically. If feasibility exposes a contradiction, return STRUCTURE_CONFLICT with affected IDs and evidence.

## Resolve the design

Define necessary information, actions, constraints, feedback, and recovery within the frozen structure. Compare alternatives only for material decisions, then select one coherent project-specific direction and state consequences without exposing hidden reasoning.

Do not turn internal truth into visual reassurance. Verification, freshness, provenance/source, sync/processing, confidence, and service-health copy is hidden by default. In FULL, render only claims declared for the exact surface/state in `operationalMetadataPolicy.requiredClaims`; in MICRO/STANDARD, require explicit user-request, approved-design/product-requirement, or legal/safety authority. Existing UI is evidence to critique, not automatic authority to repeat a claim. Never self-authorize a claim because it seems relevant or because a backend field exists.

For a new or materially changed visual direction, read [references/visual-direction.md](references/visual-direction.md). Product Design owns the `VisualDirectionContract`; renderers do not reinterpret it. A material redesign sets `visualDirectionPolicy` to `required`, persists the contract at the canonical product-design session path, and locks its SHA before the first visual artifact. The bounded STANDARD preview exception freezes the same contract in its non-promotable output receipt instead of creating FULL runtime state; it cannot authorize implementation or later acceptance. Direction lock is separate from artifact approval.

Own semantic priority, hierarchy, perceptual relationships, and the signature system—not implementation novelty. A product-specific direction must permit Project Fit to realize it with mature project primitives, framework/platform facilities, or well-fitted libraries. Never require hand-written controls merely to make the design feel unique.

Read [references/ux-research.md](references/ux-research.md) only when current external guidance or comparison can change a material decision.

Before creating a visual artifact, read [references/artifact-choice-and-validation.md](references/artifact-choice-and-validation.md). Choose the lightest evidence that can test the decision: annotated specification, existing-component composition, runnable prototype, browser screenshot, or ImageGen-rendered bitmap. In FULL v3, render only representative outputs with required design evidence and within the confirmed budget; all outputs with required runtime evidence remain separate QA obligations. The first representative visual artifact must pass the shared direction critique regardless of renderer. For a redesign, PASS additionally requires a region-by-region delta check against `redesignBoundary`: count only named material dimensions, never palette swaps or minor spacing as a complete redesign. If the replace region still has the source macro-layout/module topology or another forbidden carryover, return `REVISE_ARTIFACT` or `REVISE_DIRECTION` and do not show it as the requested redesign.

## Route adjacent work without cascading

- Use frontend-copy-guard when this design authors or materially changes user-visible claims, operational metadata, validation, consent, pricing, or recovery text. Reusing supplied approved labels is not a new copy stage.
- Use art-direct-imagegen only for an actual requested bitmap, when a generated visual materially tests the locked direction, or when `visualArtifactPolicy` is `imagegen-required`. Pass the direction reference and SHA; ImageGen is otherwise optional and does not own upstream concept selection.
- Use frontend-project-fit only when implementation is authorized.
- Use frontend-runtime-qa only after visible implementation or for explicit rendered/design-fidelity QA.

For FULL review-each-stage, mark each user-visible checkpoint as approval-required and preserve exact pending output IDs. Do not begin dependent output work until explicit acceptance.

## Handoff and runtime gates

Read [references/frozen-handoff.md](references/frozen-handoff.md) before a STANDARD/FULL implementation handoff. Freeze authorized scope, product-model and shell identities, coverage, decisions, protected behavior, scoped references, accepted design evidence, the locked visual-direction reference and SHA when required, permitted adaptations, and unresolved items. Keep design evidence distinct from later runtime evidence.

For FULL, set workflowProfile to full and keep the same lifecycle session. When visual direction is required, its lock must be current before any visual artifact or implementation begins. Every output with required design evidence must be accepted or promoted before downstream implementation invokes begin-implementation. Under `imagegen-required`, each such output needs user-authorized acceptance; runtime-only coverage does not require a raster. A design-only run stops there with an empty implementation-target scope. Targets are populated only when implementation is authorized. After implementation, Runtime QA must bind distinct hashed PASS evidence to every runtime-required output, plus accepted artifact and direction identities when applicable. `complete-implementation` reaches only final gallery review; delivery completes after the user accepts its digest.

MICRO/read-only work writes nothing. Create durable artifacts only for an authorized cross-skill handoff, generated media, or requested design file, and keep workflow state under the ignored /.frontend-workbench/ session rather than product source.

## Completion

Finish when the requested decision is resolved, required coverage is accounted for, any required visual direction is locked and referenced, chosen evidence is reviewed when applicable, authority is preserved, and blocked/deferred/unverified items are explicit. Keep direction evidence, artifact acceptance, implemented code, local validation, and production proof distinct.
