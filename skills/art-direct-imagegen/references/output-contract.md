# Output contract core

Read this for every render. It defines one truthful bitmap output without loading FULL checkpoint mechanics.

## Normalize one output

Treat upstream product objects, protected capabilities, nested shell, page/state/viewport, content, interaction, scoped references, visual direction, and evidence policy as authoritative. For a standalone request, derive only what the user explicitly named and synthesize a bitmap-only direction through the shared Product Design reference.

A source used to understand behavior is not automatically an ImageGen input. Keep `FUNCTIONAL_REFERENCE` bytes analysis-only when its scoped content, states, relationships, and interaction facts can be expressed completely in the current-output brief. Attach source bytes only when a declared binding depends on an exact visible invariant or relationship that semantic facts cannot preserve; expose the narrowest applicable region and name the source's style, brand, shell, layout, and unrelated content as non-authoritative. Visual preservation requires an applicable `VISUAL_ANCHOR` or `EDIT_TARGET`, not silent promotion of a functional source.

For a redesign, require the direction's `redesignBoundary` before prompting. `preserveRegions` is an allowlist, not a hint: preserve only those named regions and invariants. Every other affected region must be declared under `replaceRegions`; keep its `mustChange`, `minimumChangedDimensions`, and `forbiddenCarryover` exact in the review contract. The renderer prompt carries the preserve-only scope plus a positive product/perceptual departure for each replace region, not a recitation of rejected source forms. “Keep the sidebar” cannot become “keep the recognizable shell.” Missing or broadened boundary is `BLOCKED` before ImageGen.

When `contentDistribution.strategy` is `progressive-scroll`, render separate outputs for the first viewport and continuation. Each band assigns stable `contentIds`; these are the visibility allowlist for that output. A source fact, metric, action, or module keeps one ID across bands—do not rename it “summary” and “detail” to duplicate it. Only IDs listed in `sharedContentIds` may repeat, and that list is normally empty; persistent shell invariants do not need content IDs. Each prompt contains only its band's content plus shared shell/truth constraints. Use the accepted top artifact as the visual anchor for the continuation when continuity matters. Do not repeat all data in both images or shrink the entire page into one screenshot.

`mustRemainReachable` protects the complete product and later runtime coverage. It does not require every protected capability or fact to appear in the representative design bitmaps. Absence from a top/continuation design anchor never authorizes removal from implementation; Runtime QA proves reachability across the complete surface.

The renderer may choose composition inside the direction's semantic hierarchy and role constraints. It may not redefine product structure, change the primary object, replace an inherited shell, broaden a reference, invent controls/states/claims, or prescribe implementation ownership. A distinctive bitmap does not authorize hand-written controls; it must remain realizable through mature project, framework/platform, or library capabilities.

When a locked structural or relational direction declares a representation grammar, preserve its context model, relation carrier, focus transition, and entity embodiment. These fields decide how meaning is carried, not where elements sit: composition, exact topology, coordinates, component geometry, palette nuance, and material execution remain renderer choices unless separately locked.

Relational truth is current-output content. For every supplied relation whose endpoints or direction affect meaning, carry the exact subject, predicate, object, and direction into the renderer brief. A bag of node and edge labels is insufficient. Keep arrangement, connector form, grouping, emphasis, and every other visual encoding choice open to the renderer unless the locked direction constrains them.

Parallel content sets are not related merely because their lengths or ordering match. Without an explicit supplied relation, do not pair projects with capabilities, people with statuses, records with categories, or any analogous sets through adjacency, shared containers, repeated alignment, or one-to-one sequencing. Keep each set independently legible or request the missing mapping.

Bound relational design evidence to what one bitmap can communicate truthfully. If the complete graph or dependency set would make exact relations illegible or dominate the prompt, declare a representative current-output subgraph/content band and keep the remaining supplied topology under `mustRemainReachable` for runtime evidence. A preview may use only explicitly authorized non-semantic ambient structure; it may not invent apparently real nodes or edges merely to make a sparse graph look rich.

A representative band must preserve primary-object identity. Hiding non-current content may reduce detail, but it cannot make the requested product object read as a different artifact type merely because that completion is easier for the renderer. The object should remain recognizable from its relational behavior and context even when titles and exact labels are ignored.

Operational metadata is hidden by default. Include verification, freshness, provenance/source, sync/processing, confidence, or service-health text only when `operationalMetadataPolicy.requiredClaims` contains an exact claim for this surface/state with `user-request`, `product-requirement`, `approved-design`, or `legal-safety` authority and a concrete `sourceRef`. Existing UI, available data, internal proof, an accepted design, or renderer judgment does not authorize it.

Output IDs, filenames, artifact names, fixture descriptions, and internal purpose statements are not visible product copy. Render them only when the supplied current-output content explicitly authorizes the same string as a label.

