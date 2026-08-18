# Typed frontend structure contract

Use this reference to create a compact source of truth for a multi-page site, application, or multi-step flow.

## Core model

Use the smallest applicable subset:

~~~ts
type ScopeKind = "site" | "application" | "flow";
type StructureAuthority = "locked" | "revisable";
type CoverageStatus = "planned" | "validated" | "deferred" | "unsupported";

interface FrontendStructureContract {
  schemaVersion: 1;
  contractId: string;
  scopeKind: ScopeKind;
  authority: {
    pageStructure: StructureAuthority;
    interactionModel: StructureAuthority;
    contentRepartition:
      | "within-surface-only"
      | "authorized-across-surfaces";
  };
  sharedShell: string[];
  surfaces: Surface[];
  pageFamilies: PageFamily[];
  states: State[];
  viewports: Viewport[];
  edges: NavigationEdge[];
  outputs: CoverageOutput[];
}

interface Surface {
  id: string;
  kind: "page" | "screen" | "flow-step" | "overlay";
  route?: string;
  userJob: string;
  requiredInformation: string[];
  requiredActions: string[];
  permissionBoundary?: string;
  pageFamilyId?: string;
  uniqueReason?: string;
}

interface PageFamily {
  id: string;
  sharedStructure: string;
  surfaceIds: string[];
  representativeSurfaceIds: string[];
}

interface State {
  id: string;
  surfaceId: string;
  trigger: string;
  visibleChange: string;
  recovery?: string;
}

interface Viewport {
  id: string;
  class: "wide" | "narrow" | "mobile" | "custom";
  transformation: string;
}

interface NavigationEdge {
  from: string;
  to: string;
  trigger: string;
  returnPath?: string;
}

interface CoverageOutput {
  id: string;
  surfaceId: string;
  stateId: string;
  viewportId: string;
  scrollPosition?: string;
  required: boolean;
  approvalRequired: boolean;
  status: CoverageStatus;
  coveredBy?: string;
  reason?: string;
}
~~~

Use stable path-safe IDs. Keep file paths workspace-relative when the contract is persisted.

## Structural decisions

Choose a separate page or route when the surface has one or more of:

- an independent user job or completion moment;
- a shareable or restorable destination;
- a distinct permission or data boundary;
- substantial complexity or navigation identity;
- a hierarchy that cannot remain contextual without losing task clarity.

Choose a derived state or contextual container when the work is temporary, belongs to one parent context, and does not need an independent destination. Modal, drawer, tab, and page are interaction meanings, not overflow buckets.

## Page-family rules

Group pages only when they share structure, user-job shape, interaction model, and responsive behavior. Content similarity alone is not enough. A representative output covers a family only when unique pages do not require different hierarchy or actions.

Explicit “every page separately” requests disable representative visual collapse, even when implementation later reuses one template.

## Coverage rules

- Map every named surface.
- Require a default state for every unique surface or representative family.
- Require a state when it changes understanding, action, safety, permission, failure, or recovery.
- Require a viewport when navigation, hierarchy, composition, or interaction transforms materially.
- Give every hidden surface a discoverable trigger.
- Do not move content or actions across locked page boundaries.
- Use `deferred` only for an explicit scope boundary or checkpoint with a reason.
- Use `unsupported` only when product content or behavior is genuinely absent.

Coverage is complete when every required entity maps to a required output, every output has a status, and no named page, meaningful state, or material responsive transformation disappears.

## Handoff

Pass the rich frozen contract by workspace-relative path as `structure.json`. Consumers must receive the authority block, surfaces, page families, states, viewports, edges, and required outputs. They may enrich visual or implementation details but cannot silently change locked structure.

Also derive `coverage.json` for the runtime helper. It deliberately flattens the rich structure into the machine-checkable contract:

~~~json
{
  "schemaVersion": 1,
  "contractId": "site-contract",
  "authority": {
    "pageStructure": "locked",
    "interactionModel": "locked",
    "contentRepartition": "within-surface-only"
  },
  "surfaces": [
    {"id": "home", "kind": "page", "route": "/", "userJob": "Understand the offer"}
  ],
  "edges": [],
  "outputs": [
    {
      "id": "home-default-wide",
      "surfaceId": "home",
      "state": "default",
      "viewport": "wide",
      "scrollPosition": "full-page",
      "required": true,
      "approvalRequired": false,
      "dependsOn": [],
      "promotionRequired": false,
      "promotionTarget": null
    }
  ]
}
~~~

`state` and `viewport` use stable IDs from `structure.json`. Page-family metadata remains in the rich contract; the runtime only needs the flattened output graph and authority required to prevent false completion.

Default `approvalRequired` to `false`. A downstream product-design checkpoint policy may set it to `true` without changing sitemap or interaction authority; that field controls delivery sequencing, not information architecture.

When visual design or implementation discovers an impossible constraint, return a `STRUCTURE_CONFLICT` with the affected IDs and evidence. Reopen the contract instead of inventing a different sitemap downstream.
