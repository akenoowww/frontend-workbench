# Capability and dependency selection

Use this reference whenever a frontend implementation requires choosing how a capability should be provided. Apply it to any domain: data access, state, forms, validation, dates, editors, charts, media, accessibility behavior, cryptography, parsing, testing, build tooling, or another capability discovered in the task. Do not reduce it to HTTP clients or a fixed package list.

## Start from the capability

Describe the needed behavior in technology-neutral terms. Capture only constraints that can change the decision:

- required behavior, states, edge cases, and failure recovery;
- browser, server, edge, mobile-web, rendering, and build environments;
- project architecture, package manager, framework, language, and support matrix;
- security, privacy, accessibility, compliance, and data sensitivity;
- performance, bundle, offline, observability, and testing requirements;
- realistic frequency and reuse across current or planned work.

Do not begin with “use package X” or “write this from scratch” unless the user or project has already made that an explicit constraint.

## Preserve the project before expanding it

Search the affected path, dependency manifests and lockfiles, workspace packages, shared utilities, framework configuration, generated code, and internal documentation. Search by behavior as well as package name.

If a compatible project solution exists, reuse its public API or extend it coherently. A new library must not silently create a second client, cache, store, form model, validation system, component system, or equivalent architectural owner.

When the established solution has a concrete safety, compatibility, maintenance, or capability gap, document it. Prefer a compatible local fix. If resolution requires replacing the project-wide approach, separate that migration from the feature and obtain the required authority.

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

When current package behavior, maintenance, license, compatibility, or security affects the choice, inspect current primary documentation, source, release history, and advisories rather than relying on memory or popularity.

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

Do not build abstractions for hypothetical reuse. Count reuse that is already present or reasonably expected from concrete roadmap evidence.

## Record a compact decision

Use this artifact when the choice is material; keep it proportional for small work:

```text
CAPABILITY DECISION
- Capability:
- Existing project solution:
- Material constraints:
- Dynamically generated candidates:
- Selected approach:
- Why it minimizes lifetime cost and risk:
- New obligations or trade-offs:
- Validation:
```

For a trivial choice, one sentence may be enough. For a new foundational dependency or deviation from project practice, preserve the evidence in the task handoff or the project's normal decision record.
