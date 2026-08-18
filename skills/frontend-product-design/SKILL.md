---
name: frontend-product-design
description: "Use for explicit UI/UX interaction or visual design, redesign, new-surface design, or critique after structure is known. Consume an information-architecture contract for multi-page work and implement only when requested. Do not use for sitemap-only work, specified implementation, small styling or copy edits, bugs, tests, performance, or backend work."
---

# Frontend Product Design

Resolve material product-design decisions from user and project evidence, then hand off a frozen design contract. Do not activate this workflow merely because frontend code will change.

## 1. Freeze scope, authority, and checkpoints

Record:

- requested outcome and target zone;
- confirmed facts, constraints, exclusions, and evidence gaps;
- `authority`: `design-only`, `critique-only`, or `design-and-implementation`;
- `checkpointMode`: `continuous`, `review-before-artifact`, `review-each-stage`, or `review-before-implementation`.

Infer the checkpoint mode from the request. Use `continuous` when the user authorized the whole sequence and no material choice requires approval. Use `review-each-stage` when the user asks for step-by-step work, separate page review, or approval before continuing: checkpoint after structure, selected direction, accepted master, and each required page family or explicitly named page. Use another review mode only when requested or when proceeding would commit to a materially different direction. Ask one concise question only when scope, authority, or a consequential choice cannot be inferred safely.

For redesigns, read [references/redesign-boundaries.md](references/redesign-boundaries.md). A redesign changes only the agreed zone and never silently removes required capabilities, states, accessibility, or data contracts.

## 2. Inspect project evidence

When repository access exists, read [references/project-archeology.md](references/project-archeology.md). Inspect the affected surface, similar internal surfaces, design tokens, shared components, interaction conventions, responsive behavior, localization, accessibility, data/state constraints, and tests. Keep the resulting project evidence concise and cite paths or runtime observations for material claims.

If the relevant project or surface is unavailable, use only supplied artifacts and state the limitation. Do not claim project fit from framework defaults or one screenshot.

## 3. Consume structure and model the product decisions

For a new multi-page site, application structure, sitemap, navigation model, or multi-step flow, apply the bundled `$frontend-information-architecture` workflow first when available. Consume its frozen surfaces, routes, page families, navigation edges, states, viewports, required outputs, and authority block. Do not silently redesign that structure downstream.

If the host cannot compose the structure skill, use a compact fallback before visual work: list every named page or surface, its user job, page family, navigation destination, meaningful states, and material viewports. Keep `page`, `state`, `viewport`, `scroll position`, and `output` separate. For a fully specified single surface, reuse the supplied structure without creating an unnecessary site contract.

Define the necessary information, actions, constraints, feedback, and recovery inside the frozen structure. Resolve only decisions that materially change behavior or hierarchy. If visual feasibility exposes a structural contradiction, return a `STRUCTURE_CONFLICT` with affected IDs and evidence instead of changing routes or page ownership silently.

## 4. Research and choose one coherent direction

Use internal evidence first. Read [references/ux-research.md](references/ux-research.md) only when current external guidance, mature product behavior, or comparison can change an important decision.

Compare viable alternatives only for material decisions. Select one project-specific direction, resolve conflicts across decisions, and record consequences. Do not copy a product, assemble unrelated best practices, or expose private chain-of-thought; present concise evidence, alternatives when useful, and the decision.

## 5. Choose the lightest useful artifact

Read [references/artifact-choice-and-validation.md](references/artifact-choice-and-validation.md) before creating a visual artifact or validation plan.

Choose among an annotated specification, existing-component composition, runnable prototype, browser screenshot, or ImageGen concept according to what can actually test the decision. ImageGen is optional. Invoke the bundled `$art-direct-imagegen` only when generated bitmap exploration or a coherent rendered page/state set materially helps. Do not block authorized implementation merely because ImageGen is unavailable; require appropriate browser, runtime, or visual verification instead.

Before freezing a mockup or renderer brief that authors user-visible labels, claims, pricing, validation, consent, or recovery text, apply `$frontend-copy-guard` to that affected copy. Art direction consumes approved exact labels; it does not invent or validate product claims.

If `checkpointMode` is `review-before-artifact`, present the design and coverage decision before producing the selected artifact.

If `checkpointMode` is `review-each-stage`, set `approvalRequired: true` on each output that closes a user-visible checkpoint. Do not start the next dependent artifact or page output until the runtime records explicit approval. Persist the exact pending output IDs so a later task resumes rather than replans.

## 6. Use the hidden task workspace without stray artifacts

Create durable working artifacts only when the task needs cross-skill handoff, generated media, or a requested design file. Before the first write, require the exact root `.gitignore` entry `/.frontend-workbench/`, verify it with `git check-ignore`, and use the bundled runtime helper when available. Keep canonical `state.json`, `structure.json`, and `coverage.json` at the session root. Use `product-design/` only for design-specific decision notes and `design-handoff.md`; ImageGen prompts and reviews belong to `art-direct-imagegen/`, binary outputs to `artifacts/`, and rendered QA evidence to `qa/`. Never scatter discretionary files in the repository root or source directories.

Do not create the workspace for a read-only answer that needs no file artifact. For greenfield visual work with no consumer repository, provision an allowed task-scoped temporary Git workspace with the same exact ignore rule before durable multi-output execution; never use the plugin source repository as the consumer. If neither a safe project workspace nor temporary Git workspace is available, keep a handoff-only record in the conversation and state that resumable rendering was not initialized. Project-native source changes and explicitly requested assets still belong in their normal project paths.

## 7. Freeze the handoff and complete truthfully

Read [references/frozen-handoff.md](references/frozen-handoff.md) before handing design to implementation or producing a durable design handoff.

For `design-and-implementation`, freeze the authorized scope, coverage, selected decisions, protected behavior, accepted evidence, permitted implementation adaptations, and unresolved items. Then invoke `$frontend-project-fit`; if implementation affects user-visible text, also invoke `$frontend-copy-guard`, and use `$frontend-runtime-qa` for rendered verification after visible changes. This skill does not own ordinary implementation or QA mechanics.

If `checkpointMode` is `review-before-implementation`, stop at the frozen handoff until approval. Reopen design only when implementation discovers a material contradiction; do not let incidental code choices silently redesign the product.

Complete only when the requested design decision is resolved, required coverage is accounted for, the chosen artifact or validation evidence is reviewed when applicable, authority boundaries are preserved, and blocked, deferred, or unverified items are explicit. Distinguish design evidence, implemented code, local validation, and production proof.
