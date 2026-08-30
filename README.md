# Frontend Workbench

An extensible Agent Plugin for complete, project-aligned frontend product work.

Repository: <https://github.com/akenoowww/frontend-workbench>

Frontend Workbench keeps six responsibilities separate: information architecture, product design and visual direction, implementation fit, user-facing copy, ImageGen rendering, and rendered QA. It selects a proportional `micro`, `standard`, or `full` workflow. FULL v3 derives a task-specific product/object model, scenario trace, nested shells, scoped references, capability requirements, and independent design/runtime evidence before implementation. It then locks renderer-neutral direction when required, requires a capability-first implementation plan, preserves contract lineage, separates technical gates from user acceptance, and stores SHA-bound evidence in an ignored `.frontend-workbench/` runtime workspace.

An explicitly preview-only, non-promotable redesign evaluation may remain STANDARD when its target, preserve/replace boundary, scoped references, named outputs, and fixed render budget are already supplied and no implementation or durable acceptance follows. This keeps design experiments proportional without weakening the FULL gates required before implementation or promotion.

Bundled evaluation cases are synthetic and fictional. Repository validation rejects personal home-directory paths, email-like identifiers, private-key material, and any visual fixture whose provenance is not `synthetic-fictional-eval-spec`. Real user projects, account data, screenshots, names, and local paths do not belong in the plugin archive.

## Bundled skills

| Skill | Use it for | Do not use it for |
| --- | --- | --- |
| `frontend-information-architecture` | Sitemap, routes, page families, navigation edges, flow steps, content/action ownership, and structural coverage | Visual styling, component implementation, copy polish, ImageGen, or runtime QA |
| `frontend-product-design` | UI/UX decisions, renderer-neutral visual direction, redesign, new-surface design, or critique after structure is known | Sitemap-only work, fully specified implementation, small CSS/copy fixes, bugs, tests, performance, or backend work |
| `frontend-project-fit` | Authorized frontend implementation through the host project's architecture, reusable UI, and justified capability choices | Design-only work, backend-only work, or claims of project fit without source access |
| `frontend-copy-guard` | Affected user-visible copy, localization, accessibility wording, validation, errors, and safe cross-layer mappings | Unrelated repository-wide copy audits or unauthorized backend changes |
| `art-direct-imagegen` | Bitmap instances of a locked upstream direction, or a standalone bitmap-only direction when no product-design contract exists | Generic UI planning, code implementation, fixed surgical edits, or tasks that do not require generated bitmap output |
| `frontend-runtime-qa` | Rendered page identity, console health, interactions, responsive layout, accessibility, and design fidelity | Design-only planning, source-only review, backend-only testing, implementation, or image generation |

Codex may display plugin skills with names such as `frontend-workbench:frontend-product-design`. Use the skill picker or the exact name shown by the host for explicit invocation. Ordinary prompts can rely on the narrow skill descriptions.

## Workflow profiles

| Profile | Use it for | Runtime behavior |
| --- | --- | --- |
| `micro` | Read-only diagnosis, one specified local fix, one bounded copy/design decision, or one rendered smoke target | No durable workspace or automatic Copy Guard/Runtime QA cascade |
| `standard` | A scoped surface or flow whose implementation, copy, interaction, or rendered state needs proportional evidence | Load only the execution-envelope slices; every durable runtime-required output needs a canonical browser probe before completion |
| `full` | Multi-page work, material redesign, dependent ImageGen outputs, staged approval, or design-to-code fidelity | Intent teach-back, typed coverage, direction policy/lock, artifact policy, lineage, implementation fingerprints, strict fidelity receipts, and final user review |

Start with the lightest profile supported by the request and project evidence. Escalate only when a discovered requirement meets a higher-profile boundary; preserve an existing contract's `workflowProfile`.

## FULL lifecycle gates

A new FULL contract uses `schemaVersion: 3` and includes:

- `productModel`: the root, primary/supporting objects, downstream evidence, and implementation details unique to this task;
- SHA-bound rich structure: domains, scenarios, nested shells, scoped reference bindings, and surface ownership;
- `capabilityRequirements`: bounded, complex, or foundational behavior that implementation must assign to a proven owner;
- `productIntent`: problem, representative scenarios, required domains, protected capabilities, anti-goals, and success signals;
- `operationalMetadataPolicy`: `hidden-unless-required` plus any explicitly authorized verification, freshness, provenance, sync, confidence, or service-health claims bound to covered surfaces/states;
- `visualDirectionPolicy`: `required` or `not-required`;
- `visualArtifactPolicy`: `runnable`, `imagegen-required`, or `no-imagegen`;
- `checkpointMode`: the review policy;
- separate `designEvidenceRequired` and `runtimeEvidenceRequired` output obligations;
- a render budget when ImageGen is selected;
- optional surface-bound implementation targets and session lineage.

