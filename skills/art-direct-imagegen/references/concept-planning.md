# Concept Planning

Use this reference to create and select the visual idea before compiling an image prompt.

## Contents

- Start from the task
- Quarantine predictable answers
- Diverge and select dialectically
- Build the internal concept sheet
- Translate intent without fixing geometry

## Start from the task, not a style

Extract the behavior, tension, constraint, or information relationship that makes this request specific. A concept should be named from that source, not from a fashionable aesthetic category.

Weak starting point:

```text
<fashionable style label>, <palette cue>, <layout adjective>
```

Stronger starting point:

```text
The visual system is organized by <task-specific behavior or information relationship>; each compositional decision clarifies <the user's next decision>.
```

The first is a look. The second can generate a look, structure, symbol language, and interaction logic without prescribing a reusable house concept.

## Quarantine the autocomplete

Identify the answer a generic model would most likely produce. Do not simply negate it and keep its structure. Move to a different organizing mechanism.

Examples of predictable clusters:

- SaaS dashboard: equal cards, rounded rectangles, gradient accent, generic outline icons;
- premium landing page: oversized headline, floating product render, black background, glow;
- editorial redesign: serif headline plus arbitrary offset grid;
- futuristic interface: neon cyan, glass panels, HUD marks;
- playful app: pastel blobs, emoji-like illustrations, pill buttons.

These elements are not universally forbidden. They fail when they are the source of the idea rather than a consequence of it.

## Divergence lenses

Use different lenses to generate semantically distant candidates. Do not use all of them mechanically.

- **Behavior or ritual**: organize the visual around what the user repeatedly does, decides, compares, or confirms.
- **Information relationship**: let hierarchy, provenance, uncertainty, chronology, or contrast become the visual system.
- **Spatial metaphor**: reinterpret the artifact as a field, instrument, archive, stage, workspace, index, or other coherent spatial logic.
- **Material logic**: derive behavior from one material property such as folding, layering, erosion, stamping, reflection, tension, or translucency.
- **Temporal logic**: make progression, accumulation, reveal, before/after, or rhythm carry the concept.
- **Subtraction or inversion**: remove the expected container, reverse foreground/background, or make normally secondary evidence become the organizing layer.
- **Scale shift**: let one normally small element become the dominant navigation or compositional device.

A candidate qualifies as independent only when its composition or perceptual structure would still differ after removing color and typography.

## Concept card

Keep each candidate short:

```text
Name:
Thesis:
Feeling:
Signature gesture:
Functional/content mapping:
Why it belongs to this task:
Main risk:
Renderer freedom:
```

Avoid filling the card with component geometry or design tokens.

## Dialectical selection

For each serious candidate:

1. **Thesis** — articulate its strongest case.
2. **Antithesis** — attack its clarity, originality, feasibility, and fit.
3. **Synthesis** — remove the weakness without weakening the central idea.

Reject a concept when:

- it is a style label rather than an organizing idea;
- it could be transferred unchanged to an unrelated task or artifact;
- it requires invented content or misleading controls;
- its memorable element is decorative rather than structural;
- it makes the primary task harder to understand;
- it needs many unrelated tricks to feel creative.
- it becomes recognizable only after exact spatial topology is prescribed.

Prefer a concept when:

- one sentence predicts the composition and visual language, plus interaction language when applicable;
- its signature gesture grows from the task or content;
- it survives without its palette;
- it can remain functional and implementable;
- it leaves the renderer meaningful visual decisions;
- its biggest weakness can be corrected without losing its identity.

Do not merge all surviving concepts. Select one. A hybrid is allowed only when the second idea resolves a specific weakness in the winner and remains subordinate.

## Internal concept sheet

First distill the winner for internal planning:

```text
Concept thesis: one sentence
Desired feeling: one phrase
Visual tension: one contrast
Signature move: one decisive system-level gesture
Supporting moves: zero to two
Locks: functional/content invariants
Creative latitude: decisions intentionally left open
Avoid: only the failure modes most likely to erase the concept
```

The sheet is complete when another art director can understand the point of view without knowing the final grid, palette, typeface, or component geometry.

## Translate intent, not geometry

Do not send the internal signature move to the renderer verbatim when it already specifies the solution. Abstract it one level upward.

Keep named metaphors and artifact types internal when they would dictate the final aesthetic, material, or decoration. A useful planning metaphor may generate the concept, but the renderer-facing sentence should express the underlying relationship, tension, or perceptual outcome rather than asking for a literal imitation of that artifact.

Keep a direction internal when it fixes several of these at once:

- exact orientation or position;
- a named region layout;
- a fixed number of visual nodes or zones;
- exact shapes, connectors, or topology;
- predetermined placement of secondary content.

Translate it into the relationship or perceptual result that the renderer should solve. The renderer-facing concept should state what must become understandable or memorable, while leaving open how composition, hierarchy, type, material, and symbol language achieve it.

Apply the freedom test before compiling:

1. Remove the sentence that claims creative latitude.
2. Read the remaining brief.
3. If a competent designer could already sketch the main wireframe from it, the concept is over-specified.
4. Remove geometry until at least two materially different visual solutions can still satisfy the same concept.
5. Remove metaphor nouns that make one surface treatment or decorative vocabulary inevitable.

If a non-geometric prompt produces a generic result, treat that as evidence against the concept rather than permission to dictate the missing layout. Re-branch through a different behavior, information relationship, temporal logic, inversion, or scale shift. Do not turn the internal signature gesture into renderer instructions during a structural retry.
