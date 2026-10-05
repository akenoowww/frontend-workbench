# FULL runtime and fidelity gates

Read this only for `workflowProfile: full`: dependent/coherent design anchors, approval checkpoints, durable resume/promotion, or design-to-implementation fidelity. Also read [the shared FULL lifecycle contract](../../frontend-product-design/references/full-lifecycle.md).

## Require confirmed v3 identities

Before an expensive call, validate the active helper-owned session and current revision. The handoff must bind:

- confirmed full contract, structure, and coverage digests plus the authority receipt bound to those identities and the current action;
- product-model root, current domain/scenario IDs, surface primary object, required capability-requirement IDs, and nested shell;
- locked visual-direction path/SHA when required;
- applicable reference-binding IDs/source SHAs;
- the current output with `designEvidenceRequired: true` and `artifactKind: imagegen`;
- artifact kind, checkpoint requirement, and remaining render budget;
- non-null `anchorOutputId`, exact `anchorArtifactSha256`, and the renderer brief's preserve/change-only requirement when continuity is required.

Do not reconstruct any identity from chat or one screenshot. A missing, changed, stale, or mismatched identity is blocked and returns to its owning layer.

Direction lock is not artifact acceptance. A changed domain/scenario, protected capability or owner/constraints, evidence flag/kind, direction, shell/product owner, reference scope, anchor, implementation authority, or render budget requires explicit lifecycle change control before another call. The authority receipt plus change-control record binds base contract/structure digests, canonical delta, resulting contract/structure digests, exact action, and user turn; “current” or pre-change-only authority is insufficient.

## Keep design anchors separate from runtime coverage

Derive two v3 sets from output flags:

- outputs with `designEvidenceRequired: true` — representative design anchors;
- outputs with `runtimeEvidenceRequired: true` — every required scenario/surface/state/viewport/scroll capture, with route identity when the surface is routable.

ImageGen transitions only declared design anchors with `designEvidenceRequired: true` and `artifactKind: imagegen`. A runtime-only output does not enter the ImageGen queue. Stopping, deferring, or completing ImageGen never removes that output from Runtime QA.

Under `imagegen-required`, every required design anchor must use real PNG/JPEG/WebP bytes, valid ImageGen provenance, and exact user-authorized acceptance before implementation. The policy does not require a raster for every runtime-covered surface/state/viewport.

Design-output statuses remain:

```text
pending -> generating -> reviewing -> accepted -> promoted
                        |       |
                        |       +-> awaiting-approval -> accepted
                        +-> pending

pending/generating/reviewing/awaiting-approval -> blocked
pending/blocked -> deferred
blocked -> pending
```

At most one connected output may be generating or reviewing. An explicit awaiting-approval checkpoint blocks continuation. In v3 review-before-implementation, internally reviewed outputs with approvalRequired: false may become accepted anchors for serial continuation; this is not user acceptance, and exact design-set/direction authorization still precedes implementation or durable promotion. A required unfinished design anchor blocks the design gate. A deferred design output needs explicit upstream authority and may not silently defer its runtime counterpart.

## Enforce artifact kind and provenance

An ImageGen artifact always requires a file-backed receipt and non-symlink trace binding session, output ID, artifact SHA, and locked direction SHA, regardless of whether the overall artifact policy is `runnable` or `imagegen-required`. Declaring different policy or renaming a PNG does not change its kind.

Provenance proves trace integrity, not provider authenticity, semantic quality, acceptance, or runtime behavior. A runnable/specification/browser artifact follows its own kind and evidence rules; do not substitute one kind for another.

## Enforce the render budget

Validate `renderBudget.maxCallsTotal`, `maxAttemptsPerOutput`, and `maxConceptResets` immediately before every render. Count actual external calls. A concept reset is an explicit Product Design-authorized replacement of the current concept/direction before another render; a targeted artifact retry is not a reset. Status transitions, review, retries, batches, carry-forward, or resume do not reset the count.

The helper atomically reserves the total call, per-output attempt, and any concept-reset increment before the external call; concurrent independent work cannot race past the budget. Block before a reservation that would exceed a limit. A negative/invalid budget or a budget changed after confirmation is a contract failure. Raising or relaxing the budget requires fresh material-change authority; reducing it must not erase calls already consumed.

