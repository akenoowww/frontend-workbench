# Frontend Workbench

An extensible [Agent Plugin](https://agent-plugins.org/) for focused frontend workflows.

Repository: <https://github.com/akenoowww/frontend-workbench>

The plugin is intentionally a container of narrowly triggered skills, not one universal frontend prompt. Its first design workflow runs only when the user explicitly asks for design judgment; ordinary implementation, bug-fixing, testing, refactoring, and performance work remain outside that skill. Future frontend concerns can be added as independent siblings under `skills/`.

## Bundled skills

| Skill | Use it for | Do not use it for |
| --- | --- | --- |
| `$frontend-product-design` | Explicit UI/UX design or redesign, information architecture, interaction design, visual direction, design critique, or a substantial frontend surface whose structure must be designed | Ordinary frontend coding, implementing a complete supplied design, small CSS/copy changes, tests, refactors, performance, or backend work |
| `$art-direct-imagegen` | Concept-first visual art direction, coherent multi-state imagery, and reviewed image-generation handoff | Fixed surgical image edits or tasks whose visual solution is already fully specified |

`frontend-product-design` may hand a resolved visual specification to the bundled `art-direct-imagegen` skill. Agent Plugins 1.0 does not define a portable dependency graph or cross-skill invocation protocol, so the frontend skill also produces a complete visual handoff and reports when a host cannot perform that invocation.

## Design workflow boundary

The full workflow is:

```text
explicit design request
-> project archaeology and PROJECT UI DNA
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

Examples that should activate `$frontend-product-design`:

- “Redesign this onboarding flow and then implement the approved direction.”
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
├── plugin.json                         # portable Agent Plugins 1.0 manifest
├── .codex-plugin/
│   └── plugin.json                     # Codex compatibility metadata
├── LICENSE
├── README.md
└── skills/
    ├── frontend-product-design/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml
    │   └── references/
    └── art-direct-imagegen/
        ├── SKILL.md
        ├── agents/openai.yaml
        └── references/
```

The portable manifest follows [Agent Plugins 1.0](https://agent-plugins.org/specification). Compatible clients discover only immediate child directories of `skills/` that contain `SKILL.md`; no skill list is maintained in the portable manifest. `.codex-plugin/plugin.json` is a Codex-specific compatibility artifact and is not part of the portable core.

Agent Plugins standardizes package discovery, not installation or enablement. Load this plugin root through the source/local-plugin workflow of a [compatible client](https://agent-plugins.org/compatible-clients).

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

Keep each skill independently valid and give it a narrow activation description that states both positive triggers and important exclusions. Avoid a catch-all `frontend` skill that competes with every other workflow. Reuse another bundled skill through an explicit handoff, while keeping a truthful fallback because portable Agent Plugins do not define skill dependencies.

No root portable-manifest change is required when adding another skill.

## Art-direct migration and duplicate names

The bundled `art-direct-imagegen` subtree is copied from the standalone skill at source commit `b9357628f874b2ef1a60e578636890841dc02027`. The standalone repositories remain untouched during this merge.

Do not enable both this plugin and the standalone `art-direct-imagegen` plugin in the same client unless that client documents deterministic handling of duplicate skill names. Agent Plugins 1.0 does not define collision resolution across installed plugins.

## Validation

Validate each skill:

```bash
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
