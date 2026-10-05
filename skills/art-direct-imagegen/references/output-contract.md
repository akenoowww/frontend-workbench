# Output contract core

Read this for every render. It defines one truthful bitmap output without loading FULL checkpoint mechanics.

## Normalize one output

Treat upstream product objects, protected capabilities, nested shell, page/state/viewport, content, interaction, scoped references, visual direction, and evidence policy as authoritative. For a standalone frontend UI request, derive only what the user authorized and obtain a bitmap-scoped direction by applying the actual [Product Design skill](../../frontend-product-design/SKILL.md) in its direction-only entry. Do not synthesize a renderer-owned direction from a shared reference. Both entry modes consume the Product Design handoff before compiling a prompt.

For an existing product, also consume its affected functional baseline and capability mapping. An imported visual pattern or accepted bitmap cannot replace current actions, fields/data meanings, permissions, validation, persistence, or outcomes. A `preserve-only` boundary governs visual carryover, not which functionality survives. The bitmap may show representative content only when the remaining capability has an honest mapped control/state in the complete authorized design; omission from one viewport must not turn into deletion during implementation. Missing or contradictory mapping returns to Product Design rather than inviting a competitor-shaped substitute.

A source used to understand behavior is not automatically an ImageGen input. Keep `FUNCTIONAL_REFERENCE` bytes analysis-only when its scoped content, states, relationships, and interaction facts can be expressed completely in the current-output brief. Attach source bytes only when a declared binding depends on an exact visible invariant or relationship that semantic facts cannot preserve; expose the narrowest applicable region and name the source's style, brand, shell, layout, and unrelated content as non-authoritative. Visual preservation requires an applicable `VISUAL_ANCHOR` or `EDIT_TARGET`, not silent promotion of a functional source.

For a redesign, require the direction's `redesignBoundary` before prompting. `preserveRegions` is an allowlist, not a hint: preserve only those named regions and invariants. Every other affected region must be declared under `replaceRegions`; keep its `mustChange`, `minimumChangedDimensions`, and `forbiddenCarryover` exact in the review contract. The renderer prompt carries the preserve-only scope plus a positive product/perceptual departure for each replace region, not a recitation of rejected source forms. “Keep the sidebar” cannot become “keep the recognizable shell.” Missing or broadened boundary is `BLOCKED` before ImageGen.

When `contentDistribution.strategy` is `progressive-scroll`, first freeze `artifactTopology: separate-bands` (`single-tall` requires an explicit user request for one-call overview generation), `canvasRole: viewport-band | authored-full-page`, and `continuityRequirement: system-coherent | authored-breaks | seamless-page`. `system-coherent` preserves one visual system without implying a stitched page; `authored-breaks` permits visible section changes only when their handoffs look intentionally designed at full-scroll scale; `seamless-page` permits no accidental raw tonal cut, ghosting, separator, or second root start. For landing pages, storefronts, and other multi-section scrolling pages, use separate full-size bands by default and render them serially. Derive their count from content jobs and normal UI reading scale. Each band occupies the full desktop width and one normal viewport-height canvas, without page miniatures or compressing later sections into an introductory screen. One requested final file, a homepage, a complete page, sparse content, or preview-only scope does not authorize `single-tall`. That exception requires the user to explicitly choose generating the complete overview in one call; record that method choice before freezing. The assembled complete page remains a separate derived output.

For separate bands, each band assigns stable `contentIds`; these are the visibility allowlist for that output. A source fact, metric, action, or module keeps one ID across bands—do not rename it “summary” and “detail” to duplicate it. Only IDs listed in `sharedContentIds` may repeat, and that list is normally empty; persistent shell invariants do not need content IDs. Each prompt contains only its band's content plus shared shell/truth constraints. For final assembly or an explicitly authorized one-call overview, freeze the ordered band IDs and their union allowlist before the call; preserve their semantic jobs without forcing equal-height viewport panels. Do not repeat all data across bands, shrink a full page into one ordinary viewport, or relabel an authored full-page canvas as a device screenshot.

