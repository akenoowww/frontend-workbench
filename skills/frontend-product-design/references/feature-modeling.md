# Feature modeling and UX decomposition

Use this reference after project archaeology and before research or visual design.

## Contents

1. Feature model
2. UX decision decomposition
3. Usage optimization
4. Complexity calibration

## 1. Feature model

Model the requested feature as a user and product system rather than a component inventory.

```text
FEATURE MODEL

Primary user goal
- ...

Secondary user goals
- ...

Primary information
- ...

Primary actions
- ...

Secondary actions
- ...

Inputs
- ...

Outputs
- ...

Dependencies
- ...

Constraints
- ...

Potential edge cases
- ...
```

Also identify:

- frequent versus rare actions;
- reversible versus destructive actions;
- information that must remain visible during interaction;
- state or context that must persist;
- system input requirements and output guarantees;
- permissions, latency, incomplete data, and failure constraints.

Do not assume product logic solely from the feature name. Mark unsupported facts as unresolved rather than inventing them.

## 2. UX decision decomposition

Create an atomic list such as:

```text
UX DECISIONS

D01 - How should ...?
D02 - When should ...?
D03 - What remains visible while ...?
```

A decision belongs in the list only when its answer materially changes behavior, hierarchy, state, safety, or responsive transformation.

Possible decision families include information hierarchy, navigation, search, filtering, sorting, selection, editing, creation, deletion, confirmation, drill-down, progressive disclosure, modes, comparison, bulk actions, pagination, detail inspection, onboarding, validation, error recovery, saving, preview, upload, export, permissions, collaboration, notifications, and mobile behavior. Treat these as prompts, never mandatory features.

Split unrelated decisions. Avoid one question such as "What is the best design for this page?"

## 3. Usage optimization

For each meaningful decision, test whether the interaction can become easier, faster, clearer, or safer for the actual user.

Evaluate:

- interaction count and action frequency;
- discoverability and cognitive load;
- visual clutter and loss of context;
- accidental activation and reversibility;
- keyboard, touch, and mobile use;
- state persistence;
- progressive disclosure of advanced behavior;
- clarity of what changed;
- feedback, error prevention, and recovery;
- accessibility of the proposed interaction.

Prefer the simplest interaction that satisfies the real use case and project constraints. Do not add sophistication for its own sake.

## 4. Complexity calibration

Use the full model for new or substantially redesigned surfaces and flows. For one focused design question, retain only the relevant goals, constraints, decision, affected states, and evidence.

Do not omit a material edge case to keep the artifact short. Do not pad a simple decision with irrelevant categories.
