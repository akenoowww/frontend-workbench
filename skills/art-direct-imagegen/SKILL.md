---
name: art-direct-imagegen
description: "Plan and art-direct image generation before invoking imagegen. Use for vague or judgment-heavy visual requests such as making an image, page, screen, campaign, or asset more beautiful, conceptual, distinctive, modern, expressive, or radically redesigned; for dense UI screenshots that may need several screens or interaction states; for related image sets that need one coherent visual language; and when earlier generations were literal, generic, template-like, or over-specified. Explore semantically different concepts, critique them, select one direction, preserve functional/content invariants, map multi-state outputs, and compile deliberately non-over-specified prompts. Do not use the full workflow for simple surgical edits, literal transformations, background removal, or other requests whose creative solution is already fixed."
---

# Art-Direct ImageGen

Create the visual idea before asking `imagegen` to render it. Keep the problem precise and the solution space open.

The core principle is **radical shell, conservative semantics**:

- lock content, function, user jobs, required states, and critical text;
- guide feeling, tension, hierarchy, and one conceptual thesis;
- leave composition, visual system, geometry, palette nuance, typography character, and supporting details open unless the concept truly depends on them.

Do not turn a request for creativity into a longer rendering specification.

Keep two artifacts separate throughout the workflow:

- **global contract**: the complete inventory of supplied content, functions, actions, states, and exact copy across the deliverable set;
- **current-output brief**: only what must be visible in the one asset or state being generated now.

Never paste the global contract into an `imagegen` prompt.

## Load the relevant references

- Read [references/concept-planning.md](references/concept-planning.md) for every original, aesthetic, or judgment-heavy request.
- Also read [references/flow-architecture.md](references/flow-architecture.md) for UI, dense information, multiple screens, modals, drawers, tabs, or related states.
- Read [references/prompt-compilation.md](references/prompt-compilation.md) immediately before preparing prompts for `imagegen`.
- Read [references/evaluation.md](references/evaluation.md) before judging generated results or deciding how to iterate.

## Choose the workflow

Use the full art-direction workflow when the user asks for interpretation, originality, conceptual redesign, taste, memorability, a new visual direction, or several connected outputs.

Use the system `imagegen` skill directly when the user has already fixed the desired result and only needs execution, such as changing one object, preserving everything except a named edit, extracting a background, or rendering a tightly specified asset.

If the user supplies an image, label its role before planning:

- **functional/content reference**: preserve jobs, information, actions, and states, but not layout or styling;
- **style reference**: borrow named visual qualities, not content or composition;
- **edit target**: preserve everything except explicitly allowed changes;
- **visual-system anchor**: keep the established language consistent across later outputs.

Never silently treat a functional reference as an edit target.

## Workflow

### 1. Extract the global contract

Separate the request into four layers:

- `LOCK`: exact functions, content, user tasks, platform, required actions, states, brand facts, and literal text.
- `GUIDE`: desired feeling, hierarchy, visual tension, product posture, and the quality that should remain memorable.
- `FREE`: composition, grouping, spatial rhythm, palette nuance, typography character, material language, background, custom symbols, and supporting details.
- `FORBID`: invented functionality or copy, misleading affordances, known clichés, irrelevant decoration, and explicit user prohibitions.

Do not promote the source layout, current card boundaries, component shapes, or page boundaries into `LOCK` unless the user explicitly requires them.

Preserve semantic importance and workflow meaning, not the source's visual hierarchy. Record actions, triggers, opened surfaces, and system states separately. Never infer an unsupported state, confirmation, or opened surface from an action or trigger label alone.

For dense interfaces, inventory every meaningful content block and state before ideating. The complete information set must survive across the output set, not on every output and not necessarily on the first screen.

### 2. Interrupt the obvious answer

Before choosing a visual direction, name the nearest predictable medium-specific completion privately and quarantine it: a stock composition, fashionable surface treatment, generic symbolism, familiar layout archetype, or a style label pasted onto unchanged structure.

Do not use a ban list as a substitute for a concept. A concept explains what organizes the work; prohibitions only remove failure modes.

### 3. Diverge by mechanism

Develop at least three semantically different concept candidates for a substantial creative request. They must differ in organizing logic, not merely palette, typeface, or decoration.

For each candidate, define only:

1. one-sentence thesis;
2. intended feeling;
3. main structural or compositional gesture;
4. how the required function/content lives inside it;
5. why it is not a transferable template;
6. its strongest usability or coherence risk;
7. what remains intentionally free for the renderer.

Do not expose the whole internal list unless comparison benefits the user. The goal is selection pressure, not a portfolio.

### 4. Select dialectically

Apply a short thesis/antithesis/synthesis pass to each serious candidate:

- **Thesis**: why the concept is memorable and fitted to this specific task.
- **Antithesis**: how it could become decorative, confusing, derivative, or impossible to implement.
- **Synthesis**: whether the weakness can be removed without killing the concept.

First reject candidates that lose content, function, legibility, discoverability, or implementability. Among survivors, choose the direction with the clearest point of view and strongest transfer resistance. Do not average or merge all candidates into style soup.

### 5. Plan the output set

For a single independent asset, proceed to the concept sheet.

For dense UI or connected states:

1. classify information as primary, secondary, or contextual;
2. choose scroll, tabs, drawer, modal, or separate screen by interaction meaning;
3. map every source item to a destination;
4. define the minimum output manifest;
5. ensure every hidden surface has a discoverable trigger in an earlier state;
6. generate each required screen or state with a separate `imagegen` call;
7. use the first accepted output as the visual-system anchor for subsequent outputs.

