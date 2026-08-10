# Copy audit, validation, and reporting

Use this reference to keep the review proportional and to distinguish new work from pre-existing findings.

## Evidence collection

Start with the requested flow and affected files. Use repository history or the current diff when available to determine provenance, while preserving unrelated user changes.

Search likely rendered sources, including:

- components, templates, formatters, and view models;
- localization catalogs and fallback locale behavior;
- validation schemas and form libraries;
- notifications, dialogs, toasts, tables, filters, and empty states;
- accessibility names and descriptions;
- API error adapters and server-generated structured content;
- persisted or legacy text transformed before rendering;
- mobile, responsive, admin, or secondary routes touched by the same feature.

Do not scan the entire repository by default. Expand only when a shared key, formatter, generator, or contract can affect the requested surface.

## Provenance ledger

Maintain a small ledger while working:

| Finding | Surface | Provenance | Action | Verification |
| --- | --- | --- | --- | --- |
| User-relevant description | File, locale, or state | Current task / pre-existing / uncertain | Fixed / retained with reason / reported | Source / test / rendered flow |

When provenance is uncertain, label it uncertain rather than claiming the task introduced it.

## Fix policy

For current-task violations during authorized implementation:

- correction is mandatory before handoff;
- update every affected locale and state;
- update assertions, snapshots, fixtures, and documentation that encode the copy;
- validate the actual source of server-generated text.

For pre-existing violations encountered during normal inspection:

- report them in a separate section even when fixed;
- fix them when they are on the affected surface and the change is safe and authorized;
- leave unrelated, ambiguous, or contract-dependent findings untouched and state why;
- do not mix them into the current-task change summary as though newly introduced.

For read-only requests, never edit either category; report evidence and suggested wording.

## Validation ladder

Use the highest available proof appropriate to the change:

1. inspect the final diff for user-visible strings;
2. search affected locale and generated-copy paths;
3. run focused unit, localization, validation, or snapshot tests;
4. build or type-check when the change affects integration;
5. reproduce the exact UI flow, including error and recovery states;
6. verify live or production behavior only when deployment and external verification were requested and performed.

State which level was actually reached. Source inspection is not rendered proof, and local rendering is not production proof.

## Handoff format

Use concise sections only when relevant:

```text
CURRENT-TASK COPY
- What changed, why it is user-facing, and how it was verified.

PRE-EXISTING COPY FINDINGS
- Location, issue, fixed or not, and reason. Say “None encountered” only if the affected sources were inspected.

BACKEND CONTRACT
- In scope / out of scope. List contract changes or confirm that backend was not modified.

PENDING OR UNVERIFIED
- Residual contract limits, states not rendered, locales not verified, or follow-up work.
```

Never omit a pre-existing finding merely because it was fixed opportunistically.
