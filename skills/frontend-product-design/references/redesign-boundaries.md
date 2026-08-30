# Redesign boundaries

Use this reference after project inspection when the user asks to redesign, refresh, rethink, overhaul, modernize, or materially restyle an existing interface.

## Establish the baseline

Capture the current target surface, its primary/supporting/downstream product objects, included states and viewports, nested shell ancestry, component composition, visual hierarchy, interaction behavior, scoped reference bindings, and protected product capabilities. Use source and rendered evidence when available; either alone can miss important constraints.

## Define a typed redesign contract

~~~ts
type RedesignDepth = "refresh" | "evolve" | "rethink";
type SystemRelationship = "evolve-current-system" | "redefine-within-zone";
type ComponentAuthority =
  | "preserve-and-adjust"
  | "selectively-recompose"
  | "replace-within-zone";

interface RedesignContract {
  targetZone: string[];
  includedStates: string[];
  includedViewports: string[];
  adjacentEffects: string[];
  exclusions: string[];
  depth: RedesignDepth;
  systemRelationship: SystemRelationship;
  componentAuthority: ComponentAuthority;
  visualDirectionPolicy: "required" | "not-required";
  mustPreserve: string[];
  authorizedRemovalsOrReplacements: string[];
}
~~~

When the user names a retained fragment and asks to redo the rest, also write the Visual Direction `redesignBoundary`. It is stricter than `mustPreserve`:

```text
mode: preserve-only
preserveRegions:
  - regionId: primary-sidebar
    sourceRef: <current screenshot/source>
    invariants: [information architecture, labels, persistent position]
replaceRegions:
  - regionId: dashboard-main
    sourceRef: <current screenshot/source>
    mustChange: [macro-layout, information-hierarchy, module-topology, typography-scale, surface-language]
    minimumChangedDimensions: 4
forbiddenCarryover: [equal KPI card grid, repeated donut-card rail, unchanged main-content composition]
```

The preserve list is exhaustive. Do not add top bars, cards, widgets, shell regions, or layout relationships merely because preserving them feels safer. Product data/behavior can remain truthful while its presentation is fully recomposed.

Infer the smallest depth that satisfies the request:

- **refresh**: change tokens, typography, spacing character, icon treatment, or motion without changing the product structure;
- **evolve**: refine hierarchy, layout, grouping, density, composition, or progressive disclosure while preserving the current system as authoritative;
- **rethink**: permit a new hierarchy, composition, interaction pattern, or local information architecture inside the target zone.

Use a numeric intensity only when the user supplies one. Treat it as a boundary, not a quality score; do not invent dimension percentages.

Choose **redefine-within-zone** or **replace-within-zone** only when the request or a confirmed design decision authorizes structural departure. Even then, preserve required capabilities, data contracts, accessibility, localization, recovery, and unrelated architecture.

Distinguish product invariants from visual carryover. “Keep the same values, actions, and permissions” does not mean keep their cards, order, chart form, grouping, or visual weight. Conversely, “keep the sidebar” preserves only its declared semantics/region; it does not preserve the complete surrounding shell.

Also distinguish availability from first-screen density. If the current surface contains more truthful information than one viewport can carry well, select one strategy explicitly:

- `progressive-scroll`: the first viewport holds the highest-priority job and signals; a coherent continuation holds secondary summaries or detail;
- `on-demand`: secondary evidence remains reachable through a truthful existing interaction/state;
- `multi-surface`: use only when confirmed structure authorizes another route/page;
- `single-viewport`: use only when hierarchy remains readable without compression.

Record the chosen bands in `contentDistribution`. Give each visible fact, metric, action, or module one stable `contentId`; assign it once unless intentional repetition is declared in `sharedContentIds`. Do not invent “summary” and “detail” aliases for the same value. Do not invent a second route to solve density, but do use separate top/continuation outputs for one long page when scroll is part of the confirmed surface. Protected content must remain reachable in the implemented product; representative design PNGs need not exhaustively display it, and it need not all be visible above the fold.

In FULL v3, protected capabilities are monotonic within the confirmed lifecycle. A redesign may add detail or capability, but demotion/removal, changed product-object ownership, changed parent shell, broader reference scope, or reduced evidence is a material contract change requiring a fresh receipt plus base/delta/result change-control record. Do not hide the change as a component disposition or visual simplification.

## Set visual-direction policy

Use `visualDirectionPolicy: required` whenever the redesign materially authors or changes visual hierarchy, brand posture, density rhythm, typography/color roles, surface language, motion tone, imagery role, or a signature visual mechanism. This normally includes `evolve` and `rethink`; a bounded `refresh` may use `not-required` only when every relevant visual decision is already specified and no project-specific direction must be selected.

When required, read [visual-direction.md](visual-direction.md), derive `preserveFromProjectDNA` from the evidence-backed baseline, name every intentional departure, and lock the direction contract before creating a visual artifact. Artifact choice and approval do not replace this lock.

## Component disposition

For each materially affected baseline component, record one disposition:

- **KEEP**;
- **ADJUST**;
- **RECOMPOSE**;
- **REMOVE**;
- **REPLACE**.

Attach a product reason to **REMOVE** and **REPLACE**. Visual novelty is not sufficient. Prefer composition or a supported variant when it expresses the selected direction cleanly. Component disposition describes design semantics, not implementation ownership; Project Fit may use mature internal, framework/platform, or library capabilities, and uniqueness never requires a hand-written control.

## Resolve ambiguity proportionally

Ask one combined question only when the target zone, structural authority, or protected behavior cannot be inferred and different answers would materially change the deliverable. Otherwise record the inferred contract and proceed.

Research, artifacts, and implementation must stay inside the contract. If evidence shows that the agreed depth cannot solve the user problem, reopen the contract instead of silently widening it.
