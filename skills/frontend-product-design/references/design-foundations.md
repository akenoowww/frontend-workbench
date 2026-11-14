# Composition, color and typography

Use for open or materially changed visual decisions. Start from authorized scope, existing design tokens, the user's brand and the primary task. Keep an established treatment when it supports that task. Compare alternatives only where the choice has a visible consequence.

## Compose for the work

Name what the user should notice first and what they need in view to act. Check the first viewport with representative real-length content. Compare a contained measure, use of the available work area, or an adjacent panel only when each can serve the job. Judge row scan distance, visible useful content, and whether related context stays available. Base global navigation on actual destinations and their priority.

Consider the controls together. A visible group suits frequent switching and comparison at a glance. A compact selection can make room for other needed filters. Evaluate both on the smallest relevant width when the trade-off matters. Distinguish a display-only fact from an affordance to change it. If a common task requires a missing control, record the gap and check authorization before adding it. Define whether details interrupt or coexist with the source view and preserve required position, focus, and selections on return.

## Choose a palette by role

Preserve authorized project or brand tokens. Use the bundled [palette selection workflow](palette-selection.md) for open UI color roles. Compare candidates on the same content and hierarchy. Assign page and raised surfaces, primary and muted text, separators, action and selected states, focus, and applicable semantic statuses. Check required states and themes on their actual backgrounds and use labels or other non-color cues for status.

## Choose typography by hierarchy

Use the project type system or compare plausible families with the needed language coverage, glyphs, weights and numeral behavior. Judge how headings, controls and data read together at actual scale. Specify roles for page and section titles, primary content, control labels and secondary metadata as applicable. Set relative size, weight, line height and spacing to serve the reading order. Keep a title compact when users spend most of their time comparing records. Give the title more visual weight when orientation or a deliberate editorial entrance is the primary job.

Review the longest realistic labels, names, values and text in the supported languages. Check readable rows and controls at wide and narrow sizes, with user zoom or text scaling where relevant. For repeated numeric comparisons, consider right alignment and tabular numerals. Verify that text remains distinguishable when color is removed and that the layout survives fallback fonts.

Record the selected palette and type roles, one credible alternative where the foundations were open, and what changed the choice. Pass visible roles into the existing `VisualDirectionContract`. Implementation resolves compatible token names and CSS mechanisms.
