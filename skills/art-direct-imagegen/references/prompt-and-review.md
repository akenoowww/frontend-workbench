# Renderer Prompt and Review

Compile and judge one output at a time; in FULL it must be a declared design-evidence output. Keep product reasoning, the full `VisualDirectionContract`, SHA bookkeeping, authority receipts, render-budget counters, implementation decisions, and runtime state outside the renderer prompt.

## Lean prompt contract

Send only:

- current output ID, surface, supplied state, and viewport;
- intended use, canvas, and immediate purpose;
- only render-time reference bindings applicable to this surface/aspect and the role of each attached image; keep analysis-only functional sources out of the call;
- inherited shell invariants for the current content slot;
- content marked `now` and a few critical short labels;
- exact `subject —predicate→ object` triples for current-output relations whose endpoints or direction carry meaning;
- for a distributed surface, the current `contentBandId` and only its `contentIds`;
- the one relevant non-geometric relationship from the locked direction;
- the selected context model, relation carrier, focus transition, and entity embodiment when structural or relational presentation is material;
- validated anchor continuity only when `anchorOutputId` is non-null;
- truthfulness and state invariants;
- explicit creative latitude;
- for redesigns, the exact preserve-only scope plus one positive product/perceptual departure for each replace region; keep material-change thresholds and `forbiddenCarryover` outside the renderer prompt for review;
- up to three causal avoid items.

Keep out:

- the full upstream/global or visual-direction contract;
- content assigned to other outputs;
- global truth copied in as visible content merely because it must remain reachable somewhere in the product;
- rejected concepts and dialectical critique;
- analysis-only `FUNCTIONAL_REFERENCE` images whose scoped truth is already encoded in the brief;
- product information architecture or implementation reasoning;
- output IDs, filenames, artifact names, fixture descriptions, or internal purpose prose presented as visible product copy;
- slogan-like direction theses, metaphors, explanatory sentences, or symbol suggestions that are not in the visible-copy/content allowlist;
- complete component trees, coordinates, region topology, or design-token catalogues;
- a prescribed graph, connector, node placement, or other visual encoding merely because semantic triples were supplied;
- source-specific rejected topology, palettes, components, or visual devices repeated as negative prompt anchors;
- forecast mode names/categories repeated in an avoid clause or other renderer instruction;
- long copy and universal anti-style lists.

Prefer roughly 120–220 words when that preserves every current-output invariant. Treat length as a diagnostic rather than an automatic failure: keep additional exact text only when it is truly part of this output. Split supplied text according to the declared coverage outputs; do not invent another page or state to make the prompt shorter.

## Prompt recipes

Base output:

```text
Create <output-id> for <surface, supplied state, viewport, and use>.

Use <inputs and roles>. Render only the supplied current output; do not copy a
functional reference's layout or invent product behavior.

This output must communicate <purpose>. Show <now content>. Preserve these
critical short labels: <labels>.

Locked art direction: <one relevant relationship or perceptual outcome, without geometry>.
Choose composition, typography character, palette nuance, material language,
and supporting detail freely within the contract.

Keep <truth/state invariants>. Avoid <up to three causal failure modes>.
One readable high-fidelity visual direction; no collage or watermark.
```

Anchored output, only when `anchorOutputId` is non-null:

```text
Create <output-id>, the supplied <state or viewport> related to accepted <anchor-output-id>.

Use <helper-validated accepted anchor artifact path> as the visual-system anchor.
Preserve <anchorRequirement.preserve>. Change only
<anchorRequirement.changeOnly> for <purpose>.

Show <now content> and preserve <critical labels>. Do not introduce another
concept, product behavior, page, state, or unsupported outcome.

One readable state; no collage or watermark.
```

Omit lines that add no information. “Same style” is too vague when continuity matters; name the few qualities that must survive without prescribing every pixel.

An avoid item names a causal failure class, not an inventory of rejected visual forms. Unless the user explicitly locks a visual prohibition, translate source carryover and critique examples into the positive relationship the new output must achieve and enforce the exact rejected forms only during review.

Validate `anchorOutputId`, artifact SHA, direction SHA, shell identity, and render-brief identity outside the prompt before using the anchor artifact path. Do not print hashes to the renderer merely to prove bookkeeping.

