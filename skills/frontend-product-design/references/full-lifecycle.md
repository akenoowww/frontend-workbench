# FULL frontend lifecycle

Read this reference only when `workflowProfile` is `full` and work crosses structure, design, implementation, or rendered QA. Keep one helper-owned session as the source of truth; do not reconstruct authority or mutable state from chat.

## Confirm the product before choosing its visible scenario

FULL v3 confirms both product intent and the task-specific product-object hierarchy:

```text
productIntent
- problem
- representativeScenarios[]
- requiredDomains[]
- protectedCapabilities[]
- antiGoals[]
- successSignals[]

productModel
- rootObjectId
- objects[]
  - id / role / parentId / evidenceForObjectIds[]
  - role: root | primary | supporting | downstream-evidence |
          implementation-detail
- relations[]
  - id / fromObjectId / toObjectId / kind

capabilityRequirements[]
- id / capability / complexity / constraints
- ownerObjectId / surfaceIds / required
```

Derive them from the user's request and current project evidence. A scenario is one end-to-end job, not the product definition. A prominent dashboard, generated artifact, technical mechanism, or downstream evidence must not demote the primary work object or erase another required domain.

Protected capabilities are monotonic within a confirmed lifecycle. Later discovery may add detail or capabilities; it may not remove, narrow, rename away, transfer ownership of, or make an existing protected capability visually subordinate without explicit material change control.

Before FULL IA or design, give the user a concise teach-back covering:

- product meaning, object hierarchy, required domains, representative scenarios, and anti-goals;
- protected capabilities and what may not become the dominant object;
- nested shell ownership;
- operational-metadata visibility;
- visual-direction, artifact, checkpoint, reference-binding, and render-budget policies;
- design-anchor scope versus exhaustive runtime coverage;
- whether implementation is authorized now, later, or not at all.

Silence, source inspection, a general request to continue, or a boolean `userAuthorized` field is not a v3 authority receipt. Bind confirmation to the current session, user turn, intended action, and full contract/structure/coverage digests through the installed helper's documented authority mechanism before a dependent stage begins.

## Trace domains and objects to runtime coverage

IA owns the rich trace:

```text
required domain / product object
  -> representative scenario
  -> surface
  -> meaningful state
  -> material viewport
  -> runtime evidence output
```

Each scenario names its objects, entry, job-appropriate completion, and applicable recovery surfaces. Completion may be an answered question or stable resumable state, not only a mutation. Each surface names its scenarios and primary object. Every required domain and protected capability must reach at least one runtime-covered surface that owns the user job; mention in another page or downstream evidence is not coverage.

Design evidence is intentionally narrower. Outputs with `designEvidenceRequired: true` are the representative anchors needed to establish materially distinct shell, hierarchy, state, responsive, or visual mechanisms. Outputs with `runtimeEvidenceRequired: true` retain every required implemented route/state/viewport. Never make a runtime route optional because no bitmap was requested, and never rasterize every route merely because Runtime QA must visit it.

## Preserve nested shells and scoped references

Nested shells are structural owners. A child shell inherits the parent product identity, navigation, and persistent regions unless a confirmed structural replacement says otherwise. The v3 structure names the occupied parent slot through matching shell invariants because it has no separate `parentSlotId`; an ambiguous slot is a structure conflict. Product Design may design local navigation inside that slot but may not let a renderer invent a second application shell or brand.

Every supplied reference uses one or more scoped `referenceBindings` entries with source identity, roles, affected surfaces/aspects, and explicit non-influence boundaries. A functional reference does not become style authority; a visual anchor does not authorize behavior; a module-specific anchor does not redesign unrelated routes. Broadening a binding is a material contract change.

## Default operational metadata to hidden

The FULL contract carries:

```text
operationalMetadataPolicy
- defaultVisibility: hidden-unless-required
- requiredClaims[]
  - id
  - surfaceId
  - states[]
  - meaning
  - authority
  - sourceRef
```

Operational metadata includes verification/check status, freshness timestamps, provenance/source, sync or processing state, confidence, and service/connection health. Available data, internal proof, a generic trust goal, or agent judgment does not authorize display. Only `user-request`, `product-requirement`, `approved-design`, or `legal-safety` authority bound to the exact surface/state qualifies.

Existing UI is evidence to review, not authority to propagate a claim. Include non-empty claims in the teach-back. Product-model truth, protected capabilities, quality gates, provenance receipts, design artifacts, and runtime evidence never become UI copy by implication.

## Lock visual direction without prescribing bespoke code

Set `visualDirectionPolicy` explicitly:

- `required` — select and lock a renderer-neutral direction before the first material visual artifact or implementation;
- `not-required` — existing evidence and specified behavior already determine the work without a new direction.

For `required`, persist and lock the canonical `product-design/visual-direction.json` path and semantic SHA. Runnable prototypes, browser renders, and ImageGen outputs bind to the same direction. Direction lock and artifact acceptance are separate decisions.

The direction owns semantic hierarchy, signature relationships, density rhythm, typography/color roles, surface language, and continuity. It does not own component trees, packages, custom-control decisions, or implementation geometry. Product specificity must survive implementation through mature project primitives, platform/framework facilities, or suitable libraries; uniqueness never requires hand-written controls.

A material direction revision uses explicit invalidation or supersession. Never repair drift by mutating the lock, lengthening a renderer prompt, or asking implementation to imitate incidental bitmap pixels.

## Lock artifact, checkpoint, and render policies

Set `visualArtifactPolicy` explicitly:

- `runnable` — use project-compatible runnable evidence; ImageGen is optional;
- `imagegen-required` — generated evidence is required for the declared design anchors before code;
- `no-imagegen` — use specifications, project-native composition, or runnable evidence.

