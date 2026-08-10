# Interaction and state modeling

Use this reference before visual synthesis or implementation planning.

## Contents

1. Interaction model
2. State inventory
3. State relationships
4. Coverage review

## 1. Interaction model

Describe the feature as a behavioral system:

```text
INTERACTION MODEL

Entry point
- ...

Default state
- ...

Primary path
- ...

Secondary paths
- ...

Action results and feedback
- ...

Overlays and dismissal
- ...

Persistence
- ...

Validation, errors, and recovery
- ...

Destructive actions
- ...

Keyboard and focus behavior
- ...

Responsive behavior
- ...
```

Specify what remains visible, what changes immediately, what requires confirmation, where focus moves, how the user exits, and what survives navigation or reload when relevant.

## 2. State inventory

Inventory only visually or behaviorally meaningful states. Consider:

- default, loading, empty, partial-data, and error;
- disabled, hover, focus, selected, and permission-denied;
- editing, validation-error, saving, success, and failure;
- menu-open, overlay-open, drawer-open, dialog-open, and confirmation;
- desktop, narrow, touch, and mobile variants.

Do not create a separate visual artifact for an insignificant difference. Do not omit a state that changes the user's understanding, action, safety, or recovery path.

## 3. State relationships

Model parent and derived states:

```text
FEATURE
|- default
|- loading
|- empty
|- error
|- action-active
|  |- unchanged
|  |- changed
|  `- invalid
|- result
`- responsive variants
```

For each transition, record:

- trigger;
- preconditions;
- visible change;
- system side effect;
- feedback;
- dismissal, undo, or recovery path;
- persisted versus ephemeral state.

Keep business state, UI state, and network state distinct when conflating them would create false feedback or race conditions.

## 4. Coverage review

Before visual synthesis, verify:

- every visible control has a supported outcome;
- every hidden surface has a discoverable trigger;
- destructive and irreversible paths are safe;
- validation explains how to recover;
- loading and failure do not erase necessary context;
- responsive changes preserve task priority;
- keyboard and focus behavior remain coherent;
- no state or system outcome was invented merely to complete a composition.