## Preflight gate

Do not call ImageGen when:

- the FULL output does not have `designEvidenceRequired: true` and `artifactKind: imagegen`;
- the confirmed render budget has no remaining total or per-output attempt;
- product/domain/scenario/primary-object or protected-capability identity is missing or stale;
- more than one declared output or visible state appears in the prompt;
- a STANDARD multi-output render begins before the complete required coverage set, semantic responsibilities, content allowlists, ordering, anchors, delivery paths, and derived call ceiling are frozen;
- content not assigned to this output appears;
- a progressive-scroll prompt contains another band's label, numeric value, state, action, or an alias of the same source fact;
- a default/closed state exposes supplied hidden-state content;
- required information cannot fit legibly in the supplied viewport;
- a relational dataset is too dense for exact legible rendering and no representative current-output subgraph/content band or authorized non-semantic ambient policy is declared;
- the concept fixes the whole wireframe before declaring freedom;
- a material structural/relational STANDALONE direction leaves representation grammar unspecified or merely restates the forecast mode with new style words;
- the private selection receipt does not evidence at least two representation-grammar field differences from every forecast mode and surviving candidate;
- a representative content band removes enough relational/context structure that the primary product object collapses into another artifact type;
- an upstream material render lacks a validated direction reference/SHA;
- an applicable reference binding is missing, stale, or broader than this surface/aspect;
- a declared visual anchor is missing its validated binding or any bound SHA differs;
- the output replaces or duplicates an inherited parent shell;
- exact geometry was added merely to repair a generic result;
- a STANDALONE direction's positive thesis, signature relationship, or imagery role conflicts with its own avoid list;
- `FUNCTIONAL_REFERENCE` bytes are attached even though their scoped meaning is fully encoded and no exact visible invariant or relationship requires renderer exposure;
- an output ID, filename, artifact label, or internal purpose statement is promoted into visible copy without explicit content authority;
- direction prose remains caption-ready or implies an unsupplied badge/status symbol instead of being compiled into nonverbal perceptual constraints;
- a redesign prompt repeats source-specific forbidden visual forms instead of stating a positive departure and retaining the exact list for the delta ledger;
- relational content is reduced to disconnected node/edge labels even though endpoints or direction change the product meaning;
- independent supplied sets are paired or aligned as if a mapping exists when no such relation was supplied;
- the prompt invents product facts, controls, states, copy, or outcomes;
- after removing the latitude sentence, fewer than two materially different compositions remain possible.

Return a coverage or product-contract contradiction upstream as `blocked`; do not solve it by creating new information architecture.

## Review gates

Save the returned artifact before review and bind it to the direction SHA used for the prompt.

### Bitmap and output-contract gate

Reject it when any required condition fails:

- correct output ID/type, platform, page/state/viewport, and purpose;
- required current content and critical labels are recognizable and not misleading;
- no invented fact, control, state, outcome, or product structure;
- the primary product object stays dominant, protected capabilities remain present at their declared hierarchy/visibility, and downstream evidence or implementation details stay subordinate;
- the primary product object remains recognizable from its visual behavior and context without relying on the prompt, title, or exact labels;
- supplied actions and states are represented truthfully;
- every supplied relation retains its exact endpoints and direction; decorative connectors or arrowheads do not invent reverse or additional semantics;
- independent supplied sets remain semantically separate; repeated proximity, alignment, containers, or labels do not imply an undeclared mapping;
- no direction thesis, metaphor, explanatory prose, or symbolic treatment leaks into unsupported visible copy, status, outcome, or reassurance;
- the relevant locked direction relationship is perceptible without reading the prompt;
- result is coherent, readable, and plausible for its intended context;
- anchored output preserves the exact bound anchor invariants and changes only the supplied delta;
- visual specificity comes from hierarchy and relationships, not an implied need for bespoke implementation controls.
- only declared preserve regions remain materially similar; every replace region clears its named change threshold and carries none of the forbidden source layout/topology.

Generated bitmap text can be imperfect, but missing or misleading critical labels fail the output. Never describe a bitmap as production-ready or implementation-complete.

