---
name: frontend-copy-guard
description: "Review or change user-visible UI text, localization, labels, validation, and errors. Not for unrelated copy audits or backend-only work."
---

# Frontend Copy Guard

Keep affected interface copy clear, truthful, actionable, and expressed in the user's domain language.

## Choose the workflow profile

- **MICRO** — review or replace a few known strings on one surface, with no cross-layer mapping or new material claim. Inspect only the affected text and its immediate state; do not create a ledger or invoke Runtime QA automatically.
- **STANDARD** — copy across a user flow, several states, localization keys, accessibility names, or frontend error mapping. Apply the quality rules and focused source/runtime evidence that the wording requires.
- **FULL** — critical pricing, eligibility, consent, privacy, destructive-action, or safety language across surfaces/locales, or a backend-shaped contract that materially controls the UI. Preserve provenance and participate in the existing checkpointed workflow.

Escalate only for discovered impact, not because another frontend skill is active. Preserve an existing contract's workflowProfile.

## Scope

- Limit work to user-visible text in the requested or directly affected flow.
- During authorized implementation, fix current-task violations; during review, report replacements without editing.
- Do not infer backend authority from inspected files or a poor API message.
- Treat verification, freshness, provenance, synchronization, processing, confidence, and service-health details as hidden operational evidence unless an explicit visibility authority requires the exact claim on the current surface and state.
- Treat demo, fixture, sample, preview, cached, and fallback data provenance as a material data boundary whenever users could mistake it for canonical/live product data. Never let copy erase that boundary.
- Preserve material rules and consequences, and do not turn incidental strings into a repository-wide audit.

This skill owns affected copy, localization/accessibility wording, provenance, and authorized cross-layer mapping. It does not own frontend architecture or invoke another bundled skill back.

## Load references conditionally

- Read [references/copy-quality-rules.md](references/copy-quality-rules.md) for STANDARD/FULL work, when a MICRO classification is ambiguous, or whenever operational metadata could become visible.
- Read [references/cross-layer-contracts.md](references/cross-layer-contracts.md) only when opaque identifiers, enums, raw errors, or backend-shaped inputs/outputs reach the UI.

## Guard the affected copy

### Establish audience and surface

Identify who sees the text, their task, established product vocabulary, and the decision or recovery it supports. Technical language is valid when the intended audience needs it.

For FULL, consume `operationalMetadataPolicy` from the validated handoff. Its default is `hidden-unless-required`; an absent or empty `requiredClaims` array authorizes no visible operational claims. For MICRO/STANDARD, accept visibility authority only from the user's request, an approved product requirement/design, or a supplied legal/safety requirement. Existing code or copy alone is evidence to review, not authority to propagate a claim. Backend fields, available timestamps, internal evidence, generic best practice, and agent judgment are not visibility authority.

Inspect only relevant labels, help, confirmations, loading/empty/disabled/validation/error/success states, affected locales, accessibility text, and server messages actually rendered by the frontend. Ignore .frontend-workbench/; it is workflow state, not product copy.

### Fail closed for demo, fixture, and fallback data

Do not silently render demo, fixture, sample, preview, or fallback records on a canonical/live surface after a request, connection, authorization, or parsing failure. A successful schema parse, local fixture, screenshot, HTTP response, build, or prior cached render does not authorize copy such as “live”, “current”, “verified”, “synced”, “passed”, or “available”.

The product contract must provide a distinct typed state and authority for any intentional demo/fixture surface. Its copy must make the user-relevant boundary and disabled or non-canonical consequences clear without exposing test mechanics. Keep sample outcomes sample: they cannot become canonical success/failure history, operational evidence, counts, or timestamps.

If provenance or authority is missing or ambiguous, fail closed: do not substitute the data, suppress canonical actions and operational claims that depend on it, and use the established unavailable/empty/recovery state. Do not invent a reassuring badge or vague disclaimer. If the current frontend cannot distinguish live from fixture data, report the typed-contract gap; wording alone cannot make the state safe.

### Classify and rewrite

For each questionable string, determine whether it:

- provides information needed for the task or an informed decision;
- uses product rather than storage/transport language;
- exposes an internal identifier, enum, route, stack trace, vendor detail, or mechanic unnecessarily;
- explains what happened and the supported next action;
- would hide a material rule if simplified.

“Less technical” must not become vague, deceptive, or unrecoverable.

Do not self-authorize a status because it seems useful, reassuring, or decision-relevant. If the exact operational claim lacks authority for this surface/state, omit it without replacing it with vague cautionary copy. If authority exists, express only the declared user-facing meaning and supported action; keep the evidence and mechanism internal. When an unavailable live source would otherwise trigger fixture fallback, omission of one badge is insufficient: the whole canonical claim path must fail closed.

Use established localization, formatter, component, notification, and error-adapter paths. Update the affected states, locales, accessibility text, and tests. Do not rename UUID to “ID” and call the contract fixed: repair the domain mapping only when backend/full-stack scope is authorized; otherwise make the safest truthful frontend mapping and record the limitation.

### Preserve scope and provenance

Fix a pre-existing issue only when it is on the touched surface, materially harms the requested task, and the correction is safe within authority. Label material findings CURRENT TASK, PRE-EXISTING, or UNCERTAIN.

Validate new visible strings, affected locale/generated-copy paths, fixture/live state separation, accessibility names, and focused tests. Reproduce a rendered state only when the user requested it or visibility, provenance, truncation, recovery, or state timing cannot be proven from source. Copy review alone does not cascade into full Runtime QA.

For read-only work, write nothing. When a STANDARD/FULL parent flow already needs durable evidence, store only the minimal copy handoff in its ignored /.frontend-workbench/ session; never create reports or screenshots in product source.

## Completion

Finish when affected copy is truthful and consistent, demo/fixture data cannot masquerade as canonical/live state, unauthorized operational claims fail closed, material rules remain visible, internal details are hidden unless needed, backend authority was respected, and residual limitations are explicit.
