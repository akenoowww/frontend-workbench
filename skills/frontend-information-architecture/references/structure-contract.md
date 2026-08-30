# Typed frontend structure contract

Use this reference for a STANDARD/FULL multi-page site, application, or flow. STANDARD applies the structural decision and traceability rules proportionally and persists only the compact handoff another authorized stage needs; it does not manufacture FULL runtime fields, receipts, budgets, or state. FULL v3 separates rich IA structure from the compact runtime coverage contract while binding both by path and SHA.

## Rich v3 structure

Build the smallest task-specific model that preserves the confirmed product. Use stable path-safe IDs; do not copy another product's objects, scenarios, or shell tree.

~~~ts
interface FrontendStructureContractV3 {
  schemaVersion: 3;
  contractId: string;
  surfaces: RichSurface[];
  scenarios: Scenario[];
  shells: Shell[];
  objectBindings: ObjectBinding[];
  referenceBindings: ReferenceBinding[];
}

interface RichSurface {
  id: string;
  route?: string | null;
  scenarioIds: string[];
  domainIds: string[];
}

interface Scenario {
  id: string;
  job: string;
  objectIds: string[];
  entrySurfaceId: string;
  completionSurfaceId: string;
  recoverySurfaceIds: string[];
}

interface Shell {
  id: string;
  parentShellId: string | null;
  slots: string[];
  invariants: string[];
}

interface ObjectBinding {
  id: string;
  surfaceId: string;
  primaryObjectId: string;
  supportingObjectIds: string[];
  forbiddenDominantObjectIds: string[];
}

interface ReferenceBinding {
  id: string;
  sourceRef: string;
  sourceSha256: string | null;
  roles: Array<
    | "functional-reference"
    | "style-reference"
    | "visual-anchor"
    | "edit-target"
    | "constraint"
  >;
  surfaceIds: string[];
  aspects: string[];
  constraints: string[];
  mustNotInfluence: string[];
}
~~~

`structure.json` contains only these rich structural fields. Product intent, product model, policies, capability requirements, compact surfaces, and evidence outputs stay in `coverage.json`; the compact contract carries a `structure` identity with the exact `structure.json` path and SHA.

## Relevant compact v3 coverage

The compact contract preserves the lifecycle and evidence identities needed downstream:

~~~ts
interface CoverageContractV3 {
  schemaVersion: 3;
  contractId: string;
  workflowProfile: "full";
  productIntent: ProductIntent;
  productModel: ProductModel;
  structure: {
    id: string;
    path: "structure.json";
    sha256: string;
  };
  authority: {
    pageStructure: "locked" | "revisable";
    interactionModel: "locked" | "revisable";
    contentRepartition:
      | "within-surface-only"
      | "authorized-across-surfaces";
  };
  visualDirectionPolicy: "required" | "not-required";
  visualArtifactPolicy: "runnable" | "imagegen-required" | "no-imagegen";
  checkpointMode:
    | "continuous"
    | "review-before-artifact"
    | "review-each-stage"
    | "review-before-implementation";
  operationalMetadataPolicy: OperationalMetadataPolicy;
  capabilityRequirements: CapabilityRequirement[];
  surfaces: CoverageSurface[];
  edges: Array<{ from: string; to: string; trigger: string }>;
  outputs: CoverageOutput[];
  implementationTargets: Array<{
    path: string;
    surfaceIds: string[];
    sharedOwner: boolean;
  }>;
  renderBudget?: RenderBudget;
}

type ProductObjectRole =
  | "root"
  | "primary"
  | "supporting"
  | "downstream-evidence"
  | "implementation-detail";
type ArtifactKind =
  | "none"
  | "specification"
  | "runnable"
  | "browser-screenshot"
  | "imagegen";

interface ProductIntent {
  problem: string;
  representativeScenarios: string[];
  requiredDomains: string[];
  protectedCapabilities: string[];
  antiGoals: string[];
  successSignals: string[];
}