Within each ordered scroll sequence, declare `shellRole: root | continuation`, `shellOwnership: owns | inherits`, `shellOwnerOutputId`, and `shellChrome: owner-visible | headerless | explicitly-persistent`. A continuous-page root owns the outer shell and its chrome appears once; continuations inherit that identity and are headerless by default. Persistent chrome is valid only when the artifact is explicitly viewport evidence or product behavior requires it. These fields govern shell lineage and visibility, not layout, typography, palette, or composition.

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

For MICRO/STANDARD, keep a concise brief containing the bounded objective, complete necessary coverage set, current output's input roles/content/direction/truth constraints, order and delivery paths. MICRO uses one output only when it covers the whole request; STANDARD derives the separate readable outputs the page/flow needs. Do not manufacture FULL shell hashes, approvals, promotion, or runtime state. The typed fields below apply only when an upstream FULL v3 contract exists.

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

### Freeze coherent-set choreography

Before any ImageGen call in a coherent multi-output set, freeze a set-level plan containing:

- artifact topology, canvas role, target width/aspect, and the reason those preserve legibility and evidence quality;
- continuity requirement and the visible evidence that would satisfy or fail it;
- global visual-system invariants that every output shares;
- shell role, ownership, owner ID, and chrome state for every ordered output;
- each output's perceptual job, representation signature (`contextModel`, `relationCarrier`, `focusTransition`, and `entityEmbodiment`), and visual signature (`layoutGrammar`, `focalBehavior`, `density`, `imageTextRatio`, `assetFamily`, `hierarchy`, `imageryRole`, and `compositionRhythm`);
- imagery slots with stable IDs, semantic roles, and `reusePolicy: unique | shared | continued`;
- entry and exit transition contracts for adjacent scroll bands, including `transitionMode: continuous | deliberate-break | independent`, `exitState`, `entryState`, `handoffCarrier`, and `edgeTreatment`;
- the exact renderer-image exposure for each output or boundary, its continuity purpose, and its `mayInfluence` and `mustNotInfluence` boundaries;
- the final delivery method: ImageGen for a continuous page by default, or local-only when explicitly requested. Only the ImageGen method adds an assembly output ID and extra call; for either method record ordered sources, content coverage, target canvas, permitted edits, and delivery path in the stage handoff. A local comparison is a separate requested artifact, not a replacement for a requested ImageGen result.

The raw transition fields are planning and review evidence. Compile them into one non-geometric perceptual relationship for the renderer; do not serialize field names, edge coordinates, or a bridge/blend/gradient mechanism into the prompt unless the user explicitly locked that mechanism.

Global coherence comes from the locked role system, not repeated scenes or duplicated composition. Treat every generated subject, scene, crop, and hero-like image as `unique` unless an explicitly shared product/brand asset requires reuse. A shared color/material family does not authorize reuse of the same photograph, room, object arrangement, or crop.

Freeze a compact signature-distance row before rendering. It is an anti-template diagnostic, not a quota: adjacent bands may preserve many fields when physical or editorial continuity requires it, but changing only copy, heading, or image crop is insufficient. Each band's prompt must carry its own perceptual job, imagery role, focal behavior, density, and composition rhythm rather than reuse one template with substituted text.

For each separate-band boundary, choose the least contaminating renderer-image exposure that can preserve the actual invariant. Omit image bytes when the locked textual direction is sufficient. Use a scoped boundary/style region when local geometry, light, surface, typography, or material evidence needs bytes while the current imagery or layout must remain unique. When several small non-dominant regions are necessary, a deterministic `systemCapsule` may assemble them without generative fill: record every source crop/path/SHA, assembly operation, allowed influence, and contamination boundary; exclude root chrome, complete copy, and dominant scene geometry whenever possible. The capsule is reference evidence, not another design output or permission to copy its arrangement.