When the requested deliverable includes a continuous complete-page image and its selected method is ImageGen, include a final assembly output in the confirmed contract. Separate page/state design images do not need an extra composite unless that deliverable is required. Budget one initial call for each band plus one for that page's assembly; it consumes a normal per-output attempt and total call through the helper. It is not post-processing outside `renderUsage`. Only an explicitly requested one-call overview needs no extra assembly call; a normal full-page delivery is rendered as source bands plus assembly. When local-only delivery is explicitly requested before confirmation, do not add an ImageGen assembly output or budget; preserve the normal source-band obligations.

A renderer defect may use one targeted retry only when the output and total budgets permit. A product-model, structure, shell, reference, direction, or impossible-density failure returns upstream and does not justify a concept reset inside ImageGen.

## Validate visual anchors independently of dependencies

`dependsOn` controls ordering/evidence dependency. It does not imply visual anchoring.

When `anchorOutputId` is non-null, the renderer brief must supply an `anchorRequirement` for that source and the helper must bind the accepted source bytes as `anchorArtifactSha256`. Validate the source remains accepted/promoted and that the anchor SHA plus structure, reference, shell, direction, and render-brief identities remain current before rendering.

A root design output has no anchor. Carry-forward from another session requires explicit lineage and an exact matching accepted artifact SHA. Copying a file, reusing a path, or describing “the same style” is insufficient.

## Canonical workspace

Use the active consumer repository's ignored session:

```text
.frontend-workbench/sessions/<session-id>/
  state.json
  structure.json
  coverage.json
  artifacts/<output-id>/attempt-<n>.<ext>
  provenance/
  art-direct-imagegen/
    render-briefs/
      <output-id>.json
    assembly-plans/
      <assembly-id>.json
    prompts/<output-id>.md
    reviews/<output-id>-attempt-<n>.json
    handoff.md
  product-design/
    visual-direction.json
    critiques/<output-id>-attempt-<n>.json
  qa/
```

Before the first write, require the exact root ignore rule `/.frontend-workbench/`; stop if the directory is tracked, unignored, symlink-escaped, or outside the consumer workspace. Never use plugin source as a greenfield consumer.

Use only the installed helper's documented interface. Do not hand-edit runtime state, create a parallel state writer, or invent unsupported flags. The root orchestrator is the sole state writer and ImageGen caller; subagents may inspect/review bounded evidence but may not render connected outputs, consume authority, promote, or clean up.

## Serial render execution

1. Validate session/revision, base/delta/result change-control identities when applicable, product/domain/scenario/capability trace, current design-evidence output, artifact kind, budget, direction, shell, references, and any required anchor output/SHA.
2. Compile and hash the lean render brief. Confirm it contains only current-output content, applicable bindings, inherited shell invariants, and the allowed anchor delta.
3. Record the actual attempt, transition the output, and invoke exactly one ImageGen call.
4. If the call yields, wait for its final result. An unknown paid-call outcome becomes blocked with an exact reconciliation action; never retry blindly.
5. Save returned bytes under the output directory and attach the verified provenance receipt before review.
6. Apply bitmap/output-contract review and, for the first representative artifact, the shared direction critique.
7. Return a bounded execution defect to pending only when a retry remains. Return product/structure/direction/reference failures upstream. Move a passing approval checkpoint to awaiting approval or accept it according to the contract.
8. Bind user acceptance to the exact reviewed path/SHA. Modified bytes require review again.

Persist lean prompts, reviews, hashes, consumed budget, and next action in stage files. The helper owns central status, revisions, identities, blockers, and promotion. Never store base64, secrets, or hidden reasoning.

Batch only independent results already known. A v3 batch must not repeat one output ID, parallelize connected renders, consume authority, or bypass budget/anchor/review gates.

## Final assembly output

