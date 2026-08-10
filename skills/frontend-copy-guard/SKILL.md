---
name: frontend-copy-guard
description: "Guard user-visible frontend copy during implementation and review. Use whenever any part of a task creates, changes, or renders interface text such as labels, help, validation, notifications, errors, empty states, status messages, accessibility names, or backend-generated copy shown in the UI; also use when ordinary inspection of task-relevant files reveals existing copy that leaks technical identifiers, raw errors, internal fields, APIs, algorithms, thresholds, workflow mechanics, or other internal implementation logic. Replace violations with task-focused product language, report pre-existing findings separately, and coordinate contract fixes only when backend work is already authorized in the current session. Do not use for work with no user-visible text or expand into a whole-repository copy audit unless requested."
---

# Frontend Copy Guard

Keep interface copy useful to the person completing a task without exposing implementation details they should not need to understand. Apply this guard across ordinary frontend implementation, not only design work.

## Preserve the request boundary

Activate this skill when any frontend or backend part of a task creates, changes, reviews, or renders user-visible interface text. Text introduced by any agent or subprocess during the current task counts as new task copy.

Do not activate it for code changes that cannot affect user-visible text. Do not turn a local implementation task into a whole-repository content audit.

Respect the user's authority:

- During implementation, fix violating copy before handoff.
- During a read-only review or diagnosis, report findings and proposed replacements without editing files.
- Do not infer backend authority merely because backend files exist or were inspected.
- Keep required legal, safety, pricing, eligibility, consent, and destructive-action information visible; rewrite it clearly instead of hiding it as “business logic.”

When fulfilling an implementation request, also apply the bundled `$frontend-project-fit` before editing. Copy corrections must use the host project's existing architecture, localization, components, styles, and error-handling paths rather than introducing parallel mechanisms.

## Load the references

- Read [references/copy-quality-rules.md](references/copy-quality-rules.md) before classifying or rewriting text.
- Read [references/cross-layer-contracts.md](references/cross-layer-contracts.md) when a UI exposes identifiers, enums, raw errors, or another backend-shaped input or output.
- Read [references/audit-and-reporting.md](references/audit-and-reporting.md) before validation and handoff.

## Follow the guard workflow

### 1. Establish audience and task

Identify who sees the text, what they are trying to accomplish, the product vocabulary already in use, and what information they need to decide or recover. Technical wording can be appropriate in a developer tool when the intended user genuinely needs it; do not classify by vocabulary alone.

### 2. Inspect all affected copy surfaces

Review both the current diff and the ordinary files needed to understand the change. Inspect, when relevant:

- JSX, templates, components, view models, and formatters;
- localization keys and every affected locale;
- labels, placeholders, help, tooltips, `aria-label`, alt text, and screen-reader-only copy;
- loading, empty, partial, disabled, validation, error, success, toast, dialog, and confirmation states;
- server or API messages rendered by the frontend;
- API-generated structured text, persisted or legacy copy, localization transforms, and secondary affected surfaces.

Do not limit review to strings added in the diff. Copy encountered in any task-relevant file inspected during ordinary work can be a pre-existing finding, even when that surface is not otherwise changed.

### 3. Classify before rewriting

For each questionable string, ask:

1. Does the user need this information to complete the task, make an informed decision, or recover from failure?
2. Is it expressed in the user's domain language rather than the system's storage, transport, or implementation language?
3. Does it reveal an internal identifier, field name, enum key, API path, stack trace, vendor detail, algorithm, ranking formula, hidden threshold, or workflow mechanic?
4. Does it tell the user what happened and what to do next without making an unsupported promise?
5. Would removing detail conceal a material constraint, charge, eligibility rule, consent consequence, or safety fact?

Rewrite only after resolving these tensions. “Less technical” must not become vague, deceptive, or incomplete.

### 4. Track provenance

Separate findings into:

- **Current-task copy**: introduced or materially changed by any agent during this task.
- **Pre-existing copy**: already present before the task and encountered during normal inspection.

Use version control when available, but do not assume every uncommitted line belongs to this task. Preserve unrelated user changes.

### 5. Fix current-task violations

Do not finish with newly introduced technical or internally revealing copy. Replace it with concise product language and adjust all affected locales, states, accessibility text, and tests.

Do not merely rename `UUID` to “ID” while still requiring the person to understand or enter an opaque value. When the wording exposes a contract problem, apply the backend scope matrix below.

Implement the correction through existing project components, variants, formatters, localization keys, and error adapters whenever compatible ones exist. Do not create a one-off copy or notification mechanism for convenience.

### 6. Handle pre-existing violations

Always record an encountered pre-existing violation separately and tell the user where it appears and why it conflicts with the guard.

During authorized implementation, fix it when it is on the affected surface, the correction is safe, and it stays within the current frontend scope. If it is unrelated, contract-dependent, ambiguous, or outside the authorized boundary, leave it unchanged and report it as a pre-existing follow-up. Never silently attribute it to the current diff.

### 7. Apply the backend scope matrix

When backend work is already part of the user-authorized task or current full-stack session, fix the experience end to end:

- replace manual opaque identifiers or raw enum input with domain options, user text, a stable product key, or a selector backed by lookup data;
- resolve internal IDs behind the interface rather than asking the user to know them;
- validate the domain input at the contract boundary;
- return stable domain errors and map them to localized, actionable interface copy;
- update frontend integration, backend behavior, and affected tests together.

When backend work is not part of the current session, do not broaden scope into backend changes. Fix the interface copy and any frontend-only mapping that the existing contract safely supports, map known raw errors to product language, retain diagnostic detail in logs, and continue. If the existing contract makes a nontechnical experience impossible, state the residual limitation explicitly instead of disguising or inventing support.

### 8. Validate the rendered outcome

Review the final diff for new strings, search affected localization and generated-copy paths, run relevant tests or snapshots, and reproduce the exact user-facing state when runtime access exists. Confirm that diagnostics remain available to developers without appearing as primary interface copy.

### 9. Report separately

In the final handoff, distinguish:

- current-task copy fixed or intentionally retained;
- pre-existing copy findings and whether each was fixed;
- backend contract changes, if backend was in scope;
- residual limitations, unverified states, and follow-up work.

Do not claim a copy issue is resolved from source inspection alone when the rendered path or server-generated message remains unverified.

## Keep these guardrails

- Prefer the user's task, object, and next action over storage or transport terminology.
- Do not expose raw UUIDs, database keys, enum constants, API routes, stack traces, or internal error codes unless the intended audience truly needs them.
- Do not reveal ranking formulas, fraud controls, moderation internals, private thresholds, or operational workflow mechanics that are unnecessary for the task.
- Do explain material product rules and consequences in plain language.
- Do not replace precise copy with generic “Something went wrong” when a safe, actionable explanation is available.
- Do not leak diagnostics into toasts or dialogs; log them through the project's established diagnostic path.
- Do not change backend contracts outside the authorized backend scope.
- Do not leave a newly introduced violation for the user to discover after handoff.
