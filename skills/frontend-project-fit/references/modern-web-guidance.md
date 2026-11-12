# Web platform guidance

Use Modern Web Guidance for a concrete platform decision that can change a user outcome. Start with the product's required behavior, its existing component or framework owner, and its supported browsers. Read the relevant support policy or Browserslist when present. In the absence of a project target, use the guides' Baseline Widely available default. Check explicit WebView or older-browser targets individually.

## Find guidance

Use the project-pinned or already available `modern-web-guidance` CLI from the product root so its browser policy can apply. Search for a single generic capability in English. Set `guide_id` to the selected result and `guide_path` to a file in an authorized scratch directory. Redirect retrieval there to keep long guides in scope.

```bash
DISABLE_TELEMETRY=1 modern-web-guidance search "modal dialog focus restoration"
DISABLE_TELEMETRY=1 modern-web-guidance retrieve "$guide_id" > "$guide_path"
```

When the command is absent and registry access is available, use the published CLI with `DISABLE_TELEMETRY=1 npx --yes modern-web-guidance@1.0.0` followed by the same subcommand. This version requires Node.js 22 or newer. Keep queries to generic web capabilities. If results are weak, rephrase once with a concrete UI or platform term. If a lookup is unavailable or still misses the case, check the corresponding primary platform documentation and carry on with the evidence available.

## Apply the relevant part

Read the selected guide's interaction requirements, browser support, and fallback guidance. Check that the proposed primitive fits the required outcomes and support policy. Prefer the project's compatible existing owner when it covers those outcomes. Reuse a guide already retrieved for this decision when the browser target and capability still match.

Record the guide ID or primary source, the browser target when material, the resulting decision, and the observable check in the existing rationale, handoff, or capability plan. For a design handoff, carry the visible state and user-facing consequences into its existing content and interaction decisions. Product Design owns hierarchy and visual direction. Art-Direct ImageGen receives the visual expression of the applicable state.

## Review legacy patterns when requested

For an authorized broad modernization audit, run `legacy-scan <frontend-path> --json` with the same CLI on the scoped source path. Check the candidates against their `keepWhen` and `dropWhen` rubrics and the surrounding code. Keep intentional compatibility behavior and retrieve the relevant guide before proposing a replacement. The scanner covers the patterns listed by its active rules. An authorized change still needs the project's normal behavior and browser checks.
