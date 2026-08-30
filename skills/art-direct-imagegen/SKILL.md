---
name: art-direct-imagegen
description: "Render locked frontend visual directions as one bitmap or a coherent set, with a standalone bitmap-only fallback. Not for design-only analysis, code/Figma/vector work, or surgical edits."
---

# Art-Direct ImageGen

Translate a locked visual direction into the requested bitmap outputs and report their status truthfully. This skill owns renderer briefs, ImageGen calls, bitmap-specific review, continuity, and accepted-image delivery—not upstream concept, product behavior, IA, copy, routes, code, or implementation. Only a standalone bitmap request may use the bounded direction fallback below.

## Choose the workflow profile

- **MICRO** — one independent output with a fixed objective and no dependency, approval checkpoint, durable resume, promotion gate, or downstream fidelity gate. Render and review it without initializing the full runtime.
- **STANDARD** — one output or a small set needing art direction and bounded iteration, but no staged implementation contract. This includes an explicitly preview-only, non-promotable redesign evaluation when the target, preserve/replace boundary, reference roles, named outputs, and fixed call budget are all supplied and no implementation or durable acceptance follows. Render one output per call and preserve files through the system ImageGen path rules.
- **FULL** — dependent/coherent outputs that carry user acceptance or downstream authority, page-by-page approval, a complete/material redesign intended for implementation, durable resume/promotion, or a design-to-implementation fidelity contract. Use workflowProfile full and the runtime state machine.

If the request is only analysis, exit this skill. Route a fixed surgical bitmap edit to the system imagegen workflow without adding art direction. Escalate from MICRO/STANDARD only when a FULL criterion appears.

## Choose the contract mode

- **UPSTREAM CONTRACT** — consume the supplied objective, locks, direction, content, reference scope, and delivery requirements. FULL v3 additionally requires product/scenario/shell identities, scoped `referenceBindings`, declared design-evidence outputs, and any applicable render budget. Treat supplied direction, page, state, viewport, content, and product decisions as fixed. A material upstream render without a required locked direction is blocked and returns to Product Design.
- **STANDALONE** — extract only the user's explicit content, references, constraints, and requested outputs. Use the shared Product Design method to synthesize a bitmap-only `VisualDirectionContract`, but do not invent product pages, controls, states, copy, navigation, code, or implementation authority. A complete/material redesign normally routes through Product Design and FULL. The only exception is an explicitly preview-only STANDARD evaluation with a supplied preserve/replace boundary, scoped references, named outputs, fixed budget, and no implementation, promotion, or durable acceptance; its result is non-promotable design evidence and must be rebound through Product Design/FULL before downstream use. Block on an unresolved product decision.

Label supplied images FUNCTIONAL_REFERENCE, STYLE_REFERENCE, EDIT_TARGET, or VISUAL_ANCHOR. Apply each only through applicable `referenceBindings` entries and their surfaces/aspects; never silently treat a functional reference as an edit target or let a module reference replace an inherited shell.

## Load only what the profile needs

- Read [references/output-contract.md](references/output-contract.md) for every run.
- Read [the shared visual-direction reference](../frontend-product-design/references/visual-direction.md) only for the STANDALONE fallback or the shared first-artifact critique. Do not reopen an upstream locked direction.
- Read [references/prompt-and-review.md](references/prompt-and-review.md) before the first ImageGen call and before acceptance.
- Read [references/full-runtime.md](references/full-runtime.md) only for FULL.

## Render