Schemas v1/v2 remain readable for existing sessions. They do not gain v3 product-model, structure, plan, lineage, or user-acceptance guarantees implicitly; material continuation uses an explicit v3 replacement. The fail-closed browser completion gate is cross-version: an in-progress legacy session must refresh any old screenshot-only PASS receipt with a canonical runtime probe before completion.

Before a v3 design output can generate, review, or accept, the user-facing teach-back must be confirmed through `confirm-intent` against the complete contract and rich-structure identities using a file-backed, action-scoped authority receipt. Operational evidence is not UI copy: absence of an authorized claim means verification badges, freshness timestamps, provenance/source labels, sync/confidence messages, and service-health reassurance remain hidden. When direction is required, `lock-visual-direction` validates and freezes a `VisualDirectionContract` before the first artifact. For `artifactKind: imagegen`, every design artifact must be real image bytes and carry file-backed provenance regardless of the overall artifact policy. Runtime-only coverage does not consume ImageGen calls.

Before `begin-implementation`, the v3 implementation plan resolves every required capability through `reuse`, `extend`, `compose`, platform/framework support, a mature external dependency, or a justified project-owned primitive. `decisionTier` keeps the cost proportional: `direct` for bounded work, `known-fit` for a complex non-project-owned owner whose exact fit is already proven, and `comparative` for foundational work, uncertain dependencies, or complex project-owned primitives. A proven React Flow-style library may therefore win directly; an unavailable dependency blocks implementation instead of triggering a custom SVG/canvas fallback.

ImageGen attempts also have explicit identity. MICRO/STANDARD permit one call for one output in one user turn; a failed render returns `REVISE_ARTIFACT` instead of silently creating the same output again. A later user retry edits that saved artifact, not the original references, and supplied `STYLE_REFERENCE`, `FUNCTIONAL_REFERENCE`, and `VISUAL_ANCHOR` roles cannot be promoted to `EDIT_TARGET`. FULL retries remain serial and require a render-budget reservation.

Material redesigns carry a region-level `redesignBoundary`. In `preserve-only` mode, the named regions and invariants are the complete preservation allowlist. Every replace region declares material change dimensions and a minimum coverage threshold, plus source structures that must not survive. Thus “keep only the primary sidebar” cannot silently become “keep the whole recognizable shell”; an unchanged main-content macro-layout/card topology fails even when colors and spacing look cleaner.

Material contract replacement uses an explicit parent/supersession link and computed JSON-pointer delta. The prior session becomes `superseded`; rejected, superseded, or cancelled sessions cannot silently become active parents.

Direction lock and artifact approval are separate decisions. The former freezes the renderer-neutral concept, roles, project-DNA preservation, and intentional departures; the latter accepts one concrete runnable or bitmap instance. Quality is recorded through independent gates:

```text
intent -> coverage -> runtime -> fidelity -> user acceptance
```

`complete-implementation` is the sole completion authority for durable STANDARD and FULL work. Both profiles require the latest PASS runtime receipt for every runtime-required output; the implementing agent cannot set completion itself. STANDARD then becomes `completed`. FULL ends at `awaiting-user-review`: the helper derives a delivery digest from the current coverage contract, locked direction SHA, implementation fingerprints, design-instance SHAs, manifests, canonical browser traces, and runtime screenshots. Only `accept-delivery --user-authorized` can make that exact gallery `completed`; rejection leaves the session terminal and records the reason.

## Canonical browser probe

Rendered PASS is produced through `scripts/runtime_state.py run-runtime-qa`, which invokes `scripts/browser_runtime_probe.py`, writes the manifest, and records the receipt atomically. Manual PASS recording is rejected. A declarative v1 spec under the active session `qa/` names the exact URL, route, state, viewport, app-root selector, ready condition, target interaction, observable assertions, and output paths. The helper:

- uses an already-installed `agent-browser` and never runs `npm install` in the product;
- navigates directly to the target, rejects `file://` and search-engine hosts, and restricts network domains to that target by default;
- binds the trace to the current implementation-target snapshot, declared state, and verified scroll/full-page position;
- rejects `html`, `body`, a selector resolving to either document shell, or another fake app root;
- proves a mounted child, visible geometry, meaningful text, and a landmark or interactive element;
- exercises at least one action and requires both a changed before/after fingerprint and a postcondition that was false/different beforehand;
- records console errors, uncaught page errors, failed requests, and axe critical/serious violations;
- produces a distinct PNG of at least 320x200 pixels plus a normalized JSON trace.

The fidelity manifest binds `runtimeProbe.path` and `runtimeProbe.sha256`. The trace in turn binds the exact probe spec and screenshot bytes. A missing browser path is `BLOCKED`; Google/search navigation, direct ad hoc Chrome control, source success, and screenshot-only manifests cannot substitute.

## Responsibility flow

```text
explicit design request
-> confirm FULL product intent when scope is material
-> frontend-information-architecture when site/flow structure is new or changing
-> frontend-product-design
   -> extract supplied brand/reference evidence when present
   -> select and lock one renderer-neutral visual direction when required
   -> create the lightest runnable or bitmap instance that can test it
   -> run one shared conceptual critique on the first representative artifact
   -> frontend-copy-guard when the design authors user-visible labels or claims
   -> art-direct-imagegen only when ImageGen is the selected renderer
   -> frontend-project-fit only when implementation is authorized
      -> frontend-copy-guard when visible copy changes
      -> frontend-runtime-qa after visible implementation

direct implementation request
-> frontend-project-fit
   -> frontend-copy-guard only for materially affected user-visible meaning
   -> frontend-runtime-qa only when rendered behavior must be proven

micro request
-> one owning skill
-> focused evidence
-> no automatic cross-skill cascade
```

The graph is one-way. No skill invokes an earlier skill back. Agent Plugins do not provide a portable cross-skill dependency graph, so each skill includes a small truthful fallback when a host cannot compose another bundled workflow.

## Multi-page and multi-state coverage

A website is not treated as one master screenshot. `frontend-information-architecture` records separate entities for:

```text
site -> surface/page family -> page/route -> state -> viewport -> scroll position -> output
```

Each required output has a stable ID, evidence target, dependency, approval policy, and status. Named pages cannot disappear into a homepage, and a page is never confused with a state, breakpoint, scroll position, or bitmap output.

Structurally equivalent dynamic routes may share a representative page-family output unless the user explicitly requests every page separately. A unique user job, hierarchy, composition, or interaction requires its own output.

## Direction and renderer policy are explicit

Product Design owns concept and direction independently of renderer. For material visual change it creates a compact `VisualDirectionContract` covering thesis, brand posture, visual tension, signature move, hierarchy and density, typography/color roles, surface/motion/imagery language, project-DNA preservation, intentional departures, avoid items, and provenance-backed evidence. The locked path and canonical SHA travel through handoff and implementation, so changing from runnable HTML to ImageGen does not silently change the design.

Product Design separately records whether the FULL flow uses a runnable artifact, requires ImageGen, or explicitly excludes it. Within that policy it chooses the lightest artifact that can test the locked direction:

- annotated specification;
- existing-component composition;
- runnable prototype;
- browser screenshot;
- ImageGen-rendered instance.

When `imagegen-required` is selected, `art-direct-imagegen` receives the confirmed intent, frozen authority, coverage contract, and locked direction ref/SHA. It compiles renderer prompts and renders one dependency-ready output at a time without reopening the concept. Only a standalone bitmap request with no upstream product-design contract may create its own direction, and that fallback cannot authorize later product implementation. Implementation cannot substitute a wireframe or runnable screen for the required visual stage.

The first representative runnable or ImageGen artifact passes the same conceptual critique: concept specificity, hierarchy, execution, project-DNA preservation, restraint, usability, and feasibility. The verdict is `PASS`, `REVISE_ARTIFACT`, `REVISE_DIRECTION`, or `BLOCKED`; fake precision such as an unexplained `3/5` is not evidence.

An accepted homepage never completes a multi-page request. Dependent UI renders remain sequential to preserve one visual system; independent research can still run in parallel.

When the user asks to review every stage or page separately, the reviewed output enters `awaiting-approval`. The runtime blocks all later outputs until explicit approval changes it to `accepted`; conversational intent alone cannot bypass the checkpoint.

