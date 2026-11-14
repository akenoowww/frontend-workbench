---
name: frontend-product-design
description: "Design or critique web UI/UX. Use Modern Web Guidance and current product evidence to resolve behavior, composition, color, and typography. Not for specified implementation, minor styling or copy fixes, tests, or backend work."
---

# Frontend Product Design

Own the user-facing design from product intent through reviewed evidence. Work in this order: establish the scope, consult Modern Web Guidance, compare and select the design, then deliver the decisions and any requested design evidence. A direct Product Design request can finish with a specification or a scoped prototype. Generated images require an explicit user request or an authorized artifact policy that calls for them.

When Art-Direct ImageGen calls Product Design, apply the same pre-render workflow in direction-only mode and return to that renderer. Reuse a current scoped handoff, including its MWG evidence. This entry does not authorize implementation, a second renderer, or a FULL session by itself.

## Establish scope and profile

- **MICRO** handles critique or a bounded decision on a known surface. Inspect only affected evidence, complete the scoped research and guidance steps, and answer directly without durable state or automatic downstream work.
- **STANDARD** covers a surface or scoped flow with known structure. Derive enough representative evidence to test the complete request. A bounded preview that cannot be promoted may stay STANDARD with fixed scope, references, required outputs and budget.
- **FULL** covers multi-page work, a material redesign intended for implementation or durable acceptance, a staged approval process, or a coherent set with dependent acceptance. Read [full-lifecycle.md](references/full-lifecycle.md) first. Consume the confirmed v3 product model, nested shells, structure and coverage, operational metadata, visual/artifact policies, scoped reference bindings, checkpoints, and budget. Preserve an existing contract's profile.

Record the target, user job, constraints, gaps, and authority (critique-only, design-only, or design-and-implementation). For existing products, inspect the current surface, source, relevant adjacent states and product rules first. In STANDARD/FULL read [project-archeology.md](references/project-archeology.md). Use [visual-reference-extraction.md](references/visual-reference-extraction.md) for supplied websites, screenshots or brand guidance. Use frontend-information-architecture only if authorized work genuinely needs unresolved navigation, ownership, page structure or a multi-step flow.

Inventory the current layout, tokens and components, then the actions, data meanings, routes, permissions, persistence and recovery affected by the request. Map each existing capability to a reachable equivalent or an authorized change. Controls may move within scope while preserving state and outcomes. A reference, omission in a contract, or cleaner screenshot cannot remove a capability or authorize a new business operation. Return `STRUCTURE_CONFLICT` with affected IDs when feasibility contradicts frozen structure or behavior. Surface a material missing workflow need as a proposal when it falls outside scope.

For redesign, read [redesign-boundaries.md](references/redesign-boundaries.md). When the user keeps only a named region, use `preserve-only` with that region's exact visual invariants. Treat other in-scope regions as replacements with explicit material changes and forbidden carryover. Preserve their functional capabilities independently of visual carryover.

## Complete Modern Web Guidance before choosing the design

Read the [mandatory Product Design workflow](references/mwg-design-stage.md). Translate the actual user jobs into material design questions before naming a solution. Use the Workbench launcher for every Modern Web Guidance CLI call. Retrieve and read the relevant full guides and evaluate their fit to the scenario and supported browsers. Do this for every new web design or critique within this skill, including MICRO and standalone ImageGen direction, before finalizing recommendations, locking direction, or rendering. One bounded question is enough for a narrow task. Reuse matching, current evidence within a task.

Record a decision supported by each relevant guide or the concrete reason it was inapplicable. Evaluate viable alternatives raised in the search results or guides before settling interaction and layout. A successful search with no relevant guide is a valid documented outcome. A failed lookup requires the recovery described in the reference. Until the mandatory stage can be completed, the affected recommendation stays provisional and cannot become a validated direction or renderer handoff.

## Compare and select the design