Direction theses, metaphors, candidate names, and explanatory relationship prose are instructions, not visible copy or icon authority. Compile them into nonverbal emphasis, cadence, contrast, disclosure, and continuity constraints. Do not give ImageGen caption-ready wording or symbolic implications that could appear as an unsupported headline, annotation, badge, lock, checkmark, success mark, or outcome.

For MICRO/STANDARD, stop at a concise brief containing the bounded objective, one requested bitmap, applicable input roles, current content, direction, truth constraints, and delivery path. Do not manufacture FULL IDs, shell hashes, budgets, approvals, promotion, or runtime state. The typed fields below apply only when an upstream FULL v3 contract exists.

In FULL v3, render only outputs with `designEvidenceRequired: true` and `artifactKind: imagegen`. Outputs with `runtimeEvidenceRequired: true` remain authoritative for the scenario → surface → state → viewport → scroll trace, with a route only when the surface is routable; they do not automatically become an ImageGen set.

Each v3 output has stable coverage identity:

```text
id: workspace-default-wide
surfaceId: workspace
state: default
viewport: wide
scrollPosition: top
designEvidenceRequired: true
runtimeEvidenceRequired: true
artifactKind: imagegen
approvalRequired: true
dependsOn: []
promotionRequired: false
promotionTarget: null
anchorOutputId: null
```

Keep renderer-only guidance separate under the same ID:

```text
purpose: what this bitmap must communicate
visualDirectionRef: product-design/visual-direction.json
visualDirectionSha256: <locked semantic digest>
domainIds: <confirmed domains exercised here>
scenarioIds: <confirmed scenarios exercised here>
primaryObjectId: <surface owner>
protectedCapabilityRequirementIds: <required capabilities exercised here>
shellIds: <declared outer-to-inner shell ancestry>
shellSha256: <validated shell contract digest>
now: only content visible in this output
exactLabels: critical short labels only
invariants: truth, hierarchy, and continuity locks
referenceBindingIds: only bindings applicable to this surface/aspect
anchorRequirement: null
renderBriefSha256: <validated brief digest>
```

When the contract's `anchorOutputId` declares visual continuity, keep the renderer requirement and runtime SHA distinct:

```text
anchorRequirement
- sourceOutputId: <anchorOutputId>
- preserve[]
- changeOnly[]

runtime output
- anchorOutputId
- anchorArtifactSha256
```

The runtime helper owns `anchorArtifactSha256` and validates it against the accepted `anchorOutputId`; the stage handoff separately preserves the current render-brief, shell, direction, and reference identities. A path, copied image, chat statement, or similar-looking result is not a valid anchor. `dependsOn` expresses ordering/evidence dependency and is independent of visual anchoring; do not infer `anchorOutputId` from it.

For MICRO/STANDARD, these fields may stay as a concise conversational brief. A typed FULL coverage contract must not contain renderer prose; keep it in the Product Design/ImageGen handoff. An upstream material render without a valid direction reference/SHA or applicable reference binding is blocked.

Reject duplicate IDs, missing surfaces/briefs, an output without required ImageGen design evidence, invalid artifact kind, dependency cycles, unknown shell/reference IDs, stale hashes, or a missing/mismatched `anchorArtifactSha256`. Do not merge page, state, viewport, scroll position, design evidence, and runtime evidence.

## Enforce attempt identity

MICRO permits one ImageGen call for one output. STANDARD permits one call per output in a pre-render frozen coverage set when IA/Product Design established that multiple named scroll bands, page-family screens, or related outputs are necessary to fulfill the user's requested artifact. This required decomposition does not need the user to spell out an output count. Optional variants, alternative concepts, and speculative extra pages do require explicit authorization.

Before the first STANDARD call, freeze the full set's IDs, order, semantic responsibilities, content IDs/allowlists, delivery paths, dependencies, visual anchors, and total call ceiling. Derive the number of outputs from legibility, hierarchy, interaction/scroll semantics, and page jobs; never use one, two, or another fixed count as a default. Do not add an output after rendering starts, and do not merge frozen bands to save calls. Review each saved result before the next. `REVISE_ARTIFACT` is a truthful turn result, not permission for an autonomous second generation or later-output continuation. A later user message may authorize one retry; that retry must use the saved failed artifact as `EDIT_TARGET`, preserve its artifact identity in the handoff, and express one bounded delta. It must not issue another from-scratch `Create <same-output-id>` prompt. A complete/material redesign of an existing page normally uses FULL with a locked `redesignBoundary` and render budget. It may stay STANDARD only as an explicitly non-promotable preview evaluation with supplied target, preserve/replace boundary, scoped reference roles, a frozen coverage set, a bounded call ceiling, and no implementation or durable acceptance. Default each output to one attempt unless the confirmed contract explicitly authorizes more.

