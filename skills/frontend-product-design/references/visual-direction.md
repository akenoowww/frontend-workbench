# Visual direction

Use this reference when a product-design task must establish, preserve, or critique a project-specific visual direction. Product Design owns this direction independently of the artifact or renderer used to express it.

## Keep ownership explicit

- **Product-design flow** — frontend-product-design derives and locks the direction. Runnable prototypes, browser renders, and ImageGen outputs are instances of that direction.
- **Fixed upstream direction** — consume its reference and SHA without reinterpreting it. Reopen Product Design only when evidence shows a material contradiction.
- **Standalone ImageGen** — when the request is bitmap-only and no upstream product-design contract exists, art-direct-imagegen may synthesize the same compact contract as a local fallback. That does not authorize new product behavior, IA, copy, code, or implementation.

If a standalone bitmap later becomes an implementation brief, route it through Product Design to validate the direction against project evidence and produce a frozen handoff.

## Start from evidence and tension

Use the user brief, confirmed product-object hierarchy, nested shells, Product UI DNA, supplied references, protected behavior, and redesign authority. When a site, screenshot set, or brand guide is supplied, first read [visual-reference-extraction.md](visual-reference-extraction.md). In FULL v3, consume only reference bindings applicable to the current surfaces and aspects; do not turn an available source into whole-product authority.

For redesign language such as “keep only the sidebar and completely redo the main page,” freeze a region-level boundary before choosing a direction. “Preserve X” means preserve only the named region and listed invariants; it does not authorize preserving the rest of the shell, top bar, module layout, card topology, or hierarchy. Everything named for replacement must carry measurable material-change dimensions. If the boundary is ambiguous, resolve it before rendering rather than drifting into a restyle.

Extract the behavior, information relationship, brand posture, or emotional tension that makes the work specific. A strong thesis has this form:

```text
The visual system makes <project-specific relationship or tension> perceptible
so the experience communicates <its product purpose>.
```

A style label, palette, fashionable layout adjective, or transferable mood is not a direction.

## Quarantine the predictable answer

Privately identify the nearest generic completion: equal dashboard cards, an oversized premium hero, an arbitrary editorial offset grid, neon HUD, glass panels, pastel blobs, or another familiar default. These devices are not universally forbidden; they fail when they are the source of the idea rather than a consequence of product evidence.

Move to a different organizing mechanism instead of merely banning the default.

## Diverge and select

For high-ambiguity or high-stakes work, compare two or three candidates that would still differ after removing color and typography. For a bounded surface, one candidate plus one adversarial countercheck is enough. Useful lenses include:

- the supplied user ritual or decision;
- hierarchy, provenance, chronology, uncertainty, or contrast;
- a coherent material behavior such as folding, layering, stamping, tension, or reflection;
- progression, accumulation, reveal, inversion, subtraction, or scale shift.

Keep candidates short: thesis, intended feeling, signature relationship, preservation of supplied content/function, project fit, main clarity or feasibility risk, and renderer freedom.

Attack each serious candidate for clarity, specificity, feasibility, restraint, and transferability. Reject it when it is only a style label, fits another product unchanged, requires invented content, weakens the user job, or becomes legible only after prescribing exact geometry. Select one direction; do not average every survivor into style soup.

## Write the compact contract

Use this renderer-neutral shape:

~~~ts
interface VisualEvidence {
  sourceType:
    | "project-file"
    | "screenshot"
    | "brand-guide"
    | "website"
    | "user-input";
  sourceRef: string;
  observation: string; // FULL v3 includes exact binding:<reference-binding-id>
  sourceSha256?: string;
}

interface VisualDirectionContract {
  schemaVersion: 1;
  conceptThesis: string;
  brandPosture: string;
  visualTension: string;
  signatureMove: string;
  hierarchyPrinciples: string[];
  densityRhythm: string;
  typographyRoles: string[];
  colorRoles: string[];
  surfaceLanguage: string;
  motionTone: string;
  imageryRole: string;
  preserveFromProjectDNA: string[];
  intentionalDepartures: string[];
  redesignBoundary?: {
    mode: "preserve-only" | "restyle-within-structure" | "greenfield";
    preserveRegions: Array<{
      regionId: string;
      sourceRef: string;
      invariants: string[];
    }>;
    replaceRegions: Array<{
      regionId: string;
      sourceRef: string;
      mustChange: Array<
        | "macro-layout"
        | "information-hierarchy"
        | "module-topology"
        | "typography-scale"
        | "surface-language"
        | "color-role-expression"
        | "data-visualization-form"
        | "spacing-density"
        | "imagery-role"
      >;
      minimumChangedDimensions: number;
    }>;
    forbiddenCarryover: string[];
  };
  contentDistribution?: {
    strategy: "single-viewport" | "progressive-scroll" | "multi-surface" | "on-demand";
    firstViewportRule: string;
    bands: Array<{
      id: string;
      placement: "first-viewport" | "continuation" | "on-demand";
      responsibilities: string[];
      contentIds: string[];
    }>;
    sharedContentIds: string[];
    mustRemainReachable: string[];
  };
  avoid: string[];
  evidence: VisualEvidence[];
}
~~~

Every core field is present. `hierarchyPrinciples`, `typographyRoles`, `colorRoles`, `avoid`, and `evidence` contain at least one supported entry; preservation and departure arrays may be empty when evidence supports no honest value. `redesignBoundary` is conditional as defined below. Do not invent a departure, source, font, token, or motion rule to fill the shape. Keep exact coordinates, component trees, renderer prompts, and implementation mechanisms out of this contract.