Do not request multiple final screens as one collage unless the user explicitly wants a comparison board. See [references/flow-architecture.md](references/flow-architecture.md).

Do not treat source visibility as semantic priority. A complete form, detailed provenance or history, and long supporting content are not primary merely because the source displayed them beside the central task. Keep only information required immediately or compared simultaneously on Output 1.

Before prompt compilation, mark every inventory item as `NOW`, `ELSEWHERE`, or `UNSUPPORTED` for the current output. Do not continue while any item lacks a destination.

Use `UNSUPPORTED` only for absent content, data, outcomes, or behavior. A new presentation-only tab, drawer, modal, expandable region, or scroll continuation is information architecture rather than an invented product function when it only relocates supplied content, creates no new data or outcome, and has a discoverable entry point. Introduce and render that state separately when density requires it.

Reject the output plan before generation when it combines a single viewport, long-form primary copy, complete contextual forms or details, readable typography, and generous negative space. Split the output set instead. A state described as default, closed, or unopened must not simultaneously show the inner contents of its closed surfaces.

Require multiple outputs when long primary content competes with a complete independent form and detailed supporting regions. Do not waive this because the original canvas is large or technically legible.

### 6. Distill one concept sheet

Before writing the renderer prompt, freeze only:

- the one-sentence concept thesis;
- the intended feeling and visual tension;
- one signature move and at most two supporting moves;
- the `LOCK` list;
- a short `FORBID` list;
- the output/state being rendered now.

If the sheet contains exact coordinates, a complete component tree, many color values, every corner radius, or instructions for every secondary element, it is probably a layout specification rather than art direction. Remove details that do not carry the concept or protect functionality.

Keep the signature move in planning. Translate it one level upward for the renderer: describe the organizing relationship, perceptual outcome, or tension, not its exact direction, position, count, shape, or topology unless the user explicitly fixed that geometry.

### 7. Compile prompts per asset

Prepare one prompt for each distinct asset or state. Include only the source role, current output goal, non-geometric concept intent, current-output locks, creative latitude, and the few avoid items that matter.

Do not paste the full discovery reasoning, coverage map, rejected concepts, or global lock list into the prompt. Do not ask the renderer to literalize every cue. Put only critical short text required in this output into the prompt; keep long copy in the source reference, coverage map, or implementation layer. Split it across outputs instead of forcing unreadable density.

Fail prompt compilation and return to output planning when:

- the prompt describes more than one state or includes `ELSEWHERE` content;
- the prompt says to preserve every supplied item in one output instead of naming the current-output subset;
- the prompt carries a long catalogue of labels or content regions that should have been distributed;
- creative latitude is declared after composition or topology has already been fixed;
- a one-viewport request also demands all long copy, full forms, and spacious readability;
- the avoid list becomes a generic anti-style catalogue;
- the asset is called shippable or production-ready rather than a high-fidelity visual direction.

Use the recipes in [references/prompt-compilation.md](references/prompt-compilation.md).

### 8. Invoke the system image workflow

Follow the installed system `imagegen` skill for tool choice, input-image handling, save paths, transparency, and delivery. Use the built-in image-generation tool by default.

For multiple distinct outputs, issue one call per asset or state. After accepting the first output, provide it as the visual-system reference for later outputs while repeating critical invariants.

### 9. Critique the actual image

Judge the output, not the elegance of the prompt. Apply [references/evaluation.md](references/evaluation.md).

Use two kinds of iteration:

- **Local failure**: make one targeted change, restate invariants, and preserve the accepted concept.
- **Structural or generic failure**: return to concept branching or output architecture. Do not append more adjectives, bans, coordinates, style references, named regions, or topology to a failed concept.

Maintain monotonic creative freedom across structural retries: a new renderer prompt must not prescribe more layout, geometry, orientation, count, layering, or placement than the failed prompt. Change the semantic concept instead. If the same concept yields a transferable or generic result twice, discard it and select a different candidate from another divergence mechanism.

Never rescue an illegible concept by spelling out its wireframe. If the concept becomes visible only after exact planes, zones, exposed portions, connectors, or spatial order are prescribed, the concept is unsuitable for this workflow. Precision is allowed only for a local edit after the visual system has already passed the creative gate.

Stop when the output is functionally truthful, conceptually legible, coherent, distinctive, and usable for its intended purpose. Report the selected concept, generated outputs, and final prompt set as required by the system image workflow.

## Non-negotiable guardrails

- Never confuse detail with creativity.
- Never let the first plausible concept win without opposition.
- Never call palette swaps or style-label swaps independent concepts.
- For interactive outputs, never hide primary information solely to make a screen look cleaner.
- Never invent content, metrics, states, or controls to fill a composition.
- Never make every element unusual; concentrate originality in one decisive system-level move.
- For dense interactive outputs, never force all information into one viewport merely because the source used one page.
- Never show the contents of a closed surface in a default or unopened state.
- Never let a renderer prompt carry the complete global content inventory.
- Never classify every visible source block as primary without proving simultaneous task dependency.
- Never call presentation-only relocation an invented function.
- Never claim creative freedom after prescribing the full composition.
- Never make a structural retry more geometrically specific than the failed prompt.
- Never keep the same concept after two generic structural failures.
- Treat generated UI imagery as visual direction, not implementation proof, until it is built and tested.
- For text-bearing bitmap outputs, never promise perfect long-form text. Split content, verify critical labels, and preserve exact copy in implementation artifacts when fidelity matters.
