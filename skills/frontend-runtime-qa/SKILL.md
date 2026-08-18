---
name: frontend-runtime-qa
description: "Use for rendered frontend testing or debugging: page identity, console health, interactions, responsive layout, accessibility, and accepted-design fidelity. Use after visible implementation or for explicit UI QA. Do not use for design planning, source-only review, backend-only tests, implementation, or image generation."
---

# Frontend Runtime QA

Verify the actual rendered experience and return evidence that another workflow can trust. A passing build or source inspection is not rendered proof.

## Scope and authority

- For QA-only, review, or diagnosis requests, do not edit production source.
- When the user also authorized a fix, produce a precise finding handoff for `frontend-project-fit`; rerun the same QA flow after the fix instead of silently editing under this skill. Allow at most two fix-and-recheck cycles for the same finding before marking it blocked with the repeated evidence.
- Do not install browsers or dependencies unless the current task authorizes dependency changes.
- Do not claim production proof from a local server or mock data.
- Preserve the exact requested host, route, data boundary, viewport, and user flow.

This skill owns runtime evidence, failure reproduction, responsive and interaction checks, and design-fidelity comparison. It does not own product design, implementation architecture, ImageGen, or backend changes.

## Select the verification path

Prefer the strongest already-available path:

1. an installed in-app Browser or Computer Use capability with the required session;
2. the project's existing e2e, component-browser, or visual-regression workflow;
3. an already-installed Playwright or equivalent browser runner;
4. source and automated checks only when no rendered path is available, reported explicitly as a limitation.

Read [references/runtime-checks.md](references/runtime-checks.md) before browser interaction or a rendered-fidelity claim.

## Workflow

### 1. Define the target flow

State one exact path:

```text
entry route -> user action or state -> expected rendered result
```

For a smoke test, use: app loads -> first meaningful screen renders -> primary visible controls respond without relevant runtime errors.

Identify the accepted design output or frozen handoff when fidelity is part of the request. If no reference exists, verify coherence and project fit without inventing pixel-perfect requirements.

### 2. Keep QA artifacts isolated

For an artifact-producing implementation task, require the exact root `.gitignore` entry `/.frontend-workbench/`, verify it with `git check-ignore`, and use the bundled runtime helper when available. Store task-owned screenshots, DOM snapshots, traces, logs, and comparison notes inside `.frontend-workbench/sessions/<session-id>/qa/`. Do not create `screenshots/`, reports, or PNG files in the repository root, `docs/`, source, or public asset directories.

For read-only QA, do not modify `.gitignore` or create a persistent project workspace. Keep concise evidence in the conversation and use an allowed task-scoped temporary directory only when a screenshot or trace is necessary. If the user explicitly requests durable QA evidence and the ignored workspace already exists, it may be reused without changing source or repository metadata.

### 3. Establish the environment

Confirm the page URL, title, viewport, data or mock boundary, browser path, and relevant build. Reuse an existing server when safe. Start a project server only through its documented command and do not change the host or port contract silently.

Record relevant pre-existing console or network failures separately from failures caused by the current change.

### 4. Exercise the flow

Collect the cheapest evidence that proves each transition:

- URL, title, and meaningful DOM or accessibility state;
- visible control and resulting state change;
- focused element, overlay, toast, selection, navigation, or persisted state;
- relevant console and network errors;
- screenshot for visual claims.

Test the requested interaction rather than only loading the page. For visible work, verify the first viewport plus one materially different responsive viewport when practical. Cover additional states only when they change understanding, action, safety, recovery, or the accepted design contract.

### 5. Compare behavior and design

Check functional truth first: required content, controls, states, and recovery must exist and behave correctly. Then compare hierarchy, density, spacing character, typography, component language, navigation, responsive transformation, and accepted visual invariants.

Maintain a short mismatch record with: reference, observed evidence, severity, likely ownership, and whether the mismatch is a defect or an intentional project-compatible adaptation. Do not call ImageGen bitmap text or unsupported details authoritative over product requirements.

### 6. Report or hand off a fix

For each material failure, provide:

- exact route, viewport, and reproduction steps;
- expected and observed result;
- screenshot, DOM, console, or network evidence;
- likely source boundary without claiming an unproven cause;
- whether the current user request authorizes a fix.

When a fix is authorized, hand the finding to `frontend-project-fit`, then repeat this same target flow after implementation. Reuse one stable finding ID and count the recheck. After two failed fix-and-recheck cycles, stop with `BLOCKED` rather than looping. Keep QA evidence independent from the implementation rationale.

## Completion contract

Finish only when:

- page identity and meaningful rendering are confirmed;
- the target interaction and resulting state were exercised;
- relevant console and network health were checked;
- required responsive, accessibility, and design-fidelity claims have evidence;
- screenshots and traces stayed inside the hidden workspace or task-scoped temporary storage;
- local, mock, staging, and production proof are labeled accurately;
- failures, untested states, and remaining uncertainty are explicit.

If the user explicitly requested browser or rendered verification and no rendered path is available, completion is `BLOCKED`; source inspection or a build cannot substitute for that proof.
