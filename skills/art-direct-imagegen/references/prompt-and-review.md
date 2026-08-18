# Renderer Prompt and Review

Compile and judge one manifest output at a time. Keep product reasoning and runtime bookkeeping outside the renderer prompt.

## Lean prompt contract

Send only:

- current output ID, surface, supplied state, and viewport;
- intended use, canvas, and immediate purpose;
- role of each input image;
- content marked `now` and a few critical short labels;
- one non-geometric concept relationship;
- parent-anchor continuity for dependent outputs;
- truthfulness and state invariants;
- explicit creative latitude;
- up to three causal avoid items.

Keep out:

- the full upstream/global contract;
- content assigned to other outputs;
- rejected concepts and dialectical critique;
- product information architecture or implementation reasoning;
- complete component trees, coordinates, region topology, or design-token catalogues;
- long copy and universal anti-style lists.

Prefer roughly 120–220 words when that preserves every current-output invariant. Treat length as a diagnostic rather than an automatic failure: keep additional exact text only when it is truly part of this output. Split supplied text according to the existing manifest; do not invent another page or state to make the prompt shorter.

## Prompt recipes

Base output:

```text
Create <output-id> for <surface, supplied state, viewport, and use>.

Use <inputs and roles>. Render only the supplied current output; do not copy a
functional reference's layout or invent product behavior.

This output must communicate <purpose>. Show <now content>. Preserve these
critical short labels: <labels>.

Art direction: <one relationship or perceptual outcome, without geometry>.
Choose composition, typography character, palette nuance, material language,
and supporting detail freely within the contract.

Keep <truth/state invariants>. Avoid <up to three causal failure modes>.
One readable high-fidelity visual direction; no collage or watermark.
```

Dependent output:

```text
Create <output-id>, the supplied <state or viewport> of the accepted <parent-id> experience.

Use <accepted parent path> as the visual-system anchor. Preserve <named shell,
brand, hierarchy, material, and semantic invariants>. Change only <supplied
changeFromParent> for <purpose>.

Show <now content> and preserve <critical labels>. Do not introduce another
concept, product behavior, page, state, or unsupported outcome.

One readable state; no collage or watermark.
```

Omit lines that add no information. “Same style” is too vague when continuity matters; name the few qualities that must survive without prescribing every pixel.

## Preflight gate

Do not call ImageGen when:

- more than one manifest output or visible state appears in the prompt;
- content not assigned to this output appears;
- a default/closed state exposes supplied hidden-state content;
- required information cannot fit legibly in the supplied viewport;
- the concept fixes the whole wireframe before declaring freedom;
- exact geometry was added merely to repair a generic result;
- the prompt invents product facts, controls, states, copy, or outcomes;
- after removing the latitude sentence, fewer than two materially different compositions remain possible.

Return a manifest or product-contract contradiction upstream as `blocked`; do not solve it by creating new information architecture.

## Review gate

Save the returned artifact before review. Reject it when any required condition fails:

- correct output ID/type, platform, page/state/viewport, and purpose;
- required current content and critical labels are recognizable and not misleading;
- no invented fact, control, state, outcome, or product structure;
- supplied actions and states are represented truthfully;
- concept is perceptible without reading the prompt;
- result is task-specific, coherent, restrained, usable, and plausible for its intended context;
- dependent output preserves the accepted anchor's visual identity and changes only the supplied delta.

Generated bitmap text can be imperfect, but missing or misleading critical labels fail the output. Never describe a bitmap as production-ready or implementation-complete.

## Iteration

### Local failure

For one missing label, emphasis, contrast, icon, or small artifact:

1. keep the concept and anchor;
2. request one targeted change;
3. repeat critical invariants;
4. re-run the full review gate.

### Structural failure

For a generic template, unclear concept, impossible density, contract drift, or inconsistent child state:

1. do not lengthen the failed prompt;
2. identify whether concept translation or the supplied contract is at fault;
3. if concept is at fault, branch to a semantically different candidate;
4. if contract is at fault, mark `blocked` and return it upstream;
5. compile a fresh short prompt only after the fault is resolved.

After two generic results from one concept, abandon that concept. Do not convert its internal signature move into a renderer wireframe.

Accept only when the review gate passes and no safe, relevant single correction remains. Record the decision, artifact path, digest when available, and prompt before moving to the next manifest output.