Before selecting a design, use [ux-research.md](references/ux-research.md) to inspect current comparable working products and confirm their status and UI evidence. Use two eligible products when available, scoped to decisions that matter. Record dated sources, inspected surfaces, what was directly seen or documented, and which decisions the evidence supports. Use other eligible sources if access fails. Missing material research leaves the recommendation provisional. Honor explicit limits on external research and identify decisions whose evidence they narrow.

Compare options on the actual job and across representative widths. For each open material decision, explain the selected and credible competing approaches in terms of what the user sees and can do. Consider shell and available working width together. For controls, compare frequency, discoverability, room alongside other controls and keyboard behavior. For details, establish whether the original context must stay usable and how users resume. For dense surfaces decide what is visible first, what continues on scroll and what can move on demand while remaining reachable. Read [design-foundations.md](references/design-foundations.md) for these decisions and for palette and typography.

For a new or materially changed direction, apply [visual-direction.md](references/visual-direction.md). Select a project-specific visual idea that still has a clear hierarchy without its colors. Keep authorized project and brand colors. For open site UI color roles, run [palette selection](references/palette-selection.md) with one palette subagent before finalizing the design. Verify the selected colors and include their exact role values in the specification or the direction's `colorRoles`. Compare applicable type treatments using representative content and record the selected hierarchy, typography, and palette rationale. Current or external images may guide only their declared reference aspects. Popularity is a discovery cue; actual product fit decides.

Keep unapproved operational claims out of UI. In FULL use exact surface/state claims in `operationalMetadataPolicy.requiredClaims`. In MICRO/STANDARD only render them with explicit user, product/approved-design, or legal/safety authority. Never derive display authority from a data field, an old screenshot, or a verification result.

## Freeze evidence and review

Derive representative surfaces, states, viewports and outputs from the complete requested experience. Group equivalent states. For scroll continuations or dependent renders, use [scroll-and-output-planning.md](references/scroll-and-output-planning.md) before freezing coverage. Read [artifact-choice-and-validation.md](references/artifact-choice-and-validation.md) before producing evidence. Select the lightest artifact that can test the decision.

For STANDARD/FULL honor the existing checkpoint mode, or choose continuous, review-before-artifact, review-each-stage or review-before-implementation according to scope. A material redesign defaults to review-before-implementation. A bounded non-promotable preview may run continuously. A dependency on a reviewed anchor does not create a user checkpoint by itself. Never cross a named approval checkpoint on silence.

A material redesign requires the renderer-neutral `VisualDirectionContract` and a locked SHA before the first artifact. FULL uses the canonical lifecycle session. The bounded STANDARD preview exception freezes the contract in its non-promotable receipt. A direction lock and artifact approval are distinct. Inspect the first representative artifact against the selected hierarchy, visual roles, usability and fit. For redesign, check the region-by-region delta. A palette or spacing change alone does not satisfy a required macro-layout or topology change.

## Handoff and completion

- Use frontend-copy-guard for material user-visible claims, metadata, validation, consent, pricing or recovery text. Reusing approved labels does not require it.
- Route explicitly requested generated UI bitmaps or authorized `artifactKind: imagegen` outputs to art-direct-imagegen with the locked direction and bound references. Use the selected specification or prototype for direct Product Design work.
- Use frontend-project-fit only for authorized implementation. Read [frozen-handoff.md](references/frozen-handoff.md) before a STANDARD/FULL implementation handoff. Carry the existing research and guidance decisions, authority, protected behavior, coverage, accepted evidence and current direction identity when required. Leave implementation mechanisms to Project Fit.
- Use frontend-runtime-qa after visible implementation or for explicit rendered QA. In FULL, required design evidence must be accepted or promoted before implementation. Required ImageGen outputs need user-authorized acceptance. A design-only run has no implementation targets. Runtime QA binds separate PASS evidence to every required output. FULL delivery completes only when the user accepts the runtime gallery digest.

Complete the requested decision when its scope, research, MWG outcome, preserved capabilities and material choices are supported. Review the actual artifact when requested. State any gap that limits the recommendation. Present the chosen design and its main trade-off in user terms. Write durable evidence only where the authorized handoff or artifact needs it, under the ignored Workbench session for workflow state.