`redesignBoundary` is mandatory whenever the request preserves only part of an existing screen, asks for a complete/material redesign, or rejects a prior result as too similar. Use region IDs that describe semantic ownership, not pixel rectangles. In `preserve-only`, list only user-authorized invariants for the retained regions. For every replaced region, require at least two change dimensions and set `minimumChangedDimensions` high enough to distinguish a redesign from recoloring or card reshuffling. Put recognizable source structures that must disappear into `forbiddenCarryover`.

`contentDistribution` is mandatory when density or scroll materially changes what belongs in the first viewport. It records semantic priority, not fixed pixel geometry. Give every visible source fact, metric, action, or module one stable `contentId` and assign it to a band. The same content ID may appear in multiple bands only when explicitly listed in `sharedContentIds`; do not create summary/detail aliases to smuggle the same value into both. Persistent shell regions are invariants, not repeated band content.

Preserve the complete product through `mustRemainReachable`, but do not equate product coverage with design-bitmap density. Representative top/continuation artifacts may show only the content needed to prove hierarchy and visual continuity; later implementation and Runtime QA retain and verify the rest. A top screenshot and continuation screenshot are separate evidence outputs for one surface, not separate product pages.

`signatureMove` is a system-level relationship, not a literal wireframe. It is open enough when at least two materially different compositions or renderers could satisfy it. Each typography or color entry names a role, its purpose, and intended expression in one concise string before naming implementation tokens; project-native tokens may be referenced when verified. Evidence observations carry the source role plus whether the claim is direct or inferred in prose, while `sourceRef` and optional `sourceSha256` provide machine-checkable provenance. Because the current compact direction schema has no separate binding field, every FULL v3 observation also includes the exact `binding:<id>` marker from `structure.json`; missing or ambiguous binding identity is blocked. Each source must remain inside that binding's surfaces/aspects, and provenance does not broaden the scope.

## Preserve implementation freedom

Product specificity comes from semantic priority, hierarchy, rhythm, and signature relationships—not from bespoke implementation. Keep component trees, packages, custom-control choices, exact geometry, and renderer mechanisms outside the direction contract.

Project Fit is free and expected to realize the direction with mature project/internal components, supported variants, composition, platform/framework facilities, or well-fitted libraries. Two implementations may differ materially in DOM, component ownership, layout mechanism, or control package while satisfying the same direction. Reject a direction that becomes distinctive only when a team hand-writes a complex graph, editor, form system, overlay, chart, or other foundational control without a product-driven capability gap.

## Lock direction before artifacts

For a material redesign, set `visualDirectionPolicy` to `required`. Persist the validated contract at:

```text
.frontend-workbench/sessions/<session-id>/product-design/visual-direction.json
```

Lock its path and SHA through the active lifecycle state before producing the first visual artifact. Every runnable, browser-rendered, or ImageGen artifact created under that direction carries the same direction SHA.

A direction lock is not approval of a PNG, prototype, or implementation. Artifact review and user authorization remain separate SHA-bound decisions. Under `review-before-artifact` or `review-each-stage`, present the locked contract and obtain explicit authorization of that same SHA before the first artifact; the helper may persist the immutable lock first and authorize it in a separate idempotent call. Under `continuous`, no direction authorization is required. Under `review-before-implementation`, Product Design may render against the locked SHA, but implementation still requires separate direction authorization at its checkpoint.

Do not mutate a locked file. A material direction revision must explicitly invalidate or supersede downstream artifacts bound to the old SHA through the lifecycle mechanism; never repair drift by silently changing the file or renderer prompt.

## Apply a shared first-artifact critique

Review the first representative artifact of a locked direction, regardless of renderer, against:

- **concept specificity** — the idea belongs to this product and is perceptible without its prompt;
- **hierarchy** — product priority and attention order remain clear;
- **execution** — composition, type, color, surfaces, imagery, and motion express the contract coherently;
- **project DNA** — required foundations remain recognizable and departures are intentional;
- **redesign delta** — only declared preserve regions remain materially similar, every replace region clears its minimum changed-dimension count, and forbidden carryover is absent;
- **restraint** — the signature move does not become decoration or compete with the user job;
- **usability** — content, controls, states, and responsive priorities remain truthful and legible;
- **feasibility** — the artifact can be realized within the known architecture and constraints.

Feasibility includes implementation latitude: the artifact should communicate the locked hierarchy and relationships without making incidental bitmap geometry, sample content, or homemade controls mandatory.

Use one qualitative verdict:

- `PASS` — direction and execution are strong enough to continue;
- `REVISE_ARTIFACT` — direction remains valid; fix a bounded execution defect;
- `REVISE_DIRECTION` — the contract itself is generic, unclear, contradictory, or unfit;
- `BLOCKED` — missing evidence or a product/structure conflict prevents a safe judgment.

Do not fabricate aesthetic scores. `minimumChangedDimensions` is a coverage threshold: record which named dimensions changed materially and why; do not average them into a quality number. A polished artifact that preserves the old main-content macro-layout or module topology outside the preserve boundary is `REVISE_DIRECTION`/`REVISE_ARTIFACT`, never PASS. Bind a durable FULL critique to both the direction SHA and artifact SHA under `product-design/`. A dependent artifact normally needs continuity and contract-fidelity review, not a complete conceptual reset, unless it introduces a materially new visual mechanism.
