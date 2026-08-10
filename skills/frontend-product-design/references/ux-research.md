# Atomic UX research and decision records

Use this reference when a design decision needs external evidence, product comparison, alternative evaluation, or a durable rationale.

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
-> DOMAIN OR UX EVIDENCE
-> REAL PRODUCT EXAMPLES
-> SCREENSHOT INSPECTION WHEN USEFUL
-> PATTERN EXTRACTION
-> TRADE-OFF ANALYSIS
-> PROJECT-SPECIFIC DECISION
```

Phrase a behavioral question whose answer can change the interface. Keep appearance subordinate to the user task.

## 2. External evidence

Use web research when current conventions, accessibility guidance, platform behavior, domain practice, or mature real-world examples can improve the decision. Do not browse merely to collect decoration.

Prefer authoritative primary sources for platform rules, design systems, and accessibility requirements. When inspecting products, distinguish direct observation from inference and note when behavior is hidden behind authentication or unavailable states.

Inspect multiple relevant products when useful. Study:

- control placement and visibility;
- entry, exit, dismissal, and back behavior;
- preserved context and persistent state;
- immediate versus confirmed changes;
- selection and progress feedback;
- failure and recovery behavior;
- progressive disclosure;
- desktop and mobile differences.

Do not copy one product directly.

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
- ...

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
- Never hardcode a product domain, layout archetype, or visual style.
- Never select a pattern solely because it is common, modern, or aesthetically impressive.
- Never represent a screenshot as proof of hidden interaction behavior.
- Keep citations or source links close to the decisions they support.
- State uncertainty and time-sensitive observations.
