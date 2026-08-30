# Visual reference and brand extraction

Use this reference when supplied websites, screenshots, brand guidance, visual anchors, or external examples can materially change the project-specific visual direction. It complements project archaeology; it does not replace source or runtime inspection.

## Assign source roles and provenance

Label every source as `functional-reference`, `style-reference`, `visual-anchor`, `edit-target`, or `constraint`. One source may support multiple observations, but a functional reference is never silently treated as a layout template or edit target.

For FULL v3, record one or more scoped `referenceBindings` rather than giving the source ambient authority:

```text
referenceBinding
- id
- sourceRef / sourceSha256 when stable bytes exist
- roles[]
- surfaceIds[]
- aspects[]
- constraints[]
- mustNotInfluence[]
```

Use separate bindings when one source has different roles on different surfaces. Bind only the aspects the evidence can support, such as shell continuity, information hierarchy, density, typography, color, material language, imagery, motion, interaction, or content. `mustNotInfluence` should name the likely leakage: a functional example must not set style, a visual anchor must not invent behavior, and a module-specific reference must not replace an inherited parent shell.

For every material observation record:

- `sourceType`: `project-file`, `screenshot`, `brand-guide`, `website`, or `user-input`;
- a precise `sourceRef`: repository-relative path, artifact ID, screenshot path, page URL, or brand-guide section;
- an `observation` that states the source role, the observed rule or relationship, and whether it is direct or inferred;
- `sourceSha256` when stable local bytes exist.
- the state, viewport, theme, and capture date when they affect interpretation.

Keep the evidence close to the `VisualDirectionContract` field it supports. The compact persisted JSON uses only `sourceType`, `sourceRef`, `observation`, and optional `sourceSha256`; richer source-role and confidence notes belong in the observation rather than incompatible extra fields. A provenance entry proves where an observation came from, not ownership, licensing, current runtime behavior, or permission to copy it.

The compact direction evidence does not replace the upstream binding. It cites the same source and, in FULL v3, includes the exact `binding:<id>` marker in `observation` while the lifecycle contract owns which surfaces and aspects may consume it. This marker is required because multiple scoped bindings may share one source and the compact direction schema has no dedicated binding property. Broadening that scope, changing a stable source SHA, or changing a visual anchor requires explicit contract change control before dependent artifacts continue.

## Extract roles, not decoration

Inspect only dimensions that can change the direction:

### Color

- semantic roles, emphasis hierarchy, neutrals, status colors, contrast, and theme behavior;
- declared tokens versus colors sampled or visually inferred from a raster;
- where color is intentionally absent.

Do not turn every observed hex value into a project token.

### Typography

- display, reading, interface, label, and data roles;
- family or category, weight, width, scale, line height, case, and rhythm when directly available;
- optical contrast and hierarchy, not only font names.

### Layout and density

- grid or alignment logic, content width, spacing cadence, grouping, whitespace pressure, and dense/quiet alternation;
- responsive reflow, collapse, prioritization, and touch-space changes;
- radius, border, divider, elevation, and layering behavior.

### Imagery and surfaces

- image purpose, subject posture, crop, framing, texture, treatment, illustration or photography relationship;
- surface hierarchy, material character, overlays, transparency, and depth;
- component posture: quiet or emphatic, editorial or operational, compact or expansive, literal or expressive.

### Motion

- trigger, direction, duration class, easing character, continuity, emphasis, and reduced-motion behavior when observable;
- distinguish live observation from an inference based on a still image.

## Separate preservation from departure

Map supported observations into:

- `preserveFromProjectDNA` when existing project identity or product familiarity must survive;
- `intentionalDepartures` only when scope and evidence justify a change;
- `typographyRoles`, `colorRoles`, `surfaceLanguage`, `motionTone`, and `imageryRole` as renderer-neutral rules;
- `avoid` only for likely failures with a causal relationship to the chosen direction.

When sources conflict, state the conflict and choose according to user authority, current project truth, source recency, and relevance to the target surface. Do not average incompatible references into a moodboard-style mixture.

For nested shells, prefer one accepted parent-shell anchor bound to the shell/hierarchy aspects over repeating vague “same style” instructions. Child outputs inherit only the named shell invariants and may change only their declared content slot; they do not gain authority to create a second global shell.

## Evidence boundaries

- A screenshot can prove visible composition, not hidden interaction behavior or implementation tokens.
- Generated CSS can reveal emitted values, not necessarily the authoritative design system.
- A public site may have changed; record when it was observed.
- A brand guide may be authoritative for identity but silent about product usability or responsive behavior.
- Missing runtime, fonts, representative data, or source access remains an explicit evidence gap.

If a missing source would materially change brand posture, preservation, or an intentional departure, pause that decision. Otherwise proceed with a labeled assumption and keep it out of `direct` evidence.