1. **Validate the current output.** MICRO/STANDARD need only the bounded objective, requested bitmap, applicable inputs/roles, direction, content, and delivery path. FULL additionally confirms stable output/surface/state/viewport identity, required design evidence, artifact kind, shell/reference IDs, direction SHA, approval/promotion fields, and remaining render budget. Do not add a page or state to solve density, and do not render runtime-only coverage.
2. **Resolve direction ownership.** For UPSTREAM CONTRACT, validate and preserve the locked direction. For STANDALONE only, select one direction through the shared reference and freeze the bitmap-only contract before prompting. Keep internal candidate reasoning out of the renderer prompt.
3. **Start the right execution path.** MICRO/STANDARD do not initialize the full checkpoint runtime. FULL validates or resumes the active .frontend-workbench session before any expensive call and follows the state machine in full-runtime.md.
4. **Render serially.** Make one built-in ImageGen call for one output. Never use parallel calls, n, a collage, or subagents for connected deliverables. MICRO/STANDARD allow exactly one ImageGen call per user turn unless the user explicitly requested multiple named outputs or variants. A failed first render ends the turn as `REVISE_ARTIFACT`; do not issue another `Create` call for the same output. FULL retries require a successful render-budget reservation. A long page may have separate `top` and `continuation` outputs, one call each, when `contentDistribution` declares progressive scroll; do not compress both bands into one viewport. Before each call, treat the current band's `contentIds` as a visibility allowlist: no other band's metric, label, status, action, or source fact may enter the prompt unless its stable ID is explicitly in `sharedContentIds`. Global product truth is a preservation constraint across the complete product, not an instruction to render every fact in this bitmap. Ordering dependencies do not imply visual continuity. When `anchorOutputId` is non-null, use only its accepted artifact bound by `anchorArtifactSha256` and verify the renderer brief's preserve/change-only delta plus current direction, shell, content-distribution, and reference identities before the call.
5. **Review before acceptance.** Check bitmap and output-contract fidelity first, then apply the shared first-artifact critique when this is the representative artifact for the direction. For every FULL output with `artifactKind: imagegen`, attach the helper-verified provenance receipt before review regardless of the overall artifact policy. On a later user-authorized retry, edit the saved failed artifact itself; keep all supplied input roles immutable and never promote a `STYLE_REFERENCE` or `FUNCTIONAL_REFERENCE` to `EDIT_TARGET`. Return upstream `REVISE_DIRECTION` or `BLOCKED` without silently changing a locked concept.
6. **Deliver truthfully.** Save accepted artifacts through system ImageGen rules. Promote a project-bound FULL artifact only through the runtime helper. Preview-only output may remain in allowed task storage.

## Keep prompts and status lean

Compile one prompt for one visible output: ID/type, immediate purpose, applicable reference bindings/input roles, only the current band's content IDs and critical short labels, the relevant locked direction relationship, continuity locks, creative latitude, and at most three causal avoid items. For progressive scroll, perform a literal prompt-to-band check before the expensive call: remove every label, value, action, and status owned by another band, and do not disguise repetition through “summary” versus “detail” aliases. Exclude the full direction/global contract, rejected concepts, other outputs, product reasoning, implementation instructions, and long copy.

For MICRO/STANDARD, report `PASS`, `REVISE_ARTIFACT`, `REVISE_DIRECTION`, or `BLOCKED` after that single call without pretending it is a durable checkpoint. User feedback in a later turn authorizes one new attempt, not an autonomous chain of fresh renders. The retry must reference the previous artifact and state one bounded delta; if the direction itself changed, treat it as a new initial attempt and still stop after one call. For FULL, use only runtime-defined statuses and transitions; never regenerate accepted/promoted work or report success while a required design anchor is unfinished. Downstream implementation may begin only through begin-implementation after every output with required design evidence is accepted or promoted; `imagegen-required` makes each such acceptance user-authorized. Runtime-only outputs remain for Runtime QA.

Generated UI is an instance of visual direction, not the direction contract, component specification, runtime evidence, or implementation proof. It may express project-specific hierarchy without requiring custom controls; Project Fit chooses mature implementation capabilities. Report the direction reference/SHA, output status, accepted/promoted paths, anchor identity when applicable, budget use, critique verdict, and final prompt set. A standalone direction remains bitmap-only until Product Design validates it for a downstream handoff.
