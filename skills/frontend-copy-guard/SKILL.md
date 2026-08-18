---
name: frontend-copy-guard
description: "Use when the task changes or reviews user-visible interface text, including localization, accessibility labels, validation, errors, and server-originated UI messages. Make affected copy truthful and actionable. Do not expand into unrelated pre-existing copy or unauthorized backend changes."
---

# Frontend Copy Guard

Keep the affected interface copy clear, truthful, actionable, and expressed in the user's domain language.

## Scope and authority

- Apply this workflow only to user-visible text in the requested or directly affected flow.
- During authorized implementation, fix current-task violations before handoff.
- During review or diagnosis, report evidence and suggested replacements without editing.
- Do not infer backend authority from inspected files or a poor API message.
- Preserve material pricing, eligibility, consent, privacy, destructive-action, and safety facts.
- Do not turn incidental strings into a whole-repository content audit.

This skill owns affected copy, localization and accessibility wording, copy provenance, and authorized cross-layer mapping. It does not own frontend architecture or invoke another bundled skill back.

## Load references conditionally

- Read [references/copy-quality-rules.md](references/copy-quality-rules.md) before classifying or rewriting questionable text.
- Read [references/cross-layer-contracts.md](references/cross-layer-contracts.md) only when opaque identifiers, enums, raw errors, or backend-shaped inputs and outputs affect the UI.

## Workflow

### 1. Establish audience and task

Identify who sees the copy, what they are trying to accomplish, the product vocabulary already in use, and what they need to decide or recover. Technical terms can be correct in a developer-facing product when that audience genuinely needs them; do not classify by vocabulary alone.

### 2. Inspect the affected copy surface

Review the current diff and the ordinary sources needed to understand the flow, including relevant:

- labels, placeholders, help, tooltips, and confirmations;
- loading, empty, disabled, validation, error, success, and recovery states;
- localization keys and affected locales;
- `aria-label`, alt text, and screen-reader-only text;
- server or structured messages actually rendered by the frontend.

Do not inspect `.frontend-workbench/` ledgers, prompts, renders, or QA notes as interface copy. They are private workflow artifacts.

### 3. Classify before rewriting

For each questionable string, determine:

- whether the information is required for the task or an informed decision;
- whether it uses product language rather than storage or transport language;
- whether it exposes an internal identifier, enum, route, stack trace, vendor detail, formula, threshold, or workflow mechanic unnecessarily;
- whether it explains what happened and the supported next action;
- whether removing detail would conceal a material rule or consequence.

“Less technical” must not become vague, deceptive, or impossible to recover from.

### 4. Fix current-task copy through existing paths

Use the project's established localization, formatter, component, notification, and error-adapter mechanisms. Update all affected states, locales, accessibility text, and tests. Do not create a one-off copy or notification system.

Do not solve an opaque-input problem by renaming `UUID` to “ID.” If the current authorized scope includes backend or full-stack work, fix the domain contract end to end. If backend is out of scope, make the safest truthful frontend mapping supported by the current contract and record the residual limitation.

### 5. Handle pre-existing findings proportionally

Report a pre-existing issue only when it appears on the touched surface and materially harms the requested task, truthfulness, safety, or recovery. Fix it when the correction is safe and stays within the authorized surface. Leave unrelated, ambiguous, or contract-dependent copy unchanged.

Keep provenance explicit: `CURRENT TASK`, `PRE-EXISTING`, or `UNCERTAIN`. Never attribute an existing line to the current change without evidence.

### 6. Validate and hand off

Inspect the final diff for new user-visible strings, search affected locale and generated-copy paths, run focused tests, and reproduce the exact rendered state when runtime access exists. Keep raw diagnostics in the project's logging path rather than toasts or dialogs.

Do not create `ANALYSIS.md`, a copy report, screenshots, or other discretionary artifacts in product source. When a durable ledger or rendered evidence is required and a local filesystem is available, require and verify the exact `/.frontend-workbench/` ignore rule, then store it in the current runtime session. For a read-only response with no requested artifact, write nothing.

## Completion contract

Finish only when:

- current-task copy is truthful, actionable, and consistent across affected states and locales;
- implementation details are hidden unless the intended audience needs them;
- material product rules remain visible;
- backend changes stayed inside explicit authority;
- rendered verification is reported separately from source inspection;
- material pre-existing or residual limitations on the touched flow are stated without expanding scope.
