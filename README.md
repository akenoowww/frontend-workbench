# Frontend Workbench

An extensible [Agent Plugin](https://agent-plugins.org/) for project-aligned frontend workflows.

Repository: <https://github.com/akenoowww/frontend-workbench>

The plugin is a container of composable frontend skills rather than one universal design prompt. Two cross-cutting guards cover implementation fit and user-facing copy. The full product-design workflow still runs only when the user explicitly asks for design judgment. Future frontend concerns can be added as independent siblings under `skills/`.

## Bundled skills

| Skill | Use it for | Do not use it for |
| --- | --- | --- |
| `$frontend-project-fit` | Any frontend implementation in an existing project: inspect its architecture and reuse compatible components, widgets, styles, tokens, utilities, and data/state patterns before creating anything new | Work with no frontend implementation, repository-wide migrations that were not requested, or claims of project fit when the project is unavailable |
| `$frontend-copy-guard` | Any frontend or backend work that creates, changes, renders, or encounters user-visible interface copy, including labels, validation, errors, statuses, accessibility text, localization, and server-generated messages shown in the UI | Tasks with no user-visible text, or an unsolicited whole-repository content audit |
| `$frontend-product-design` | Explicit UI/UX design or redesign, including calibration of the target zone, redesign intensity, relationship to the current design system, component-change permissions, information architecture, interaction design, visual direction, and critique | Ordinary frontend coding, implementing a complete supplied design, small CSS/copy changes, tests, refactors, performance, or backend work |
| `$art-direct-imagegen` | Concept-first visual art direction, coherent multi-state imagery, and reviewed image-generation handoff | Fixed surgical image edits or tasks whose visual solution is already fully specified |

The skills compose by scope:

- ordinary frontend implementation uses `$frontend-project-fit`;
- implementation that affects user-visible text also uses `$frontend-copy-guard`;
- an explicit design question adds `$frontend-product-design`;
- a resolved visual brief may invoke `$art-direct-imagegen`.

Agent Plugins 1.0 does not define a portable dependency graph or cross-skill invocation protocol, so each skill states its handoff explicitly and reports when a host cannot perform another bundled invocation.

## Cross-cutting implementation guards

### Project architecture and reuse

Before frontend code or design is produced in an existing repository, the workflow traces the affected route and inspects similar surfaces, module boundaries, shared components and widgets, styling and tokens, state/data patterns, localization, accessibility helpers, and tests.

If a project component, style, utility, or pattern can satisfy the requirement directly or through a coherent extension, it must be reused. A new primitive is allowed only after an evidence-backed search identifies why existing candidates do not fit semantically, behaviorally, architecturally, or accessibly. Convenience and personal framework preference are not sufficient reasons to create a parallel solution.

### User-facing copy

Any interface text written or changed during the task must use clear product language. It must not require the user to understand raw UUIDs, database fields, enum keys, API paths, stack traces, ranking formulas, private thresholds, or unnecessary workflow mechanics. Material pricing, eligibility, consent, destructive-action, and safety facts remain visible in plain language.

The guard reviews both the current diff and user-visible text encountered during normal inspection of any task-relevant file. Pre-existing violations are reported separately, even if fixed.

When a new copy problem exposes a technical contract and backend work is already authorized in the current session, the implementation is fixed end to end: the user receives domain options or text instead of an opaque technical input, the server resolves and validates it, and errors become stable product states. If backend is outside the current session scope, backend remains untouched; the frontend copy and any safe existing mapping are corrected, and an unavoidable contract limitation is reported rather than disguised.

## Design workflow boundary

The full workflow is:

```text
explicit design request
-> project archaeology and PROJECT UI DNA
-> for redesign: target zone, baseline, intensity, system strategy, and component-change mode
-> feature model
-> atomic UX decisions
-> decision-specific research
-> interaction and state models
-> visual specification
-> art-direct-imagegen master and derived states
-> visual review
-> implementation gate
-> implementation only when requested
-> technical, product, visual, responsive, and accessibility validation
```

### Redesign calibration

“Redesign” never defaults automatically to “replace the whole page.” After project archaeology, the design skill creates a `REDESIGN CONTRACT` before external research, image generation, or implementation.

The contract defines four independent axes:

- **Zone:** element, component, section, page, flow, application shell, or whole frontend/design system, including relevant states, breakpoints, adjacent effects, and exclusions.
- **Intensity:** an overall 0–100% permission boundary plus a dimension profile for tokens, layout, component composition, interaction, information architecture, and content/state coverage.
- **System strategy:** `EVOLVE CURRENT SYSTEM` or `REDEFINE STRUCTURE`.
- **Component mode:** `PRESERVE AND ADJUST`, `SELECTIVELY DECOMPOSE`, or `REPLACE AND REIMAGINE`.

Default intensity bands:

| Intensity | Meaning |
| --- | --- |
| 0–20% | Token/style refresh while structure and logical components remain |
| 21–45% | Layout refinement: reposition, resize, regroup, reorder, or change emphasis while retaining required logical components |
| 46–70% | Selective recomposition: compact, merge, progressively disclose, or omit nonessential subparts without losing required actions, information, states, or recovery |
| 71–100% | Full rethink inside the agreed zone; hierarchy, composition, interaction, or local IA may be replaced while required product behavior, contracts, accessibility, and explicit constraints remain |

A single percentage is not treated as sufficient evidence. For example, a redesign may be 35% overall with a 90% token change and only a 10% structural change. If the target zone is not identifiable from the request, repository, selected files, screenshot, or current runtime surface, the skill asks one concise scope question before continuing. If intensity or system strategy remains materially ambiguous, it asks one combined calibration question.

Even under `REDEFINE STRUCTURE`, the workflow first inspects the project's current architecture, component library, styles, tokens, and reusable foundations. Existing primitives must still be reused when compatible; a full redesign authorizes structural departure within the zone, not arbitrary replacement of application architecture or required capabilities.

Examples that should activate `$frontend-product-design`:

- “Redesign this onboarding flow and then implement the approved direction.”
- “Redesign this dashboard by about 60%: keep the current design system, but compact or remove nonessential component subparts.”
- “Refresh the product color and typography tokens by about 15% without changing layout or interaction.”
- “How should this editor expose version history without losing context?”
- “Design a new account-management page that belongs in this product.”
- “Critique the UX and visual hierarchy of this panel.”

Examples that should not activate it:

- “Fix the broken submit handler.”
- “Implement this complete Figma screen exactly as supplied.”
- “Rename this label and change the button color.”
- “Refactor these React hooks.”
- “Improve bundle performance.”

## Package structure

```text
frontend-workbench/
├── .agents/plugins/
│   └── marketplace.json                # repository-owned Codex marketplace
├── plugin.json                         # portable Agent Plugins 1.0 manifest
├── .codex-plugin/
│   └── plugin.json                     # Codex compatibility metadata
├── LICENSE
├── README.md
└── skills/
    ├── frontend-project-fit/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   └── references/
    ├── frontend-copy-guard/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   └── references/
    ├── frontend-product-design/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   └── references/
    └── art-direct-imagegen/
        ├── SKILL.md
        ├── agents/openai.yaml
        └── references/
```

The portable manifest follows [Agent Plugins 1.0](https://agent-plugins.org/specification). Compatible clients discover only immediate child directories of `skills/` that contain `SKILL.md`; no skill list is maintained in the portable manifest. `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json` are Codex-specific compatibility and installation artifacts, not part of the portable core.

Agent Plugins standardizes package discovery, not installation or enablement. Non-Codex hosts should load this plugin root through the source/local-plugin workflow of a [compatible client](https://agent-plugins.org/compatible-clients).

## Install in Codex

Using the official [Codex plugin CLI flow](https://developers.openai.com/plugins/build/plugins), first register this repository-owned marketplace, then install the plugin:

```bash
codex plugin marketplace add akenoowww/frontend-workbench --ref main
codex plugin add frontend-workbench@frontend-workbench
```

Verify the installed and enabled state:

```bash
codex plugin list
```

Start a new Codex session after installation so skill discovery uses the updated package.

## Runtime capabilities

The package contains instructions and references only. It has no MCP server, hook, executable script, bundled binary, credential, or remote endpoint.

Depending on the request, the design workflow benefits from:

- repository and runtime access for project archaeology;
- browser or web access for current decision-specific UX research;
- an image-generation-capable host for the rendering stage.

Without image generation, the workflow can still complete product research, UX decisions, interaction and state models, and a renderer-ready visual handoff. It must report the skipped rendering and visual-review proof. For a full-track design-and-implementation request, production UI edits remain blocked until that visual gate runs.

## Extending the plugin

Add each future frontend concern as a new immediate child:

```text
skills/<focused-skill-name>/SKILL.md
```

Keep each skill independently valid and give it an activation description that states both positive triggers and important exclusions. A cross-cutting guard may apply broadly only when its responsibility is precise; a specialized workflow such as product design must keep a narrow trigger. Reuse another bundled skill through an explicit handoff, while keeping a truthful fallback because portable Agent Plugins do not define skill dependencies.

No root portable-manifest change is required when adding another skill.

## Art-direct migration and duplicate names

The bundled `art-direct-imagegen` subtree is copied from the standalone skill at source commit `b9357628f874b2ef1a60e578636890841dc02027`. The standalone repositories remain untouched during this merge.

Do not enable both this plugin and the standalone `art-direct-imagegen` plugin in the same client unless that client documents deterministic handling of duplicate skill names. Agent Plugins 1.0 does not define collision resolution across installed plugins.

After verifying this plugin in Codex, remove a previously installed standalone copy if it is registered as `art-direct-imagegen@personal`:

```bash
codex plugin remove art-direct-imagegen@personal
```

## Validation

Validate each skill:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  ./skills/frontend-project-fit

python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  ./skills/frontend-copy-guard

python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  ./skills/frontend-product-design

python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  ./skills/art-direct-imagegen
```

Validate Codex compatibility metadata when the system plugin tools are available:

```bash
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Release checks should also validate root `plugin.json` against the [canonical schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), resolve all local Markdown links, compare the migrated art-direct subtree with its source, reject symlinks that escape the package, and scan for credentials or private project artifacts.

## License

MIT. See [LICENSE](LICENSE).