interface ProductModel {
  rootObjectId: string;
  objects: Array<{
    id: string;
    role: ProductObjectRole;
    parentId: string | null;
    evidenceForObjectIds: string[];
  }>;
  relations: Array<{
    id: string;
    fromObjectId: string;
    toObjectId: string;
    kind:
      | "contains"
      | "supports"
      | "governs"
      | "evidence-for"
      | "implements"
      | "depends-on"
      | "relates-to";
  }>;
}

interface CapabilityRequirement {
  id: string;
  capability: string;
  complexity: "bounded" | "complex" | "foundational";
  constraints: string[];
  ownerObjectId: string;
  surfaceIds: string[];
  required: boolean;
}

interface CoverageSurface {
  id: string;
  kind: "page" | "screen" | "flow-step" | "overlay";
  route?: string;
  userJob: string;
  primaryObjectId: string;
  shellIds: string[];
  referenceBindingIds: string[];
}

interface CoverageOutput {
  id: string;
  surfaceId: string;
  state: string;
  viewport: string;
  scrollPosition?: string;
  approvalRequired: boolean;
  dependsOn: string[];
  promotionRequired: boolean;
  promotionTarget: string | null;
  designEvidenceRequired: boolean;
  runtimeEvidenceRequired: boolean;
  artifactKind: ArtifactKind;
  anchorOutputId: string | null;
  evidenceEquivalentTo?: string;
  equivalenceJustification?: string;
}

interface RenderBudget {
  maxCallsTotal: number;
  maxAttemptsPerOutput: number;
  maxConceptResets: number;
}

interface OperationalMetadataPolicy {
  defaultVisibility: "hidden-unless-required";
  requiredClaims: Array<{
    id: string;
    surfaceId: string;
    states: string[];
    meaning: string;
    authority:
      | "user-request"
      | "product-requirement"
      | "approved-design"
      | "legal-safety";
    sourceRef: string;
  }>;
}
~~~

V3 lifecycle inclusion is expressed only by `designEvidenceRequired` and `runtimeEvidenceRequired`; do not recreate the legacy overloaded `required` flag. `artifactKind` is `none` when design evidence is not required; a required design artifact must name its real kind. `renderBudget` exists only when an ImageGen artifact is present, is required under `imagegen-required`, and is absent under `no-imagegen`.

## Protect the product model

Derive `productModel` from the current task and repository evidence. The root names the product context. `primary` objects are what users mainly create, inspect, decide, or complete. `supporting` objects enable that work. `downstream-evidence` proves or reports on another object. `implementation-detail` describes a mechanism and must not become product hierarchy.

Treat `objects[].parentId` as the canonical containment hierarchy and `objects[].evidenceForObjectIds` as the canonical evidence ownership. If `relations` also includes `contains` or `evidence-for`, those edges must exactly agree with the canonical object fields; contradictory duplicate graphs are a contract error, not an alternative interpretation.

Direction is fixed: `contains` is parent object → child object, and `evidence-for` is evidence object → served object. Therefore `child.parentId == parent.id` must match `parent -> child`, while `evidence.evidenceForObjectIds` must match `evidence -> served`.

Require one root-role object, make `rootObjectId` point to it, validate unique/reachable acyclic parents and relation endpoints, and prevent `downstream-evidence` or `implementation-detail` from becoming an ancestor of a `primary` object. Each rich `objectBinding.primaryObjectId` must equal the compact surface's `primaryObjectId` for the same surface.

Use `objectBindings` to prevent a visually convenient downstream or implementation object from taking over a surface whose job belongs to a primary object. `evidenceForObjectIds` and `evidence-for` relations state what downstream evidence serves; they do not promote it above its owner.

Protected capabilities are monotonic inside one confirmed lifecycle. Later discovery may add capabilities, but a scenario, reference, design artifact, or implementation constraint may not remove, narrow, rename away, transfer ownership of, visually demote, or reduce the complexity classification of an existing protected capability. Until the schema carries a separate protected-capability ID, each `productIntent.protectedCapabilities` string must match exactly one `capabilityRequirement.capability` with `required: true`; duplicate or approximate matches are blocked. Its requirement ID, complexity, owner object, constraints, and surfaces remain stable. A relaxation is a material contract replacement with fresh authority.