For a `full` design-to-implementation handoff, accepted artifacts are not merely advisory. `begin-implementation` refuses to start until intent, required direction lock/authorization, coverage, checkpoint approval, verified provenance when required, and at least one safe product target pass. Runtime QA records each comparison through a structured manifest matching route, state, viewport, scroll position, accepted design-instance SHA-256, and actual image dimensions. Duplicate screenshot bytes are rejected unless the lifecycle-confirmed contract explicitly declares the exact equivalent output pair and justification; a QA manifest cannot invent equivalence later.

## Private runtime workspace

Resumable or artifact-producing work uses:

```text
<project-root>/.frontend-workbench/
└── sessions/
    └── <session-id>/
        ├── state.json
        ├── structure.json
        ├── coverage.json
        ├── ledger.md
        ├── artifacts/
        ├── product-design/
        │   ├── visual-direction.json
        │   └── critiques/
        ├── art-direct-imagegen/
        ├── qa/
        └── tmp/
```

Before writing an artifact, the runtime helper verifies that the exact directory is ignored and atomically installs the staged structure and coverage contracts with `state.json`. Skills never pre-create or hand-edit a canonical session. The shared repository rule is:

```gitignore
/.frontend-workbench/
```

The workspace is not created for read-only work by default. Read-only screenshots or traces use task-scoped temporary storage; an existing ignored runtime session may be reused only when the user explicitly requests durable evidence, without changing repository metadata. When a local project cannot safely host runtime state, the workflow uses an allowed task-scoped temporary directory or keeps a compact record in the conversation and reports the limitation.

The hidden workspace supports resume after ordinary task changes and context compaction. Full sessions also persist intent confirmation, the immutable direction lock and artifact bindings, lineage, independent quality gates, implementation fingerprints, fidelity receipts, and delivery review. It is local ignored state, not a backup: destructive cleanup such as `git clean -fdx`, workspace deletion, or disk loss can remove it.

Use `runtime_state.py handoff` to pass a compact contract/gate/next-action envelope to a child agent instead of rereading every workflow. Its SHA-bound `executionEnvelope` selects one stage owner, only the relevant reference slices/tools, exact runtime probes, capability validation obligations, authorized operational claims, and forbidden substitutions. This is the prompt/token boundary: child agents do not preload all six skills or every reference. Use bounded `batch-mark` for a serial group of known transitions; the batch validates on a copy and commits once, so a failed transition leaves persisted state unchanged.

For greenfield design before a consumer repository exists, the workflow provisions an allowed task-scoped temporary Git workspace with the same ignore rule and runtime helper. It never writes runtime state into the plugin repository. That fallback is explicitly temporary and cannot be described as durable after cleanup or host restart.

## Repository artifact policy

Working prompts, design reports, generated mockups, contact sheets, screenshots, traces, and QA evidence stay inside `.frontend-workbench/`.

For read-only work, temporary evidence remains task-scoped and outside the product tree unless the user explicitly asks to retain it in an already ignored runtime session.

The workflow does not create discretionary files such as `ANALYSIS.md`, `DESIGN.md`, `PLAN.md`, `REPORT.md`, `output.png`, or `screenshots/` in product source. A final generated asset may leave the workspace only when it has:

- an approved project-native destination;
- a real code, build, or test consumer;
- verified promotion and no unauthorized overwrite.

Project-standard source, tests, migrations, fixtures, and explicitly requested documentation remain in their normal paths. Cleanup targets only artifacts owned by the current run; broad destructive globs are forbidden.

## Package structure

```text
frontend-workbench/
├── .codex-plugin/plugin.json
├── .agents/plugins/marketplace.json
├── plugin.json
├── AGENTS.md
├── README.md
├── LICENSE
├── schemas/
├── scripts/             # lifecycle helper, canonical browser probe, eval runners
├── tests/
├── evals/
└── skills/
    ├── frontend-product-design/
    ├── frontend-information-architecture/
    ├── frontend-project-fit/
    ├── frontend-copy-guard/
    ├── art-direct-imagegen/
    └── frontend-runtime-qa/
```

`.codex-plugin/plugin.json` is the required OpenAI plugin manifest. Root `plugin.json` preserves Agent Plugins 1.0 portability for compatible non-OpenAI hosts. Validation keeps their shared metadata synchronized.

The plugin contains no MCP server, hook, credential, bundled remote service, or automatic external action.

## Install in Codex

The latest published stable tag is `v0.9.0`.

For the current development branch:

```bash
codex plugin marketplace add akenoowww/frontend-workbench --ref main
codex plugin add frontend-workbench@frontend-workbench
codex plugin list
```

