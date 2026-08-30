---
name: frontend-runtime-qa
description: "Test or debug rendered frontend flows, responsive layout, accessibility, console health, or design fidelity. Not for source-only review or implementation."
---

# Frontend Runtime QA

Verify the rendered experience with evidence another workflow can trust. A build or source inspection is not rendered proof.

## Choose the workflow profile

- **MICRO** — one route/state/viewport diagnosis or post-fix smoke check. Keep it read-only, exercise the target behavior, and report concise evidence without creating persistent project state.
- **STANDARD** — a scoped flow requiring interaction, responsive, accessibility, console/network, or fix-and-recheck evidence.
- **FULL** — multi-route/state coverage or implementation against accepted design artifacts. Consume the active runtime contract and implementation plan, then produce SHA-bound fidelity receipts before completion.

Escalate for observed scope, not merely because a frontend file changed. Preserve an existing contract's workflowProfile.

## Scope and authority

- QA-only, review, and diagnosis requests do not authorize production-source edits.
- If the user authorized a fix, hand the finding to frontend-project-fit and rerun the same flow after implementation. After two failed fix-and-recheck cycles for one stable finding, mark it blocked.
- Do not install browsers or dependencies unless authorized.
- Preserve the requested host, route, data boundary, viewport, and flow.
- Do not claim production proof from a local server or mock data.

This skill owns runtime reproduction, responsive/interaction checks, evidence, and design-fidelity comparison. It does not own design, implementation, ImageGen, or backend changes.

## Select the verification path

Prefer the strongest already-available path:

1. an installed browser/computer-use capability with the required session;
2. the project's e2e, component-browser, or visual-regression workflow;
3. an already-installed browser runner;
4. source/automated evidence only when rendered access is unavailable, labeled as a limitation.

When `agent-browser` is already installed, use it as the canonical generic adapter. Open the exact target URL directly; never discover the target through Google or another search engine. Do not install `agent-browser`, Chromium, Playwright, or project packages inside the tested repository during QA unless the user explicitly authorized that environment change.

The canonical helper may need the host's local-browser/socket permission when Codex runs inside a restricted sandbox. If the first exact command fails with a socket-directory or local-bind permission error, rerun that same `run-runtime-qa` command through the host approval path once. Do not switch adapters, install another browser, or downgrade to source/screenshot evidence.

Read [references/runtime-checks.md](references/runtime-checks.md) for STANDARD/FULL, or before a MICRO accessibility, responsive, or fidelity claim.

For FULL, also read [the lifecycle contract](../frontend-product-design/references/full-lifecycle.md) for quality-gate meanings, evidence identity, and final gallery acceptance. Consume the validated v3 implementation plan from the compact handoff; a missing or mismatched plan blocks plan-bound runtime claims.

## Verify the flow

### Define one target

State the exact entry route, action/state, expected result, viewport, and data boundary. Name the implementation-plan vertical slice and capability owner when the target uses a complex/foundational control. For smoke testing: meaningful screen renders, primary visible controls respond, and no relevant runtime error occurs.

When fidelity is in scope, identify the locked visual-direction reference/SHA, accepted design artifact/SHA, implementation-plan identity, and frozen handoff. If no accepted artifact exists, verify coherence and project fit without inventing pixel requirements. If direction is required but its lock is missing or stale, block the fidelity claim.

### Establish and exercise

Confirm URL, title, viewport, relevant build, data/mock boundary, and browser path. Reuse an existing server when safe; start one only through the project's documented command.

Collect the cheapest evidence that proves each transition: meaningful DOM/accessibility state, visible control and resulting change, focus/overlay/navigation/persistence state, relevant console/network health, and a screenshot for visual claims. Test the requested interaction rather than only loading the page.