## Trace domain and object to runtime evidence

Audit one continuous chain:

```text
required domain / product object
  -> representative scenario
  -> entry, work, completion, and recovery surfaces
  -> output state
  -> material viewport
  -> runtimeEvidenceRequired output
```

Use each rich surface's `domainIds` and `scenarioIds` to connect confirmed `requiredDomains` and scenarios. A scenario identifies its product objects and entry/completion/recovery surfaces. The compact version of each surface binds its primary object, shell ancestry, references, route, and user job.

Map each `productIntent.representativeScenarios` entry one-to-one to a unique rich `Scenario.id/job` in the confirmed teach-back; duplicate or approximate mappings are blocked. Every scenario's entry, completion, and recovery surfaces must reciprocally list its ID in `scenarioIds`. Compact `edges` must provide a reachable path from entry to completion and to each recovery surface when that recovery is triggered.

`completionSurfaceId` means the surface where the job's question is answered or a stable resumable outcome is reached; it does not require a mutation or wizard-style finish. `recoverySurfaceIds` may be empty only when the scenario has no material failure, blocked, permission, or recovery condition.

The current schemas do not carry separate domain, state, viewport, or page-family registries. Define normalized domain IDs, state triggers, viewport transformations, and page-family reasoning in the confirmed IA handoff, then use those exact strings in rich surfaces and coverage outputs. Treat this as a semantic audit boundary rather than claiming schema-only proof; dangling or ambiguous IDs block the handoff.

Require rich/compact parity before confirmation: both contract IDs and the compact `structure.id` identify the same contract; the compact structure path/SHA matches the exact rich bytes; rich and compact surface ID/route sets agree; each compact `shellIds` and `referenceBindingIds` value resolves in rich structure; each output surface resolves in both; and rich/compact primary-object bindings agree.

Every required domain and protected capability must reach at least one surface that owns its job and at least one runtime-required output. Mention in a dashboard, another domain, or downstream evidence is not coverage. A scenario is one end-to-end job, not the definition of the entire product; preserve materially different objects and jobs even when one scenario is more visible.

## Preserve nested shells

`shells` form an acyclic ownership tree. `parentShellId` establishes ancestry and `slots` lists fillable regions. Because v3 has no separate `parentSlotId`, name the exact occupied parent slot and inherited identity/navigation regions in the child and parent `invariants`; ambiguity is a structure conflict. A nested module may add local navigation inside that slot, but it must not create a second application shell, brand, or global information architecture by renderer inference.

Each compact surface lists its complete `shellIds` ancestry from outer to inner shell. Validate that child routes keep parent invariants, breadcrumbs/return paths preserve ownership, and responsive transformations do not silently discard critical navigation.

## Bind references narrowly

A reference affects only its `surfaceIds` and `aspects`, subject to `constraints`. Use `mustNotInfluence` to prevent leakage: a functional example must not set style, a visual anchor must not invent behavior, and a module-specific source must not replace an inherited shell. A stable local source uses its SHA; changed bytes invalidate the binding.

Reference provenance proves identity and scope, not permission to copy, runtime truth, artifact acceptance, or whole-product authority. Broadening a binding is a material contract change.

## Separate representative design evidence from runtime coverage

Derive two sets from `outputs`:

- **representative design anchors** — outputs with `designEvidenceRequired: true`;
- **runtime coverage** — outputs with `runtimeEvidenceRequired: true`.

A page family may share one design artifact only when hierarchy, shell, interaction shape, and responsive behavior are genuinely shared. Unique visual mechanisms and user-requested separate page designs remain separate design outputs. Every required route/state/viewport remains runtime coverage even when it needs no design artifact.

Record page-family membership and the representative-design rationale in the IA/Product Design handoff because the current v3 structure schema has no page-family property. This reasoning never waives per-output runtime evidence.

An accepted design artifact never proves an implemented route. A runtime-only output does not become optional because ImageGen stopped. Conversely, do not spend render calls on every route when a representative design artifact is sufficient.

