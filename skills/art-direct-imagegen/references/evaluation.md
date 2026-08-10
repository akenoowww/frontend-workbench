# Evaluation and Iteration

Judge the generated artifact in layers. Functional truth is a gate; originality is not allowed to compensate for missing content or unusable interaction.

## Contents

- Reject invalid prompts before generation
- Apply functional and multi-state gates
- Evaluate creative quality and template resistance
- Choose local or structural iteration

## Prompt preflight gate

Reject the renderer prompt before generation when any condition is true:

- it contains the global inventory instead of only current-output content;
- it asks to preserve every supplied item in the current output or carries a long catalogue of unrelated labels;
- it requests more than one visible state or lacks an output manifest for dense UI;
- every source region is marked primary or `NOW` without task-dependency evidence;
- presentation-only containers or scroll positions are marked unsupported while their supplied content remains crowded into the main output;
- it calls a surface closed or unopened while requiring its inner contents;
- it combines one viewport, long-form copy, complete secondary or contextual regions, spaciousness, and full legibility;
- its concept fixes the main topology, regions, connectors, orientation, or placement before declaring creative freedom;
- a structural retry adds more topology, orientation, count, layering, or placement than the failed prompt;
- its avoid list is a generic catalogue rather than a short concept-specific guard;
- it describes a generated bitmap as shippable or production-ready;
- after removing the creative-latitude sentence, fewer than two materially different compositions remain possible.

Return to output architecture or concept translation instead of polishing a prompt that fails this gate.

## Gate checks

Fail the output if any critical condition is false:

- correct asset type, intended context or platform, and requested state when applicable;
- all content/actions mapped to this output are present;
- no invented feature, metric, copy, or control materially changes the task;
- no trigger or action has been misread as an unsupported system state or invented opened surface;
- critical text is readable enough to evaluate and is not misleading;
- for interactive outputs, primary actions and hidden-surface triggers are discoverable;
- the result can plausibly serve its intended purpose.

For multi-state sets, also fail when:

- a later state has no visible entry point;
- content disappears from the complete output manifest;
- an unsupported opened surface or system state is fabricated from a label alone;
- later screens drift into another design system;
- a modal, drawer, or tab is used contrary to the interaction meaning;
- all states were compressed into one unreadable collage.

For dense UI, also fail a nominally readable single output when long primary content, a complete independent form, and detailed supporting regions remain simultaneously visible without a real comparison requirement. Technical fit is not sufficient evidence of good information architecture.

## Creative checks

Score each from 1 to 5:

1. **Concept legibility** — can the organizing idea be perceived without reading the prompt?
2. **Structural originality** — is the memorable move compositional or systemic rather than cosmetic?
3. **Task specificity** — would this design lose its meaning if transferred unchanged to another task, artifact, domain, or audience?
4. **Coherence** — do hierarchy, symbols, type character, materiality, and composition express one idea?
5. **Restraint** — is originality concentrated rather than spread across unrelated tricks?
6. **Usability clarity** — are intended reading order, hierarchy, and any applicable actions or states understandable at a glance?
7. **Renderer contribution** — did the result contain tasteful visual decisions that were not mechanically dictated by the prompt?

Treat scores below 3 in concept legibility, task specificity, coherence, or usability clarity as structural failures for ordinary work.

For an explicitly conceptual, highly creative, distinctive, or radical redesign, require at least 4 in concept legibility, structural originality, task specificity, coherence, usability clarity, and renderer contribution. A polished score of 3 is still a generic failure in this mode.

## Template-resistance questions

- Is the result just the source layout with a new skin?
- Is the concept only a palette, font pairing, or style label?
- Could the same composition be reused for an unrelated task or artifact?
- Did familiar AI markers return as the organizing system?
- Does removing the signature gesture leave a generic template?
- Did the prompt prescribe so much that the renderer had no meaningful choice?

Treat yes to source-reskinning, unchanged transferability, or a mechanically dictated result as a structural failure. If the prompt prescribed so much that the renderer had no meaningful choice, do not accept the artifact merely because it is coherent.

## Choose the correct iteration loop

### Local failure

Examples: one missing label, wrong emphasis, awkward icon, insufficient contrast, minor text error.

Action:

1. preserve the accepted concept and visual-system anchor;
2. request one targeted change;
3. repeat critical invariants;
4. re-check the gate.

### Structural failure

Examples: generic template, unclear concept, impossible density, wrong information architecture, decorative metaphor, state drift.

Action:

1. do not lengthen the same prompt;
2. identify whether concept selection or output mapping failed;
3. return to the relevant planning stage;
4. choose or synthesize a stronger direction;
5. compile a fresh short prompt.

After two generic results from the same concept, reject the concept and branch through a different semantic mechanism. Do not convert its internal signature move into an exact renderer wireframe.

### Taste disagreement

If the output is coherent and functional but the user dislikes it, treat that as evidence about feeling, posture, or tension. Update `GUIDE`, not the entire component specification. Produce a genuinely different concept rather than recoloring the rejected one.

## Completion rule

Complete when:

- every gate passes;
- the chosen concept is visible in the artifact;
- the output is not a transferable template;
- when applicable, the output set or interaction flow is complete for the supplied content;
- later assets remain visually coherent;
- no safe, relevant single change is clearly needed.