Only when the requested deliverable includes one continuous complete-page image and its assembly method is ImageGen, declare that final page before confirmation as its own `artifactKind: imagegen`, `designEvidenceRequired: true` output with `dependsOn` listing the necessary source bands. A set of separate page/state images needs no automatic composite. Reuse product/surface/state identities and name its canvas as an authored full page rather than inventing a route, state or viewport capture. Assembly itself does not add runtime coverage; existing obligations remain intact.

Save the ordered source IDs/paths/SHAs, union content allowlist, permitted join/overlap edits, and target dimensions in `art-direct-imagegen/assembly-plans/<assembly-id>.json` as a stage file. The helper-bound JSON at `art-direct-imagegen/render-briefs/<output-id>.json` has a closed schema: only `schemaVersion`, `outputId`, `visualDirectionSha256`, `shellIds`, `referenceBindingIds`, `anchorOutputId`, `anchorArtifactSha256`, `preserve`, and `changeOnly` are allowed. Put preservation, source identity, and permitted-edit instructions in its existing `preserve`/`changeOnly` string arrays; do not add assembly metadata keys to that bound file or to central state. Compile the renderer prompt from both files while keeping IDs and hashes out of visible copy. This does not add a content-distribution band. Verify every source is accepted/promoted and unchanged before attaching its full saved bytes. The one optional `anchorOutputId` binds only that source; validate the rest explicitly from the dependency artifacts.

Transition this output through the existing generating, provenance, review, and acceptance flow. The helper reserves its render call exactly as for a band. The assembly is a new artifact: it neither overwrites nor retries any accepted source output, and acceptance of those sources does not accept it. Under `imagegen-required`, it also requires user-authorized acceptance before implementation. If an older confirmed session lacks the assembly output/budget, resolve it through existing change control before rendering; do not hand-edit state or call outside the budget. Assembly failure or an unknown external-call outcome follows the same bounded failure/reconciliation rules as any other render.

## Implementation and runtime evidence

Design and implementation are distinct gated stages:

1. Settle every required design anchor while preserving its direction, artifact, provenance, reference, shell, and anchor identities.
2. Begin implementation only when authorized. A FULL design-only session legitimately stops without implementation targets.
3. When implementation is authorized, consume the validated plan binding exact safe targets to surfaces/capabilities and let the helper capture baselines. Project Fit may realize the design with mature internal/project/framework/library capabilities; accepted bitmap controls are not implementation specifications.
4. Runtime QA exercises every output with `runtimeEvidenceRequired`, including those with no design artifact, across its scenario/surface/state/viewport/scroll identity and route when one exists. It tests product behavior, data/error/recovery, accessibility, responsive transformation, console/network health where relevant, and planned complex-control behavior.
5. For an output with accepted design evidence, fidelity compares only the hierarchy, shell, direction, and visual invariants owned by that artifact. For a runtime-only output, verify coherence against the direction without inventing pixel requirements.
6. Store distinct runtime screenshots/manifests under `qa/` and bind them to scenario/surface, state, viewport, scroll position, optional route, dimensions, implementation-plan identity, direction SHA, and accepted design SHA when one exists.

Never reuse accepted design bytes as a runtime screenshot. An implementation build, source diff, screenshot, or hash cannot substitute for semantic interaction checks. Completion requires current PASS evidence for every runtime-required output and the lifecycle's implementation/target conditions; it enters final user review rather than automatic completion.

Present the digest-bound runtime gallery, clearly distinguishing outputs that had representative design anchors from runtime-only coverage. Only the user's explicit decision on that exact delivery digest completes or rejects delivery.

## Resume, promotion, and cleanup

On resume, validate session/revision, authority, direction, contract/reference/shell/brief hashes, consumed budget, and every accepted/promoted artifact. Preserve accepted work and reconcile stale active outputs; never regenerate an accepted/promoted anchor.

Rejected, superseded, and completed sessions are terminal. Continue a material change only through explicit lineage and base/delta/result-bound authority. A child session cannot rename, narrow, reassign, omit, or make root protected capabilities/runtime coverage optional.

Promote project-bound artifacts only through the helper and verify destination bytes. Cleanup is terminal and session-scoped; never delete an unpromoted accepted artifact or target a broad repository path. A blocked handoff preserves completed outputs, the blocker, and exact resume action.
