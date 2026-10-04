# Atomic UX research and decision records

Use this reference for every Product Design recommendation, critique, or direction, including MICRO, and for standalone frontend UI direction in Art-Direct ImageGen. Research scope follows the decision; lighter profiles do not waive current implemented-product evidence.

## Contents

1. Atomic research loop
2. External evidence
3. Pattern extraction
4. Alternative evaluation
5. Decision record
6. Cross-decision synthesis
7. Research guardrails

## 1. Atomic research loop

Research each important decision separately:

```text
QUESTION
-> PROJECT CONSTRAINTS
-> FRESH WEB SEARCH FOR COMPARABLE WORKING PRODUCTS
-> OPERATING-STATUS AND FRESHNESS CHECK
-> ACTUAL UI OR CURRENT OFFICIAL UI EVIDENCE INSPECTION
-> RELEVANT CURRENT PLATFORM AND ACCESSIBILITY REQUIREMENTS
-> PATTERN EXTRACTION
-> TRADE-OFF ANALYSIS
-> PROJECT-SPECIFIC DECISION
```

Phrase a behavioral question whose answer can change the interface. Keep appearance subordinate to the user task.

## 2. External evidence

Always search the web before settling a design recommendation. Use Google when an available search tool supports it; otherwise use the available web search. Search by the actual user job, product category, and interface pattern, then refine by candidate product and relevant screen. Do not stop at the first result, a remembered brand shortlist, or a query for fashionable design standards. Date filters can aid discovery but do not establish freshness.

Compare at least two relevant operating products when available. Prefer established products with evidence of real use in the relevant category: current customer deployments, maintained public applications, or credible recent adoption evidence. Popularity must not override functional fit; do not fabricate rankings or usage figures. If fewer qualify after a reasonable targeted search, record the rejected candidates and exact gap, and bound the recommendation instead of substituting unrelated famous products.

### Qualify each product and source

Check both independently:

- **Operating status:** open the current official product/application/demo and corroborate active availability through current help, supported versions, a maintained repository for an open-source product, or recent releases. A reachable marketing domain, copyright year, or HTTP 200 does not prove the product works. Record whether an actual interface was accessible, officially documented, or hidden behind authentication; documented availability is not a successful hands-on run.
- **Interface freshness:** inspect the relevant current live screen, or official UI screenshots, interactive demos, or help/video material tied to the current product. Record source publication/update/capture date separately from today's access date. Prefer corroborating release/support/UI evidence from the past 12 months, but do not reject a still-supported stable interface merely for its age. An older or undated screenshot/article is usable as a current pattern only when a live observation or current official evidence confirms that same relevant implementation. A new blog date, active product, or current release alone does not make an old screenshot current.

Discontinued services, obsolete product versions, archives, unverified galleries, concept mockups, and old first search results cannot be the sole basis of a current design decision. A ten-year-old article may explain history; it must never silently establish today's implementation. A marketing homepage proves only the interface actually shown there, not hidden application screens or flows.

Open and inspect evidence beyond search snippets. For a visual decision, actually view the relevant screen/demo/screenshot; text-only help can establish documented behavior, but cannot establish typography, visual density, or layout. For an interaction decision, inspect the available flow or current official description of the relevant state and distinguish it from behavior inferred from pixels. If the product requires unavailable authentication, use eligible official material or another comparable product; never invent unseen states or bypass access controls.

Prefer current authoritative primary sources for accessibility requirements and platform rules that constrain the observed patterns. These supplement product inspection; a design-system component page, generic best-practice article, or trends list does not substitute for a working comparable application's implementation.

### Inspect the actual decision

Study the surfaces and states relevant to the user job:

- information hierarchy, visual density, typography roles, and responsive allocation;
- control placement and visibility;
- entry, exit, dismissal, and back behavior;
- preserved context and persistent state;
- immediate versus confirmed changes;
- selection and progress feedback;
- failure and recovery behavior;
- progressive disclosure;
- desktop and mobile differences.

