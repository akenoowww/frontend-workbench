# Frontend feature design report

Use this as a concise working artifact. Keep sections proportional to the task and cite project files or external sources near material claims.

```text
FRONTEND FEATURE DESIGN REPORT

0. Scope and authority
- Requested outcome:
- Design-only / critique / design-and-implementation:
- Known constraints:
- Evidence gaps:

1. User request
- ...

2. Project UI DNA
- ...

3. Relevant internal references
- Surface 1:
- Surface 2:
- Reusable primitives:

4. Redesign contract (only for explicit redesign)
- Target zone, included states, breakpoints, and exclusions:
- Current baseline:
- Overall intensity and dimension profile:
- EVOLVE CURRENT SYSTEM / REDEFINE STRUCTURE:
- PRESERVE AND ADJUST / SELECTIVELY DECOMPOSE / REPLACE AND REIMAGINE:
- Must preserve:
- Authorized removals or replacements:

5. Feature model
- Primary goal:
- Information:
- Actions:
- Inputs and outputs:
- Constraints and edge cases:

6. UX decisions
- D01:
- D02:

7. Research findings
- Internal evidence:
- External evidence:
- Extracted patterns:

8. Decision records
- Selected approaches and trade-offs:

9. Interaction model
- Entry, paths, results, dismissal, persistence, recovery:

10. State model
- Default:
- Meaningful derived states:
- Responsive variants:

11. Visual specification
- Hierarchy, components, affordances, responsive transformation:
- Redesign component dispositions (KEEP / ADJUST / DECOMPOSE / REMOVE / REPLACE):

12. ImageGen state plan
- Master state:
- Derived states:
- Visual-system anchor:
- Skipped with reason, if nonvisual:

13. Implementation plan
- Only when implementation is requested:

IMPLEMENTATION GATE
[ ] Project UI DNA is evidence-backed.
[ ] Redesign zone, intensity, system strategy, and component mode are explicit when applicable.
[ ] The primary user goal and feature model are clear.
[ ] Important UX decisions have selected approaches and rationale.
[ ] Interaction and meaningful states are modeled.
[ ] Required visual states are reviewed, or this is a focused nonvisual decision.
[ ] The technical integration path is understood.
[ ] The user authorized implementation.

Status: NOT READY / READY FOR IMPLEMENTATION / DESIGN-ONLY COMPLETE / DESIGN HANDOFF COMPLETE - VISUALS DEFERRED
```

For a focused track, keep only the scope, relevant project evidence, one decision, affected states, selected option, and validation plan. Never mark the gate ready by filling unknowns with assumptions.