In v3, `imagegen-required` applies to outputs with `designEvidenceRequired`, not to every runtime-covered route. Every required ImageGen design anchor remains approval-required and user-authorized before implementation. Runtime-only outputs remain required for QA but do not consume design renders.

Record `checkpointMode` explicitly. A material redesign defaults to `review-before-implementation`; use `review-each-stage` only when requested or when a later design output truly depends on an accepted anchor. Do not infer a checkpoint decision from a request to proceed quickly.

Whenever an output uses `artifactKind: imagegen`, the confirmed `renderBudget` limits total paid/expensive calls, attempts per output, and concept resets. It is absent under `no-imagegen`. Count actual render calls, not status transitions. Review, batch operations, retries, carry-forward, or changing policy must not bypass it. Block before exceeding the budget; a product, structure, direction, or reference contradiction returns to its owner instead of consuming retries as prompt experiments.

`dependsOn` and visual anchoring are independent. Ordering alone does not create a visual anchor. A non-null `anchorOutputId` selects the source; the renderer brief's `anchorRequirement` records preserved/change-only constraints. Rendering may use only the accepted source whose exact bytes are recorded as `anchorArtifactSha256`, with current structure, reference, shell, direction, and render-brief identities. A path, screenshot resemblance, or chat statement is not an anchor binding.

## Separate design evidence, implementation, and runtime evidence

For every v3 output, keep `designEvidenceRequired` and `runtimeEvidenceRequired` independent:

- design evidence tests a proposed hierarchy, direction, or representative mechanism;
- implementation evidence proves source was changed within authorized targets and capability decisions;
- runtime evidence proves the implemented route/state/viewport and interactions;
- fidelity evidence compares only the visual invariants owned by the accepted design and locked direction.

An accepted PNG is not a runtime screenshot. A browser screenshot is not proof that an interaction, data boundary, recovery path, or complex control works. A green build is neither. Never reuse design bytes as runtime evidence.

When no design artifact is required for a runtime output, Runtime QA verifies product truth, interaction, accessibility, responsive behavior, and coherence against the locked direction without inventing pixel requirements. When a representative anchor exists, compare only the hierarchy and visual relationships it owns; do not copy sample data, fake controls, or incidental implementation details from it.

## Control material changes with authority receipts

Classify contract changes before continuing:

- **compatible addition** — adds detail while preserving product hierarchy, protected capabilities, shell ownership, policies, required evidence, references, anchors, and budget;
- **material change** — removes or demotes a protected capability/domain/scenario/surface, changes a primary object or shell owner, broadens a reference, relaxes checkpoint/artifact/evidence policy, replaces an anchor, changes implementation authority, or raises the render budget;
- **replacement** — changes product meaning or direction enough to invalidate dependent work.

A material change requires a fresh user-turn-bound authority receipt plus change-control record binding the base full/structure digests, canonical proposed delta, resulting digests, and exact action before mutation. A pre-change-only receipt, old receipt, copied confirmation, boolean flag, or approval of a different action cannot be replayed. Replacement uses explicit lineage and invalidates or supersedes affected artifacts, plans, and receipts. Do not silently downgrade `required` work to `optional` after a stage becomes inconvenient.

Continue one lifecycle through IA, Product Design, ImageGen when required, implementation, Runtime QA, and delivery. Create a child/replacement session only for a genuinely derived scope with explicit parent/supersession lineage. A narrow child cannot erase root coverage.

Do not silently reinterpret v1/v2 sessions as v3. Preserve their original rules or perform an explicit validated migration.

## Handoff to implementation without designing the mechanism

Implementation begins only when authorized and after required design evidence settles. A FULL design-only session legitimately keeps `implementationTargets` empty.

The frozen handoff carries the product/structure/coverage identities, protected capabilities, shell identities, scoped references, direction SHA, accepted design anchors, implementation authority, and unresolved items. When implementation is authorized, also bind an implementation plan mapping declared targets to surfaces/capabilities and recording capability requirements/decisions.

Project Fit must inspect current repository truth and is free—and expected—to realize the frozen semantics with existing project systems, supported component variants, framework/platform facilities, composition, or mature external libraries. A local implementation adaptation does not reopen design when it preserves user jobs, object priority, shells, behavior, coverage, and direction. A plan or design that requires a bespoke complex control without evidence of a real capability gap returns for revision.

## Keep quality gates separate

Direction lock, artifact acceptance, implementation state, and `qualityGates.intent`, `coverage`, `runtime`, `fidelity`, and `userAcceptance` answer different questions. Keep each `pending`, `pass`, `fail`, `blocked`, or `not-required` independently. Do not collapse them into “validated”.

Completion requires current runtime evidence for every runtime-required output, not merely settled design anchors. Present the final runtime gallery from distinct QA evidence, labeled with output, route, state, viewport, scroll position, dimensions, accepted design identity when applicable, locked direction SHA, and delivery digest. Only explicit acceptance of that exact delivery digest completes the lifecycle.

A declared evidence-equivalence exception must exist in the confirmed contract before evidence collection and match the exact output pair, evidence channel, and justification. Design equivalence never substitutes for runtime proof. Runtime equivalence is allowed only when the captured route/state/viewport evidence is semantically identical; convenience, an unvisited state, or an after-the-fact explanation is not equivalence.

## Keep orchestration compact

Use the helper's validated read-only handoff for subagents. Add only the task-specific route, object/capability, file owner, render output, or check. The root orchestrator remains the sole state writer and authority consumer.

Batch only already-decided independent transitions. A batch must not duplicate an output transition, invent authority, parallelize connected renders, bypass anchor/budget checks, or replace semantic review.
