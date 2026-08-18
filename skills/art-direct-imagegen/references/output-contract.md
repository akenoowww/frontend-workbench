# Output Contract and Durable Execution

Use this reference for every run. It defines the handoff boundary, typed output manifest, serial state machine, checkpoint/resume behavior, and artifact rules.

## Contract modes

### UPSTREAM CONTRACT

An upstream workflow owns product discovery and supplies two artifacts:

1. the canonical coverage contract accepted by `scripts/runtime_state.py`;
2. renderer briefs keyed by its output IDs.

```json
{
  "schemaVersion": 1,
  "contractId": "account-redesign",
  "authority": {
    "pageStructure": "locked",
    "interactionModel": "locked",
    "contentRepartition": "within-surface-only"
  },
  "surfaces": [
    {"id": "account", "kind": "page", "route": "/account", "userJob": "Review account details"}
  ],
  "edges": [],
  "outputs": [
    {
      "id": "account-desktop-default",
      "surfaceId": "account",
      "state": "default",
      "viewport": "desktop-1440x1024-top",
      "scrollPosition": "top",
      "required": true,
      "approvalRequired": false,
      "dependsOn": [],
      "promotionRequired": false,
      "promotionTarget": null
    }
  ]
}
```

Treat all coverage decisions as upstream-owned even when the contract records broader revision authority for another skill. Do not change surfaces, edges, output IDs, state meaning, viewport purpose, content, or interaction semantics. If the contract is contradictory or incomplete, return the affected output `blocked` with the smallest missing decision.

### STANDALONE

The user directly requests generated frontend images. Build the same strict coverage contract from explicitly named surfaces, states, viewports, and references. Use `pageStructure: locked`, `interactionModel: locked`, and `contentRepartition: within-surface-only`; STANDALONE art direction does not grant product revision authority. You may choose visual concept and renderer composition. You may not invent product pages, states, controls, copy, navigation, or content relocation. A missing product decision is a blocker, not creative latitude.

## Coverage outputs and renderer briefs

The coverage contract is strict: do not add renderer-only keys to it. Its `outputs` contain exactly:

```yaml
- id: home-desktop
  surfaceId: home
  state: default
  viewport: desktop-1440x1024-top
  scrollPosition: top
  required: true
  approvalRequired: false
  dependsOn: []
  promotionRequired: false
  promotionTarget: null
```

Use a separate renderer brief with the same ID:

```yaml
home-desktop:
  purpose: <what this bitmap must communicate>
  now: <only content visible in this output>
  exactLabels: <critical short labels only>
  invariants: <truth and continuity locks>
  changeFromParent: null
  sourceRoles: <references used by this output>
  anchorId: null
  checkpointAfter: false
```

The surface supplies page/flow-step/screen/overlay identity; `state` names the supplied visible state; `viewport` names its supplied breakpoint and dimensions; optional `scrollPosition` names a full-page, top, middle, bottom, or another contract-defined frame. This skill renders those definitions and does not create their information architecture.

Every coverage output needs exactly one renderer brief. A dependent output must name its parent through `dependsOn` and point to an `accepted` or `promoted` `anchorId` in its brief. Reject duplicate IDs, missing surfaces/briefs/dependencies, and dependency cycles before generation.

## Status state machine

At most one output may be `generating`, `reviewing`, or `awaiting-approval`.

```text
pending -> generating -> reviewing -> accepted -> promoted
                        |       |
                        |       +-> awaiting-approval -> accepted
                        +-> pending

pending/generating/reviewing/awaiting-approval -> blocked
pending/blocked -> deferred  (explicit user/upstream decision only)
blocked -> pending           (blocker explicitly resolved)
```

- `pending`: required work has not started or is ready for a bounded retry.
- `generating`: one recorded ImageGen call is in flight.
- `reviewing`: a returned artifact is saved and awaiting the quality gate.
- `awaiting-approval`: review passed, but a `review-each-stage` checkpoint requires explicit user approval before acceptance or later work.
- `accepted`: review passed and a verified artifact path is recorded.
- `promoted`: a workspace-bound accepted artifact was copied to its final destination and verified.
- `blocked`: completion is impossible or unsafe now; record `code`, `retryable`, and `nextAction`; keep supporting detail in the stage handoff.
- `deferred`: the user or upstream contract explicitly removed rendering from this run.

Do not use `deferred` for time pressure, tool failure, retry exhaustion, or agent convenience. Do not finalize a successful run while any required output is `pending`, `generating`, `reviewing`, `awaiting-approval`, or `blocked`.

## Serial anchored execution

Use one built-in ImageGen call per output. Do not use parallel calls or `n` for distinct deliverables.

1. Checkpoint `pending -> generating` with output ID, attempt number, exact prompt, dependencies, and expected promotion.
2. Invoke ImageGen. If the call yields, wait for completion.
3. Copy the returned image into the session's `artifacts/<output-id>/` directory, then checkpoint `generating -> reviewing` with that relative path before critique.
4. Review. Accept it, move it to `awaiting-approval` when the renderer brief requires a checkpoint, or record one targeted rejection and return the same output to `pending` within the retry budget.
5. After `accepted`, unlock only direct dependents whose prerequisites now pass.
6. Use the accepted master or parent file path as the visual anchor; do not rely on conversation-image recency.

When the upstream checkpoint mode requires separate review, set `checkpointAfter: true` for the relevant brief. Move the reviewed artifact to `awaiting-approval`, persist its session-relative path and SHA-256, and stop. Accept it only through a user-authorized transition for that exact path and digest; replacement or modified bytes require review again. Dependencies and unrelated outputs remain locked until acceptance. Do not convert a checkpoint into `deferred`.

