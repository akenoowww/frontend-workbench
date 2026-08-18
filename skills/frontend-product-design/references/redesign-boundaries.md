# Redesign boundaries

Use this reference after project inspection when the user asks to redesign, refresh, rethink, overhaul, modernize, or materially restyle an existing interface.

## Establish the baseline

Capture the current target surface, included states and viewports, shared shell, component composition, visual hierarchy, interaction behavior, and protected product capabilities. Use source and rendered evidence when available; either alone can miss important constraints.

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
  mustPreserve: string[];
  authorizedRemovalsOrReplacements: string[];
}
~~~

Infer the smallest depth that satisfies the request:

- **refresh**: change tokens, typography, spacing character, icon treatment, or motion without changing the product structure;
- **evolve**: refine hierarchy, layout, grouping, density, composition, or progressive disclosure while preserving the current system as authoritative;
- **rethink**: permit a new hierarchy, composition, interaction pattern, or local information architecture inside the target zone.

Use a numeric intensity only when the user supplies one. Treat it as a boundary, not a quality score; do not invent dimension percentages.

Choose **redefine-within-zone** or **replace-within-zone** only when the request or a confirmed design decision authorizes structural departure. Even then, preserve required capabilities, data contracts, accessibility, localization, recovery, and unrelated architecture.

## Component disposition

For each materially affected baseline component, record one disposition:

- **KEEP**;
- **ADJUST**;
- **RECOMPOSE**;
- **REMOVE**;
- **REPLACE**.

Attach a product reason to **REMOVE** and **REPLACE**. Visual novelty is not sufficient. Prefer composition or a supported variant when it expresses the selected direction cleanly.

## Resolve ambiguity proportionally

Ask one combined question only when the target zone, structural authority, or protected behavior cannot be inferred and different answers would materially change the deliverable. Otherwise record the inferred contract and proceed.

Research, artifacts, and implementation must stay inside the contract. If evidence shows that the agreed depth cannot solve the user problem, reopen the contract instead of silently widening it.