For a first install after an immutable release tag exists, prefer the pinned form:

The latest published stable tag is `v0.9.0`.

```bash
codex plugin marketplace add akenoowww/frontend-workbench --ref v0.9.0
codex plugin add frontend-workbench@frontend-workbench
codex plugin list
```

To upgrade an existing installation whose `frontend-workbench` marketplace is already configured,
refresh that marketplace instead of adding the same name again:

```bash
codex plugin marketplace upgrade frontend-workbench
codex plugin add frontend-workbench@frontend-workbench
codex plugin list
```

Start a new Codex task after installation or reinstall so skill discovery uses the updated package.

Plugins are supported in ChatGPT and Codex surfaces documented by OpenAI, including the ChatGPT desktop app and Codex CLI. The Codex IDE extension supports standalone skills but not plugin browsing or installation.

## Validate

Install the pinned development requirements, then run the repository checks:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests
python3 scripts/validate_repo.py .
python3 scripts/run_evals.py --mode fixtures --cases evals/cases
python3 scripts/run_visual_evals.py --mode fixtures --cases evals/design-cases
```

Validation covers manifest synchronization, JSON schemas, skill metadata, prompt lengths, Markdown links, runtime-state transitions, intent/direction/lineage/delivery gates, multi-page completion, path containment, ignored-workspace hygiene, blind-packet separation, and unapproved generated artifacts.

Lifecycle fixture mode validates cases and contracts and explicitly reports that no model behavior was scored. Score measured baseline and Workbench lifecycle runs only when both complete result sets exist:

```bash
python3 scripts/run_evals.py \
  --mode paired \
  --cases evals/cases \
  --baseline-results evals/results/baseline \
  --workbench-results evals/results/workbench \
  --scorecard evals/results/scorecard.json
```

Paired result schema v3 requires token usage, model/tool calls, duration, assertion coverage, outcome/fidelity defects, and a case-bound evidence receipt with source identity, prompt SHA-256, and a safe relative `tracePath`. The runner verifies that the trace is a real non-symlink file under the variant result root and that its bytes match `traceSha256`. Complete captures require positive measured work; failed zero-token captures require an explicit outcome defect. Missing cases or any Workbench assertion/defect fail the command. Case counts are derived from the checked-in fixture directories during validation rather than repeated manually in documentation.

Design quality is a separate adversarial track. Its fixture mode derives the checked-in case count and validates sanitized product/DNA contracts, capture matrices, and the schema-locked pairwise rubric while explicitly reporting `NO visual quality was scored.` Real scoring requires matched baseline/Workbench trials. The runner recomputes prompt/fixture identity and requires file-backed byte receipts for model configuration, environment, capture harness, and task budget before treating a pair as matched. Those receipts prove exact supplied bytes, not that a collector described the real environment truthfully. `blind-pack` verifies real non-symlink PNG bytes, hashes, dimensions, and trace receipts, then copies only anonymized A/B packets for judges while keeping variant mappings private:

```bash
python3 scripts/run_visual_evals.py \
  --mode blind-pack \
  --cases evals/design-cases \
  --baseline-results evals/results/visual/baseline \
  --workbench-results evals/results/visual/workbench \
  --blind-root evals/results/visual/blind
```

Give judges only `evals/results/visual/blind/packets/`, never `private-mappings/`. After at least three independent provenance-bound judgments per trial, aggregate pairwise `A`, `B`, `tie`, or `not-judgeable` verdicts for specificity, hierarchy, UX correctness, UI-DNA preservation, responsiveness, and genericness:

```bash
python3 scripts/run_visual_evals.py \
  --mode visual-paired \
  --cases evals/design-cases \
  --baseline-results evals/results/visual/baseline \
  --workbench-results evals/results/visual/workbench \
  --blind-root evals/results/visual/blind \
  --judgments evals/results/visual/judgments \
  --scorecard evals/results/visual/scorecard.json
```

The visual scorecard reports raw preferences and disagreement, never a synthetic `3/5` or a causal-uplift claim. Hashing proves byte integrity, not semantic authenticity; screenshots do not prove hidden interaction behavior. Raw traces, results, packets, mappings, judgments, scorecards, and generated images remain ignored under `evals/results/`; only cases, sanitized fixture manifests, schemas, and rubrics belong in the package.

Release validation also requires a clean checkout, installed-cache verification, a real new-task smoke test, an immutable tag, and a tested rollback target.

## License

MIT. See [LICENSE](LICENSE).