The helper must refuse `generating` while another output is `generating`, `reviewing`, or `awaiting-approval`, and must refuse it until every `dependsOn` output is `accepted` or `promoted`. A deferred dependency does not unlock a child.

An unknown in-flight outcome is non-idempotent and potentially costly. Mark it `blocked` with code `unknown_outcome`, reconcile the host result or generated-image path, and do not retry blindly.

## `.frontend-workbench` artifacts

For multi-output work, use the active consumer-workspace session. The shared helper owns machine status and artifact hashes; the stage directory owns lean prompts and renderer briefs.

```text
.frontend-workbench/sessions/<session-id>/
  state.json
  artifacts/<output-id>/attempt-<n>.<ext>
  art-direct-imagegen/
    render-briefs.json
    prompts/<output-id>.md
    reviews/<output-id>-attempt-<n>.json
    handoff.md
```

Use `scripts/runtime_state.py`; do not hand-edit `state.json`. The root orchestrator is the sole state writer and ImageGen caller. Subagents may inspect or review an assigned artifact, but may not render connected outputs, promote files, change statuses, or clean up.

Resolve `<plugin-root>` from the installed skill path (`skills/art-direct-imagegen/` is two levels below it). A required multi-output run is `blocked` if `<plugin-root>/scripts/runtime_state.py` is unavailable; do not claim durable resume from prose or chat history alone.

Before creating runtime files, require the shared gitignore preflight. The canonical project rule is `/.frontend-workbench/`. If the directory is tracked, unignored, or symlinked outside the workspace, stop instead of taking ownership. Never use `git clean` for runtime cleanup.

For a greenfield design request with no consumer repository yet, do not use the plugin source repository as the consumer. Create an allowed task-scoped temporary directory, initialize a temporary Git repository there, add the exact ignore rule, and run the same helper against that root. Persist its path in the handoff and state clearly that temporary runtime state is not durable after cleanup or host restart. If a temporary Git workspace cannot be provisioned, use `handoff-only` planning and do not claim resumable multi-output execution.

The core commands are:

```text
python3 <plugin-root>/scripts/runtime_state.py init --root <repo> --session-id <id> --contract <coverage.json> [--structure <structure.json>]
python3 <plugin-root>/scripts/runtime_state.py status --root <repo> --session-id <id>
python3 <plugin-root>/scripts/runtime_state.py mark --root <repo> --session-id <id> --output-id <output> --status <status> --expected-revision <n> [...]
python3 <plugin-root>/scripts/runtime_state.py resume --root <repo> --session-id <id> --expected-revision <n>
python3 <plugin-root>/scripts/runtime_state.py validate --root <repo> --session-id <id> --expected-revision <n>
python3 <plugin-root>/scripts/runtime_state.py promote --root <repo> --session-id <id> --output-id <output> --expected-revision <n>
```

For `reviewing`, `awaiting-approval`, and `accepted`, pass the artifact again as a session-relative path beginning with `artifacts/`. Accepting an awaiting checkpoint also requires `--user-authorized`. For `blocked`, pass a problem code and next action. For `deferred`, pass explicit user authority and a reason. Use the returned revision for the next mutation.

```text
python3 <plugin-root>/scripts/runtime_state.py mark --root <repo> --session-id <id> --output-id <output> --status reviewing --expected-revision <n> --artifact artifacts/<output>/<attempt>.png
python3 <plugin-root>/scripts/runtime_state.py mark --root <repo> --session-id <id> --output-id <output> --status awaiting-approval --expected-revision <n> --artifact artifacts/<output>/<attempt>.png
python3 <plugin-root>/scripts/runtime_state.py mark --root <repo> --session-id <id> --output-id <output> --status accepted --expected-revision <n> --artifact artifacts/<output>/<attempt>.png --user-authorized
python3 <plugin-root>/scripts/runtime_state.py mark --root <repo> --session-id <id> --output-id <output> --status blocked --expected-revision <n> --code unknown_outcome --retryable --next-action "Inspect the renderer result."
python3 <plugin-root>/scripts/runtime_state.py mark --root <repo> --session-id <id> --output-id <output> --status deferred --expected-revision <n> --user-authorized --reason "User deferred this output."
```

Checkpoint after every transition with: exact prompt, attempt/tool result reference, concise review, remaining outputs, and next action in stage files; let the helper persist central status, artifact path/hash, blocker, and promotion result. Keep metadata small; never store base64, secrets, or hidden reasoning.

## Resume and promotion

On resume:

1. validate the session and expected state revision;
2. verify every accepted/promoted artifact path and digest;
3. preserve accepted work and recompute the first valid pending action;
4. reconcile any stale `generating` or `reviewing` output before retrying, and preserve a verified `awaiting-approval` checkpoint without advancing it;
5. re-read only the current output brief, accepted anchor, and required invariants.

Project-bound artifacts must not remain only under `.frontend-workbench`. Run session validation after all required outputs settle, then use helper promotion to copy each accepted output to its contract `promotionTarget` with readback verification. Do not overwrite an existing target without explicit authority and guarded replacement evidence; revise the contract target or block on conflict.

Delete temporary and rejected attempts only after the session is terminal. Never delete an unpromoted accepted artifact. Preview-only accepted images may remain in the ignored runtime directory. A blocked handoff must preserve the resume path and exact next action.
