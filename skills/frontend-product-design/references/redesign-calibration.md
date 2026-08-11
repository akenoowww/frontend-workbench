# Redesign calibration

Use this reference after project archaeology whenever the user explicitly asks to redesign, refresh, rethink, overhaul, modernize, or substantially restyle an existing interface.

## Contents

1. Establish the baseline
2. Define the redesign zone
3. Calibrate intensity
4. Select the system strategy
5. Select the component-change mode
6. Resolve ambiguity
7. Produce the redesign contract
8. Keep later work inside the contract

## 1. Establish the baseline

Do not redesign from the prompt alone when project evidence exists. Capture the current state of the requested surface and the systems that shape it:

- route, layout, component ownership, data and state path;
- current page or flow hierarchy and meaningful states;
- shared component library, widgets, variants, composition APIs, and icons;
- style system, theme, tokens, typography, spacing, color, radius, elevation, motion, and breakpoints;
- navigation, forms, feedback, overlays, accessibility, localization, and testing conventions;
- reusable project surfaces with similar responsibility or interaction;
- functional requirements, data contracts, permissions, and user actions that cannot disappear accidentally.

Use `PROJECT UI DNA` as the baseline. For visual evidence, inspect the actual rendered surface or supplied screenshots when available. Source alone may not reveal density, overflow, responsive behavior, or state transitions.

## 2. Define the redesign zone

Name exactly what can change. Use the narrowest accurate zone:

- one element or control;
- one reusable component or widget;
- a section within a page;
- one page or route;
- a multi-step flow;
- application shell, navigation, or information architecture;
- the whole frontend or design system.

Record included states and breakpoints, not just the default desktop view. Also record adjacent surfaces that may be affected and explicit exclusions.

If the prompt, open project, selected files, screenshot, or current browser state does not identify the target, stop and ask one concise question such as:

> Что именно входит в зону редизайна: этот блок, вся страница, связанный flow или общая структура приложения?

Do not research or visualize an undefined target.

## 3. Calibrate intensity

Use an overall 0–100% intensity as a permission boundary. It describes how far the solution may depart from the baseline, not how good or complete it is.

Always pair the overall number with a dimension profile because equal percentages can mean different changes:

- tokens and visual language;
- layout and hierarchy;
- component composition;
- interaction behavior;
- information architecture and navigation;
- content and state coverage.

Use these default bands:

| Overall intensity | Default interpretation | Allowed departure |
| --- | --- | --- |
| 0–20% | Token or style refresh | Preserve structure and logical components; adjust color, type, spacing, radius, elevation, icon treatment, and motion within the requested zone |
| 21–45% | Layout refinement | Preserve required logical components and actions; reposition, resize, regroup, reorder, and change emphasis or density |
| 46–70% | Selective recomposition | Merge, compact, progressively disclose, or remove nonessential component subparts while preserving required information, actions, states, and recoverability |
| 71–100% | Full rethinking | Replace hierarchy, component composition, interaction pattern, or local IA inside the zone while preserving required product capabilities, contracts, accessibility, and explicit constraints |

Do not average the dimension profile mechanically. A redesign can be 35% overall with 90% token change and 10% structural change. State the profile explicitly.

If the user supplies a percentage, treat it as authoritative unless it conflicts with a stated requirement. If no percentage is supplied, infer a provisional band from wording and evidence:

- “refresh colors/tokens” usually indicates 0–20%;
- “improve hierarchy, move and resize” usually indicates 21–45%;
- “make it more compact and remove secondary parts” usually indicates 46–70%;
- “rethink completely” usually indicates 71–100%.

State the inference. Ask only when two plausible bands would produce materially different work.

## 4. Select the system strategy

Choose exactly one strategy:

### `EVOLVE CURRENT SYSTEM`

Keep the existing design language authoritative. Reuse current components, widgets, variants, tokens, styles, interaction conventions, and responsive patterns. Extend them only where the redesign requires a coherent new capability.

Use this by default when the user has not explicitly authorized a structural or design-system reset.

### `REDEFINE STRUCTURE`

Allow a new hierarchy, composition, navigation model, or visual direction inside the redesign zone. This still begins with project archaeology and preserves applicable code architecture, product contracts, accessibility, and compatible foundational primitives.

Do not interpret this strategy as permission to replace the entire application, design system, or frontend architecture when only one page or section is in scope.

## 5. Select the component-change mode

Choose the highest permitted mode. Lower modes remain allowed.

### `PRESERVE AND ADJUST`

Keep all logical components and their required behavior. Change placement, size, spacing, grouping, emphasis, variants, tokens, and responsive arrangement.

### `SELECTIVELY DECOMPOSE`

Allow a component to use only the subparts required for this context. Merge, compact, hide behind progressive disclosure, or remove nonessential subparts. Verify that no required action, information, state, accessibility name, or recovery path disappears.

Prefer composition or a supported variant. Do not fork a shared component merely to remove one subpart.

### `REPLACE AND REIMAGINE`

Allow an existing component or structure to be removed and replaced inside the redesign zone. Record why direct reuse, composition, or coherent extension cannot express the selected direction. Reuse lower-level project primitives and foundations wherever they remain compatible.

For every relevant baseline component, record one disposition:

- `KEEP`;
- `ADJUST`;
- `DECOMPOSE`;
- `REMOVE`;
- `REPLACE`.

Attach a user or product reason to `REMOVE` and `REPLACE`; visual novelty alone is insufficient.

## 6. Resolve ambiguity

Ask one combined, concise question only when missing information materially changes the outcome. Prefer:

> Что именно редизайним и насколько глубоко: около 30% с сохранением структуры, 60% с выборочным упрощением компонентов или 90% с полной перестройкой этой зоны?

Do not ask when the user already named the zone and intent clearly or when project evidence makes a safe, reversible inference possible. Record inferred values as provisional.

## 7. Produce the redesign contract

Use this compact artifact:

```text
REDESIGN CONTRACT

Target zone
- ...

Included states and breakpoints
- ...

Adjacent effects and exclusions
- ...

Current baseline
- ...

Overall intensity
- ...%

Dimension profile
- Tokens/visual language: ...%
- Layout/hierarchy: ...%
- Component composition: ...%
- Interaction behavior: ...%
- IA/navigation: ...%
- Content/state coverage: ...%

System strategy
- EVOLVE CURRENT SYSTEM / REDEFINE STRUCTURE

Component-change mode
- PRESERVE AND ADJUST / SELECTIVELY DECOMPOSE / REPLACE AND REIMAGINE

Must preserve
- Required capabilities, data, states, accessibility, constraints:

Authorized removals or replacements
- ...

Implementation authority
- Design-only / design-and-implementation:
```

Keep the artifact proportional. A token refresh needs a short contract; a whole-product rethink needs explicit boundaries and state coverage.

## 8. Keep later work inside the contract

After calibration:

1. model the user problem and atomic UX decisions;
2. research only patterns that can inform those decisions;
3. compare external evidence against the baseline and permitted intensity;
4. synthesize interaction and state models;
5. create visuals that show the approved component dispositions;
6. reject outputs that exceed the zone or silently change protected behavior;
7. implement only when authorized and apply `$frontend-project-fit` plus `$frontend-copy-guard` when relevant;
8. report achieved intensity and any deliberate deviation from the contract.

External examples are evidence, not permission to widen scope. If research reveals that the agreed band cannot solve the user problem, return to the contract and ask for a scope or intensity change before proceeding.
