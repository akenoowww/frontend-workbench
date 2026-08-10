# Implementation planning and validation

Use this reference only when the user has authorized implementation.

## Contents

1. Implementation plan
2. Implementation gate
3. Coding rules
4. Validation
5. Handoff

## 1. Implementation plan

Map the approved design onto the existing architecture:

- routes and entry points;
- files to modify;
- existing components to reuse or extend;
- justified new components;
- local, shared, server, and URL state;
- data dependencies and API integration;
- permissions and feature flags;
- loading, partial, empty, error, and recovery behavior;
- responsive and keyboard behavior;
- accessibility semantics;
- tests and runtime verification.

Prefer the smallest architectural change that cleanly supports the feature.

## 2. Implementation gate

Do not edit production UI until the materially relevant items are resolved:

- project design language;
- reusable primitives and internal reference surfaces;
- primary user goal and feature structure;
- important interactions and selected patterns;
- meaningful state coverage;
- visual direction or a recorded reason visualization cannot test the decision;
- technical integration path;
- explicit or clearly implied implementation authority.

Return to the relevant design phase when an unresolved choice would change behavior or architecture. Do not use code as a way to avoid making the design decision.

## 3. Coding rules

### Reuse before invention

Search, inspect, and compose existing components first. Extend an existing primitive when its semantics remain coherent. Add a new primitive only when reuse would create a misleading API or unsupported behavior.

### Match the project

Follow existing conventions for file organization, naming, component APIs, hooks, state, data fetching, styling, tests, error handling, localization, permissions, accessibility, and responsive design.

Do not impose unrelated architecture because it is familiar or fashionable.

### Implement behavior, not screenshots

Reproduce hierarchy, interactions, states, transitions, feedback, recovery, and responsive transformations. Do not pixel-match one static image while omitting system behavior.

Keep unsupported backend behavior out of the UI. Use real contracts and data states rather than mock success paths unless the user explicitly requests a prototype.

## 4. Validation

Run checks in proportion to risk and project conventions.

### Technical

- build and type-check;
- lint affected code;
- run focused and relevant broader tests;
- check imports, runtime errors, and duplicated primitives;
- verify real data and state integration where available.

### Product

- reproduce the primary task;
- exercise secondary and destructive actions;
- verify loading, empty, partial, failure, validation, and recovery states;
- confirm updates, persistence, permissions, and feedback;
- verify that no visual control promises unsupported behavior.

### Visual and responsive

- compare the implementation with project conventions and approved direction;
- inspect important states at representative breakpoints;
- check overflow, focus visibility, content density, and component variants;
- verify overlays, scrolling, dismissal, and touch targets;
- use screenshots or browser inspection when available.

### Accessibility

- verify semantics, names, labels, and reading order;
- test keyboard navigation and focus management;
- check contrast and non-color state communication;
- respect reduced motion and platform conventions where relevant.

## 5. Handoff

Report separately:

- decisions implemented;
- files changed;
- checks run and results;
- runtime or visual flows directly verified;
- unverified assumptions, environment gaps, and pending work.

Do not describe generated images as implemented UI, local checks as production proof, or an untested state as working.
