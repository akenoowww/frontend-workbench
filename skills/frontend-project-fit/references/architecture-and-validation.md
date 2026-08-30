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

## Implement vertical slices through typed boundaries

Prefer vertical slices that complete one user job through route orchestration, typed data and mutation contracts, explicit loading/empty/failure/recovery states, capability integration, product copy, and focused tests. A slice may compose shared primitives, but it should not place unrelated page families, fixture/live data models, API adaptation, persistence, visual controls, and workflow orchestration into one monolithic component or module.

Use the project's established typed contracts. When a boundary is new, define the smallest discriminated domain state or adapter contract that prevents UI code from guessing source, status, errors, permissions, or capability behavior. Keep library-specific objects behind the feature or shared adapter that owns them rather than leaking them across routes.

Extract shared code only when responsibility and concrete reuse are established. Do not build a homemade component system, graph/editor framework, form engine, overlay stack, or similar custom control layer as a side effect of delivering one screen.

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
| Complex/foundational capability | Implementation-plan requirement/decision, existing owner inventory, at least two credible candidates for a new dependency or project-owned approach, typed integration boundary, and rendered control behavior |
| New primitive | Search evidence, candidate evidenceRef, concrete gap, lifetime rationale, obligations, focused tests, and comparison with closest candidates |
| Vertical slice | Route-to-contract trace, explicit state/error boundary, capability adapter, and focused end-to-end or integration evidence without unrelated monolith growth |
| Visible UI change | Exact rendered path, relevant desktop/mobile viewports, console health, interaction result, and comparison with an approved design when present |
| Working artifacts | All task-owned prompts, screenshots, mockups, traces, and reports remain inside the ignored `.frontend-workbench/` run |

Run project-standard lint, type, build, and focused tests when available, but do not treat them as proof of visual or architectural fit. Reproduce the affected UI path when practical.

Do not inspect `.frontend-workbench/` as product evidence. Before handoff, check task-created paths and the Git working tree. A generated image may leave the runtime workspace only when it has an approved project-native destination and a verified code, build, or test consumer.

## Handoff proof

Report the reused and extended project assets by name. State the selected implementation mechanism and, if something new was necessary, the concrete capability gap it fills and the obligations it introduces. Separate source inspection, automated checks, runtime verification, and production proof.

In a FULL lifecycle, give implementation or QA subagents the helper's compact read-only `handoff`, including implementation-plan identity and the relevant capability requirement/decision, plus their exact route, vertical slice, file owner, or check. Do not duplicate the full contract, skill text, chat transcript, or mutable state; return evidence or a plan delta to the root orchestrator for one authoritative transition or `batch-mark` commit.