Before `PASS`, create a concise visible-claim ledger from the saved bitmap itself, not from the prompt. Transcribe every readable status, owner, date/time, verification, freshness, provenance, sync/processing, confidence, service-health, result, score, and success/failure phrase. Bind each entry to supplied copy, a contract field, or an exact `operationalMetadataPolicy.requiredClaims` item for this surface/state. Any unsupported entry—including plausible filler such as “Passed”, “latest run”, an owner name, timestamp, badge, or reassurance—fails the bitmap gate. If text is too distorted to classify safely, revise the artifact; visual attractiveness cannot waive semantic truth.

For a redesign, create a separate delta ledger from source and output. For each replace region, name the observed material changes using only the contract enum and check every `forbiddenCarryover`. Palette, border radius, shadow, or small spacing changes do not satisfy `macro-layout`, `information-hierarchy`, or `module-topology`. If the user asked to keep only the sidebar and the main content still reads as the same card grid, the verdict is not PASS.

### Shared first-artifact gate

For the first representative artifact of a direction, read [the shared visual-direction reference](../../frontend-product-design/references/visual-direction.md) and judge concept specificity, hierarchy, execution, project DNA, restraint, usability, and feasibility. Use only `PASS`, `REVISE_ARTIFACT`, `REVISE_DIRECTION`, or `BLOCKED`; do not invent numeric scores.

This shared gate applies equally to a runnable artifact elsewhere in the workflow. ImageGen still owns bitmap correctness; Product Design owns the direction-level judgment. Bind a durable FULL verdict to both the artifact SHA and direction SHA before acceptance.

If a semantically correct bitmap collapses into a forecast default or a different artifact type, it is not `PASS`. Use `REVISE_DIRECTION` when the locked representation grammar allowed that collapse; use `REVISE_ARTIFACT` when the direction excluded it but the renderer ignored the contract.

Before `PASS`, compare the saved bitmap's context model, relation carrier, focus transition, and entity embodiment with every forecast signature. If fewer than two fields differ from any forecast mode, the artifact has not escaped that mode regardless of polish.

## Iteration

Treat user reactions, comparisons, and examples as diagnostic evidence unless the user explicitly makes one a visual lock or prohibition. Infer the underlying direction or artifact defect, then revise that bounded source of failure. Do not accumulate examples into a style blacklist, copy a suggested composition into the renderer prompt, or anchor every later output to the last artifact merely because it was discussed.

### Local failure

For one missing label, emphasis, contrast, icon, or small artifact:

1. keep the locked direction, immutable input roles, and, only when declared, the validated anchor SHA;
2. in MICRO/STANDARD, return `REVISE_ARTIFACT` and stop the current turn after the first call;
3. after a later explicit user retry, use the saved failed artifact as the sole `EDIT_TARGET`, request one targeted change, and repeat only the critical invariants;
4. in FULL, reserve the retry first, then follow the same edit-target rule;
5. re-run the full review gate and do not chain another cleanup call autonomously.

### Direction or structural failure

For a generic template, unclear concept, impossible density, contract drift, or inconsistent child state:

1. do not lengthen the failed prompt;
2. identify whether artifact execution, locked direction, or the supplied product/coverage contract is at fault;
3. return `REVISE_ARTIFACT` for a bounded renderer defect;
4. return upstream `REVISE_DIRECTION` when the locked idea is generic, unclear, or unfit;
5. return `BLOCKED` when product or coverage truth is contradictory;
6. compile a fresh short prompt only after the owning layer resolves the fault.

After one generic result, do not immediately create the same output again from the original references. Return `REVISE_DIRECTION` when the direction is at fault or `REVISE_ARTIFACT` for a bounded renderer defect. In STANDALONE only, a later user turn may revise the bitmap-only direction through the shared method. Never convert `signatureMove` into a renderer wireframe or a requirement for hand-written controls.

Accept only when the bitmap gate passes, the shared gate is `PASS` when required, and no safe, relevant budget-compliant correction remains. Record the verdict, direction ref/SHA, artifact path/SHA, bound anchor identity when present, prompt SHA, and budget use before moving to the next design anchor. Runtime-only outputs remain for Runtime QA.
