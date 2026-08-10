---
name: frontend-product-design
description: "Research, justify, visualize, and, only when requested, implement substantial frontend product-design decisions inside an existing project. Use only when the user explicitly asks for UI/UX design, redesign, information architecture, interaction design, visual direction, design critique, or asks the agent to determine the structure or behavior of a new frontend surface. Do not use for ordinary frontend coding, implementing an already-complete design, small CSS or copy fixes, refactors, tests, performance work, backend work, or other tasks that do not ask for design judgment."
---

# Frontend Product Design

Design from project and product evidence before writing production UI code. Treat a technically valid interface as insufficient until its structure, interaction model, important states, and visual direction are justified.

## Apply the scope gate first

Use this workflow only when the request explicitly requires design judgment. Qualifying requests ask to design or redesign UI/UX, decide information architecture or interaction behavior, establish a visual direction, critique a design, or turn a product requirement into a designed frontend surface.

Exit this skill when the task is only to:

- implement a fully specified design;
- fix a frontend bug, test, type error, or performance issue;
- make a small CSS, color, spacing, or copy change;
- refactor components or data flow;
- do backend or infrastructure work;
- perform any frontend task that does not ask for a design decision.

Do not manufacture a design phase after a false-positive activation. Continue with normal project work or another narrowly relevant skill.

Preserve the user's authority boundary:

- For a design-only request, produce the requested design artifacts and do not edit production code.
- For a design-and-implementation request, pass the design gate before editing production UI.
- For a critique or research request, stop after the requested analysis or specification.
- If the desired deliverable is materially ambiguous and cannot be inferred safely, ask one concise question; otherwise proceed.

## Choose proportional depth

Use the **full track** for a new page, flow, panel, overlay, editor, major section, or substantial redesign.

Use a **focused track** for one meaningful design decision. Compress sections that genuinely add no evidence, but keep the sequence: project context -> user problem -> alternatives -> decision -> affected states -> validation.

Exit the skill for trivial cosmetic work. Never create a long report to justify an inconsequential change.

## Load references by phase

- Read [references/project-archeology.md](references/project-archeology.md) before making design decisions in an existing repository.
- Read [references/feature-modeling.md](references/feature-modeling.md) to model the user task and decompose important UX decisions.
- Read [references/ux-research.md](references/ux-research.md) before external research, product comparison, option selection, or decision recording.
- Read [references/interaction-and-state-modeling.md](references/interaction-and-state-modeling.md) before finalizing behavior or state coverage.
- Read [references/visual-synthesis-and-imagegen.md](references/visual-synthesis-and-imagegen.md) before creating a visual brief or invoking `$art-direct-imagegen`.
- Read [references/implementation-and-validation.md](references/implementation-and-validation.md) before planning or editing production code.
- Use [references/report-template.md](references/report-template.md) as the concise working artifact and implementation gate; do not pad inapplicable sections.

## Follow the design workflow

### 1. Establish the request contract

Record the requested outcome, user goal, supplied evidence, constraints, explicit prohibitions, and whether implementation is authorized. Separate known facts, reasonable inferences, and unresolved decisions.

Do not infer business logic from a feature name. Do not silently broaden a design-only request into code changes.

### 2. Inspect the host project

Inspect the actual repository before designing when access exists. Identify the frontend stack, routing, component and styling systems, tokens, typography, icons, state and data patterns, forms, motion, localization, permissions, accessibility helpers, responsive conventions, and tests.

Choose one or two structurally or behaviorally similar project surfaces as primary internal references when possible. Search for reusable components before proposing new primitives.

Produce a concise `PROJECT UI DNA` from repository evidence. If the repository or relevant surfaces are unavailable, state the evidence gap and use only supplied artifacts; never invent project conventions.

### 3. Model the feature as a product problem

Describe the primary user goal, necessary information, actions, inputs, outputs, dependencies, constraints, frequency, reversibility, persistence, and edge cases. Distinguish what must remain visible from what can be progressively disclosed.

Do not reduce the feature to a component list.

### 4. Decompose independent UX decisions

Create identifiers such as `D01`, `D02`, and `D03` only for questions whose answers materially change behavior or hierarchy. Phrase each as a precise question.

Do not research an entire page with one vague query. Omit categories that are irrelevant to the feature.

### 5. Research and decide atomically

For every important decision:

1. state the user need and project constraints;
2. gather internal evidence;
3. use external research only when it can change or support the decision;
4. inspect multiple mature products or authoritative guidance when useful;
5. extract the shared behavioral pattern rather than copying a product;
6. compare viable alternatives and their trade-offs;
7. select the project-specific approach and record consequences.