Do not copy one product directly.

For each accepted example keep a compact evidence record:

```text
Product and functional fit / evidence of established use
Research date
Current operating-status source and observed/documented access
Exact inspected surface, viewport, state or flow
UI source URL and publication/update/capture date, or undated
Why this exact implementation is current
Direct visual/interaction observation versus documented fact or inference
Supported pattern and limitations
Decision: adopt / adapt / reject, with project-specific reason
```

Keep the compact evidence in the task's working context for MICRO/read-only work and in an already-authorized decision/handoff artifact for durable workflows. This does not require a source-by-source user-facing report; provide concise attribution when requested or needed for factual support. Do not create extra project files or expose research/status metadata in product copy. Reuse this record within a task while its scope and relevant version remain current; refresh when later evidence conflicts, a surface changes, or freshness is no longer supported.

If necessary evidence is inaccessible, change sources or candidates. If the gap remains, identify the exact affected decision as provisional/blocked. Do not silently fall back to memory or call an unsupported recommendation current and researched.

## 3. Pattern extraction

Convert examples into a reusable interaction principle:

```text
Observed approaches
- Product A: ...
- Product B: ...
- Product C: ...

Shared pattern
- ...

Advantages
- ...

Disadvantages
- ...

Works when
- ...

Fails when
- ...

Fit for this project
- ...
```

Avoid reasoning that a project should use a modal, drawer, tab, or other pattern merely because a mature product does.

## 4. Alternative evaluation

Compare viable alternatives for decisions with meaningful trade-offs:

```text
OPTION A
Advantages
- ...
Disadvantages
- ...

OPTION B
Advantages
- ...
Disadvantages
- ...

SELECTED
- ...

WHY
- ...
```

Evaluate fit against task frequency, complexity, screen context, project conventions, accessibility, responsive behavior, persistence, reversibility, and implementation cost. Do not invent a third option when only two are credible.

## 5. Decision record

Record important decisions concisely:

```text
DECISION: <name>

User need
- ...

Project evidence
- ...

External evidence
- linked product observations, research date, source dates and current-status checks

Considered options
- ...

Selected approach
- ...

Why
- ...

Rejected alternatives
- ...

Consequences and trade-offs
- ...
```

Update the record explicitly when new evidence changes the decision.

## 6. Cross-decision synthesis

Before visual design, check for:

- controls competing for the same area;
- excessive overlays or modes;
- duplicated actions or terminology;
- inconsistent navigation or feedback;
- conflicting persistence and state models;
- incompatible desktop and mobile behavior;
- a flow that is more complex than the user goal.

Resolve conflicts into one coherent experience. Do not combine every isolated best practice.

## 7. Research guardrails

- Prioritize explicit user and functional requirements over research examples.
- Prefer project conventions and reusable components over fashionable external patterns.
- Require fresh comparison for the decision, not an external redesign of unrelated surfaces.
- Permit a familiar implemented pattern when current evidence and project fit support it; novelty is not a quality gate.
- Never hardcode a product domain, layout archetype, or visual style.
- Never select a pattern solely because it is common, modern, or aesthetically impressive.
- Never represent a screenshot as proof of hidden interaction behavior.
- Keep citations or source links close to the decisions they support.
- Keep ordinary user-facing answers focused on your recommendation and concrete reasons; avoid a search/process report, unsolicited comparator names, or plugin internals. Do not add “Product X does this” claims merely to legitimize an opinion. Retain a traceable evidence record and provide named examples and relevant sources when requested or when a specific external fact is necessary, with accurate attribution.
- Argue against material usability failures with consequences and alternatives, not condescension or product-count appeals. Revise for new evidence, and distinguish personal taste from supported constraints.
- State uncertainty and time-sensitive observations.
- Do not declare research complete when only product names, snippets, generic standards, or unverified old UI were collected.
