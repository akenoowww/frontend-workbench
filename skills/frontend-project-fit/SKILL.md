---
name: frontend-project-fit
description: "Fit scoped frontend implementation to an existing repository. Not for design-only or backend-only work, or when project source is unavailable."
---

# Frontend Project Fit

Make an authorized frontend change through the host project's existing architecture.

## Choose the workflow profile

Use the lightest profile that proves the requested outcome:

- **MICRO** — a read-only source diagnosis or one fully specified local fix with no new primitive, dependency, cross-route behavior, or material copy decision. Inspect the affected owner and run the smallest relevant check. Do not automatically invoke Copy Guard or Runtime QA.
- **STANDARD** — a scoped component or route change that affects state, localization, accessibility, interaction, or rendered behavior. Load only the references and adjacent skill needed by that impact.
- **FULL** — a multi-route change, foundational primitive or dependency, implementation of an approved redesign, or a checkpointed design contract. Consume the frozen handoff and its implementation plan, then require full rendered fidelity evidence.

Escalate a profile only when repository evidence reveals a criterion above. If a durable coverage contract exists, preserve its workflowProfile.

## Scope and authority

- For review or diagnosis, inspect and report without editing.
- For implementation, inspect the affected path before editing and preserve unrelated user changes.
- Consume approved structure and design handoffs when they exist, including the implementation plan, operational metadata policy, and locked visual-direction reference/SHA when required; do not manufacture a design phase for specified work.
- Do not turn a local change into a design-system or architecture migration without authorization.
- If the affected source is unavailable, state the evidence gap instead of inventing conventions.

This skill owns implementation fit, reuse, capability choice, integration, and source validation. It does not own product direction, ImageGen, rendered QA evidence, or unrelated backend contracts.

## Load references conditionally

- For STANDARD or FULL, read [references/project-discovery-and-reuse.md](references/project-discovery-and-reuse.md) before planning or editing. MICRO may inspect the bounded path directly.
- Read [references/capability-and-dependency-selection.md](references/capability-and-dependency-selection.md) when introducing or replacing a capability owner, or whenever complex/foundational UI is in scope.
- Read [references/architecture-and-validation.md](references/architecture-and-validation.md) for an uncertain integration boundary or a STANDARD/FULL handoff.
- For FULL, read [the lifecycle contract](../frontend-product-design/references/full-lifecycle.md) and use its compact helper handoff, including the validated v3 implementation plan, instead of reconstructing state from chat. Treat a missing, stale, or mismatched plan as a blocker to implementation rather than filling it from memory.

## Fit the change

### Trace and reuse

Follow the requested behavior through the relevant route, component, state, data, error, localization, accessibility, style, and test owners. Inspect one or two closest existing surfaces. Reuse or extend compatible public primitives; do not create a competing styling, state, fetching, form, validation, error, or localization system for convenience.

For each `capabilityRequirement` in a FULL implementation plan, validate `capability`, `complexity`, and `constraints` against current project evidence before editing. Inventory the existing project component/system/library owner first: dependencies and lockfiles, workspace packages, framework or platform facilities, internal primitives, feature-local compositions, and their tests. Then inspect credible mature libraries when the existing project and framework do not satisfy the requirement. The plan is a frozen decision input, not permission to skip repository discovery; return a plan delta when current truth invalidates it.

Ignore .frontend-workbench/ as product evidence.

### Gate complex and foundational capabilities

Treat graphs, editors, forms and validation, charts and data visualization, overlays and focus management, drag and drop, virtualized tables or trees, scheduling, rich media, and similarly stateful or accessibility-sensitive controls as complex/foundational capabilities. Apply the same gate to a new cross-route primitive even when its first use appears small.

Each plan decision must use one `selectedApproach`: `reuse`, `extend`, `compose`, `platform`, `framework`, `external-dependency`, or `project-owned`. Verify its `decisionTier`, `candidates`, `evidenceRef`, `selectedCandidate`, `gap`, `lifetimeRationale`, `obligations`, and `validation` rather than accepting a label alone. Use `direct` for bounded choices, `known-fit` for a complex non-project-owned capability whose exact fit is already proven by current project/session evidence, and `comparative` for foundational work or a complex project-owned primitive. A `known-fit` mature graph/chart/editor/form/overlay library is a successful reuse decision; do not manufacture a second candidate merely for ceremony.