Use the accepted full immediate predecessor only when an exact continued spatial, structural, composed-shell, or explicitly continued-asset relationship itself is required and a scoped sample would lose that invariant. Shared typography, palette, material, mood, or “same style” alone do not justify full-screen exposure. If the current band declares `unique` imagery and a different layout grammar, full-predecessor exposure requires an explicit compatible continued relationship; otherwise scope down. A prompt statement that an image is “only an anchor” is not proof: record what may influence, what must not influence, and review the returned pixels for layout, scene, crop, and content leakage. Do not expose the same distant root/hero artifact to every continuation as a generic consistency device. A non-adjacent root may be used only for an exact declared invariant or explicitly shared asset, with the immediate predecessor still owning physical adjacency.

The final assembly is a distinct compositing operation: all reviewed source bands are inputs to preserve in one page, not style references for a new band. Its source roles and complete-page scope are declared separately from each band's immutable attempt lineage. Full source exposure is necessary here and does not authorize redesign or duplicate content.

Only for an explicitly authorized one-call overview, freeze the user's method choice, one `single-tall` output ID for the contiguous range, one shell owner, the target canvas/aspect, ordered content jobs, and reference roles before the call. Separate draft bands may remain scoped references, but they do not silently become one edit target or authorize copied pixels, duplicated shell chrome, or repeated imagery.

Block before the first call if topology, target canvas/aspect, shell ownership, imagery ownership, prompt-signature diagnosis, transition lineage, or reference exposure is unresolved.

MICRO permits one ImageGen call only when one output covers the whole request. STANDARD permits the complete required set, one call per output plus any requested continuous-page assembly, in a pre-render frozen coverage set when IA/Product Design established that multiple named scroll bands, page-family screens, or related outputs are necessary to fulfill the user's requested artifact. This required decomposition does not need the user to spell out an output count. Optional variants, alternative concepts, and speculative extra pages do require explicit authorization.

Before the first STANDARD call, freeze the full set's IDs, order, semantic responsibilities, content IDs/allowlists, delivery paths, dependencies, visual anchors, and total call ceiling. Derive the number of outputs from legibility, hierarchy, interaction/scroll semantics, and page jobs; never use one, two, or another fixed count as a default. When one continuous complete-page image is a required deliverable, budget its necessary source renders plus its ImageGen assembly. A set of separate page/state images does not acquire an assembly call merely because it contains several outputs. For explicitly local-only final delivery, budget only the N source renders (zero if the reviewed sources already exist); do not create a mandatory ImageGen assembly checkpoint. This does not fix N at two. Do not add an output after rendering starts or replace the declared band renders with the final assembly to save calls. Review each saved result before the next. `REVISE_ARTIFACT` is a truthful turn result, not permission for an autonomous second generation or later-output continuation. A later user message may authorize one retry; that retry must use the saved failed artifact as `EDIT_TARGET`, preserve its artifact identity in the handoff, and express one bounded delta. It must not issue another from-scratch `Create <same-output-id>` prompt. A complete/material redesign of an existing page normally uses FULL with a locked `redesignBoundary` and render budget. It may stay STANDARD only as an explicitly non-promotable preview evaluation with supplied target, preserve/replace boundary, scoped reference roles, a frozen coverage set, a bounded call ceiling, and no implementation or durable acceptance. Default each output to one attempt unless the confirmed contract explicitly authorizes more.

