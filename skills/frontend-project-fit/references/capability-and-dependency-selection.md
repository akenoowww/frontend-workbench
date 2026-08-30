# Capability and dependency selection

Use this reference whenever a frontend implementation requires choosing how a capability should be provided. Apply it to any domain: data access, state, forms, validation, dates, editors, charts, media, accessibility behavior, cryptography, parsing, testing, build tooling, or another capability discovered in the task. Do not reduce it to HTTP clients or a fixed package list.

It is mandatory for complex/foundational UI such as graphs, editors, forms and validation, charts, overlays and focus management, drag and drop, virtualized tables or trees, scheduling, rich media, or another control with substantial interaction, accessibility, data, or lifecycle behavior.

## Start from the capability

Describe the needed behavior in technology-neutral terms. Capture only constraints that can change the decision:

- required behavior, states, edge cases, and failure recovery;
- browser, server, edge, mobile-web, rendering, and build environments;
- project architecture, package manager, framework, language, and support matrix;
- security, privacy, accessibility, compliance, and data sensitivity;
- performance, bundle, offline, observability, and testing requirements;
- realistic frequency and reuse across current or planned work.

Do not begin with “use package X” or “write this from scratch” unless the user or project has already made that an explicit constraint.

For FULL, consume the v3 implementation plan. Each `capabilityRequirement` supplies `capability`, `complexity`, and `constraints`; verify those fields against the requested behavior and current repository before accepting its decision.

## Preserve the project before expanding it

Search the affected path, dependency manifests and lockfiles, workspace packages, shared utilities, framework configuration, generated code, and internal documentation. Search by behavior as well as package name. Inventory the existing project component/system/library owner first, including its adapters, tests, and supported variants. A second implementation of an already-owned capability is a migration decision, not a feature shortcut.

If a compatible project solution exists, reuse its public API or extend it coherently. A new library must not silently create a second client, cache, store, form model, validation system, component system, or equivalent architectural owner.

When the established solution has a concrete safety, compatibility, maintenance, or capability gap, document it. Prefer a compatible local fix. If resolution requires replacing the project-wide approach, separate that migration from the feature and obtain the required authority. When no existing owner fits, inspect the platform/framework and credible mature libraries before selecting a project-owned primitive.

## Generate candidates dynamically

Generate only credible candidates from the actual stack and capability. Candidate types can include:

- reuse or extension of an existing project solution;
- a platform or language primitive;
- a framework-native facility;
- a small project-owned abstraction;
- a mature external dependency;
- an official SDK or generated client;
- a compiler, build-time transform, or specialized tool.

These are prompts for discovery, not mandatory alternatives. Add or remove categories as the task requires. Do not compare a library against a fake “pure code” option when the project already has the capability, and do not shortlist packages that are incompatible with the runtime merely to make the decision look broad.

Use exactly one implementation-plan `selectedApproach`: `reuse`, `extend`, `compose`, `platform`, `framework`, `external-dependency`, or `project-owned`. `selectedCandidate` identifies the concrete owner; the enum alone is not a decision. Set a proportional `decisionTier`:

- `direct` — bounded capability with one obvious project/platform owner;
- `known-fit` — complex non-project-owned capability with one exact, current, evidence-backed owner already known to satisfy the material constraints;
- `comparative` — foundational work, every complex project-owned primitive, or an uncertain/new complex dependency that needs alternatives.

`known-fit` is intentionally not a fake bake-off: a graph request with current evidence that React Flow fits selection, zoom, pan, accessibility, and the actual stack may select it directly. `comparative` records at least two credible candidates, each backed by `evidenceRef`. A credible candidate must plausibly meet the runtime and material constraints; padding the list with incompatible or abandoned options fails the gate.

When current package behavior, maintenance, license, compatibility, or security affects the choice, inspect current primary documentation, source, release history, and advisories rather than relying on memory or popularity.

Separate capability choice from installation authority. First inspect manifests, lockfiles, workspace packages, and installed modules. If the selected owner is absent and dependency installation or registry access is unavailable, stop with the decision intact and report `BLOCKED`; do not downgrade to hand-written SVG/canvas/custom controls to keep moving.

## Compare lifetime cost and risk

Select only the criteria material to the capability:

- correctness and coverage of difficult edge cases;
- reduction of repeated manual work and future change surface;
- security, privacy, accessibility, and safe defaults;
- fit with the project's runtime, architecture, types, testing, and observability;
- bundle size, startup, rendering, network, and resource impact;
- maturity, maintenance activity, API stability, and ecosystem fit;
- license, provenance, transitive dependencies, and supply-chain exposure;
- escape hatches, lock-in, replaceability, and migration cost;
- team comprehension and the burden of operating or debugging the solution.

Prefer the smallest *justified* solution over the shortest code or fewest packages.

A dependency is often justified when it reliably handles a standardized or complex concern, dangerous edge cases, repeated behavior, interoperability, or ongoing maintenance that the project would otherwise own. A native or small project-owned solution is often justified when the behavior is bounded, easy to test, stable, and cheaper than adopting and operating another dependency.

Neither outcome is a default. Libraries can reduce risk and labor, but their defaults, lifecycle, and transitive surface still require review. Hand-written code can be appropriate, but choosing it transfers correctness, testing, maintenance, and incident ownership to the project.

## Gate project-owned primitives

Do not select or implement a complex/foundational `project-owned` primitive unless the decision records all of the following:

- `candidates` and `evidenceRef`, including the existing project owner or closest internal primitive, platform/framework facilities, and credible mature libraries where applicable;
- `selectedCandidate` and a concrete `gap` explaining why reuse, extension, composition, platform/framework support, and mature candidates do not satisfy the requirement;
- `lifetimeRationale` covering why project ownership minimizes ongoing cost and risk rather than merely initial code or package count;
- `obligations` assigning the relevant accessibility, security, compatibility, performance, maintenance, documentation, migration, and incident responsibilities;
- `validation` naming focused automated coverage and rendered interaction checks for the difficult behavior.

If evidence cannot be obtained in the current environment, leave the decision blocked or return a plan delta. Do not turn uncertainty about libraries into permission to create a custom control.

Do not build abstractions for hypothetical reuse. Count reuse that is already present or reasonably expected from concrete roadmap evidence.

## Record a compact decision

Use this artifact when the choice is material; keep it proportional for small work:

```text
CAPABILITY DECISION
- Capability:
- Complexity and constraints:
- Existing project solution:
- Material constraints:
- Candidates and evidenceRef:
- SelectedApproach: reuse | extend | compose | platform | framework | external-dependency | project-owned
- DecisionTier: direct | known-fit | comparative
- SelectedCandidate:
- Gap:
- LifetimeRationale:
- Obligations:
- Validation:
```

For a trivial choice, one sentence may be enough. For FULL, preserve these fields in the implementation plan and consume them from the compact handoff. For a new foundational dependency or deviation from project practice, also preserve any project-native decision record the repository requires.
