# Web platform guidance

Product Design runs its [required MWG stage](../../frontend-product-design/references/mwg-design-stage.md) before settling a web design. Project Fit reuses that evidence and consults MWG for new platform decisions that can change a user outcome. Start with required behavior, the existing component or framework owner, and the supported browsers. Check the project's support policy or Browserslist where present, including explicit WebView or older-browser targets. Otherwise use Baseline Widely available.

## Find guidance

Run every Modern Web Guidance CLI call through [the Workbench launcher](../../../scripts/run_mwg.py), including version checks, retries, and fallback lookups. The launcher always sets `DISABLE_TELEMETRY=1` for the child command. Use it in place of any direct CLI or `npx` examples from upstream.

Run from the product root so its browser policy can apply. Replace `<plugin-root>` with the root of the Workbench plugin containing this reference. Search for one generic capability in English. Leave out project names, local paths, and user data. Set `guide_id` to the selected result and `guide_path` to a file in an authorized scratch directory.

```bash
python3 "<plugin-root>/scripts/run_mwg.py" search "modal dialog focus restoration"
python3 "<plugin-root>/scripts/run_mwg.py" retrieve "$guide_id" > "$guide_path"
python3 "<plugin-root>/scripts/run_mwg.py" version
```

The launcher uses an existing project or PATH CLI first. Its `npx` fallback prefers the cache and can download the pinned `modern-web-guidance@1.0.0` package from npm. That version requires Node.js 22 or newer. Pass `--offline` before the subcommand when registry access is unavailable or disallowed. If the launcher cannot run, read full guides in the installed official plugin or the [official v1.0.0 catalog](https://github.com/GoogleChrome/modern-web-guidance/tree/v1.0.0/skills/modern-web-guidance/guides).

If results are weak, rephrase once with a concrete UI or platform term. Use `python3 "<plugin-root>/scripts/run_mwg.py" list` for a broad lookup. Record the actual CLI version or official source ref consulted. Label any primary platform documentation used to fill a gap separately.

## Apply the relevant part

Read the selected guide's interaction requirements, browser support, and fallback guidance. Check that the proposed primitive fits the required outcomes and support policy. Prefer the project's compatible existing owner when it covers those outcomes. Reuse a guide already retrieved for this decision when the browser target and capability still match.

Record the guide ID or primary source, the browser target when material, the resulting decision, and the observable check in the existing rationale, handoff, or capability plan. For a design handoff, carry the visible state and user-facing consequences into its existing content and interaction decisions. Product Design owns hierarchy and visual direction. Art-Direct ImageGen receives the visual expression of the applicable state.

## Review legacy patterns when requested

For an authorized broad modernization audit, run `python3 "<plugin-root>/scripts/run_mwg.py" legacy-scan "<frontend-path>" --json` on the scoped source path. Check the candidates against their `keepWhen` and `dropWhen` rubrics and the surrounding code. Keep intentional compatibility behavior and retrieve the relevant guide before proposing a replacement. The scanner covers the patterns listed by its active rules. An authorized change still needs the project's normal behavior and browser checks.