Input roles are immutable within an attempt lineage. A supplied `STYLE_REFERENCE`, `FUNCTIONAL_REFERENCE`, or `VISUAL_ANCHOR` cannot become `EDIT_TARGET` because the first result was weak. Only the generated artifact being revised, or a source the user explicitly supplied as an edit target, may have that role. If a new reference changes direction rather than a bounded artifact defect, return to Product Design and freeze the revised authorized set before a new attempt. MICRO still ends after one output; a successful STANDARD output may continue through that required set serially. Failure, unknown outcome, a budget/scope conflict or explicit checkpoint stops continuation.

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
- Include only current-output content, applicable reference roles, and critical labels in its prompt. A final assembly owns the declared union of its source bands; this is not permission to mix unrelated pages or states.
- Preserve the frozen canvas role, target aspect, shell ownership/chrome, and artifact topology; an authored full-page bitmap is not interchangeable with a viewport or device frame.
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

## Assemble the final page through ImageGen

Unless the user explicitly chooses local-only stitching, for separate scroll bands whose deliverable is one continuous page, render the predeclared final assembly after all source bands pass individual review and any required acceptance. Make one additional built-in ImageGen call with the saved source images in their declared order. Count it against the total and assembly-output attempt budgets. Individual source receipts remain valid for those bytes; overall set PASS also requires the assembly review below. Never overwrite the sources or claim that their acceptance automatically accepts the newly generated page.

Choose the composition from the frozen output identities:

- **One continuous surface with ordered progressive-scroll bands:** pass all reviewed source files to ImageGen as assembly inputs and request one complete page in source order. Preserve the content, faces, imagery, typography, controls, prices, and section hierarchy. Limit edits to joins, background continuity, and explicitly identified duplicate overlap, keeping each owned content item once. Do not invent sections, rewrite copy, drop material to fit the canvas, or repeat the header/hero. Specify a target width/aspect that preserves legibility; measure and report the returned dimensions rather than promise pixel identity. Inspect local inputs before the call and use the system ImageGen reference mechanism. If the available input/canvas limits cannot include every source legibly, resolve the plan before rendering; do not silently drop inputs or substitute a local collage.
- **Explicitly requested one-call overview:** use its accepted raw artifact as the overview review surface; never select this branch merely because the deliverable is one complete landing-page image. Do not split it into synthetic viewport receipts or claim its tall canvas is a viewport capture.
- **Several independent routes/pages:** use a local compositor such as Pillow or ImageMagick to create a contact sheet that preserves each bitmap's aspect ratio and labels each tile only with its authorized route or output ID outside the screenshot. Do not present separate routes as one continuous scroll.
- **Mixed set:** first render the planned ImageGen assembly for each continuous progressive-scroll page, then create a local contact sheet of those complete pages and standalone page outputs.
- **Explicitly requested local stitch/comparison:** use a local compositor as requested, label it separately, and preserve source pixels except for any authorized overlap crop. It completes an explicitly local-only delivery after its own review. When the user requests both methods, keep separate obligations; a local result cannot stand in for the requested ImageGen result.

For FULL, declare the assembly as a separate `artifactKind: imagegen`, `designEvidenceRequired: true` output before contract confirmation, with `dependsOn` containing every source output. Give it the same product/surface/state identity and an authored-full-page canvas identity; it is not a new route, product state, or runtime viewport. Assembly alone does not add runtime evidence requirements or waive any existing ones. Its stage handoff owns the ordered source-band union, with preservation instructions encoded through the existing bound brief fields; do not duplicate those IDs into an invented extra content-distribution band. Record all source paths/SHAs in the handoff and verify their accepted/promoted bytes before the call. Use the helper's existing transition, budget reservation, provenance, review, and acceptance flow; a single `anchorOutputId` does not replace verification of the other sources. See [full-runtime.md](full-runtime.md).

Verify the assembled image before delivery:

- all source sections appear in the frozen order, with every owned fact/action once except explicitly shared content;
- critical copy, numeric values, faces, imagery, and controls match the sources; a smoother seam cannot excuse unrelated changes;
- the page meets its canvas, readability, shell, and continuity requirements at the actual returned resolution;
- record the assembly output path/SHA, actual dimensions, ordered source paths/SHAs, prompt, call/provenance receipt, and review status;
- the original source files remain unchanged and are delivered separately.

