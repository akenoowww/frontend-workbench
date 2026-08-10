# User-facing copy quality rules

Use these rules to distinguish product language from implementation leakage. Judge text in its audience and task context rather than banning individual words mechanically.

## The product-language test

Good interface copy answers the smallest useful set of questions:

- What is this object or action in the user's vocabulary?
- What happened or what is required?
- Why does it matter to the user's task, when an explanation is necessary?
- What can the user do next?

Prefer concrete nouns and actions already used by the product. Keep wording concise, but do not remove information required for an informed decision.

## Usually inappropriate in end-user UI

- raw UUIDs, database primary keys, foreign keys, and storage paths;
- internal field or property names such as `user_status_code`;
- raw enum constants such as `PENDING_REVIEW_V2`;
- API routes, HTTP mechanics, payload shapes, vendor names, and queue names;
- stack traces, exception classes, request IDs as the primary message, and internal error codes;
- ranking formulas, recommendation weights, fraud signals, private thresholds, or moderation heuristics;
- implementation sequencing such as “waiting for worker 3” or “record not persisted”;
- self-justifying copy that explains internal engineering constraints instead of helping the user.

These details may remain in logs, diagnostics, support tools, or developer-facing products when the intended audience needs them. If a support reference is useful, place it after the human explanation rather than making it the message.

## Information that must not be hidden

Do not use this guard to conceal:

- price, billing, renewal, or cancellation consequences;
- eligibility and availability constraints;
- consent, privacy, or data-use implications;
- destructive or irreversible outcomes;
- safety requirements and meaningful risk;
- product limits the user needs in order to complete the task.

State these facts in plain language at the decision point. The problem is implementation leakage, not truthful product policy.

## Rewrite patterns

| Leaking copy | Product-language direction |
| --- | --- |
| `Enter project UUID` | Let the user choose a project by name or another domain label. Do not solve only by renaming UUID to ID. |
| `Invalid enum value: ACTIVE_V2` | Describe the valid status choices using their localized labels. |
| `POST /v1/orders returned 409` | Explain the order conflict and the available recovery action. |
| `recommendation_score < 0.73` | Explain the user-relevant outcome, not the ranking threshold. |
| `NullReferenceException` | State what could not be completed and how to retry or recover; retain the exception in diagnostics. |
| `Your record is in the moderation queue` | State the visible review state and expected next step without exposing internal queue mechanics. |

Treat each pattern as a direction, not canned copy. Match product voice, locale, and the actual supported behavior.

## Quality self-check

Challenge the first rewrite:

1. Did it merely replace one technical synonym with another?
2. Did it become so generic that recovery is impossible?
3. Did it hide a material rule or consequence?
4. Does it promise an action, timing, or result the product cannot guarantee?
5. Does the same issue remain in another locale, state, accessibility label, or server-generated message?

Revise until the copy is clear, truthful, actionable, and consistent across the affected experience.
