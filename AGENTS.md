# Frontend Workbench contributor rules

- Do not copy user-level instructions, chat memory, private preferences, or environment-only policy into repository files unless the user explicitly asks to make that policy part of the project.
- Keep runtime state under `/.frontend-workbench/` in the host repository. Never write design reports, model traces, or generated images beside product files unless the user names that destination.
- Require the exact root `.gitignore` entry `/.frontend-workbench/` before creating runtime state. For an authorized artifact-producing task, add only that exact line while preserving the file, then verify it with `git check-ignore`. For read-only work, use conversation evidence or task-scoped temporary storage; reuse an existing ignored runtime session only when the user explicitly requested durable evidence, and never modify repository metadata for read-only QA.
- Treat `.frontend-workbench/`, `evals/results/`, raw model output, and generated review images as untracked runtime material. Never include them in the plugin archive.
- Keep `plugin.json` and `.codex-plugin/plugin.json` names and versions synchronized. Tagged releases must use an immutable marketplace ref matching the version tag.
- Add detailed workflow guidance only to an existing `SKILL.md` or its `references/` directory. Do not add auxiliary README or changelog files inside a skill.
- Preserve user files and unrelated worktree changes. Runtime cleanup must target one validated session ID and must never use a broad repository path.
- Before handoff, run `python3 -m unittest discover -s tests -v` and `python3 scripts/validate_repo.py .`. Run `python3 scripts/run_evals.py --mode fixtures --cases evals/cases` when eval fixtures change; fixture validation must never be described as model-behavior scoring.