Freeze whether dimensions are required (exact size or minimum) or preferred in the stage plan, from the user/downstream requirement before the call. Do not downgrade that requirement after seeing the output. A prompt requests a canvas; it does not prove that the renderer returned it. Measure the native saved pixels. A mismatch with an exact size, a result below minimum dimensions, or a wrong required aspect is `REVISE_ARTIFACT` even when its copy is readable and its seams look good. Do not silently resize, upscale, crop, or change renderer to claim compliance. For a preferred target, accept a different measured size only when the declared readability and visual requirements pass, and report the difference. Further attempts still follow the frozen budget.

Local tools may inspect dimensions/hashes, prepare scoped references, or produce an explicitly requested comparison. They do not perform the default final page assembly. Treat generated composition as a new bitmap whose text and detail can drift; do not describe it as lossless stitching.

Then review the complete page and its source-band sequence. Compare source bands with each other for unintended repetition, and compare the assembly with those bands for fidelity; expected source-to-assembly reuse is not a duplicate-output defect:

- no `unique` imagery slot, materially similar scene, crop, subject arrangement, or hero composition repeats across outputs;
- every authorized `shared` or `continued` slot matches its declared lineage and scope;
- shell/header chrome follows the declared owner and does not restart inside a continuous-page continuation;
- adjacent bands visibly realize their frozen exit state, entry state, handoff carrier, and edge treatment without accidental hard seams, ghosting, unexplained separators, or repeated full-screen composition; a `deliberate-break` must look authored at full-scroll scale rather than rely on its label to excuse a raw tonal cut;
- the scroll/page sequence has intentional tempo and hierarchy rather than one renderer template with different text;
- adjacent signatures preserve the intended relationship without collapsing into copy-swapped templates, and global typography, color, and material roles remain coherent;
- the complete scroll has intentional rhythm across density, whitespace, heading scale, image/text occupancy, and focal movement rather than an equal-height cadence of repeated shells;
- content, CTA, shell, and imagery do not duplicate across bands unless explicitly shared.

When local tooling supports it, add perceptual-similarity evidence for declared imagery slots or suspected dominant crops. Use hashes or similarity metrics only to flag likely reuse for visual inspection; they never replace the semantic lineage and full-scroll judgment.

If the composite exposes a set-level defect, keep the source artifact receipts but set the overall coherent-set verdict to `REVISE_ARTIFACT`, `REVISE_DIRECTION`, or `BLOCKED` and name the affected outputs/boundaries. Do not deliver an overall PASS merely because every bitmap passed in isolation or because it ranks above another candidate. The planned assembly may realize its declared joins, but a failed assembly does not authorize another call, a local fallback, or a topology switch. For STANDARD, stop and report the defect; later user feedback may authorize one bounded edit of that failed assembly. FULL follows its existing retry budget and authority. Return artifact choice to Product Design when the required continuity or legibility cannot be achieved within the plan.

Record `artifactTopology`, canvas role/actual dimensions, shell lineage/chrome, `compositeArtifact` path/SHA when applicable, `compositeStatus`, per-output `visualSignatures`, `assetLineage`, `reuseDeclarations`, `seamChecks`, and `rhythmChecks` in the final set receipt. Missing provenance, target-scale copy review, or set-level evidence remains unverified rather than implicitly passed.

The ImageGen assembly is a separately reviewed design output and the complete-page review surface; it does not prove implemented scrolling, routing, responsiveness, interaction, or production fidelity. Local contact sheets remain navigation/review aids only. For the ImageGen method, distinguish known render/review failure (`REVISE_ARTIFACT`) from an unknown provider outcome (`BLOCKED`). For an unknown outcome, preserve the counted attempt and reconcile the original call or saved artifact before further work; do not retry an uncertain call blindly or silently substitute local stitching. Overall PASS requires each deliverable under the selected method to pass: an explicitly local-only page has no ImageGen-assembly prerequisite.
