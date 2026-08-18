# Frontend Workbench

An extensible Agent Plugin for complete, project-aligned frontend product work.

Repository: <https://github.com/akenoowww/frontend-workbench>

Frontend Workbench keeps six responsibilities separate: information architecture, product design, implementation fit, user-facing copy, ImageGen art direction, and rendered QA. It uses a typed coverage contract for multi-page work and an ignored `.frontend-workbench/` runtime workspace so prompts, mockups, screenshots, and design ledgers do not pollute product source.

## Bundled skills

| Skill | Use it for | Do not use it for |
| --- | --- | --- |
| `frontend-information-architecture` | Sitemap, routes, page families, navigation edges, flow steps, content/action ownership, and structural coverage | Visual styling, component implementation, copy polish, ImageGen, or runtime QA |
| `frontend-product-design` | Explicit UI/UX interaction and visual decisions, redesign, new-surface design, or critique after structure is known | Sitemap-only work, fully specified implementation, small CSS/copy fixes, bugs, tests, performance, or backend work |
| `frontend-project-fit` | Authorized frontend implementation through the host project's architecture, reusable UI, and justified capability choices | Design-only work, backend-only work, or claims of project fit without source access |
| `frontend-copy-guard` | Affected user-visible copy, localization, accessibility wording, validation, errors, and safe cross-layer mappings | Unrelated repository-wide copy audits or unauthorized backend changes |
| `art-direct-imagegen` | ImageGen deliverables whose visual direction is still open, including coherent page/state sets | Generic UI planning, code implementation, fixed surgical edits, or tasks that do not require generated bitmap output |
| `frontend-runtime-qa` | Rendered page identity, console health, interactions, responsive layout, accessibility, and design fidelity | Design-only planning, source-only review, backend-only testing, implementation, or image generation |

Codex may display plugin skills with names such as `frontend-workbench:frontend-product-design`. Use the skill picker or the exact name shown by the host for explicit invocation. Ordinary prompts can rely on the narrow skill descriptions.

## Responsibility flow

```text
explicit design request
-> frontend-information-architecture when site/flow structure is new or changing
-> frontend-product-design
   -> frontend-copy-guard when the design authors user-visible labels or claims
   -> art-direct-imagegen only when ImageGen materially helps
   -> frontend-project-fit only when implementation is authorized
      -> frontend-copy-guard when visible copy changes
      -> frontend-runtime-qa after visible implementation

direct implementation request
-> frontend-project-fit
   -> frontend-copy-guard when needed
   -> frontend-runtime-qa for rendered proof
```

The graph is one-way. No skill invokes an earlier skill back. Agent Plugins do not provide a portable cross-skill dependency graph, so each skill includes a small truthful fallback when a host cannot compose another bundled workflow.

## Multi-page and multi-state coverage

A website is not treated as one master screenshot. `frontend-information-architecture` records separate entities for:

```text
site -> surface/page family -> page/route -> state -> viewport -> scroll position -> output
```

Each required output has a stable ID, evidence target, dependency, approval policy, and status. Named pages cannot disappear into a homepage, and a page is never confused with a state, breakpoint, scroll position, or bitmap output.

Structurally equivalent dynamic routes may share a representative page-family output unless the user explicitly requests every page separately. A unique user job, hierarchy, composition, or interaction requires its own output.

## ImageGen is optional, but complete when selected

Product design chooses the lightest artifact that can test a material decision:

- annotated specification;
- existing-component composition;
- runnable prototype;
- browser screenshot;
- ImageGen concept.

When ImageGen is selected, `art-direct-imagegen` receives the frozen authority and coverage contract. It renders one dependency-ready output at a time, accepts or retries that output, saves the accepted anchor, and continues until every required output is accepted, explicitly deferred, or truthfully blocked.

An accepted homepage never completes a multi-page request. Dependent UI renders remain sequential to preserve one visual system; independent research can still run in parallel.

When the user asks to review every stage or page separately, the reviewed output enters `awaiting-approval`. The runtime blocks all later outputs until explicit approval changes it to `accepted`; conversational intent alone cannot bypass the checkpoint.

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
        ├── art-direct-imagegen/
        ├── qa/
        └── tmp/
```

Before writing an artifact, the runtime helper verifies that the exact directory is ignored and atomically installs the staged structure and coverage contracts with `state.json`. Skills never pre-create or hand-edit a canonical session. The shared repository rule is:

```gitignore
/.frontend-workbench/
```

The workspace is not created for read-only work by default. Read-only screenshots or traces use task-scoped temporary storage; an existing ignored runtime session may be reused only when the user explicitly requests durable evidence, without changing repository metadata. When a local project cannot safely host runtime state, the workflow uses an allowed task-scoped temporary directory or keeps a compact record in the conversation and reports the limitation.

The hidden workspace supports resume after ordinary task changes and context compaction. It is local ignored state, not a backup: destructive cleanup such as `git clean -fdx`, workspace deletion, or disk loss can remove it.

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
├── scripts/
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

For the current development branch:

```bash
codex plugin marketplace add akenoowww/frontend-workbench --ref main
codex plugin add frontend-workbench@frontend-workbench
codex plugin list
```

For a first install after an immutable release tag exists, prefer the pinned form:

```bash
codex plugin marketplace add akenoowww/frontend-workbench --ref v0.5.0
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
```

Validation covers manifest synchronization, JSON schemas, skill metadata, prompt lengths, Markdown links, runtime-state transitions, multi-page completion, path containment, ignored-workspace hygiene, and unapproved generated artifacts.

Behavioral evals must include direct, indirect, negative, and boundary prompts. Raw model traces and generated eval images stay outside Git; only cases, fixtures, schemas, rubrics, and compact expected results belong in the repository.

Release validation also requires a clean checkout, installed-cache verification, a real new-task smoke test, an immutable tag, and a tested rollback target.

## License

MIT. See [LICENSE](LICENSE).
