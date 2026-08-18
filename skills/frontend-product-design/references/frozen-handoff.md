# Frozen design handoff

Use this reference before implementation begins or when the user requests a durable design handoff.

## Freeze the authorized contract

Create the smallest complete handoff:

~~~ts
type DesignAuthority = "design-only" | "critique-only" | "design-and-implementation";
type CheckpointMode =
  | "continuous"
  | "review-before-artifact"
  | "review-each-stage"
  | "review-before-implementation";

interface FrozenDesignHandoff {
  authority: DesignAuthority;
  checkpointMode: CheckpointMode;
  requestedOutcome: string;
  targetZone: string[];
  exclusions: string[];
  coverageRecord: string;
  selectedDecisions: string[];
  protectedBehavior: string[];
  acceptedEvidence: string[];
  permittedImplementationAdaptations: string[];
  requiredCopyOrTerminology: string[];
  unresolved: string[];
  blockedOrDeferred: string[];
}
~~~

Reference a workspace-relative coverage file instead of pasting a large record into the handoff. Keep exact copy, source links, or visual artifacts close to the decision they support.

## Separate fixed decisions from implementation freedom

Freeze:

- user and product capabilities that must survive;
- target page, surface, state, and viewport coverage;
- selected hierarchy, interaction, navigation, and feedback decisions;
- explicit redesign removals or replacements;
- accessibility, localization, safety, and recovery requirements;
- artifact evidence that was actually reviewed.

Leave implementation free to choose project-compatible file boundaries, component composition, supported variants, state ownership, and technical mechanisms through **$frontend-project-fit**, provided those choices do not change the frozen product behavior.

Pass accepted artifact IDs, required routes, states, and viewports to **$frontend-runtime-qa** after visible implementation so rendered proof can be checked against the same frozen contract.

A local adaptation does not reopen design when it preserves the user job, hierarchy, behavior, coverage, and constraints. A material contradiction does reopen design when implementation would otherwise remove a required capability, change the interaction contract, invent unsupported behavior, exceed the redesign zone, or invalidate accepted evidence.

## Enforce the checkpoint

Under **continuous**, hand the frozen contract to implementation as soon as the design gate passes.

Under **review-each-stage**, preserve every accepted checkpoint and pending output ID. Approval of one page or state authorizes only the next declared stage, not the rest of the manifest.

Under **review-before-implementation**, present the selected direction, coverage, evidence, and unresolved risks, then wait for explicit approval. Do not represent a prepared handoff as authorized implementation.

Design-only and critique-only work ends with the requested artifact or recommendation. It never grants production-code authority.

## Store and report

When a durable file is useful, write it inside the active product-design run directory as **design-handoff.md** and record any linked artifacts. Do not place it in the repository root or promote it into project documentation unless the user requested that deliverable.

At completion, report only:

- the decision and scope resolved;
- coverage and artifact evidence;
- implementation authority and checkpoint state;
- blocked, deferred, unsupported, or unverified items;
- durable artifacts retained or promoted.

Do not call generated imagery implemented UI, local validation production proof, or a deferred output complete.
