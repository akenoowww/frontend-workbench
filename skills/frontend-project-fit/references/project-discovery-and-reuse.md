# Project discovery and reuse inventory

Use this reference before frontend design or implementation in an existing repository.

## Discover from the affected path outward

Start with the route, component, or behavior named by the user. Trace imports and runtime ownership outward only as far as needed to understand:

- application shell, route and layout nesting;
- component composition and public APIs;
- local, shared, server, and URL state;
- data fetching, caching, mutations, and error adaptation;
- styling, tokens, themes, breakpoints, motion, and icons;
- localization and content generation;
- accessibility helpers and focus behavior;
- tests, stories, fixtures, and mocks.

Prefer repository search and direct source inspection over assumptions based on framework defaults.

## Find internal reference surfaces

Choose one or two surfaces that are closest to the requested work by responsibility and interaction. Good references demonstrate several of these together:

- the same layout role;
- similar input or decision flow;
- the same data ownership and loading model;
- comparable states and recovery behavior;
- the same responsive transformation;
- current rather than deprecated project conventions.

If references conflict, prefer the one used by the current feature area or the most recently adopted shared primitive. Confirm with imports, tests, or project documentation when possible.

## Search beyond names

Search for:

- rendered labels and accessible roles;
- component props and variant names;
- distinctive CSS tokens or utility classes;
- hooks, stores, query keys, and form schemas;
- state names such as loading, empty, editing, pending, and failed;
- import paths from known shared UI modules;
- tests describing the same user behavior.

A project may call a confirmation dialog `DecisionModal`, an entity picker `ResourceCombobox`, or a card `SummaryPanel`. Search by purpose before inventing a generic equivalent.

## Build a minimal evidence record

Capture only what affects the task:

```text
PROJECT FIT
- Architecture path:
- Internal reference surface(s):
- Reusable components/widgets:
- Reusable styles/tokens/icons:
- Reusable state/data/form/error patterns:
- Relevant tests or stories:
- Gaps requiring a new solution:
```

This record supports implementation decisions; it is not a request for a long repository audit.

## Reuse decision test

Reuse directly when the candidate already supports the required semantics and states.

Extend when one responsibility is shared and a small public capability can serve existing and new consumers without unrelated flags.

Compose when several existing primitives together express the new surface without duplicating their behavior.

Create new only when candidates fail on semantics, ownership, accessibility, behavior, or maintainable extension. Record the closest candidate and concrete mismatch.

Do not reject reuse because default styling differs when supported tokens or variants solve the difference. Do not force reuse solely because two elements look similar when their responsibilities differ.