`dependsOn` expresses ordering or evidence dependency. `anchorOutputId` independently names the accepted output that supplies visual continuity; do not infer it from `dependsOn`. The renderer brief refines a non-null anchor into an `anchorRequirement` with `preserve[]` and `changeOnly[]`. Runtime state records the exact accepted source bytes as `anchorArtifactSha256`; structure, reference, shell, direction, and render-brief identities remain separately validated. A path or similar-looking image is not an anchor binding.

An anchor must reference another design-bearing output, be ordered before the child when sequencing is required, and be accepted/promoted before its SHA is bound. Reject self/unknown/stale anchors. A dependency may exist without visual continuity; it must never silently become an anchor.

The confirmed `renderBudget` limits actual render calls, attempts per output, and concept resets. It is not a target to exhaust. Product, structure, shell, direction, reference, or density contradictions return upstream instead of consuming retries as prompt experiments.

## Structural and page-family decisions

Choose a separate page or route when the surface has an independent user job or completion moment, a shareable/restorable destination, a distinct permission/data boundary, substantial complexity/navigation identity, or a hierarchy that cannot remain contextual without losing clarity.

Choose a derived state or contextual container when the work is temporary, belongs to one parent context, and does not need an independent destination. Modal, drawer, tab, and page are interaction meanings, not overflow buckets.

Group pages only when they share structure, user-job shape, interaction model, and responsive behavior. Content similarity alone is insufficient. Explicit “every page separately” requests disable representative design collapse even when implementation later reuses a template.

Visual uniqueness comes from product-object hierarchy, composition, content, typography, media, material behavior, and restrained motion. Do not invent unconventional controls or gestures to manufacture distinctiveness. A bespoke interaction requires an explicit product capability, owner, authority, accessibility/recovery contract, and later capability-selection evidence.

## Coverage and change-control rules

- Map every named domain, scenario, product object, protected capability, surface, and hidden-surface trigger.
- Require entry and job-appropriate completion surfaces for each scenario, plus recovery surfaces whenever a material blocked/failure path exists.
- Require an output when state or viewport changes understanding, action, safety, permission, failure, recovery, navigation, hierarchy, composition, or interaction materially.
- Treat ordinary surface information as display authority only for ordinary product content. Operational metadata also needs an authorized surface/state claim.
- Use `deferred` or `unsupported` only through an explicit authorized decision recorded in the helper-owned runtime output status and reason; `coverage.json` does not carry those mutable statuses. Never use either to hide an over-budget or unmodeled runtime route.
- Declare any evidence-equivalence exception before confirmation and bind it to the exact output pair, evidence channel, and specific justification. Because the current schema has no channel field, prefix `equivalenceJustification` with exact `design:` or `runtime:` and require both outputs to have that evidence flag. Never use design equivalence as runtime proof. Runtime equivalence is allowed only when the two outputs are semantically the same captured route/state/viewport evidence and the preconfirmed justification explains why; convenience is insufficient.

Coverage is complete only when the domain/object-to-runtime trace closes and no named page, meaningful state, material responsive transformation, or protected capability disappears.

Pass `structure.json` and compact `coverage.json` by workspace-relative path/SHA. Any material relaxation—removing/demoting a protected capability, domain, scenario, surface, or primary object; changing shell ownership; broadening a reference; reducing evidence; changing artifact/checkpoint policy; replacing an anchor; or increasing the render budget—requires a fresh user-turn-bound authority receipt plus change-control record binding the base digests, canonical proposed delta, resulting contract/structure digests, and exact action. A boolean authorization flag, pre-change-only receipt, or old receipt is insufficient.

Do not silently reinterpret v1/v2 sessions as v3. Continue their original semantics or perform an explicit compatible migration. A FULL design-only contract may keep `implementationTargets` empty; target scope becomes relevant only when implementation is authorized.

When design or implementation discovers an impossible constraint, return `STRUCTURE_CONFLICT` with affected IDs and evidence. Reopen the owning contract instead of inventing a different hierarchy downstream.