Optimize for the user's real workflow: interaction count, discoverability, cognitive load, context preservation, safety, undoability, keyboard and mobile use, persistence, accessibility, and feedback.

### 6. Synthesize one coherent experience

Resolve conflicts between individually reasonable decisions. Remove competing controls, duplicated actions, inconsistent terminology, excessive overlays, incompatible state models, and desktop/mobile contradictions.

Prefer the simplest coherent interaction that satisfies the user goal and fits the project. Do not assemble a collage of best practices.

### 7. Build interaction and state models

Specify the entry point, default state, primary and secondary paths, action results, transitions, overlays, dismissal, persistence, validation, errors, recovery, destructive actions, keyboard behavior, and responsive changes.

Model only meaningful states, including relevant loading, empty, error, partial, disabled, selected, editing, saving, success, failure, permission, overlay, and mobile variants. Relate derived states to a shared parent instead of treating them as unrelated screenshots.

### 8. Create and review the visual system

Combine `PROJECT UI DNA`, the feature model, selected decisions, interaction model, state model, and current state into a visual specification. Reuse project tokens and components instead of inventing arbitrary colors, spacing, radii, typography, or navigation.

For the full track, invoke the bundled `$art-direct-imagegen` skill only after UX synthesis. Generate the master/default state first, then the minimum set of meaningful derived states while preserving one visual identity. For a focused nonvisual decision, skip image generation only when an image cannot test the decision, and record why. If the user explicitly forbids or defers image generation, prepare the complete handoff, record the deferred stage, and preserve that boundary.

Review actual outputs for project fit, hierarchy, clarity, density, discoverability, state consistency, functional truthfulness, and implementability. If a visual exposes a UX flaw, revise the relevant decision rather than blindly implementing the image.

If the host cannot invoke the bundled art-direction skill, finish a complete visual handoff and report that rendering is blocked by client capability. For a full-track task, stop before production implementation until the required visual stage can run. Do not silently claim that a generic image call completed the art-direction stage.

### 9. Plan implementation

Only when implementation is requested, map the approved design onto routes, existing files and components, new components that are truly required, state, APIs, permissions, loading and error handling, responsiveness, accessibility, and tests.

Prefer the smallest architectural change that cleanly supports the designed behavior.

### 10. Enforce the implementation gate

Begin production UI edits only when all materially relevant items are understood:

- project design language and reusable primitives;
- primary user goal and feature structure;
- important interactions and selected patterns;
- meaningful states and responsive transformations;
- visual direction;
- technical integration path;
- implementation authority from the user.

Do not translate unresolved important design questions into arbitrary code decisions. Return to the relevant phase when the gate fails.

### 11. Implement behavior, not a screenshot

Reuse or extend existing components before inventing primitives. Match project conventions for file organization, naming, component APIs, state, data fetching, styling, tests, error handling, accessibility, and responsive behavior.

Treat generated UI images as design references, never as proof. Implement the intended hierarchy, interactions, states, transitions, and recovery behavior.

### 12. Validate and report truthfully

Validate technical correctness, product behavior, visual consistency, responsiveness, and accessibility in proportion to the change. Reproduce the exact user flow and important states when possible.

Separate in the final handoff:

- design decisions and evidence;
- visual artifacts reviewed;
- code implemented;
- checks actually run and their results;
- anything unverified, blocked, or pending.

Never call a mockup production proof or local checks live verification.

## Use this evidence order

When evidence conflicts, prioritize:

1. explicit user requirements;
2. functional and product requirements;
3. existing project conventions;
4. existing reusable components;
5. user-usage and UX reasoning;
6. relevant real-world product patterns;
7. general design conventions;
8. pure aesthetic preference.

Document an explicit user-requested deviation from existing project conventions.

## Keep these guardrails

- Do not design a major frontend surface before inspecting the project when repository access exists.
- Do not assume business logic from labels or feature names.
- Do not copy one external product or choose a pattern because it is popular.
- Do not hardcode a domain, cards, tables, filters, sidebars, tabs, modals, or any visual style as universal.
- Do not let external references override the host product without a reason.
- Do not visualize only the default state when meaningful interaction states exist.
- Do not invoke `$art-direct-imagegen` before UX synthesis.
- Do not create a new UI primitive without searching for an existing one.
- Do not begin implementation while important design decisions remain unresolved.
- Do not expose long private reasoning; present concise evidence, options, decisions, and consequences.
