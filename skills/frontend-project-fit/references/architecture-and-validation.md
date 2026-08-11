# Architecture fit and validation

Use this reference to integrate and verify frontend changes without introducing parallel project systems.

## Respect established boundaries

Determine where the project currently places:

- route-level orchestration;
- reusable presentation components;
- feature-specific components;
- business or domain transformations;
- server and client data access;
- state and cache ownership;
- validation and error mapping;
- localization and formatting;
- telemetry and diagnostics;
- unit, integration, browser, and visual tests.

Put the new responsibility at the matching boundary. Do not move unrelated code or redesign the architecture unless the requested outcome requires it.

## Avoid parallel systems

Before adding a library or abstraction, check for an established project solution, then apply the capability decision in [capability-and-dependency-selection.md](capability-and-dependency-selection.md). Common accidental duplicates include:

- a second component library;
- bespoke CSS beside an existing token or utility system;
- a new fetch client or cache;
- component-local global state;
- a second form or validation framework;
- hand-written overlays beside a dialog primitive;
- raw icons beside the project icon wrapper;
- new error or localization mechanisms;
- local date, number, or currency formatting.

Use the established system unless a documented limitation blocks the requested behavior. A limitation should be concrete and testable, not a stylistic preference. Do not interpret this as a ban on libraries: when no established solution exists, compare native, internal, external, generated, and tool-assisted candidates that are actually plausible for the capability.

## Extend without breaking consumers

When extending a shared primitive:

1. preserve existing defaults;
2. add the smallest semantic API;
3. avoid boolean combinations that encode unrelated features;
4. update types, documentation, tests, and stories where the project uses them;
5. inspect existing call sites for compatibility;
6. verify accessibility and responsive behavior for old and new variants.

If a clean extension would distort the primitive's responsibility, add a feature-level composition or a new narrowly scoped primitive at the correct layer.

## Validation matrix

Select checks based on the change:

| Risk | Evidence |
| --- | --- |
| Component reuse | Existing API and call-site inspection; focused component tests |
| Shared extension | Existing consumer tests plus new behavior coverage |
| Styling | Token/utility inspection and representative rendered states |
| State or data integration | Exact flow with loading, success, empty, failure, and recovery |
| Responsive behavior | Relevant breakpoints and overflow/content-density checks |
| Accessibility | Semantics, accessible names, keyboard, focus, and non-color communication |
| Localization | Affected locales, fallback behavior, variable/plural formatting |
| Capability/tool selection | Project search, material alternatives, lifetime-cost rationale, and implemented edge cases |
| New dependency | Current primary docs/source, manifest and lockfile, runtime/build/type compatibility, defaults, license/provenance, transitive surface, bundle impact where material, and focused tests |
| New primitive | Search evidence, rationale, ownership, tests, and comparison with closest candidates |

Run project-standard lint, type, build, and focused tests when available, but do not treat them as proof of visual or architectural fit. Reproduce the affected UI path when practical.

## Handoff proof

Report the reused and extended project assets by name. State the selected implementation mechanism and, if something new was necessary, the concrete capability gap it fills and the obligations it introduces. Separate source inspection, automated checks, runtime verification, and production proof.
