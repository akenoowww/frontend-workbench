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
| Original bitmap asset or genuinely open visual direction | ImageGen concept |
| Coherent generated page or state set | **$art-direct-imagegen** with the complete coverage handoff |

Do not create an image merely because the task is visual. A bitmap cannot prove interaction, responsive behavior, exact long-form text, accessibility, data integration, or implementation feasibility.

## ImageGen is optional

Invoke **$art-direct-imagegen** only when generated imagery can resolve a material visual question or is itself a requested deliverable. Pass the selected direction, protected product semantics, project evidence, and required coverage outputs. The art-direction skill owns prompt compilation, render sequencing, visual-system continuity, and bitmap critique.

For multi-page or multi-state work, do not collapse required coverage into one representative image after ImageGen is chosen. One accepted master may anchor later outputs, but completion still follows the coverage record.

If ImageGen is unavailable, continue with another valid artifact when it can test the decision. Report ImageGen as blocked only when the user explicitly requested generated imagery or no substitute can validate the material visual question.

## Apply checkpoints

For **review-before-artifact**, show:

- selected direction and material trade-offs;
- required coverage;
- chosen artifact and why it can test the decision;
- any cost, latency, or fidelity consequence that changes the user's choice.

Do not pause for routine, reversible artifact production under **continuous**.

## Review evidence, not intent

Inspect the artifact actually produced. Verify:

- the primary user job and necessary context remain clear;
- required pages, surfaces, states, and viewports are accounted for;
- hierarchy, density, actions, feedback, and recovery are coherent;
- project language and reusable foundations remain recognizable when required;
- responsive changes preserve task priority;
- controls and content do not promise unsupported behavior;
- the artifact is feasible in the current architecture.

When an artifact exposes a product contradiction, revise the affected design decision or coverage record. Do not hide it with visual polish.

Generated UI remains visual direction, not production proof. Implemented UI requires project-fit implementation and source checks through **$frontend-project-fit**, followed by behavioral, responsive, accessibility, and rendered-flow evidence through **$frontend-runtime-qa** when available.
