# Prompt Compilation

Compile one prompt for one asset or visible state. Treat the prompt as a small rendering brief, not a transcript of UX planning and not a product specification.

## Contents

- Separate planning from renderer context
- Apply the precision and contradiction gates
- Keep structural retries at equal or greater freedom
- Compile base and later outputs
- Handle exact text and avoid lists

## Separate planning context from renderer context

Keep these in planning only:

- the global content and functionality inventory;
- full long-form copy;
- rejected concepts and dialectical critique;
- the coverage map and reasons for choosing scroll, tabs, drawers, modals, or screens;
- content assigned to other outputs;
- complete anti-pattern lists;
- exact geometry of the internal signature move.

Send the renderer only:

- the current output and state;
- the role of each input image;
- the immediate user job of this output;
- items marked `NOW`, including only critical short labels;
- one non-geometric concept statement;
- a compact truthfulness constraint;
- explicit creative latitude;
- canvas and delivery constraints.

Never include `ELSEWHERE` or `UNSUPPORTED` items. Do not repeat the global contract to prove that it was preserved.

## Use a strict precision budget

Freeze only what protects semantic truth or carries the concept:

- one current state;
- one task or reading goal;
- one concept relationship or perceptual outcome;
- critical current-output content;
- usually three to eight critical short labels;
- at most three relevant failure modes.

Leave composition, topology, region placement, typography character, palette nuance, material language, geometry, bespoke symbols, and micro-detail open unless the user explicitly fixed them.

Aim for roughly 120–220 words. Treat more than 300 words as a failed compilation unless the user explicitly requires substantial current-output copy. If many literal labels or several full sections are needed, return to the coverage map and split the output rather than compressing the prose.

Reject wording such as `preserve every supplied item`, `show all content`, or `everything in one viewport` in a dense current-output prompt. Those belong to the global contract, not the renderer brief.

Do not use claims such as `shippable`, `production-ready`, or `implementation-complete` for a generated bitmap. Use `high-fidelity visual direction` or `high-fidelity UI concept`.

## Run the contradiction gate

Do not invoke `imagegen` until every answer is safe:

1. Does the prompt describe exactly one visible state?
2. Does every content item belong to `NOW`?
3. If the state is default, closed, or unopened, are hidden-surface contents absent?
4. Can the requested content fit legibly without violating the requested amount of space?
5. Does the concept describe an organizing relationship rather than a wireframe?
6. After removing the creative-latitude sentence, can at least two materially different compositions still satisfy the brief?
7. Does the avoid list protect this concept instead of reciting generic anti-style preferences?
8. Has each substantial region earned simultaneous visibility through task dependency or comparison?

If any answer is no, revise the output architecture or concept translation before generating.

## Preserve freedom during structural retries

Compare every structural-regeneration prompt with the failed prompt. Reject the new prompt if it adds exact orientation, named layout regions, fixed counts, layered topology, exposed portions, connectors, or placement instructions merely to force the concept to appear.

Use this decision rule:

- local artifact within an accepted concept: make one precise edit;
- first generic structural result: re-check concept translation and regenerate without adding geometry;
- second generic result from the same concept: abandon that concept and select a semantically different candidate;
- repeated generic results across concepts: return to the user's tension, task, or source role rather than writing a longer prompt.

A structural retry may become semantically clearer, but it must remain equally or more open compositionally.

## Minimal base-output recipe

Adapt only the lines that carry information:

```text
Create <Output N and named visible state> for <use and canvas>.

Use <input image> as a functional and content reference only; do not copy its
layout or styling. Render only the current-output subset named below.

This output must help the user <immediate job>. Show <NOW content groups> and
the visible entry points to <named later outputs>. Other supplied content belongs
to those later outputs.

Art direction: <one relationship or perceptual outcome, without geometry>.
Choose the composition and visual system freely. Add no product facts, jobs,
data, outcomes, or unsupported states.

Preserve these critical short labels: <only labels required now>.
One readable high-fidelity visual direction; no collage, device frame, or watermark.
```

Do not fill every slot mechanically. Omit a line when the source or current output already makes it clear.

## Minimal later-output recipe

```text
Create <Output N and named visible state> of the same experience.

Use the accepted Output 1 as the visual-system anchor. Keep its shell and authored
language coherent while changing only <the current state or scroll position>.

Show <NOW content>. Preserve <critical short labels and semantic invariants>.
Do not introduce another concept, new product behavior, or unsupported state.

One readable state only; no collage or watermark.
```

For a relocated supplied section, describe the new presentation state without implying new data, permissions, validation, persistence, or outcomes.

## Handle exact text honestly

- Quote only critical short labels that must be recognizable in the current output.
- Treat a long catalogue of labels as evidence that too much content remains in `NOW`.
- Keep long body copy in the input reference, coverage map, or implementation artifact; do not paste it into every prompt.
- Split text-heavy material across scroll positions or states when legibility would otherwise fail.
- Treat missing, invented, or misleading critical labels as a failed output.
- Use real text layers during implementation when exact long-form fidelity matters.

## Keep the avoid list causal

Name no more than three likely failure modes unless the user supplied explicit prohibitions. Explain what each would damage.

Prefer:

```text
Avoid <likely generic pattern>; it would erase <the selected concept relationship>.
```

Do not append a universal list of fashionable styles, colors, shapes, effects, and components. Such a list consumes attention and creates another predetermined house style.
