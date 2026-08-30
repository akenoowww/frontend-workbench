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
type OperationalMetadataAuthority =
  | "user-request"
  | "product-requirement"
  | "approved-design"
  | "legal-safety";

interface AcceptedDesignEvidence {
  outputId: string;
  artifactRef: string;
  artifactSha256: string;
  visualDirectionSha256: string | null;
  anchorOutputId: string | null;
  anchorArtifactSha256: string | null;
  anchorPreserve: string[];
  anchorChangeOnly: string[];
}

interface AuthorityReceiptBinding {
  path: string;
  sha256: string;
  sourceRef: string;
  messageSha256: string;
  authorizedActions: string[];
}

interface FrozenDesignHandoff {
  schemaVersion: 3;
  authority: DesignAuthority;
  checkpointMode: CheckpointMode;
  productIntentSha256: string;
  fullContractSha256: string;
  structureRef: string;
  structureSha256: string;
  coverageRef: string;
  coverageSha256: string;
  productModelRootObjectId: string;
  protectedCapabilities: string[];
  capabilityRequirementIds: string[];
  shellIds: string[];
  referenceBindingIds: string[];
  operationalMetadataPolicy: {
    defaultVisibility: "hidden-unless-required";
    requiredClaims: Array<{
      id: string;
      surfaceId: string;
      states: string[];
      meaning: string;
      authority: OperationalMetadataAuthority;
      sourceRef: string;
    }>;
  };
  visualDirectionPolicy: "required" | "not-required";
  visualDirectionRef: string | null;
  visualDirectionSha256: string | null;
  visualArtifactPolicy: "runnable" | "imagegen-required" | "no-imagegen";
  requestedOutcome: string;
  targetZone: string[];
  exclusions: string[];
  designEvidenceOutputIds: string[];
  runtimeEvidenceOutputIds: string[];
  renderBudget?: {
    maxCallsTotal: number;
    maxAttemptsPerOutput: number;
    maxConceptResets: number;
  };
  renderUsage: {
    callsTotal: number;
    conceptResets: number;
    attemptsByOutput: Record<string, number>;
  };
  selectedDecisions: string[];
  protectedBehavior: string[];
  acceptedDesignEvidence: AcceptedDesignEvidence[];
  permittedImplementationAdaptations: string[];
  implementationPlanRef?: string;
  implementationPlanSha256?: string;
  authorityReceipts: AuthorityReceiptBinding[];
  changeControl?: {
    baseContractSha256: string;
    baseStructureSha256: string;
    baseCoverageSha256: string;
    proposedDeltaSha256: string;
    resultingContractSha256: string;
    resultingStructureSha256: string;
    resultingCoverageSha256: string;
    authorityReceiptSha256: string;
  };
  requiredCopyOrTerminology: string[];
  unresolved: string[];
  blockedOrDeferred: string[];
}
~~~

Reference workspace-relative structure, coverage, implementation-plan when authorized, and visual-direction files instead of pasting large records into the handoff. Consume product-model, shell, reference-binding, evidence, and operational-metadata identities from the validated compact runtime handoff; do not reconstruct them from chat. When direction is required, use the canonical `product-design/visual-direction.json` reference and helper-verified SHA. Keep exact copy, scoped source links, and visual artifacts close to the decision they support.

## Separate fixed decisions from implementation freedom

Freeze:

- the confirmed product-object hierarchy, protected capabilities, domain/scenario trace, and nested shell ownership;
- user and product capabilities that must survive;
- target page, surface, state, and viewport coverage;
- selected hierarchy, interaction, navigation, and feedback decisions;
- the locked renderer-neutral visual direction and intentional project-DNA departures;
- explicit redesign removals or replacements;
- accessibility, localization, safety, and recovery requirements;
- representative design evidence that was actually reviewed, separately from runtime outputs still requiring QA;
- scoped reference bindings, anchor output/artifact SHAs and preserve/change-only requirements, and remaining render budget.

Leave implementation free to choose project-compatible file boundaries, component composition, supported variants, state ownership, renderer, capability owner, and technical mechanisms through **$frontend-project-fit**, provided those choices do not change the frozen product behavior or locked visual direction. Product specificity does not require bespoke controls: reuse, extend, or compose mature project/internal/framework/library capabilities whenever they satisfy the frozen semantics.

Pass the direction reference/SHA, accepted artifact IDs/SHAs, required routes, states, and viewports to **$frontend-runtime-qa** after visible implementation so rendered proof can be checked against the same frozen contracts.

A local adaptation does not reopen design when it preserves the user job, product-object priority, nested shells, hierarchy, behavior, coverage, locked direction, and constraints. A material contradiction does reopen design when implementation would otherwise remove or demote a protected capability, change shell ownership or interaction, broaden a reference, invent unsupported behavior, exceed the redesign zone, violate the direction contract, require unjustified custom capability ownership, or invalidate accepted evidence.

Any material relaxation or replacement requires a fresh authority receipt plus change-control record bound to the base digest, canonical proposed delta, resulting digest, exact action, and user turn. An old or pre-change-only receipt, generic approval, or boolean authorization cannot approve a changed product model, reduced evidence, broader reference, replacement anchor, larger render budget, or different implementation scope.

## Enforce the checkpoint

Under **continuous**, hand the frozen contract to implementation as soon as the design gate passes and any required direction lock is current.

Under **review-each-stage**, preserve every accepted checkpoint and pending output ID. Approval of one page or state authorizes only the next declared stage, not the rest of the manifest.

Under **review-before-implementation**, present the locked direction, coverage, reviewed artifact evidence, and unresolved risks, then wait for explicit approval. Do not represent direction lock or a prepared handoff as authorized implementation.

For a material redesign, use **review-before-implementation** unless the user chose a stricter staged review. When `visualArtifactPolicy` is `imagegen-required`, use **review-each-stage** or **review-before-implementation**, mark every output with required design evidence approval-required, and preserve its user-authorized acceptance in the active FULL session. Runtime-only outputs remain separate QA obligations.

Design-only and critique-only work ends with the requested artifact or recommendation. It never grants production-code authority.

## Store and report

When a durable file is useful, write it inside the active product-design run directory as **design-handoff.md** and record the locked visual-direction reference/SHA plus linked artifacts. Keep using the same FULL lifecycle session; pass the helper's compact `handoff` output to downstream agents instead of copying runtime state or chat history. Do not place the handoff in the repository root or promote it into project documentation unless the user requested that deliverable.

At completion, report only:

- the decision and scope resolved;
- runtime coverage and accepted design evidence as distinct sets;
- implementation authority and checkpoint state;
- blocked, deferred, unsupported, or unverified items;
- durable artifacts retained or promoted.

Do not call generated imagery implemented UI, local validation production proof, or a deferred output complete.
