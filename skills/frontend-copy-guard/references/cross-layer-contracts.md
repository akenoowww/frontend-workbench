# Cross-layer copy and contract handling

Use this reference when technical UI copy is a symptom of the data or error contract rather than an isolated wording problem.

## Determine backend scope first

Backend is in scope only when the user's current request explicitly or clearly authorizes backend or full-stack implementation. Opening a backend file, reading an API schema, or discovering a contract limitation does not grant authority to change it.

Record one of two states:

- `BACKEND IN SESSION SCOPE`
- `BACKEND OUT OF SESSION SCOPE`

## Backend in session scope

Fix the complete task contract rather than masking the UI symptom.

### Technical input

If a user is asked to type a UUID, enum key, database key, or other opaque value:

1. identify the domain object or choice the user actually understands;
2. choose a safe input model: lookup-backed selector, allowed option, user text resolved with disambiguation, or stable domain key;
3. keep internal identifiers behind the interface;
4. validate and authorize the resolved object server-side;
5. handle missing, duplicate, stale, and unauthorized choices;
6. update frontend, backend, schemas, localization, and tests together.

Do not accept arbitrary free text when it would create ambiguity or weaken authorization. A selector can submit an internal ID invisibly when that is a normal machine contract, provided the user chooses a recognizable domain option and the backend owns validation. If the contract itself publicly requires the opaque value, add or change the product-facing lookup or semantic endpoint.

### Technical output and errors

Prefer stable machine-readable domain error identifiers plus structured safe context. Map them to localized product messages at the presentation boundary. Keep traces, raw provider responses, request payloads, and exception details in established logs.

Check that:

- the backend does not require the frontend to parse an English exception string;
- errors distinguish actionable states such as missing, forbidden, conflict, expired, and temporarily unavailable;
- user copy does not expose security controls or sensitive decision logic;
- the UI never promises retry, availability, or timing that the contract cannot support.

## Backend out of session scope

Do not mutate API handlers, schemas, databases, or server validation.

Within the frontend boundary:

- replace technical labels and explanations with product language;
- use existing lookup data to render names and options while preserving the current request shape;
- map known server errors to safe, actionable messages;
- use a truthful generic fallback for unknown errors;
- send raw diagnostic context only through the project's existing logging path;
- test that mappings do not collapse materially different user outcomes.

If no existing data or endpoint can translate an opaque requirement into a usable choice, do not pretend a label change solved the experience. Keep the backend unchanged, make the safest frontend correction available, and report the contract limitation as residual work.

## Preserve data provenance and fallback semantics

When a surface can receive live, cached, fixture, sample, preview, or fallback data, require a stable discriminated state at the established data adapter boundary. The UI must not infer provenance from object shape, record names, request timing, environment labels, or whether a fetch threw. Keep canonical actions, counts, success/failure history, verification, freshness, sync, confidence, and service-health claims bound to the states that actually authorize them.

An intentional demo or preview mode must be entered through an explicit product route, setting, workspace, or supplied contract and must define what is non-canonical or disabled. A failed canonical request must not switch into that mode implicitly. If the live state cannot be distinguished safely:

- with backend/full-stack scope, repair the typed response or adapter contract and update source-state tests;
- without backend scope, stop fixture substitution on the canonical surface, use the established unavailable/empty recovery path, and report the missing contract.

Test at least the live/canonical state, intentional demo/fixture state when authorized, and live-source failure. Assert both visible wording and the absence of canonical actions or operational claims in non-canonical and failed states. Sample pass/fail, verification, timestamps, or health values are examples, never production evidence.

## Security and privacy check

Before exposing any backend-derived detail, ask whether it can reveal:

- resource existence to an unauthorized user;
- another user's identifiers or data;
- fraud, abuse, moderation, or ranking signals;
- infrastructure, provider, or deployment details;
- input useful for enumeration or exploitation.

Use the least revealing message that still supports a legitimate next action.
