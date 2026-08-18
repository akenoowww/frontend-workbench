---
name: art-direct-imagegen
description: "Use for actual ImageGen-rendered frontend bitmap deliverables that need art direction or one coherent page, state, or viewport set. Render every required contract output serially. Do not use for design analysis without rendering, code or Figma work, product structure, deterministic vector output, or fixed surgical edits."
---

# Art-Direct ImageGen

Create a strong visual idea, render every required bitmap, and leave a truthful artifact trail. This skill owns visual concept, renderer prompts, ImageGen calls, image review, and accepted-image delivery. It does not own product behavior, information architecture, copy, routes, code, or implementation.

## Choose the contract mode

Use exactly one mode:

- **UPSTREAM CONTRACT** — another skill or workflow supplies the objective, global locks, source roles, typed output manifest, and delivery requirements. Treat its page, state, viewport, content, and product decisions as fixed. Do not repeat upstream discovery or silently rewrite the manifest.
- **STANDALONE** — the user directly requests generated frontend images. Extract only explicit content, source roles, constraints, and requested page/state/viewport outputs. Choose a visual direction, but do not invent product pages, interactions, states, copy, or navigation. If rendering requires an unresolved product decision, mark the affected output `blocked` and request that decision.

If no actual ImageGen deliverable is requested, exit this skill. If the request is a fixed local edit, hand it to the system `imagegen` workflow without running art direction.

Label every supplied image as one of: `FUNCTIONAL_REFERENCE`, `STYLE_REFERENCE`, `EDIT_TARGET`, or `VISUAL_ANCHOR`. Never silently treat a functional reference as an edit target.

## Load only the needed references

- Read [references/output-contract.md](references/output-contract.md) for every run; it defines manifests, statuses, checkpoints, resume, and artifact rules.
- Read [references/concept-planning.md](references/concept-planning.md) when the visual direction is not already fixed.
- Read [references/prompt-and-review.md](references/prompt-and-review.md) before the first ImageGen call and before accepting an output.

## Execute the render workflow

1. **Validate the contract.** Normalize the shared coverage contract for supplied surfaces and page/state/viewport outputs, plus one renderer brief per output. Each output needs a stable ID, required flag, dependencies, current visible content, exact short labels, invariants, source roles, and promotion policy. Do not add a page or state merely to solve density; return that question upstream.
2. **Select one concept.** For judgment-heavy work, branch through several semantically different ideas, attack their fit and usability, and select one coherent direction. Preserve functional truth before originality. Keep the internal concept sheet separate from renderer prompts.
3. **Start or resume the checkpoint.** For multi-output work, use the current `.frontend-workbench/sessions/<session-id>/` runtime. Verify the session manifest before any expensive call. On resume, trust validated checkpoint state and accepted artifact hashes, not conversational memory. Never regenerate an `accepted` or `promoted` output. If the contract changes materially, begin a new linked session instead of rewriting accepted history.
4. **Render serially.** Generate exactly one manifest output per built-in ImageGen call. At most one output may be `generating` or `reviewing`. Accept the master first; use its saved file path as the visual anchor for dependent outputs. Do not use parallel calls, `n`, a collage, or subagents to render connected deliverables.
5. **Review the artifact.** Check contract fidelity, concept legibility, task specificity, coherence, usability, critical text, and continuity. A local defect gets one targeted retry with invariants repeated. A structural defect returns to concept selection; do not rescue it with a longer wireframe prompt.
6. **Checkpoint every transition.** Persist the exact prompt, attempt result, accepted path, digest when supported, review decision, remaining outputs, and next action. If a call yields, wait for its final result. If its outcome is unknown after interruption, mark it `blocked`; do not spend another call until the result is reconciled.
7. **Deliver accepted artifacts.** Follow the system `imagegen` save-path rules. Promote project-bound images from runtime staging to the requested or project-native destination non-destructively, verify the result, and record the final path. Preview-only images may remain in the runtime directory.

## Keep status truthful

Use `pending`, `generating`, `reviewing`, `awaiting-approval`, `accepted`, `promoted`, `blocked`, or `deferred` exactly as defined in the output contract.

- `deferred` requires an explicit user or upstream decision not to render now.
- `blocked` means a required input, tool, permission, safe retry, or verified result is unavailable; record the cause and resume action.
- Never relabel unfinished work `deferred` for convenience.
- Never begin another required output while the current one is unaccepted.
- Never send a successful final response while a required output is `pending`, `generating`, `reviewing`, `awaiting-approval`, or `blocked`.

When interrupted, stop issuing calls, checkpoint if possible, and preserve the next action. A final blocked handoff must enumerate completed, blocked, and explicitly deferred outputs without claiming the set is complete.

## Keep renderer prompts lean

Compile one small prompt for one visible output. Include its ID/type, immediate purpose, source roles, current visible content, critical short labels, one concept relationship, continuity locks, creative latitude, and at most three causal avoid items. Exclude the global contract, rejected concepts, product reasoning, other outputs, implementation instructions, and long copy.

Treat generated UI as high-fidelity visual direction, never implementation proof. Report the selected concept, manifest status, accepted/promoted paths, and final prompt set.
