# Artifact choice and validation

Use this reference after the product decisions and required coverage are stable enough to test.

## Choose by the decision being tested

Select the lightest artifact that can provide meaningful evidence:

| Need | Prefer |
| --- | --- |
| Information architecture, terminology, or state logic | Annotated specification or flow model |
| Fit with established project components | Existing-component composition |
| Interaction, focus, persistence, or responsive behavior | Runnable prototype or implementation |
| Visual correctness of implemented UI | Browser inspection and screenshots |
| Genuinely open visual direction | `VisualDirectionContract` through [visual-direction.md](visual-direction.md) |
| Explicitly requested generated UI bitmap or set | **$art-direct-imagegen** with the applicable direction, coverage, and evidence identities |

A direct Product Design request can be fulfilled through the selected specification, composition, or prototype. Generated images require explicit user scope or an authorized output that specifies ImageGen.

## Lock direction before choosing its renderer

For a material redesign, require the renderer-neutral direction contract and its lifecycle lock before producing a runnable, browser-rendered, or ImageGen artifact. The direction defines what must remain coherent; the artifact tests one execution of it. Changing the renderer does not authorize a new concept.

Direction lock is not artifact approval. Preserve the direction SHA and bind each reviewed artifact to its own path and SHA.

## Follow the visual artifact policy

Use project-compatible runnable evidence for `runnable`. Use specifications, project-native composition, or runnable evidence for `no-imagegen`. Route a declared `artifactKind: imagegen` output through its authorized workflow. With `imagegen-required`, pass the locked direction reference/SHA, protected product semantics, applicable reference bindings, nested-shell identity, and declared design-anchor coverage. Require user-authorized acceptance of every output with `designEvidenceRequired` before implementation.

The art-direction skill owns prompt compilation, render sequencing, continuity against the locked direction, and bitmap-specific critique. Product Design owns the direction and the shared conceptual critique.

For FULL v3, derive representative design anchors from outputs with `designEvidenceRequired: true` and exhaustive runtime coverage from outputs with `runtimeEvidenceRequired: true`. A design anchor may represent a page family only when hierarchy, shell, interaction shape, and responsive behavior are genuinely shared. Unique visual mechanisms and user-requested separate page designs remain separate anchors; other required routes stay runtime obligations without consuming ImageGen calls. Never use a small design set to waive runtime coverage, and never make every runtime route a raster merely because it must be tested.

For a landing, storefront, or other scrolling page, plan evidence for the complete content and responsive hierarchy. A specification can describe the section sequence, and a runnable page can expose its natural scroll and browser evidence. When generated scroll-band images are explicitly in scope, use [scroll and output planning](scroll-and-output-planning.md) to freeze their coverage, continuity and delivery method.

Honor the confirmed `renderBudget`: total calls, attempts per output, and concept resets are hard preflight limits, not targets. A structural, product-model, direction, reference-scope, or density contradiction returns to its owner before another render. Do not use retries to discover information the upstream contract should already contain.

Ordering and visual continuity are separate. `dependsOn` does not imply a visual anchor. A non-null `anchorOutputId` selects the accepted source; the renderer brief's `anchorRequirement` names what to preserve and what may change. Use only the source artifact bound by session/output identity and SHA.

If ImageGen is unavailable, continue with another valid artifact when the policy is `runnable` and it can test the decision. Under `imagegen-required`, report the required stage blocked rather than silently substituting another artifact or changing policy.

## Apply checkpoints

For **review-before-artifact**, show:

- selected direction and material trade-offs;
- required coverage;
- chosen artifact and why it can test the decision;
- any cost, latency, or fidelity consequence that changes the user's choice.

Do not pause for routine, reversible artifact production under **continuous**.

## Review evidence, not intent

Inspect the artifact actually produced. The first representative visual artifact of a direction must use the shared critique in [visual-direction.md](visual-direction.md), whether it is runnable or generated. Verify:

- the primary user job and necessary context remain clear;
- required pages, surfaces, states, and viewports are accounted for;
- hierarchy, density, actions, feedback, and recovery are coherent;
- project language and reusable foundations remain recognizable when required;
- responsive changes preserve task priority;
- controls and content do not promise unsupported behavior;
- the artifact is feasible in the current architecture.

Feasible does not mean pixel-identical or hand-built. Confirm that the hierarchy and signature relationships can be implemented with mature project, framework/platform, or library capabilities without treating generated controls as a component specification.

Use only `PASS`, `REVISE_ARTIFACT`, `REVISE_DIRECTION`, or `BLOCKED`; do not fabricate numeric quality scores. Bind a durable FULL critique to both the direction SHA and artifact SHA under the product-design session directory.

When execution is locally weak but the direction remains sound, return `REVISE_ARTIFACT`. When the idea is generic, contradictory, or unfit, return `REVISE_DIRECTION` and use the lifecycle's explicit invalidation or supersession path rather than lengthening the renderer prompt. When an artifact exposes a product or structure contradiction, return `BLOCKED` and revise the affected decision or coverage record. Do not hide it with visual polish.

Generated UI remains one visual-direction instance, not the direction contract, implementation specification, runtime evidence, or production proof. Implemented UI requires project-fit implementation and source checks through **$frontend-project-fit**, followed by distinct behavioral, responsive, accessibility, and rendered-flow evidence through **$frontend-runtime-qa** when available.