For durable STANDARD/FULL evidence, create one declarative probe spec under `qa/`, then use `scripts/runtime_state.py run-runtime-qa`. It invokes the canonical browser probe, writes the manifest, and records the receipt atomically; manual `record-fidelity-qa --result pass` is rejected. The helper rejects document-shell roots, tiny screenshots, wrong state/scroll, stale implementation snapshots, unchanged or constant interactions, indirect/remote navigation by default, screenshot-only claims, runtime errors, failed requests, and critical/serious accessibility violations.

For a library, framework, platform, or internal complex control, verify the capability behavior that justified its selection, not merely its pixels or presence in the bundle. Exercise representative pointer and keyboard input, accessible name and focus behavior, state transitions, failure/recovery, and capability-specific behavior such as overlay dismissal and focus restoration, graph selection/zoom/pan, editor input/undo/validation, form submission/error focus, chart or table exploration, drag-and-drop alternatives, or virtualization at a meaningful boundary. Use only checks relevant to the plan constraints. A visible toolbar, imported package, mounted canvas, or screenshot is not proof that the control works.

MICRO covers its one target and only additional evidence required by the claim. STANDARD verifies one materially different responsive viewport when layout or navigation changes. FULL follows every route, state, viewport, and fidelity output required by the frozen contract and validates each complex/foundational capability against its implementation-plan `validation` obligations.

### Compare and classify

Check functional truth before visual fidelity. Then compare the implementation with both the renderer-neutral direction and the accepted artifact: hierarchy, grouping, density, typography/color roles, surface language, imagery, motion tone, component language, navigation, responsive transformation, and accepted visual invariants. Project-compatible adaptation may differ in incidental bitmap detail when it preserves the direction contract. Product truth, accessibility, and project architecture outrank decorative bitmap details.

Some accepted outputs communicate direction only and intentionally do not specify complete content, data, or interaction. For a direction-only runtime output, first verify the actual product state, typed contract, and planned capability behavior; then compare only the visual invariants the direction owns. Do not copy fake controls or sample data from a direction artifact, infer unsupported behavior, or waive runtime verification because the image was accepted. Record which assertions came from product/implementation contracts and which came from visual direction.

Record each material mismatch with reference, observed evidence, severity, likely owner, and whether it is a defect or intentional adaptation. Do not claim an unproven root cause.

### Enforce FULL fidelity

For every durable STANDARD or FULL runtime-required output, follow the manifest, canonical runtime-probe, and evidence-identity rules in the loaded references. FULL also reads the locked direction path/SHA, implementation-plan identity, and accepted artifact paths/SHAs from validated runtime state. Record each result through record-fidelity-qa against those identities; source, prose, reused design bytes, arbitrary text, a stale direction, a plan mismatch, or a manifest-only equivalence claim cannot prove PASS.

After all required receipts exist, use complete-implementation. The helper, not the implementing agent, owns the `completed` transition in STANDARD and FULL. If it refuses, report the missing or stale evidence or unchanged target instead of bypassing the gate. FULL success enters `awaiting-user-review`: present the helper-bound runtime gallery, then use accept-delivery or reject-delivery only for the user's explicit decision on that digest. Hashes prove evidence integrity, not semantic fidelity; perform the visual comparison before PASS and never hand-edit runtime state.

## Evidence and handoff

For each failure, report route, viewport, reproduction, expected/observed result, evidence, likely source boundary, and whether a fix is authorized. Keep pre-existing failures separate.

For read-only or MICRO work, do not edit repository metadata or create a persistent workspace; keep evidence in conversation or task-scoped temporary storage. STANDARD/FULL durable QA evidence belongs only in the active ignored /.frontend-workbench/ session, never product source.

## Completion

Finish when page identity and meaningful rendering are confirmed, target and library-backed interactions were exercised, direction-only outputs were judged at the correct authority boundary, relevant runtime health was checked, required responsive/accessibility/fidelity claims have evidence, environments are labeled accurately, and failures or untested states are explicit.

If rendered verification was explicitly requested and no rendered path exists, completion is BLOCKED; a build cannot substitute.