Input roles are immutable within an attempt lineage. A supplied `STYLE_REFERENCE`, `FUNCTIONAL_REFERENCE`, or `VISUAL_ANCHOR` cannot become `EDIT_TARGET` because the first result was weak. Only the generated artifact being revised, or a source the user explicitly supplied as an edit target, may have that role. If a new reference changes the direction rather than a bounded artifact defect, start one new initial attempt in the new user turn and stop after its review.

## Enforce the render budget before the call

FULL v3 confirms this whenever any output uses `artifactKind: imagegen`:

```text
renderBudget
- maxCallsTotal
- maxAttemptsPerOutput
- maxConceptResets
```

Count actual render calls. A concept reset is an explicit Product Design-authorized replacement of the current concept/direction before another render; a targeted execution retry is not a reset. The helper atomically reserves the call, output attempt, and any concept reset before invoking the external renderer so concurrent work cannot race past the budget. Review, status changes, retries, batching, carry-forward, or policy changes do not reset or bypass counters. Block before a call that would exceed any limit. A product-model, structure, direction, reference-scope, shell, or density contradiction returns upstream without spending a retry.

## Render and review

- Generate exactly one output per ImageGen call; never use a collage or one call for distinct states.
- Include only current-output content, applicable reference roles, and critical labels in its prompt.
- For a distributed surface, compare the final renderer prompt against the current band's `contentIds`; any other band's exact label, value, status, action, or renamed equivalent blocks the call.
- Preserve supplied truth, primary-object priority, shell identity, and state semantics. A density conflict is a contract blocker, not permission to invent another page.
- For an anchored output, verify the bound source bytes/SHA, preserve list, and `changeOnly` delta before prompting; review those invariants again on the saved result.
- Review the saved artifact for identity, purpose, required content, misleading text, invented behavior, legibility, scoped-reference fidelity, shell continuity, and feasible implementation latitude. Apply the shared direction critique to the first representative artifact.
- For redesigns, record a delta ledger for each replace region: which declared material dimensions changed, which preserve-only invariants remained, and whether forbidden carryover survived. Fewer than `minimumChangedDimensions`, or preservation of the old main-content macro-layout/module topology outside the allowlist, fails regardless of polish.
- Build the visible-claim ledger from the rendered bitmap and reject every operational/status/owner/date/result phrase without an exact surface/state source. Never infer semantic safety from overall polish.
- In FULL, retry one bounded execution defect only after the helper reserves another attempt, and edit the failed artifact rather than recreating the output from original references. Return upstream direction or structural failure as `REVISE_DIRECTION` or `BLOCKED` instead of lengthening the prompt into a wireframe.
- Accept only saved bytes that pass review. An ImageGen artifact requires its declared provenance receipt regardless of whether the overall policy is `runnable` or `imagegen-required`.

MICRO/STANDARD report accepted or blocked results directly and follow system ImageGen save-path rules. They must not claim durable resume, approval, or promotion state.

Generated bitmap text and visuals are design evidence only. They never prove implemented routes, responsive behavior, accessibility, data integration, interaction, or production readiness. For FULL, read [full-runtime.md](full-runtime.md) before the first call.

## Compose a deterministic final overview

After every required output in a coherent set has passed review, create a combined visual index with an available deterministic local compositor such as ImageMagick or Pillow. Do not call ImageGen, change render-budget counters, reinterpret the direction, or overwrite source artifacts.

Choose the composition from the frozen output identities:

- **One surface with ordered progressive-scroll bands:** concatenate the accepted bitmaps vertically in content order. Keep original pixel widths, aspect ratios, and bytes visible without crop, stretch, overlap, generated separators, or invented page content. Matching viewport widths are a precondition; otherwise report the mismatch instead of silently resampling.
- **Several routes/pages:** create a contact sheet that preserves each bitmap's aspect ratio and labels each tile only with its authorized route or output ID outside the screenshot. Do not present separate routes as one continuous scroll.
- **Mixed set:** first create one vertical composite per progressive-scroll surface, then create a contact sheet of those composites and standalone page outputs.

Verify the overview before delivery:

- source order matches the frozen coverage set;
- every required accepted output appears exactly once and no pending/rejected output appears;
- composite dimensions equal the deterministic arrangement of source dimensions;
- no source is cropped, stretched, overwritten, or substituted;
- the overview path and SHA are recorded together with ordered source paths and SHAs.

The overview is a navigation/review aid, not a new accepted design output and not evidence of implemented scrolling, routing, responsiveness, interaction, or production fidelity. If no deterministic compositor is available, deliver the reviewed originals and report the missing overview honestly; never use a generative call as the fallback.