Do not implement a project-owned complex/foundational primitive unless the plan documents the concrete gap left by the existing project owner, platform/framework facilities, and credible mature candidates; explains lifetime cost and risk; assigns maintenance, accessibility, security, migration, and compatibility obligations as applicable; and names focused automated plus rendered interaction validation. Missing evidence is a blocked capability decision, not an invitation to hand-write the control.

If the selected dependency is not already available and installation is not explicitly authorized or the environment has no registry access, preserve the library decision and mark implementation `BLOCKED`. Never silently replace it with custom SVG, canvas, or a bespoke interaction model just to produce visible output.

### Choose and implement the mechanism

If no established owner fits, define the required behavior and constraints before comparing plausible options from the actual stack. Keep a trivial rationale to one sentence; preserve fuller evidence for a dependency, complex/foundational primitive, security-sensitive behavior, or deviation from project practice. A mature external dependency is a credible candidate, not an automatic choice; inspect current primary evidence and its fit before selection.

Implement at the project's existing route, component, state, data, permission, localization, telemetry, and test boundaries. Prefer composition and supported variants over copies.

Implement the plan as vertical slices that connect one user job through its route, typed data/state/error contracts, capability owner, visible states, and focused tests. Prefer explicit adapters and discriminated state at boundaries over a page-scale monolith, duplicated fixture/live models, or custom controls that mix rendering, persistence, orchestration, and interaction logic. Shared extraction follows demonstrated responsibility and reuse; it is not a prerequisite for the first slice.

Do not render verification, freshness, source/provenance, sync/processing, confidence, or service-health fields merely because the data contract exposes them. Preserve the hidden default and implement only operational claims authorized for the current surface/state; route any changed visible wording through frontend-copy-guard.

### Route adjacent work without cascading

Invoke frontend-copy-guard only when the task actually changes user-visible wording or maps backend-shaped values into UI language. In MICRO, do so only when copy is the requested change or the edit alters material pricing, eligibility, consent, safety, destructive-action, or recovery meaning.

Invoke frontend-runtime-qa only when the user requests rendered proof, the defect depends on rendering or interaction, the change materially affects layout/flow/accessibility, or the profile is FULL. A source-only diagnosis or trivial bounded fix does not trigger it merely because frontend code was inspected.

For durable STANDARD and FULL work, supply the exact safe repository-relative files being implemented through predeclared implementationTargets or repeated `--implementation-target` arguments; the helper fingerprints them before changes and binds runtime evidence to their post-change snapshot. Do not record PASS before those targets materially change, and rerun QA after any later source change. For FULL, do not edit implementation code until the documented begin-implementation command succeeds after any required visual direction is locked and all required design outputs are accepted or promoted. Validate the implementation-plan identity and direction reference/SHA from the compact handoff instead of reconstructing architecture or style from chat or one artifact. Under `imagegen-required`, acceptance must be user-authorized.

Treat `executionEnvelope.selectedReferenceSlices` as the complete stage reading list unless current repository evidence creates a named gap. This is the token boundary: do not preload every bundled skill or reference.

### Validate proportionally

Run focused tests and the project-standard type, lint, build, or integration checks relevant to the changed path. Keep source checks, rendered evidence, and production proof distinct.

MICRO may finish on focused source or automated evidence when the result is not rendering-dependent and rendered proof was not requested. STANDARD uses the smallest rendered check that proves material visible behavior. FULL preserves the renderer-neutral direction principles while choosing project-compatible implementation mechanisms, then hands the locked direction reference/SHA, accepted artifact hashes, and required routes, states, viewports, scroll positions, and dimensions to Runtime QA; implementation completion enters final gallery review and does not imply user acceptance.

For read-only work, write no workflow artifacts. When STANDARD or FULL needs durable cross-skill state, use only the ignored /.frontend-workbench/ runtime workspace; never place prompts, reports, mockups, or QA evidence in product source.

## Completion

Finish when every affected capability has a plan-bound owner and reuse decision, no competing system, unjustified custom primitive, monolith, or stray artifact was introduced, proportional checks passed, required rendered proof is present or explicitly blocked, and remaining uncertainty is stated.
