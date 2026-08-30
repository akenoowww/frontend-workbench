from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import runtime_state  # noqa: E402


class RuntimeStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("/.frontend-workbench/\n", encoding="utf-8")
        (self.root / "promoted").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_contract(
        self,
        *,
        two_outputs: bool = False,
        cycle: bool = False,
        promotion_required: bool = True,
        approval_required: bool = False,
        workflow_profile: str | None = None,
        implementation_targets: list[str] | None = None,
        product_intent: dict[str, object] | None = None,
        visual_artifact_policy: str | None = None,
        visual_direction_policy: str | None = None,
        checkpoint_mode: str | None = None,
        operational_metadata_policy: dict[str, object] | None = None,
        evidence_equivalence: bool = False,
    ) -> Path:
        outputs = [
            {
                "id": "O01",
                "surfaceId": "P01",
                "state": "default",
                "viewport": "desktop",
                "scrollPosition": "top",
                "required": True,
                "approvalRequired": approval_required,
                "dependsOn": ["O02"] if cycle else [],
                "promotionRequired": promotion_required,
                **({"promotionTarget": "promoted/o1.txt"} if promotion_required else {}),
            }
        ]
        if two_outputs:
            outputs.append(
                {
                    "id": "O02",
                    "surfaceId": "P01",
                    "state": "open",
                    "viewport": "desktop",
                    "scrollPosition": "top",
                    "required": True,
                    "approvalRequired": approval_required,
                    "dependsOn": ["O01"],
                    "promotionRequired": False,
                    **(
                        {
                            "evidenceEquivalentTo": "O01",
                            "equivalenceJustification": (
                                "The open state intentionally has no visual delta from default."
                            ),
                        }
                        if evidence_equivalence
                        else {}
                    ),
                }
            )
        contract = {
            "schemaVersion": 2,
            "contractId": "test-contract",
            **(
                {"workflowProfile": workflow_profile}
                if workflow_profile is not None
                else {}
            ),
            **(
                {"implementationTargets": implementation_targets}
                if implementation_targets is not None
                else {}
            ),
            **(
                {
                    "productIntent": product_intent
                    or {
                        "problem": "The existing frontend does not cover the intended product.",
                        "representativeScenarios": [
                            "A returning user completes the primary workflow.",
                            "A new user understands and starts the primary workflow.",
                        ],
                        "requiredDomains": ["primary-workflow"],
                        "protectedCapabilities": ["existing-data-access"],
                        "antiGoals": ["Do not collapse the product to one narrow use case."],
                        "successSignals": ["Users can complete the representative scenarios."],
                    },
                    "visualArtifactPolicy": visual_artifact_policy or "runnable",
                    "visualDirectionPolicy": visual_direction_policy or "required",
                    "checkpointMode": checkpoint_mode or "continuous",
                    "operationalMetadataPolicy": operational_metadata_policy
                    or runtime_state.default_operational_metadata_policy(),
                }
                if workflow_profile == "full"
                else {
                    **(
                        {"productIntent": product_intent}
                        if product_intent is not None
                        else {}
                    ),
                    **(
                        {"visualArtifactPolicy": visual_artifact_policy}
                        if visual_artifact_policy is not None
                        else {}
                    ),
                    **(
                        {"visualDirectionPolicy": visual_direction_policy}
                        if visual_direction_policy is not None
                        else {}
                    ),
                    **(
                        {"checkpointMode": checkpoint_mode}
                        if checkpoint_mode is not None
                        else {}
                    ),
                }
            ),
            "authority": {
                "pageStructure": "locked",
                "interactionModel": "locked",
                "contentRepartition": "within-surface-only",
            },
            "surfaces": [
                {
                    "id": "P01",
                    "kind": "page",
                    "route": "/test",
                    "userJob": "Exercise the runtime helper",
                }
            ],
            "edges": [],
            "outputs": outputs,
        }
        path = self.root / "contract.json"
        path.write_text(json.dumps(contract), encoding="utf-8")
        return path

    def write_authority_receipt(
        self,
        name: str,
        authorized_actions: list[str],
        *,
        session_id: str,
        contract_sha256: str,
        structure_sha256: str,
        base_contract_sha256: str | None = None,
        result_contract_sha256: str | None = None,
        delta_sha256: str | None = None,
    ) -> Path:
        payload = {
            "schemaVersion": 1,
            "kind": "user-message",
            "sessionId": session_id,
            "contractSha256": contract_sha256,
            "structureSha256": structure_sha256,
            "baseContractSha256": base_contract_sha256,
            "resultContractSha256": result_contract_sha256,
            "deltaSha256": delta_sha256,
            "sourceRef": f"turn/{name}",
            "messageSha256": runtime_state._canonical_sha256(
                {"name": name, "actions": authorized_actions}
            ),
            "authorizedActions": authorized_actions,
            "statement": f"The user explicitly authorized {', '.join(authorized_actions)}.",
        }
        path = self.root / f"authority-{name}.json"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return path

    def write_v3_contract(
        self,
        *,
        session_suffix: str = "base",
        design_evidence_required: bool = True,
        runtime_evidence_required: bool = True,
        artifact_kind: str = "runnable",
        two_outputs: bool = False,
        anchor_second: bool = False,
        capability_complexity: str = "bounded",
        visual_artifact_policy: str = "runnable",
        checkpoint_mode: str = "continuous",
        render_budget: dict[str, int] | None = None,
    ) -> tuple[Path, Path]:
        outputs: list[dict[str, object]] = [
            {
                "id": "O01",
                "surfaceId": "P01",
                "state": "default",
                "viewport": "desktop",
                "scrollPosition": "top",
                "designEvidenceRequired": design_evidence_required,
                "runtimeEvidenceRequired": runtime_evidence_required,
                "artifactKind": artifact_kind,
                "anchorOutputId": None,
                "approvalRequired": False,
                "dependsOn": [],
                "promotionRequired": False,
            }
        ]
        surfaces: list[dict[str, object]] = [
            {
                "id": "P01",
                "kind": "page",
                "route": "/test",
                "userJob": "Exercise the v3 runtime helper",
                "primaryObjectId": "product",
                "shellIds": [],
                "referenceBindingIds": [],
            }
        ]
        if two_outputs:
            surfaces.append(
                {
                    "id": "P02",
                    "kind": "page",
                    "route": "/second",
                    "userJob": "Exercise dependent output mechanics",
                    "primaryObjectId": "product",
                    "shellIds": [],
                    "referenceBindingIds": [],
                }
            )
            outputs.append(
                {
                    "id": "O02",
                    "surfaceId": "P02",
                    "state": "default",
                    "viewport": "desktop",
                    "scrollPosition": "top",
                    "designEvidenceRequired": True,
                    "runtimeEvidenceRequired": True,
                    "artifactKind": artifact_kind,
                    "anchorOutputId": "O01" if anchor_second else None,
                    "approvalRequired": False,
                    "dependsOn": ["O01"] if anchor_second else [],
                    "promotionRequired": False,
                }
            )
        scenario_id = "scenario-primary"
        structure = {
            "schemaVersion": 3,
            "contractId": f"test-structure-{session_suffix}",
            "surfaces": [
                {
                    "id": surface["id"],
                    "route": surface["route"],
                    "scenarioIds": [scenario_id],
                    "domainIds": ["lifecycle"],
                }
                for surface in surfaces
            ],
            "scenarios": [
                {
                    "id": scenario_id,
                    "job": "Exercise the complete evidence-bound lifecycle.",
                    "objectIds": ["product"],
                    "entrySurfaceId": surfaces[0]["id"],
                    "completionSurfaceId": surfaces[-1]["id"],
                    "recoverySurfaceIds": [],
                }
            ],
            "shells": [],
            "objectBindings": [
                {
                    "id": f"binding-{surface['id']}",
                    "surfaceId": surface["id"],
                    "primaryObjectId": "product",
                    "supportingObjectIds": [],
                    "forbiddenDominantObjectIds": [],
                }
                for surface in surfaces
            ],
            "referenceBindings": [],
        }
        structure_path = self.root / f"structure-{session_suffix}.json"
        structure_path.write_text(
            json.dumps(structure, sort_keys=True),
            encoding="utf-8",
        )
        contract: dict[str, object] = {
            "schemaVersion": 3,
            "contractId": f"test-contract-{session_suffix}",
            "workflowProfile": "full",
            "structure": {
                "id": structure["contractId"],
                "path": "structure.json",
                "sha256": runtime_state._canonical_sha256(structure),
            },
            "productIntent": {
                "problem": "The product needs evidence-bound lifecycle enforcement.",
                "representativeScenarios": [
                    "A user reviews the complete product before implementation.",
                    "A user verifies every required runtime surface after implementation.",
                ],
                "requiredDomains": ["lifecycle"],
                "protectedCapabilities": ["Render and verify the product surface"],
                "antiGoals": ["Do not weaken coverage to pass a gate."],
                "successSignals": ["Every gate is bound to immutable evidence."],
            },
            "productModel": {
                "rootObjectId": "product",
                "objects": [
                    {
                        "id": "product",
                        "role": "root",
                        "parentId": None,
                        "evidenceForObjectIds": [],
                    }
                ],
                "relations": [],
            },
            "capabilityRequirements": [
                {
                    "id": "cap-core",
                    "capability": "Render and verify the product surface",
                    "complexity": capability_complexity,
                    "ownerObjectId": "product",
                    "surfaceIds": [item["id"] for item in surfaces],
                    "required": True,
                    "constraints": ["Preserve the exact coverage contract"],
                }
            ],
            "operationalMetadataPolicy": runtime_state.default_operational_metadata_policy(),
            "visualArtifactPolicy": visual_artifact_policy,
            "visualDirectionPolicy": "required",
            "checkpointMode": checkpoint_mode,
            "authority": {
                "pageStructure": "locked",
                "interactionModel": "locked",
                "contentRepartition": "within-surface-only",
            },
            "surfaces": surfaces,
            "edges": [],
            "outputs": outputs,
            "implementationTargets": [
                {
                    "path": "src/product.txt",
                    "surfaceIds": [item["id"] for item in surfaces],
                    "sharedOwner": len(surfaces) > 1,
                }
            ],
        }
        if artifact_kind == "imagegen" or render_budget is not None:
            contract["renderBudget"] = render_budget or {
                "maxCallsTotal": len(outputs) + 1,
                "maxAttemptsPerOutput": 2,
                "maxConceptResets": 1,
            }
        contract_path = self.root / f"contract-{session_suffix}.json"
        contract_path.write_text(
            json.dumps(contract, sort_keys=True),
            encoding="utf-8",
        )
        return contract_path, structure_path

    def confirm_v3(self, session_id: str, state: dict) -> dict:
        return runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The complete v3 contract, structure, coverage, and policies are authorized.",
            user_authorized=True,
            authority_receipt_file=self.write_authority_receipt(
                f"{session_id}-intent",
                ["confirm-intent"],
                session_id=session_id,
                contract_sha256=runtime_state._canonical_sha256(state["contract"]),
                structure_sha256=state["contract"]["structure"]["sha256"],
            ),
        )

    def write_implementation_plan(
        self,
        session_id: str,
        state: dict,
        *,
        decisions: list[dict[str, object]] | None = None,
        target_bindings: list[dict[str, object]] | None = None,
        output_bindings: list[dict[str, object]] | None = None,
    ) -> Path:
        contract = state["contract"]
        targets = contract["implementationTargets"]
        capability_decisions = decisions or [
            {
                "requirementId": "cap-core",
                "selectedApproach": "reuse",
                "existingOwner": "src/product.txt",
                "candidates": [
                    {
                        "name": "existing product owner",
                        "kind": "project-file",
                        "evidenceRef": "repo:evidence/existing-product-owner.md",
                    }
                ],
                "selectedCandidate": "existing product owner",
                "gap": "The owner needs the v3 surface implementation.",
                "lifetimeRationale": "Reuse keeps one durable capability owner.",
                "obligations": ["Preserve the public behavior"],
                "validation": ["Run the runtime fidelity check"],
            }
        ]
        plan = {
            "schemaVersion": 1,
            "contractId": contract["contractId"],
            "contractSha256": runtime_state._canonical_sha256(contract),
            "structureSha256": contract["structure"]["sha256"],
            "capabilityDecisions": capability_decisions,
            "targetBindings": target_bindings
            or [
                {
                    "path": target["path"],
                    "surfaceIds": target["surfaceIds"],
                    "capabilityRequirementIds": ["cap-core"],
                }
                for target in targets
            ],
            "outputBindings": output_bindings
            or [
                {
                    "outputId": output["id"],
                    "targetPaths": [target["path"] for target in targets],
                    "capabilityRequirementIds": ["cap-core"],
                }
                for output in contract["outputs"]
                if output["runtimeEvidenceRequired"]
            ],
        }
        for decision in plan["capabilityDecisions"]:
            for candidate in decision["candidates"]:
                evidence_ref = candidate["evidenceRef"]
                if evidence_ref.startswith("repo:"):
                    evidence_path = self.root / evidence_ref.removeprefix("repo:")
                elif evidence_ref.startswith("session:"):
                    evidence_path = (
                        self.root
                        / ".frontend-workbench"
                        / "sessions"
                        / session_id
                        / evidence_ref.removeprefix("session:")
                    )
                else:
                    continue
                evidence_path.parent.mkdir(parents=True, exist_ok=True)
                if not evidence_path.exists():
                    evidence_path.write_text(
                        f"Evidence for {candidate['name']}\n",
                        encoding="utf-8",
                    )
                candidate["evidenceSha256"] = runtime_state.sha256_file(
                    evidence_path
                )
        path = self.root / f"implementation-plan-{session_id}.json"
        path.write_text(json.dumps(plan, sort_keys=True), encoding="utf-8")
        return path

    def write_visual_direction(
        self,
        *,
        concept_thesis: str = "Calm operational clarity with one decisive focal move.",
    ) -> Path:
        payload = {
            "schemaVersion": 1,
            "conceptThesis": concept_thesis,
            "brandPosture": "Confident, useful, and restrained",
            "visualTension": "Dense operational facts against generous decision space",
            "signatureMove": "A single high-contrast action rail anchors each state",
            "hierarchyPrinciples": ["Task before metadata", "Recovery beside failure"],
            "densityRhythm": "Compact work bands separated by quiet checkpoints",
            "typographyRoles": ["Display for state", "Sans for action and data"],
            "colorRoles": ["Neutral structure", "One action accent", "Semantic status"],
            "surfaceLanguage": "Flat nested planes with restrained elevation",
            "motionTone": "Fast, quiet, and state-explanatory",
            "imageryRole": "No decorative imagery; evidence only",
            "preserveFromProjectDNA": ["Existing action accent"],
            "intentionalDepartures": [],
            "avoid": ["Generic dashboard mosaics", "Decorative gradients"],
            "evidence": [
                {
                    "sourceType": "project-file",
                    "sourceRef": "src/product.txt",
                    "observation": "The existing product prioritizes one primary action.",
                }
            ],
        }
        path = self.root / "visual-direction.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def artifact(self, session_id: str, name: str, contents: str) -> str:
        relative = f"artifacts/{name}"
        path = self.root / ".frontend-workbench" / "sessions" / session_id / relative
        path.write_text(contents, encoding="utf-8")
        return relative

    def artifact_bytes(self, session_id: str, name: str, contents: bytes) -> str:
        relative = f"artifacts/{name}"
        path = self.root / ".frontend-workbench" / "sessions" / session_id / relative
        path.write_bytes(contents)
        return relative

    def qa_evidence(self, session_id: str, name: str, contents: str) -> str:
        relative = f"qa/{name}"
        path = self.root / ".frontend-workbench" / "sessions" / session_id / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        return relative

    def qa_screenshot(self, session_id: str, name: str, contents: bytes | None = None) -> str:
        relative = f"qa/{name}"
        path = self.root / ".frontend-workbench" / "sessions" / session_id / relative
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(contents or self.png_bytes(800, 600))
        return relative

    @staticmethod
    def png_bytes(width: int, height: int) -> bytes:
        def chunk(kind: bytes, payload: bytes) -> bytes:
            body = kind + payload
            return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        row = b"\x00" + (b"\x00\x00\x00\xff" * width)
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * height))
            + chunk(b"IEND", b"")
        )

    def fidelity_manifest(
        self,
        session_id: str,
        name: str,
        *,
        output_id: str,
        accepted_sha256: str | None,
        result: str,
        screenshot: str | None = None,
        reason: str | None = None,
        route: str = "/test",
        state: str = "default",
        viewport: str = "desktop",
        scroll_position: str = "top",
        pixel_width: int | None = None,
        pixel_height: int | None = None,
        equivalence_justification: str | None = None,
        evidence_equivalent_to: str | None = None,
        comparison_mode: str | None = None,
        visual_direction_sha256: str | None = None,
        implementation_plan_sha256: str | None = None,
        include_runtime_probe: bool = True,
    ) -> str:
        screenshot_width: int | None = None
        screenshot_height: int | None = None
        screenshot_sha256: str | None = None
        screenshot_path: Path | None = None
        if screenshot is not None:
            screenshot_path = (
                self.root
                / ".frontend-workbench"
                / "sessions"
                / session_id
                / screenshot
            )
            screenshot_sha256 = runtime_state.sha256_file(screenshot_path)
            try:
                screenshot_width, screenshot_height = runtime_state.validate_screenshot_file(
                    screenshot_path
                )
            except runtime_state.StateError:
                screenshot_width = pixel_width if pixel_width is not None else 1
                screenshot_height = pixel_height if pixel_height is not None else 1
        payload: dict[str, object] = {
            "outputId": output_id,
            "acceptedArtifactSha256": accepted_sha256,
            "result": result,
            "route": route,
            "state": state,
            "viewport": viewport,
            "scrollPosition": scroll_position,
            "pixelWidth": pixel_width if pixel_width is not None else screenshot_width,
            "pixelHeight": pixel_height if pixel_height is not None else screenshot_height,
        }
        if screenshot_path is not None:
            payload["screenshot"] = {
                "path": screenshot,
                "sha256": screenshot_sha256,
            }
        if result == "pass" and screenshot_path is not None and include_runtime_probe:
            base_name = Path(name).stem
            spec_relative = f"qa/{base_name}.runtime-probe-spec.json"
            trace_relative = f"qa/{base_name}.runtime-probe.json"
            _, runtime_state_value = runtime_state.load_state(self.root, session_id)
            implementation_snapshot_sha256 = runtime_state.implementation_snapshot_sha256(
                self.root,
                runtime_state_value,
            )
            scroll_kind = (
                scroll_position
                if scroll_position in {"top", "bottom", "full-page"}
                else "selector"
            )
            spec = {
                "schemaVersion": 1,
                "outputId": output_id,
                "url": f"http://127.0.0.1:4173{route}",
                "route": route,
                "state": state,
                "scrollPosition": scroll_position,
                "scroll": {
                    "kind": scroll_kind,
                    **({"selector": "#root"} if scroll_kind == "selector" else {}),
                },
                "viewport": {
                    "label": viewport,
                    "width": screenshot_width,
                    "height": screenshot_height,
                },
                "rootSelector": "#root",
                "ready": {"kind": "selector", "value": "#root > *"},
                "stateSetup": [],
                "stateAssertion": {
                    "id": "covered-state",
                    "kind": "visible-text",
                    "value": "Runtime test surface",
                },
                "interactions": [
                    {
                        "id": "primary-action",
                        "action": {"kind": "click-role", "role": "button", "name": "Continue"},
                        "assertions": [
                            {"id": "state-change", "kind": "visible-text", "value": "Completed"}
                        ],
                    }
                ],
                "implementationSnapshotSha256": implementation_snapshot_sha256,
                "screenshotPath": screenshot,
                "tracePath": trace_relative,
            }
            spec_value = self.qa_evidence(
                session_id,
                f"{base_name}.runtime-probe-spec.json",
                json.dumps(spec, sort_keys=True),
            )
            spec_path = (
                self.root
                / ".frontend-workbench"
                / "sessions"
                / session_id
                / spec_value
            )
            trace = {
                "schemaVersion": 1,
                "producer": "frontend-workbench/browser-runtime-probe",
                "adapter": "agent-browser",
                "adapterVersion": "test-adapter-1",
                "generatedAt": "2026-01-01T00:00:00Z",
                "specPath": spec_relative,
                "specSha256": runtime_state.sha256_file(spec_path),
                "implementationSnapshotSha256": implementation_snapshot_sha256,
                "outputId": output_id,
                "route": route,
                "state": state,
                "viewport": viewport,
                "scrollPosition": scroll_position,
                "directNavigation": True,
                "page": {
                    "finalUrl": f"http://127.0.0.1:4173{route}",
                    "title": "Runtime test surface",
                    "rootSelector": "#root",
                    "rootFound": True,
                    "rootIsDocumentShell": False,
                    "rootVisible": True,
                    "rootEffectiveOpacity": 1.0,
                    "rootViewportIntersectionPixels": float(
                        (screenshot_width or 0) * (screenshot_height or 0)
                    ),
                    "rootChildElementCount": 1,
                    "visibleTextCharacters": 24,
                    "visibleLandmarkCount": 1,
                    "interactiveElementCount": 1,
                    "rootWidth": float(screenshot_width or 0),
                    "rootHeight": float(screenshot_height or 0),
                },
                "stateVerification": {
                    "id": "covered-state",
                    "kind": "visible-text",
                    "result": "pass",
                    "observed": "visible text contains 'Runtime test surface'",
                },
                "scroll": {
                    "kind": scroll_kind,
                    "x": 0.0,
                    "y": 0.0,
                    "maxY": 0.0,
                    "verified": True,
                    "captureFullPage": scroll_kind == "full-page",
                },
                "runtimeHealth": {
                    "consoleErrors": [],
                    "pageErrors": [],
                    "failedRequests": [],
                },
                "accessibility": {
                    "criticalViolations": 0,
                    "seriousViolations": 0,
                    "otherViolations": [],
                },
                "interactions": [
                    {
                        "id": "primary-action",
                        "action": "click role=button name=Continue",
                        "beforeSha256": "a" * 64,
                        "afterSha256": "b" * 64,
                        "stateChanged": True,
                        "assertions": [
                            {
                                "id": "state-change",
                                "kind": "visible-text",
                                "result": "pass",
                                "observed": "visible text contains 'Completed'",
                            }
                        ],
                        "result": "pass",
                    }
                ],
                "screenshot": {
                    "path": screenshot,
                    "sha256": screenshot_sha256,
                    "pixelWidth": screenshot_width,
                    "pixelHeight": screenshot_height,
                },
                "verdict": "pass",
            }
            trace_value = self.qa_evidence(
                session_id,
                f"{base_name}.runtime-probe.json",
                json.dumps(trace, sort_keys=True),
            )
            trace_path = (
                self.root
                / ".frontend-workbench"
                / "sessions"
                / session_id
                / trace_value
            )
            payload["runtimeProbe"] = {
                "path": trace_relative,
                "sha256": runtime_state.sha256_file(trace_path),
            }
        if reason is not None:
            payload["reason"] = reason
        if equivalence_justification is not None:
            payload["equivalenceJustification"] = equivalence_justification
        if evidence_equivalent_to is not None:
            payload["evidenceEquivalentTo"] = evidence_equivalent_to
        if comparison_mode is not None:
            payload["comparisonMode"] = comparison_mode
        if visual_direction_sha256 is not None:
            payload["visualDirectionSha256"] = visual_direction_sha256
        if implementation_plan_sha256 is not None:
            payload["implementationPlanSha256"] = implementation_plan_sha256
        return self.qa_evidence(
            session_id,
            name,
            json.dumps(payload, sort_keys=True),
        )

    def record_fidelity_qa(self, *args, **kwargs) -> dict:
        return runtime_state._record_fidelity_qa(
            *args,
            **kwargs,
            _canonical_probe_executed=True,
        )

    def imagegen_provenance(
        self,
        session_id: str,
        output_id: str,
        artifact: str,
    ) -> tuple[str, str, bytes]:
        session_dir = self.root / ".frontend-workbench" / "sessions" / session_id
        provenance_dir = session_dir / "provenance"
        traces_dir = provenance_dir / "traces"
        traces_dir.mkdir(parents=True, exist_ok=True)
        trace_relative = f"provenance/traces/{output_id}.jsonl"
        trace_bytes = (
            json.dumps(
                {
                    "outputId": output_id,
                    "sourceKind": "host-imagegen",
                    "sourceId": f"imagegen-{output_id}",
                },
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        (session_dir / trace_relative).write_bytes(trace_bytes)
        artifact_path = session_dir / artifact
        receipt_relative = f"provenance/{output_id}.json"
        receipt = {
            "outputId": output_id,
            "artifactSha256": runtime_state.sha256_file(artifact_path),
            "sourceKind": "host-imagegen",
            "sourceId": f"imagegen-{output_id}",
            "tracePath": trace_relative,
            "traceSha256": runtime_state.sha256_file(session_dir / trace_relative),
        }
        (session_dir / receipt_relative).write_text(
            json.dumps(receipt, sort_keys=True),
            encoding="utf-8",
        )
        return receipt_relative, trace_relative, trace_bytes

    def render_brief(
        self,
        session_id: str,
        state: dict,
        output_id: str,
    ) -> str:
        contract_output = next(
            item for item in state["contract"]["outputs"] if item["id"] == output_id
        )
        surface = next(
            item
            for item in state["contract"]["surfaces"]
            if item["id"] == contract_output["surfaceId"]
        )
        anchor_id = contract_output.get("anchorOutputId")
        anchor_sha = None
        if anchor_id is not None:
            anchor_sha = next(
                item["sha256"] for item in state["outputs"] if item["id"] == anchor_id
            )
        payload = {
            "schemaVersion": 1,
            "outputId": output_id,
            "visualDirectionSha256": state["visualDirection"]["sha256"],
            "shellIds": surface.get("shellIds", []),
            "referenceBindingIds": surface.get("referenceBindingIds", []),
            "anchorOutputId": anchor_id,
            "anchorArtifactSha256": anchor_sha,
            "preserve": ["Preserve the confirmed product hierarchy"],
            "changeOnly": ["Render only the declared output state"],
        }
        relative = f"art-direct-imagegen/render-briefs/{output_id}.json"
        path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / relative
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return relative

    def write_product_target(self, contents: str) -> Path:
        target = self.root / "src" / "product.txt"
        target.parent.mkdir(exist_ok=True)
        target.write_text(contents, encoding="utf-8")
        return target

    def settle_output(self, session_id: str, artifact: str) -> dict:
        _, current = runtime_state.load_state(self.root, session_id)
        if (
            current["contract"].get("workflowProfile") == "full"
            and not current["intentConfirmation"]["userAuthorized"]
        ):
            current = runtime_state.confirm_intent(
                self.root,
                session_id,
                current["revision"],
                product_intent_sha256=current["intentConfirmation"]["productIntentSha256"],
                lifecycle_plan_sha256=current["intentConfirmation"]["lifecyclePlanSha256"],
                teach_back="The product must preserve every required domain and representative scenario.",
                user_authorized=True,
            )
        if current.get("visualDirection", {}).get("status") == "pending":
            current = runtime_state.lock_visual_direction(
                self.root,
                session_id,
                current["revision"],
                self.write_visual_direction(),
                user_authorized=(
                    current["contract"].get("checkpointMode") != "continuous"
                ),
            )
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", current["revision"]
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=artifact,
        )
        output = next(item for item in state["outputs"] if item["id"] == "O01")
        if output["approvalRequired"]:
            state = runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "awaiting-approval",
                state["revision"],
                artifact=artifact,
            )
        return runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
            user_authorized=output["approvalRequired"],
        )

    def test_requires_exact_root_ignore_line(self) -> None:
        (self.root / ".gitignore").write_text(".frontend-workbench/**\n", encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "exact line"):
            runtime_state.preflight(self.root)

    def test_symlinked_sessions_directory_is_rejected(self) -> None:
        runtime_root = self.root / ".frontend-workbench"
        runtime_root.mkdir()
        external = self.root / "external-sessions"
        external.mkdir()
        (runtime_root / "sessions").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(runtime_state.StateError, "symlinked"):
            runtime_state.preflight(self.root)

    def test_cli_validate_returns_structured_blocked_state(self) -> None:
        script = ROOT / "scripts" / "runtime_state.py"
        session_id = "cli-session"
        init = subprocess.run(
            [
                sys.executable,
                str(script),
                "init",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--contract",
                str(self.write_contract()),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        validate = subprocess.run(
            [
                sys.executable,
                str(script),
                "validate",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(validate.returncode, 2)
        payload = json.loads(validate.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("required output O01 is pending", payload["validationErrors"])

    def test_atomic_lifecycle_validate_promote_cleanup(self) -> None:
        session_id = "session-1"
        state = runtime_state.start_session(self.root, session_id, self.write_contract())
        self.assertEqual(state["status"], "active")
        session_dir = self.root / ".frontend-workbench" / "sessions" / session_id
        self.assertTrue((session_dir / "coverage.json").is_file())
        artifact = self.artifact(session_id, "o1.txt", "accepted output\n")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        self.assertEqual(state["status"], "validated")
        state = runtime_state.promote_output(
            self.root, session_id, "O01", state["revision"]
        )
        self.assertEqual(state["status"], "promoted")
        self.assertEqual((self.root / "promoted" / "o1.txt").read_text(), "accepted output\n")
        state_files = list(
            (self.root / ".frontend-workbench" / "sessions" / session_id).glob(".state.json.*")
        )
        self.assertEqual(state_files, [])
        result = runtime_state.cleanup_session(
            self.root,
            session_id,
            confirm_session=session_id,
            expected_revision=state["revision"],
        )
        self.assertEqual(result["status"], "cleaned")
        self.assertFalse(
            (self.root / ".frontend-workbench" / "sessions" / session_id).exists()
        )

    def test_init_atomically_installs_optional_structure_contract(self) -> None:
        structure = self.root / "structure.json"
        structure.write_text(
            json.dumps({"schemaVersion": 1, "siteId": "test-site"}),
            encoding="utf-8",
        )
        session_id = "structure-session"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
            structure_file=structure,
        )
        session_dir = self.root / ".frontend-workbench" / "sessions" / session_id
        self.assertEqual(
            json.loads((session_dir / "structure.json").read_text(encoding="utf-8"))["siteId"],
            "test-site",
        )
        self.assertFalse(any(session_dir.parent.glob(".init-*")))

    def test_workflow_profile_defaults_to_standard_and_rejects_unknown(self) -> None:
        state = runtime_state.start_session(
            self.root,
            "default-profile",
            self.write_contract(promotion_required=False),
        )
        self.assertEqual(state["contract"]["workflowProfile"], "standard")
        self.assertEqual(state["implementation"]["status"], "not-started")

        contract = json.loads(
            self.write_contract(
                promotion_required=False,
                workflow_profile="turbo",
            ).read_text(encoding="utf-8")
        )
        self.assertIn(
            "contract.workflowProfile is invalid",
            runtime_state.validate_contract(contract),
        )

        full_contract = json.loads(
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
                implementation_targets=[],
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(
            any(
                "implementationTargets" in error
                for error in runtime_state.validate_contract(full_contract)
            )
        )
        contract["workflowProfile"] = []
        self.assertIn(
            "contract.workflowProfile is invalid",
            runtime_state.validate_contract(contract),
        )

    def test_full_profile_cannot_begin_until_required_design_is_promoted(self) -> None:
        session_id = "full-promotion-gate"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                implementation_targets=["src/product.txt"],
            ),
        )
        artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(runtime_state.StateError, "must be promoted"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
            )

        state = runtime_state.promote_output(
            self.root,
            session_id,
            "O01",
            state["revision"],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "conflict"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_targets=["src/other.txt"],
            )
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.assertEqual(state["implementation"]["status"], "in-progress")
        self.assertIsNotNone(state["implementation"]["startedAt"])

    def test_full_profile_rejects_deferred_design_at_implementation_gate(self) -> None:
        session_id = "full-deferred-gate"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
                implementation_targets=["src/product.txt"],
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The deferred design still belongs to the confirmed full product contract.",
            user_authorized=True,
        )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "deferred",
            state["revision"],
            reason="User deferred the design output",
            user_authorized=True,
        )
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(runtime_state.StateError, "accepted"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
            )

    def test_full_completion_requires_digest_bound_passing_fidelity_receipt(self) -> None:
        session_id = "full-fidelity-gate"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
            ),
        )
        design_artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, design_artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "fidelity QA receipt"):
            runtime_state.complete_implementation(
                self.root,
                session_id,
                state["revision"],
            )

        self.write_product_target("implemented product")
        accepted_hash = state["outputs"][0]["sha256"]
        screenshot = self.qa_screenshot(session_id, "qa-o1.png")
        evidence = self.fidelity_manifest(
            session_id,
            "qa-o1.json",
            output_id="O01",
            accepted_sha256=accepted_hash,
            result="pass",
            screenshot=screenshot,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "accepted artifact"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256="0" * 64,
                evidence_artifact=evidence,
                result="pass",
            )

        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=accepted_hash,
            evidence_artifact=evidence,
            result="pass",
        )
        screenshot_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / screenshot
        )
        original_screenshot = screenshot_path.read_bytes()
        screenshot_path.write_bytes(original_screenshot + b"tampered")
        with self.assertRaisesRegex(runtime_state.StateError, "screenshot hash mismatch"):
            runtime_state.complete_implementation(
                self.root,
                session_id,
                state["revision"],
            )
        screenshot_path.write_bytes(original_screenshot)

        evidence_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / evidence
        )
        original_manifest = evidence_path.read_text(encoding="utf-8")
        evidence_path.write_text(original_manifest + "\n", encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "manifest hash mismatch"):
            runtime_state.complete_implementation(
                self.root,
                session_id,
                state["revision"],
            )

        evidence_path.write_text(original_manifest, encoding="utf-8")
        state = runtime_state.complete_implementation(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(state["implementation"]["status"], "completed")
        self.assertEqual(state["status"], "awaiting-user-review")
        self.assertIsNotNone(state["implementation"]["completedAt"])
        state = runtime_state.accept_delivery(
            self.root,
            session_id,
            state["revision"],
            delivery_digest=state["deliveryReview"]["deliveryDigest"],
            user_authorized=True,
        )
        completed_revision = state["revision"]
        with self.assertRaisesRegex(runtime_state.StateError, "terminal session status"):
            runtime_state.validate_session(
                self.root,
                session_id,
                completed_revision,
            )
        _, unchanged = runtime_state.load_state(self.root, session_id)
        self.assertEqual(unchanged["status"], "completed")
        self.assertEqual(unchanged["revision"], completed_revision)
        result = runtime_state.cleanup_session(
            self.root,
            session_id,
            confirm_session=session_id,
            expected_revision=state["revision"],
        )
        self.assertEqual(result["status"], "cleaned")

    def test_full_design_only_can_validate_without_implementation_targets(self) -> None:
        session_id = "full-design-only"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
            ),
        )
        self.assertEqual(state["contract"]["implementationTargets"], [])
        artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        self.assertEqual(state["status"], "validated")

    def test_pass_manifest_rejects_design_bytes_and_fake_screenshot_magic(self) -> None:
        session_id = "screenshot-proof"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
            ),
        )
        design_bytes = b"\x89PNG\r\n\x1a\naccepted design"
        design_artifact = self.artifact_bytes(
            session_id,
            "o1.png",
            design_bytes,
        )
        state = self.settle_output(session_id, design_artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.write_product_target("implemented screenshot proof surface")
        accepted_hash = state["outputs"][0]["sha256"]

        copied_screenshot = self.qa_screenshot(
            session_id,
            "copied-design.png",
            design_bytes,
        )
        copied_manifest = self.fidelity_manifest(
            session_id,
            "copied-design.json",
            output_id="O01",
            accepted_sha256=accepted_hash,
            result="pass",
            screenshot=copied_screenshot,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "screenshot bytes match"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=accepted_hash,
                evidence_artifact=copied_manifest,
                result="pass",
            )

        fake_screenshot = self.qa_screenshot(
            session_id,
            "fake.png",
            b"not an image",
        )
        fake_manifest = self.fidelity_manifest(
            session_id,
            "fake.json",
            output_id="O01",
            accepted_sha256=accepted_hash,
            result="pass",
            screenshot=fake_screenshot,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "matching file magic"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=accepted_hash,
                evidence_artifact=fake_manifest,
                result="pass",
            )

    def test_full_design_only_can_promote_and_cleanup_without_implementation(self) -> None:
        session_id = "full-design-only-promoted"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(workflow_profile="full"),
        )
        artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.promote_output(
            self.root,
            session_id,
            "O01",
            state["revision"],
        )
        result = runtime_state.cleanup_session(
            self.root,
            session_id,
            confirm_session=session_id,
            expected_revision=state["revision"],
        )
        self.assertEqual(result["status"], "cleaned")

    def test_full_begin_requires_targets_and_accepts_later_authorization(self) -> None:
        session_id = "full-late-targets"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
            ),
        )
        artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(runtime_state.StateError, "non-empty implementation target"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
            )
        with self.assertRaisesRegex(runtime_state.StateError, "non-empty implementation target"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_targets=[],
            )

        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt", "src/product.css"],
        )
        self.assertEqual(
            [item["path"] for item in state["implementation"]["targetFingerprints"]],
            ["src/product.txt", "src/product.css"],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "conflict"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_targets=["src/other.txt"],
            )

    def test_standard_profile_requires_passing_runtime_probe_before_completion(self) -> None:
        session_id = "standard-lifecycle"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
        )
        design_artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, design_artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "fidelity QA receipt"):
            runtime_state.complete_implementation(
                self.root,
                session_id,
                state["revision"],
            )
        self.write_product_target("implemented standard product")
        screenshot = self.qa_screenshot(session_id, "standard-runtime.png")
        manifest = self.fidelity_manifest(
            session_id,
            "standard-runtime.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][0]["sha256"],
            evidence_artifact=manifest,
            result="pass",
        )
        state = runtime_state.complete_implementation(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(state["implementation"]["status"], "completed")

    def test_nonpass_fidelity_manifest_without_screenshot_requires_reason(self) -> None:
        session_id = "nonpass-manifest"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
        )
        design_artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, design_artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        accepted_hash = state["outputs"][0]["sha256"]
        missing_reason = self.fidelity_manifest(
            session_id,
            "missing-reason.json",
            output_id="O01",
            accepted_sha256=accepted_hash,
            result="fail",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "reason"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=accepted_hash,
                evidence_artifact=missing_reason,
                result="fail",
            )

        failed_manifest = self.fidelity_manifest(
            session_id,
            "failed.json",
            output_id="O01",
            accepted_sha256=accepted_hash,
            result="fail",
            reason="Target route did not render",
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=accepted_hash,
            evidence_artifact=failed_manifest,
            result="fail",
        )
        receipt = state["implementation"]["fidelityQaReceipts"][-1]
        self.assertEqual(receipt["result"], "fail")
        self.assertIsNone(receipt["screenshotPath"])
        self.assertEqual(receipt["reason"], "Target route did not render")
        _, reloaded = runtime_state.load_state(self.root, session_id)
        self.assertEqual(reloaded["implementation"]["fidelityQaReceipts"][-1], receipt)

    def test_pass_manifest_rejects_missing_or_blank_runtime_probe(self) -> None:
        session_id = "runtime-probe-semantics"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
        )
        artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.write_product_target("implemented runtime probe surface")
        screenshot = self.qa_screenshot(session_id, "probe.png")
        missing_probe = self.fidelity_manifest(
            session_id,
            "missing-probe.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
            include_runtime_probe=False,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "browser runtime probe"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=state["outputs"][0]["sha256"],
                evidence_artifact=missing_probe,
                result="pass",
            )

        blank_probe = self.fidelity_manifest(
            session_id,
            "blank-probe.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
        )
        manifest_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / blank_probe
        )
        manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        trace_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / manifest_payload["runtimeProbe"]["path"]
        )
        trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
        trace_payload["page"].update(
            rootFound=True,
            rootChildElementCount=0,
            visibleTextCharacters=0,
            visibleLandmarkCount=0,
            interactiveElementCount=0,
        )
        trace_path.write_text(json.dumps(trace_payload, sort_keys=True), encoding="utf-8")
        manifest_payload["runtimeProbe"]["sha256"] = runtime_state.sha256_file(trace_path)
        manifest_path.write_text(json.dumps(manifest_payload, sort_keys=True), encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "rootChildElementCount"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=state["outputs"][0]["sha256"],
                evidence_artifact=blank_probe,
                result="pass",
            )

        wrong_url = self.fidelity_manifest(
            session_id,
            "wrong-url.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
        )
        wrong_manifest_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / wrong_url
        )
        wrong_manifest = json.loads(wrong_manifest_path.read_text(encoding="utf-8"))
        wrong_trace_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / wrong_manifest["runtimeProbe"]["path"]
        )
        wrong_trace = json.loads(wrong_trace_path.read_text(encoding="utf-8"))
        wrong_trace["page"]["finalUrl"] = "http://127.0.0.1:3000/test"
        wrong_trace_path.write_text(json.dumps(wrong_trace, sort_keys=True), encoding="utf-8")
        wrong_manifest["runtimeProbe"]["sha256"] = runtime_state.sha256_file(
            wrong_trace_path
        )
        wrong_manifest_path.write_text(
            json.dumps(wrong_manifest, sort_keys=True),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "exact probe URL"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=state["outputs"][0]["sha256"],
                evidence_artifact=wrong_url,
                result="pass",
            )

    def test_micro_profile_refuses_runtime_init_without_durable_state(self) -> None:
        contract = self.write_contract(
            promotion_required=False,
            workflow_profile="micro",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "does not create durable runtime"):
            runtime_state.start_session(
                self.root,
                "micro-function",
                contract,
            )
        self.assertFalse((self.root / ".frontend-workbench").exists())

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "runtime_state.py"),
                "init",
                "--root",
                str(self.root),
                "--session-id",
                "micro-cli",
                "--contract",
                str(contract),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("does not create durable runtime", result.stderr)
        self.assertFalse((self.root / ".frontend-workbench").exists())

    def test_old_snapshot_without_workflow_fields_loads_as_standard(self) -> None:
        session_id = "legacy-snapshot"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
        )
        snapshot = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "state.json"
        )
        payload = json.loads(snapshot.read_text(encoding="utf-8"))
        payload["schemaVersion"] = 1
        payload["contract"]["schemaVersion"] = 1
        payload["contract"].pop("workflowProfile")
        payload["contract"].pop("visualDirectionPolicy")
        payload.pop("implementation")
        payload.pop("visualDirection")
        payload["lineage"].pop("visualDirectionDelta")
        for output in payload["outputs"]:
            output.pop("visualDirectionSha256")
        snapshot.write_text(json.dumps(payload), encoding="utf-8")

        _, state = runtime_state.load_state(self.root, session_id)
        self.assertEqual(state["contract"]["workflowProfile"], "standard")
        self.assertEqual(state["implementation"]["status"], "not-started")
        self.assertNotIn("visualDirection", state)

    def test_v2_snapshot_requires_direction_state_and_output_binding_key(self) -> None:
        session_id = "v2-direction-shape"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
        )
        self.assertEqual(state["schemaVersion"], 2)
        self.assertEqual(state["contract"]["schemaVersion"], 2)
        snapshot = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "state.json"
        )
        original = json.loads(snapshot.read_text(encoding="utf-8"))
        missing_direction = json.loads(json.dumps(original))
        missing_direction.pop("visualDirection")
        runtime_state.atomic_write_json(snapshot, missing_direction)
        with self.assertRaisesRegex(runtime_state.StateError, "visualDirection is required"):
            runtime_state.load_state(self.root, session_id)

        missing_binding = json.loads(json.dumps(original))
        missing_binding["outputs"][0].pop("visualDirectionSha256")
        runtime_state.atomic_write_json(snapshot, missing_binding)
        with self.assertRaisesRegex(runtime_state.StateError, "visualDirectionSha256 is required"):
            runtime_state.load_state(self.root, session_id)

    def test_full_cleanup_requires_completed_implementation(self) -> None:
        session_id = "full-cleanup-gate"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                implementation_targets=["src/product.txt"],
            ),
        )
        artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        state = runtime_state.promote_output(
            self.root,
            session_id,
            "O01",
            state["revision"],
        )
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "implementation completion"):
            runtime_state.cleanup_session(
                self.root,
                session_id,
                confirm_session=session_id,
                expected_revision=state["revision"],
            )

    def test_cli_full_profile_enforces_begin_implementation_gate(self) -> None:
        session_id = "cli-full-gate"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
            ),
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "runtime_state.py"),
                "begin-implementation",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                "1",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Implementation gate failed", result.stderr)

    def test_cli_rejects_forward_full_completion_bypasses(self) -> None:
        session_id = "cli-forward-bypass"
        product_target = self.write_product_target("before implementation")
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                promotion_required=False,
                workflow_profile="full",
            ),
        )
        design_artifact = self.artifact(session_id, "o1.txt", "accepted design")
        state = self.settle_output(session_id, design_artifact)
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        script = ROOT / "scripts" / "runtime_state.py"
        begun = subprocess.run(
            [
                sys.executable,
                str(script),
                "begin-implementation",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                str(state["revision"]),
                "--implementation-target",
                "src/product.txt",
                "--implementation-target",
                "src/product.css",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(begun.returncode, 0, begun.stderr)
        state = json.loads(begun.stdout)
        accepted_hash = state["outputs"][0]["sha256"]

        same_path = subprocess.run(
            [
                sys.executable,
                str(script),
                "record-fidelity-qa",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--output-id",
                "O01",
                "--expected-revision",
                str(state["revision"]),
                "--accepted-artifact-sha256",
                accepted_hash,
                "--evidence-artifact",
                design_artifact,
                "--result",
                "pass",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(same_path.returncode, 2)
        self.assertIn("run-runtime-qa", same_path.stderr)

        self.write_product_target("implemented CLI fidelity surface")
        copied_design = self.qa_evidence(
            session_id,
            "copied-design.txt",
            "accepted design",
        )
        same_digest = subprocess.run(
            [
                sys.executable,
                str(script),
                "record-fidelity-qa",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--output-id",
                "O01",
                "--expected-revision",
                str(state["revision"]),
                "--accepted-artifact-sha256",
                accepted_hash,
                "--evidence-artifact",
                copied_design,
                "--result",
                "pass",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(same_digest.returncode, 2)
        self.assertIn("run-runtime-qa", same_digest.stderr)

        real_evidence = self.qa_evidence(
            session_id,
            "real-fidelity.json",
            '{"result":"PASS","source":"browser"}',
        )
        linked_evidence = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "qa"
            / "linked-fidelity.json"
        )
        linked_evidence.symlink_to(Path(real_evidence).name)
        symlinked = subprocess.run(
            [
                sys.executable,
                str(script),
                "record-fidelity-qa",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--output-id",
                "O01",
                "--expected-revision",
                str(state["revision"]),
                "--accepted-artifact-sha256",
                accepted_hash,
                "--evidence-artifact",
                "qa/linked-fidelity.json",
                "--result",
                "pass",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(symlinked.returncode, 2)
        self.assertIn("run-runtime-qa", symlinked.stderr)

        arbitrary_text = self.qa_evidence(
            session_id,
            "assertions.txt",
            "PASS: looks close enough",
        )
        arbitrary = subprocess.run(
            [
                sys.executable,
                str(script),
                "record-fidelity-qa",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--output-id",
                "O01",
                "--expected-revision",
                str(state["revision"]),
                "--accepted-artifact-sha256",
                accepted_hash,
                "--evidence-artifact",
                arbitrary_text,
                "--result",
                "pass",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(arbitrary.returncode, 2)
        self.assertIn("run-runtime-qa", arbitrary.stderr)

        screenshot = self.qa_screenshot(session_id, "fidelity.png")
        qa_manifest = self.fidelity_manifest(
            session_id,
            "fidelity.json",
            output_id="O01",
            accepted_sha256=accepted_hash,
            result="pass",
            screenshot=screenshot,
        )
        recorded_state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=accepted_hash,
            evidence_artifact=qa_manifest,
            result="pass",
        )

        product_target.write_text("changed after runtime QA", encoding="utf-8")
        stale_source = subprocess.run(
            [
                sys.executable,
                str(script),
                "complete-implementation",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                str(recorded_state["revision"]),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(stale_source.returncode, 2)
        self.assertIn("implementation snapshot", stale_source.stderr)

        product_target.write_text("implemented CLI fidelity surface", encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "complete-implementation",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                str(recorded_state["revision"]),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        completed_state = json.loads(completed.stdout)
        self.assertEqual(completed_state["status"], "awaiting-user-review")
        accepted = subprocess.run(
            [
                sys.executable,
                str(script),
                "accept-delivery",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                str(completed_state["revision"]),
                "--delivery-digest",
                completed_state["deliveryReview"]["deliveryDigest"],
                "--user-authorized",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        accepted_state = json.loads(accepted.stdout)
        self.assertEqual(accepted_state["status"], "completed")
        fingerprints = completed_state["implementation"]["targetFingerprints"]
        self.assertNotEqual(
            fingerprints[0]["baselineSha256"],
            fingerprints[0]["completionSha256"],
        )

    def test_validation_blocks_pending_required_output(self) -> None:
        session_id = "pending-session"
        runtime_state.start_session(self.root, session_id, self.write_contract())
        state, errors = runtime_state.validate_session(self.root, session_id, 1)
        self.assertEqual(state["status"], "blocked")
        self.assertIn("required output O01 is pending", errors)

    def test_resume_turns_unknown_generation_into_blocked(self) -> None:
        session_id = "resume-session"
        runtime_state.start_session(self.root, session_id, self.write_contract())
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", 1
        )
        state = runtime_state.resume_session(
            self.root, session_id, state["revision"]
        )
        output = state["outputs"][0]
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(output["status"], "blocked")
        self.assertEqual(output["problem"]["code"], "unknown_outcome")

    def test_resume_reconciles_completed_atomic_promotion(self) -> None:
        session_id = "reconcile-session"
        runtime_state.start_session(self.root, session_id, self.write_contract())
        artifact = self.artifact(session_id, "o1.txt", "already copied")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        destination = self.root / "promoted" / "o1.txt"
        destination.write_text("already copied", encoding="utf-8")
        state = runtime_state.resume_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(state["status"], "promoted")
        self.assertEqual(state["outputs"][0]["status"], "promoted")

    def test_serial_generation_and_dependencies_are_enforced(self) -> None:
        session_id = "serial-session"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(two_outputs=True, promotion_required=False),
        )
        with self.assertRaisesRegex(runtime_state.StateError, "dependencies"):
            runtime_state.mark_output(
                self.root, session_id, "O02", "generating", 1
            )
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", 1
        )
        with self.assertRaisesRegex(runtime_state.StateError, "Only one output"):
            runtime_state.mark_output(
                self.root, session_id, "O02", "generating", state["revision"]
            )

    def test_checkpoint_requires_user_approval_and_blocks_next_output(self) -> None:
        session_id = "approval-session"
        runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                two_outputs=True,
                promotion_required=False,
                approval_required=True,
            ),
        )
        artifact = self.artifact(session_id, "o1.txt", "reviewed output")
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", 1
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=artifact,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "must enter awaiting-approval"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "accepted",
                state["revision"],
                artifact=artifact,
            )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "awaiting-approval",
            state["revision"],
            artifact=artifact,
        )
        awaiting_revision = state["revision"]
        awaiting_hash = state["outputs"][0]["sha256"]
        with self.assertRaisesRegex(runtime_state.StateError, "await approval"):
            runtime_state.mark_output(
                self.root, session_id, "O02", "generating", state["revision"]
            )
        with self.assertRaisesRegex(runtime_state.StateError, "user-authorized"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "accepted",
                state["revision"],
                artifact=artifact,
            )
        other_artifact = self.artifact(session_id, "o1-other.txt", "unreviewed output")
        with self.assertRaisesRegex(runtime_state.StateError, "same reviewed artifact"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "accepted",
                state["revision"],
                artifact=other_artifact,
                user_authorized=True,
            )
        _, unchanged = runtime_state.load_state(self.root, session_id)
        self.assertEqual(unchanged["revision"], awaiting_revision)
        self.assertEqual(unchanged["outputs"][0]["status"], "awaiting-approval")
        self.assertEqual(unchanged["outputs"][0]["artifact"], artifact)
        self.assertEqual(unchanged["outputs"][0]["sha256"], awaiting_hash)
        self.assertFalse(unchanged["outputs"][0]["userAuthorized"])

        reviewed_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / artifact
        )
        reviewed_path.write_text("changed after review", encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "changed while awaiting approval"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "accepted",
                state["revision"],
                artifact=artifact,
                user_authorized=True,
            )
        _, unchanged = runtime_state.load_state(self.root, session_id)
        self.assertEqual(unchanged["revision"], awaiting_revision)
        self.assertEqual(unchanged["outputs"][0]["status"], "awaiting-approval")
        self.assertEqual(unchanged["outputs"][0]["artifact"], artifact)
        self.assertEqual(unchanged["outputs"][0]["sha256"], awaiting_hash)
        self.assertFalse(unchanged["outputs"][0]["userAuthorized"])

        reviewed_path.write_text("reviewed output", encoding="utf-8")
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
            user_authorized=True,
        )
        self.assertTrue(state["outputs"][0]["userAuthorized"])
        state = runtime_state.mark_output(
            self.root, session_id, "O02", "generating", state["revision"]
        )
        self.assertEqual(state["outputs"][1]["status"], "generating")

    def test_contract_dependency_cycle_is_rejected(self) -> None:
        contract = json.loads(
            self.write_contract(two_outputs=True, cycle=True).read_text(encoding="utf-8")
        )
        errors = runtime_state.validate_contract(contract)
        self.assertTrue(any("cycle" in error for error in errors))

    def test_state_shape_rejects_two_concurrent_outputs(self) -> None:
        session_id = "invalid-concurrency"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(two_outputs=True, promotion_required=False),
        )
        state["outputs"][0]["status"] = "generating"
        state["outputs"][1]["status"] = "reviewing"
        state["outputs"][1]["artifact"] = "artifacts/not-created.txt"
        state["outputs"][1]["sha256"] = "0" * 64
        errors = runtime_state.validate_state_shape(state, session_id)
        self.assertTrue(any("only one output" in error for error in errors))

    def test_revision_conflict_is_rejected(self) -> None:
        session_id = "revision-session"
        runtime_state.start_session(self.root, session_id, self.write_contract())
        with self.assertRaisesRegex(runtime_state.StateError, "Revision conflict"):
            runtime_state.mark_output(
                self.root, session_id, "O01", "generating", 99
            )

    def test_cleanup_refuses_unpromoted_accepted_artifact(self) -> None:
        session_id = "cleanup-session"
        runtime_state.start_session(self.root, session_id, self.write_contract())
        artifact = self.artifact(session_id, "o1.txt", "keep me")
        state = self.settle_output(session_id, artifact)
        with self.assertRaisesRegex(runtime_state.StateError, "not promoted"):
            runtime_state.cleanup_session(
                self.root,
                session_id,
                confirm_session=session_id,
                expected_revision=state["revision"],
                discard_unpromoted=True,
            )

    def test_guarded_replace_keeps_backup(self) -> None:
        session_id = "replace-session"
        runtime_state.start_session(self.root, session_id, self.write_contract())
        artifact = self.artifact(session_id, "o1.txt", "new value")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        destination = self.root / "promoted" / "o1.txt"
        destination.write_text("old value", encoding="utf-8")
        old_hash = runtime_state.sha256_file(destination)
        state = runtime_state.promote_output(
            self.root,
            session_id,
            "O01",
            state["revision"],
            replace=True,
            expected_destination_hash=old_hash,
        )
        self.assertEqual(state["status"], "promoted")
        self.assertEqual(destination.read_text(encoding="utf-8"), "new value")
        backup = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "backups"
            / f"O01-{old_hash}"
        )
        self.assertEqual(backup.read_text(encoding="utf-8"), "old value")

    def test_full_contract_requires_intent_policy_and_supported_checkpoint(self) -> None:
        contract = json.loads(
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
            ).read_text(encoding="utf-8")
        )
        for field in (
            "productIntent",
            "visualArtifactPolicy",
            "visualDirectionPolicy",
            "checkpointMode",
        ):
            invalid = dict(contract)
            invalid.pop(field)
            self.assertTrue(
                any(field in error for error in runtime_state.validate_contract(invalid)),
                field,
            )

        invalid = json.loads(json.dumps(contract))
        invalid["productIntent"]["representativeScenarios"] = ["Only one scenario"]
        self.assertTrue(
            any("representativeScenarios" in error for error in runtime_state.validate_contract(invalid))
        )

        invalid = json.loads(json.dumps(contract))
        invalid["visualArtifactPolicy"] = "imagegen-required"
        invalid["checkpointMode"] = "continuous"
        self.assertTrue(any("checkpointMode" in error for error in runtime_state.validate_contract(invalid)))

        invalid["checkpointMode"] = "review-before-implementation"
        self.assertTrue(any("approvalRequired" in error for error in runtime_state.validate_contract(invalid)))

        invalid["outputs"][0]["approvalRequired"] = True
        self.assertEqual(runtime_state.validate_contract(invalid), [])

    def test_operational_metadata_policy_is_fail_closed_and_context_bound(self) -> None:
        base = json.loads(
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            base["operationalMetadataPolicy"],
            runtime_state.default_operational_metadata_policy(),
        )

        absent_policy = json.loads(json.dumps(base))
        absent_policy.pop("operationalMetadataPolicy")
        contract_path = self.root / "contract-without-operational-policy.json"
        contract_path.write_text(json.dumps(absent_policy), encoding="utf-8")
        state = runtime_state.start_session(
            self.root,
            "operational-default",
            contract_path,
        )
        self.assertEqual(
            state["contract"]["operationalMetadataPolicy"],
            runtime_state.default_operational_metadata_policy(),
        )
        self.assertEqual(
            runtime_state.compact_handoff(self.root, "operational-default")[
                "operationalMetadataPolicy"
            ],
            runtime_state.default_operational_metadata_policy(),
        )

        valid_claim = {
            "id": "offline-boundary",
            "surfaceId": "P01",
            "states": ["default"],
            "meaning": "The user requires the verification state on this view.",
            "authority": "user-request",
            "sourceRef": "current-user-request",
        }
        declared = json.loads(json.dumps(base))
        declared["operationalMetadataPolicy"]["requiredClaims"] = [valid_claim]
        self.assertEqual(runtime_state.validate_contract(declared), [])
        self.assertNotEqual(
            runtime_state.lifecycle_plan_digest(base),
            runtime_state.lifecycle_plan_digest(declared),
        )

        unknown_surface = json.loads(json.dumps(declared))
        unknown_surface["operationalMetadataPolicy"]["requiredClaims"][0][
            "surfaceId"
        ] = "missing"
        self.assertTrue(
            any(
                "unknown surface" in error
                for error in runtime_state.validate_contract(unknown_surface)
            )
        )

        uncovered_state = json.loads(json.dumps(declared))
        uncovered_state["operationalMetadataPolicy"]["requiredClaims"][0][
            "states"
        ] = ["offline"]
        self.assertTrue(
            any(
                "uncovered context" in error
                for error in runtime_state.validate_contract(uncovered_state)
            )
        )

        self_authorized = json.loads(json.dumps(declared))
        self_authorized["operationalMetadataPolicy"]["requiredClaims"][0][
            "authority"
        ] = "agent-judgment"
        self.assertTrue(
            any(
                "authority is invalid" in error
                for error in runtime_state.validate_contract(self_authorized)
            )
        )

    def test_init_refuses_legacy_v1_contract(self) -> None:
        contract_path = self.write_contract(promotion_required=False)
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["schemaVersion"] = 1
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "schemaVersion must be 2"):
            runtime_state.start_session(
                self.root,
                "legacy-init-refused",
                contract_path,
            )
        self.assertFalse(
            (
                self.root
                / ".frontend-workbench"
                / "sessions"
                / "legacy-init-refused"
            ).exists()
        )

    def test_full_intent_confirmation_is_digest_bound_and_cli_exact(self) -> None:
        session_id = "intent-gate"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(workflow_profile="full", promotion_required=False),
        )
        digest = state["intentConfirmation"]["productIntentSha256"]
        lifecycle_digest = state["intentConfirmation"]["lifecyclePlanSha256"]
        self.assertEqual(state["qualityGates"]["intent"], "pending")
        with self.assertRaisesRegex(runtime_state.StateError, "confirm-intent"):
            runtime_state.mark_output(self.root, session_id, "O01", "generating", 1)
        with self.assertRaisesRegex(runtime_state.StateError, "digest"):
            runtime_state.confirm_intent(
                self.root,
                session_id,
                1,
                product_intent_sha256="0" * 64,
                lifecycle_plan_sha256=lifecycle_digest,
                teach_back="The product spans all protected domains.",
                user_authorized=True,
            )
        with self.assertRaisesRegex(runtime_state.StateError, "lifecycle plan digest"):
            runtime_state.confirm_intent(
                self.root,
                session_id,
                1,
                product_intent_sha256=digest,
                lifecycle_plan_sha256="0" * 64,
                teach_back="The product spans all protected domains.",
                user_authorized=True,
            )

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "runtime_state.py"),
                "confirm-intent",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                "1",
                "--product-intent-sha256",
                digest,
                "--lifecycle-plan-sha256",
                lifecycle_digest,
                "--teach-back",
                "The product spans all protected domains and both representative scenarios.",
                "--user-authorized",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        confirmed = json.loads(result.stdout)
        self.assertEqual(confirmed["qualityGates"]["intent"], "pass")
        self.assertTrue(confirmed["intentConfirmation"]["userAuthorized"])
        state_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "state.json"
        )
        switched = json.loads(state_path.read_text(encoding="utf-8"))
        switched["contract"]["visualArtifactPolicy"] = "no-imagegen"
        runtime_state.atomic_write_json(state_path, switched)
        with self.assertRaisesRegex(runtime_state.StateError, "lifecyclePlanSha256"):
            runtime_state.load_state(self.root, session_id)

    def test_imagegen_required_full_flow_requires_user_authorized_outputs(self) -> None:
        session_id = "imagegen-approval"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                approval_required=True,
                visual_artifact_policy="imagegen-required",
                checkpoint_mode="review-before-implementation",
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The visual artifact must cover both representative scenarios.",
            user_authorized=True,
        )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
            user_authorized=True,
        )
        wireframe = self.artifact(
            session_id,
            "wireframe.html",
            "<html><body>Agent-authored wireframe</body></html>",
        )
        state = runtime_state.mark_output(self.root, session_id, "O01", "generating", state["revision"])
        with self.assertRaisesRegex(runtime_state.StateError, "imagegen-required.*PNG"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "reviewing",
                state["revision"],
                artifact=wireframe,
            )
        artifact = self.artifact_bytes(
            session_id,
            "imagegen.png",
            self.png_bytes(3, 2),
        )
        with self.assertRaisesRegex(runtime_state.StateError, "provenance receipt"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "reviewing",
                state["revision"],
                artifact=artifact,
            )
        provenance, trace, trace_bytes = self.imagegen_provenance(
            session_id,
            "O01",
            artifact,
        )
        session_dir = self.root / ".frontend-workbench" / "sessions" / session_id
        linked_trace = session_dir / "provenance" / "traces" / "linked.jsonl"
        linked_trace.symlink_to("O01.jsonl")
        linked_receipt = json.loads(
            (session_dir / provenance).read_text(encoding="utf-8")
        )
        linked_receipt["tracePath"] = "provenance/traces/linked.jsonl"
        linked_receipt_path = session_dir / "provenance" / "O01-linked.json"
        linked_receipt_path.write_text(
            json.dumps(linked_receipt, sort_keys=True),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "symlinked provenance trace"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "reviewing",
                state["revision"],
                artifact=artifact,
                provenance_receipt="provenance/O01-linked.json",
            )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=artifact,
            provenance_receipt=provenance,
        )
        self.assertEqual(
            state["outputs"][0]["provenance"]["providerAuthenticity"],
            "not-verified",
        )
        trace_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / trace
        )
        trace_path.write_bytes(trace_bytes + b"tampered")
        with self.assertRaisesRegex(runtime_state.StateError, "traceSha256"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "awaiting-approval",
                state["revision"],
                artifact=artifact,
            )
        trace_path.write_bytes(trace_bytes)
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "pending",
            state["revision"],
        )
        self.assertIsNone(state["outputs"][0]["provenance"])
        provenance_batch = self.root / "imagegen-provenance-batch.json"
        provenance_batch.write_text(
            json.dumps(
                [
                    {"outputId": "O01", "status": "generating"},
                    {
                        "outputId": "O01",
                        "status": "reviewing",
                        "artifact": artifact,
                        "provenanceReceipt": provenance,
                    },
                ]
            ),
            encoding="utf-8",
        )
        state = runtime_state.batch_mark(
            self.root,
            session_id,
            state["revision"],
            provenance_batch,
        )
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "awaiting-approval", state["revision"], artifact=artifact
        )
        with self.assertRaisesRegex(runtime_state.StateError, "accepted and user-authorized"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_targets=["src/product.txt"],
            )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
            user_authorized=True,
        )
        state, errors = runtime_state.validate_session(self.root, session_id, state["revision"])
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.assertEqual(state["implementation"]["status"], "in-progress")

    def test_checkpointed_runnable_full_requires_user_authorized_output(self) -> None:
        session_id = "runnable-checkpoint-approval"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                visual_artifact_policy="runnable",
                checkpoint_mode="review-before-implementation",
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The runnable design still requires explicit implementation approval.",
            user_authorized=True,
        )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
            user_authorized=True,
        )
        artifact = self.artifact(session_id, "runnable-design.txt", "agent accepted")
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", state["revision"]
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=artifact,
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
        )
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(runtime_state.StateError, "checkpoint.*user-authorized"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_targets=["src/product.txt"],
            )

        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
            user_authorized=True,
        )
        self.assertTrue(state["outputs"][0]["userAuthorized"])
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.assertEqual(state["implementation"]["status"], "in-progress")

    def test_supersession_records_machine_delta_and_updates_old_session(self) -> None:
        old_id = "planner-old"
        runtime_state.start_session(self.root, old_id, self.write_contract(promotion_required=False))
        new_contract_path = self.write_contract(
            workflow_profile="full",
            promotion_required=False,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "user-authorized supersession"):
            runtime_state.start_session(
                self.root,
                "planner-new",
                new_contract_path,
                supersedes_session_id=old_id,
            )
        state = runtime_state.start_session(
            self.root,
            "planner-new",
            new_contract_path,
            parent_session_id=old_id,
            supersedes_session_id=old_id,
            user_authorized_supersession=True,
        )
        self.assertEqual(state["lineage"]["parentSessionId"], old_id)
        self.assertEqual(state["lineage"]["supersedesSessionId"], old_id)
        delta = state["lineage"]["contractDelta"]
        self.assertNotEqual(delta["fromContractSha256"], delta["toContractSha256"])
        self.assertIn("/productIntent", delta["changedPaths"])
        _, old = runtime_state.load_state(self.root, old_id)
        self.assertEqual(old["status"], "superseded")
        self.assertEqual(old["lineage"]["supersededBySessionId"], "planner-new")

    def test_terminal_rejected_superseded_or_cancelled_session_cannot_be_parent(self) -> None:
        for status in ("rejected", "superseded", "cancelled"):
            with self.subTest(status=status):
                parent_id = f"terminal-parent-{status}"
                runtime_state.start_session(
                    self.root,
                    parent_id,
                    self.write_contract(promotion_required=False),
                )
                parent_dir, parent = runtime_state.load_state(self.root, parent_id)
                parent["status"] = status
                runtime_state.atomic_write_json(parent_dir / "state.json", parent)
                with self.assertRaisesRegex(runtime_state.StateError, "cannot be used as a parent"):
                    runtime_state.start_session(
                        self.root,
                        f"child-{status}",
                        self.write_contract(promotion_required=False),
                        parent_session_id=parent_id,
                    )

    def test_full_quality_gates_end_in_digest_bound_user_acceptance(self) -> None:
        session_id = "delivery-review"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                implementation_targets=["src/product.txt"],
            ),
        )
        artifact = self.artifact(session_id, "design.txt", "accepted design")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(self.root, session_id, state["revision"])
        self.assertEqual(errors, [])
        self.assertEqual(state["qualityGates"]["coverage"], "pass")
        state = runtime_state.begin_implementation(self.root, session_id, state["revision"])
        self.write_product_target("implemented")
        screenshot = self.qa_screenshot(session_id, "runtime.png", self.png_bytes(800, 600))
        manifest = self.fidelity_manifest(
            session_id,
            "runtime.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
            pixel_width=800,
            pixel_height=600,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][0]["sha256"],
            evidence_artifact=manifest,
            result="pass",
        )
        state = runtime_state.complete_implementation(self.root, session_id, state["revision"])
        self.assertEqual(state["status"], "awaiting-user-review")
        self.assertEqual(state["qualityGates"]["runtime"], "pass")
        self.assertEqual(state["qualityGates"]["fidelity"], "pass")
        self.assertEqual(state["qualityGates"]["userAcceptance"], "pending")
        digest = state["deliveryReview"]["deliveryDigest"]
        with self.assertRaisesRegex(runtime_state.StateError, "delivery digest"):
            runtime_state.accept_delivery(
                self.root,
                session_id,
                state["revision"],
                delivery_digest="0" * 64,
                user_authorized=True,
            )
        state = runtime_state.accept_delivery(
            self.root,
            session_id,
            state["revision"],
            delivery_digest=digest,
            user_authorized=True,
        )
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["qualityGates"]["userAcceptance"], "pass")

    def test_fidelity_manifest_matches_contract_dimensions_and_deduplicates_proof(self) -> None:
        session_id = "fidelity-contract"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                two_outputs=True,
                evidence_equivalence=True,
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="Both default and open states are distinct required outputs.",
            user_authorized=True,
        )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        for output_id in ("O01", "O02"):
            artifact = self.artifact(session_id, f"{output_id}.txt", f"design {output_id}")
            state = runtime_state.mark_output(
                self.root, session_id, output_id, "generating", state["revision"]
            )
            state = runtime_state.mark_output(
                self.root,
                session_id,
                output_id,
                "reviewing",
                state["revision"],
                artifact=artifact,
            )
            state = runtime_state.mark_output(
                self.root,
                session_id,
                output_id,
                "accepted",
                state["revision"],
                artifact=artifact,
            )
        state, errors = runtime_state.validate_session(self.root, session_id, state["revision"])
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.write_product_target("implemented fidelity contract surface")
        screenshot = self.qa_screenshot(session_id, "shared.png", self.png_bytes(800, 600))
        wrong = self.fidelity_manifest(
            session_id,
            "wrong.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
            state="open",
            pixel_width=99,
            pixel_height=600,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "state.*pixelWidth"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O01",
                state["revision"],
                accepted_artifact_sha256=state["outputs"][0]["sha256"],
                evidence_artifact=wrong,
                result="pass",
            )
        first = self.fidelity_manifest(
            session_id,
            "first.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
            pixel_width=800,
            pixel_height=600,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][0]["sha256"],
            evidence_artifact=first,
            result="pass",
        )
        second = self.fidelity_manifest(
            session_id,
            "second.json",
            output_id="O02",
            accepted_sha256=state["outputs"][1]["sha256"],
            result="pass",
            screenshot=screenshot,
            state="open",
            pixel_width=800,
            pixel_height=600,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "duplicate screenshot"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O02",
                state["revision"],
                accepted_artifact_sha256=state["outputs"][1]["sha256"],
                evidence_artifact=second,
                result="pass",
            )
        wrong_justified = self.fidelity_manifest(
            session_id,
            "second-wrong-justification.json",
            output_id="O02",
            accepted_sha256=state["outputs"][1]["sha256"],
            result="pass",
            screenshot=screenshot,
            state="open",
            pixel_width=800,
            pixel_height=600,
            evidence_equivalent_to="O01",
            equivalence_justification="The same captured frame proves a deliberate no-visual-delta transition.",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "equivalence.*contract"):
            self.record_fidelity_qa(
                self.root,
                session_id,
                "O02",
                state["revision"],
                accepted_artifact_sha256=state["outputs"][1]["sha256"],
                evidence_artifact=wrong_justified,
                result="pass",
            )
        justified = self.fidelity_manifest(
            session_id,
            "second-justified.json",
            output_id="O02",
            accepted_sha256=state["outputs"][1]["sha256"],
            result="pass",
            screenshot=screenshot,
            state="open",
            pixel_width=800,
            pixel_height=600,
            evidence_equivalent_to="O01",
            equivalence_justification=(
                "The open state intentionally has no visual delta from default."
            ),
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O02",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][1]["sha256"],
            evidence_artifact=justified,
            result="pass",
        )
        self.assertEqual(len(state["implementation"]["fidelityQaReceipts"]), 2)

    def test_duplicate_fidelity_uses_only_latest_receipt_per_other_output(self) -> None:
        session_id = "latest-fidelity-only"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                two_outputs=True,
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="Each state needs current, independently visited runtime evidence.",
            user_authorized=True,
        )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        for output_id in ("O01", "O02"):
            artifact = self.artifact(session_id, f"latest-{output_id}.txt", output_id)
            state = runtime_state.mark_output(
                self.root, session_id, output_id, "generating", state["revision"]
            )
            state = runtime_state.mark_output(
                self.root,
                session_id,
                output_id,
                "reviewing",
                state["revision"],
                artifact=artifact,
            )
            state = runtime_state.mark_output(
                self.root,
                session_id,
                output_id,
                "accepted",
                state["revision"],
                artifact=artifact,
            )
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_targets=["src/product.txt"],
        )
        self.write_product_target("implemented latest receipt surface")
        shared = self.qa_screenshot(session_id, "stale-shared.png", self.png_bytes(800, 600))
        unique = self.qa_screenshot(session_id, "latest-unique.png", self.png_bytes(801, 600))
        first = self.fidelity_manifest(
            session_id,
            "o1-stale.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=shared,
            pixel_width=800,
            pixel_height=600,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][0]["sha256"],
            evidence_artifact=first,
            result="pass",
        )
        latest = self.fidelity_manifest(
            session_id,
            "o1-latest.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=unique,
            pixel_width=801,
            pixel_height=600,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][0]["sha256"],
            evidence_artifact=latest,
            result="pass",
        )
        second = self.fidelity_manifest(
            session_id,
            "o2-current.json",
            output_id="O02",
            accepted_sha256=state["outputs"][1]["sha256"],
            result="pass",
            screenshot=shared,
            state="open",
            pixel_width=800,
            pixel_height=600,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O02",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][1]["sha256"],
            evidence_artifact=second,
            result="pass",
        )
        self.assertEqual(len(state["implementation"]["fidelityQaReceipts"]), 3)

    def test_batch_mark_is_atomic_bounded_and_handoff_is_read_only(self) -> None:
        session_id = "batch-handoff"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(promotion_required=False),
        )
        artifact = self.artifact(session_id, "batch.txt", "one atomic batch")
        transitions = self.root / "batch.json"
        transitions.write_text(
            json.dumps(
                [
                    {"outputId": "O01", "status": "generating"},
                    {"outputId": "O01", "status": "reviewing", "artifact": artifact},
                    {"outputId": "O01", "status": "accepted", "artifact": artifact},
                ]
            ),
            encoding="utf-8",
        )
        state = runtime_state.batch_mark(
            self.root,
            session_id,
            state["revision"],
            transitions,
        )
        self.assertEqual(state["revision"], 2)
        self.assertEqual(state["outputs"][0]["status"], "accepted")
        before = state["revision"]
        handoff = runtime_state.compact_handoff(self.root, session_id)
        _, unchanged = runtime_state.load_state(self.root, session_id)
        self.assertEqual(unchanged["revision"], before)
        self.assertEqual(handoff["sessionId"], session_id)
        self.assertNotIn("contract", handoff)
        self.assertIn("provider authenticity is not verified", handoff["provenanceBoundary"])
        envelope = handoff["executionEnvelope"]
        envelope_without_digest = dict(envelope)
        envelope_digest = envelope_without_digest.pop("sha256")
        self.assertEqual(
            envelope_digest,
            runtime_state._canonical_sha256(envelope_without_digest),
        )
        self.assertEqual(envelope["runtimeProbes"][0]["route"], "/test")
        self.assertEqual(envelope["runtimeProbes"][0]["adapter"], "agent-browser")
        self.assertIn("complete-implementation", envelope["completionAuthority"])
        self.assertEqual(envelope["renderAttemptPolicy"]["maxCallsPerUserTurn"], 1)
        self.assertFalse(envelope["renderAttemptPolicy"]["autonomousRetryAllowed"])
        self.assertTrue(envelope["renderAttemptPolicy"]["inputRolesImmutable"])
        self.assertTrue(
            any("search engine" in item for item in envelope["forbiddenSubstitutions"])
        )

        invalid_session = "batch-rollback"
        runtime_state.start_session(
            self.root,
            invalid_session,
            self.write_contract(promotion_required=False),
        )
        invalid = self.root / "invalid-batch.json"
        invalid.write_text(
            json.dumps(
                [
                    {"outputId": "O01", "status": "generating"},
                    {"outputId": "O01", "status": "accepted"},
                ]
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "Illegal output transition"):
            runtime_state.batch_mark(self.root, invalid_session, 1, invalid)
        _, unchanged = runtime_state.load_state(self.root, invalid_session)
        self.assertEqual(unchanged["revision"], 1)
        self.assertEqual(unchanged["outputs"][0]["status"], "pending")

        too_many = self.root / "too-many.json"
        too_many.write_text(
            json.dumps([{"outputId": "O01", "status": "pending"}] * 51),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(runtime_state.StateError, "at most 50"):
            runtime_state.batch_mark(self.root, invalid_session, 1, too_many)

    def test_planner_rejected_delivery_cannot_remain_green(self) -> None:
        session_id = "planner-rejected"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                implementation_targets=["src/product.txt"],
            ),
        )
        artifact = self.artifact(session_id, "wrong-product.txt", "polished but wrong")
        state = self.settle_output(session_id, artifact)
        state, errors = runtime_state.validate_session(self.root, session_id, state["revision"])
        self.assertEqual(errors, [])
        state = runtime_state.begin_implementation(self.root, session_id, state["revision"])
        self.write_product_target("wrong but runnable implementation")
        screenshot = self.qa_screenshot(session_id, "wrong-runtime.png")
        manifest = self.fidelity_manifest(
            session_id,
            "wrong-runtime.json",
            output_id="O01",
            accepted_sha256=state["outputs"][0]["sha256"],
            result="pass",
            screenshot=screenshot,
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=state["outputs"][0]["sha256"],
            evidence_artifact=manifest,
            result="pass",
        )
        state = runtime_state.complete_implementation(self.root, session_id, state["revision"])
        state = runtime_state.reject_delivery(
            self.root,
            session_id,
            state["revision"],
            delivery_digest=state["deliveryReview"]["deliveryDigest"],
            reason="The implementation collapses the product to one narrow use case.",
            user_authorized=True,
        )
        self.assertEqual(state["status"], "rejected")
        self.assertEqual(state["qualityGates"]["userAcceptance"], "fail")
        self.assertNotEqual(state["status"], "validated")

    def test_cli_direction_lock_gates_generation_and_binds_artifact(self) -> None:
        session_id = "direction-cli-gate"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                approval_required=True,
                checkpoint_mode="review-before-artifact",
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The visual direction must preserve the confirmed product and coverage.",
            user_authorized=True,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "not locked"):
            runtime_state.mark_output(
                self.root, session_id, "O01", "generating", state["revision"]
            )

        direction_file = self.write_visual_direction()
        lock_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "runtime_state.py"),
                "lock-visual-direction",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                str(state["revision"]),
                "--direction-contract",
                str(direction_file),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(lock_result.returncode, 0, lock_result.stderr)
        state = json.loads(lock_result.stdout)
        self.assertEqual(state["visualDirection"]["status"], "locked")
        self.assertFalse(state["visualDirection"]["userAuthorized"])
        with self.assertRaisesRegex(runtime_state.StateError, "separate user authorization"):
            runtime_state.mark_output(
                self.root, session_id, "O01", "generating", state["revision"]
            )

        authorize_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "runtime_state.py"),
                "lock-visual-direction",
                "--root",
                str(self.root),
                "--session-id",
                session_id,
                "--expected-revision",
                str(state["revision"]),
                "--direction-contract",
                str(direction_file),
                "--user-authorized",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(authorize_result.returncode, 0, authorize_result.stderr)
        state = json.loads(authorize_result.stdout)
        direction_sha = state["visualDirection"]["sha256"]
        artifact = self.artifact(session_id, "direction-bound.txt", "direction instance")
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", state["revision"]
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=artifact,
        )
        self.assertEqual(state["outputs"][0]["visualDirectionSha256"], direction_sha)
        handoff = runtime_state.compact_handoff(self.root, session_id)
        self.assertEqual(handoff["visualDirection"]["sha256"], direction_sha)
        self.assertEqual(
            handoff["visualDirection"]["path"],
            "product-design/visual-direction.json",
        )

    def test_direction_lock_is_semantic_idempotent_and_rejects_replacement(self) -> None:
        session_id = "direction-idempotent"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
            ),
        )
        direction_file = self.write_visual_direction()
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            direction_file,
        )
        locked_revision = state["revision"]
        direction_payload = json.loads(direction_file.read_text(encoding="utf-8"))
        direction_file.write_text(
            json.dumps(direction_payload, indent=4, sort_keys=True),
            encoding="utf-8",
        )
        unchanged = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            locked_revision,
            direction_file,
        )
        self.assertEqual(unchanged["revision"], locked_revision)
        replacement = self.write_visual_direction(
            concept_thesis="A materially different direction that must fork lineage."
        )
        with self.assertRaisesRegex(runtime_state.StateError, "superseding session"):
            runtime_state.lock_visual_direction(
                self.root,
                session_id,
                locked_revision,
                replacement,
            )

    def test_redesign_boundary_keeps_only_declared_regions_and_requires_material_delta(self) -> None:
        direction = json.loads(self.write_visual_direction().read_text(encoding="utf-8"))
        direction["redesignBoundary"] = {
            "mode": "preserve-only",
            "preserveRegions": [
                {
                    "regionId": "primary-sidebar",
                    "sourceRef": "screenshot:operations-current",
                    "invariants": [
                        "Preserve sidebar information architecture",
                        "Preserve sidebar labels",
                    ],
                }
            ],
            "replaceRegions": [
                {
                    "regionId": "dashboard-main",
                    "sourceRef": "screenshot:operations-current",
                    "mustChange": [
                        "macro-layout",
                        "information-hierarchy",
                        "module-topology",
                        "typography-scale",
                        "surface-language",
                    ],
                    "minimumChangedDimensions": 4,
                }
            ],
            "forbiddenCarryover": [
                "Equal KPI card grid",
                "Repeated donut-card rail",
                "Unchanged main-content composition",
            ],
        }
        direction["contentDistribution"] = {
            "strategy": "progressive-scroll",
            "firstViewportRule": "Show current-day priorities and the next meaningful action before secondary reporting.",
            "bands": [
                {
                    "id": "dashboard-top",
                    "placement": "first-viewport",
                    "responsibilities": [
                        "Current overview and urgent daily context",
                        "Upcoming work and empty-dispatch state",
                    ],
                    "contentIds": [
                        "daily-context",
                        "upcoming-work",
                        "empty-dispatch",
                    ],
                },
                {
                    "id": "dashboard-continuation",
                    "placement": "continuation",
                    "responsibilities": [
                        "Completion and readiness detail",
                        "Secondary supporting information",
                    ],
                    "contentIds": [
                        "completion-status",
                        "readiness-reporting",
                        "supporting-records",
                    ],
                },
            ],
            "sharedContentIds": [],
            "mustRemainReachable": [
                "All current values and actions",
                "Completion, safety, and equipment-readiness detail",
            ],
        }
        self.assertEqual(runtime_state.validate_visual_direction_contract(direction), [])

        broadened = json.loads(json.dumps(direction))
        broadened["redesignBoundary"]["replaceRegions"][0]["regionId"] = "primary-sidebar"
        errors = runtime_state.validate_visual_direction_contract(broadened)
        self.assertTrue(any("both preserved and replaced" in error for error in errors), errors)

        cosmetic_only = json.loads(json.dumps(direction))
        cosmetic_only["redesignBoundary"]["replaceRegions"][0]["mustChange"] = [
            "surface-language",
            "color-role-expression",
        ]
        cosmetic_only["redesignBoundary"]["replaceRegions"][0][
            "minimumChangedDimensions"
        ] = 4
        errors = runtime_state.validate_visual_direction_contract(cosmetic_only)
        self.assertTrue(any("must be between" in error for error in errors), errors)

        missing_continuation = json.loads(json.dumps(direction))
        missing_continuation["contentDistribution"]["bands"] = [
            missing_continuation["contentDistribution"]["bands"][0]
        ]
        errors = runtime_state.validate_visual_direction_contract(missing_continuation)
        self.assertTrue(any("requires first-viewport and continuation" in error for error in errors), errors)

        duplicated_content = json.loads(json.dumps(direction))
        duplicated_content["contentDistribution"]["bands"][1]["contentIds"].append(
            "daily-context"
        )
        errors = runtime_state.validate_visual_direction_contract(duplicated_content)
        self.assertTrue(any("multiple bands without sharedContentIds" in error for error in errors), errors)

        declared_shared = json.loads(json.dumps(duplicated_content))
        declared_shared["contentDistribution"]["sharedContentIds"] = [
            "daily-context"
        ]
        self.assertEqual(
            runtime_state.validate_visual_direction_contract(declared_shared), []
        )

    def test_visual_direction_tampering_blocks_material_transition(self) -> None:
        session_id = "direction-tamper"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The direction is a separate locked design decision.",
            user_authorized=True,
        )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        stored = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "product-design"
            / "visual-direction.json"
        )
        tampered = json.loads(stored.read_text(encoding="utf-8"))
        tampered["conceptThesis"] = "Tampered after lock"
        stored.write_text(json.dumps(tampered), encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "changed after locking"):
            runtime_state.mark_output(
                self.root, session_id, "O01", "generating", state["revision"]
            )
        with self.assertRaisesRegex(runtime_state.StateError, "changed after locking"):
            runtime_state.compact_handoff(self.root, session_id)

    def test_review_before_implementation_authorizes_direction_separately(self) -> None:
        session_id = "direction-implementation-approval"
        state = runtime_state.start_session(
            self.root,
            session_id,
            self.write_contract(
                workflow_profile="full",
                promotion_required=False,
                approval_required=True,
                checkpoint_mode="review-before-implementation",
                implementation_targets=["src/product.txt"],
            ),
        )
        state = runtime_state.confirm_intent(
            self.root,
            session_id,
            state["revision"],
            product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
            lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
            teach_back="The artifact instantiates a separately reviewable direction.",
            user_authorized=True,
        )
        direction_file = self.write_visual_direction()
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            direction_file,
        )
        artifact = self.artifact(session_id, "implementation-review.txt", "reviewed")
        state = runtime_state.mark_output(
            self.root, session_id, "O01", "generating", state["revision"]
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=artifact,
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "awaiting-approval",
            state["revision"],
            artifact=artifact,
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
            user_authorized=True,
        )
        state, errors = runtime_state.validate_session(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(runtime_state.StateError, "separate user authorization"):
            runtime_state.begin_implementation(
                self.root, session_id, state["revision"]
            )
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            direction_file,
            user_authorized=True,
        )
        state = runtime_state.begin_implementation(
            self.root, session_id, state["revision"]
        )
        self.assertEqual(state["implementation"]["status"], "in-progress")

    def test_v3_full_digest_and_authority_receipts_block_contract_relaxation(self) -> None:
        contract_path, structure_path = self.write_v3_contract()
        base = json.loads(contract_path.read_text(encoding="utf-8"))
        changed = json.loads(json.dumps(base))
        changed["outputs"][0]["designEvidenceRequired"] = False
        changed["outputs"][0]["artifactKind"] = "none"
        self.assertNotEqual(
            runtime_state.lifecycle_plan_digest(base),
            runtime_state.lifecycle_plan_digest(changed),
        )
        for mutate in (
            lambda item: item["surfaces"][0].update(route="/changed"),
            lambda item: item["implementationTargets"][0].update(
                surfaceIds=[]
            ),
            lambda item: item["authority"].update(pageStructure="revisable"),
        ):
            candidate = json.loads(json.dumps(base))
            mutate(candidate)
            self.assertNotEqual(
                runtime_state.lifecycle_plan_digest(base),
                runtime_state.lifecycle_plan_digest(candidate),
            )
        reordered = json.loads(json.dumps(base, sort_keys=True))
        self.assertEqual(
            runtime_state.lifecycle_plan_digest(base),
            runtime_state.lifecycle_plan_digest(reordered),
        )

        mismatched = json.loads(json.dumps(base))
        mismatched["structure"]["sha256"] = "0" * 64
        mismatch_path = self.root / "contract-structure-mismatch.json"
        mismatch_path.write_text(json.dumps(mismatched), encoding="utf-8")
        with self.assertRaisesRegex(runtime_state.StateError, "structure.*SHA"):
            runtime_state.start_session(
                self.root,
                "v3-structure-mismatch",
                mismatch_path,
                structure_file=structure_path,
            )

        state = runtime_state.start_session(
            self.root,
            "v3-authority",
            contract_path,
            structure_file=structure_path,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "authority receipt"):
            runtime_state.confirm_intent(
                self.root,
                "v3-authority",
                state["revision"],
                product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
                lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
                teach_back="The complete contract is confirmed.",
                user_authorized=True,
            )
        wrong_receipt = self.write_authority_receipt(
            "wrong-intent-action",
            ["supersede-contract"],
            session_id="v3-authority",
            contract_sha256=runtime_state._canonical_sha256(state["contract"]),
            structure_sha256=state["contract"]["structure"]["sha256"],
            base_contract_sha256="0" * 64,
            result_contract_sha256=runtime_state._canonical_sha256(state["contract"]),
            delta_sha256="0" * 64,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "confirm-intent"):
            runtime_state.confirm_intent(
                self.root,
                "v3-authority",
                state["revision"],
                product_intent_sha256=state["intentConfirmation"]["productIntentSha256"],
                lifecycle_plan_sha256=state["intentConfirmation"]["lifecyclePlanSha256"],
                teach_back="The complete contract is confirmed.",
                user_authorized=True,
                authority_receipt_file=wrong_receipt,
            )
        state = self.confirm_v3("v3-authority", state)
        self.assertEqual(
            state["intentConfirmation"]["authorityReceipt"]["authorizedActions"],
            ["confirm-intent"],
        )
        stored_intent_receipt = json.loads(
            (
                self.root
                / ".frontend-workbench"
                / "sessions"
                / "v3-authority"
                / "authority"
                / "intent.json"
            ).read_text(encoding="utf-8")
        )
        stored_intent_receipt["sessionId"] = "v3-authority-replay"
        replay_path = self.root / "authority-replay.json"
        replay_path.write_text(
            json.dumps(stored_intent_receipt),
            encoding="utf-8",
        )
        replay_state = runtime_state.start_session(
            self.root,
            "v3-authority-replay",
            contract_path,
            structure_file=structure_path,
        )
        with self.assertRaisesRegex(runtime_state.StateError, "replay"):
            runtime_state.confirm_intent(
                self.root,
                "v3-authority-replay",
                replay_state["revision"],
                product_intent_sha256=replay_state["intentConfirmation"]["productIntentSha256"],
                lifecycle_plan_sha256=replay_state["intentConfirmation"]["lifecyclePlanSha256"],
                teach_back="The complete v3 contract is authorized.",
                user_authorized=True,
                authority_receipt_file=replay_path,
            )

        changed["contractId"] = "test-contract-relaxed"
        relaxed_path = self.root / "contract-relaxed.json"
        relaxed_path.write_text(json.dumps(changed), encoding="utf-8")
        relaxed_delta = runtime_state._build_contract_delta(base, changed)
        supersede_only = self.write_authority_receipt(
            "supersede-only",
            ["supersede-contract"],
            session_id="v3-relaxed",
            contract_sha256=runtime_state._canonical_sha256(changed),
            structure_sha256=changed["structure"]["sha256"],
            base_contract_sha256=relaxed_delta["fromContractSha256"],
            result_contract_sha256=relaxed_delta["toContractSha256"],
            delta_sha256=runtime_state._canonical_sha256(relaxed_delta),
        )
        with self.assertRaisesRegex(runtime_state.StateError, "relax-contract"):
            runtime_state.start_session(
                self.root,
                "v3-relaxed",
                relaxed_path,
                structure_file=structure_path,
                supersedes_session_id="v3-authority",
                authority_receipt_file=supersede_only,
            )
        relaxed_receipt = self.write_authority_receipt(
            "supersede-relaxed",
            ["supersede-contract", "relax-contract"],
            session_id="v3-relaxed",
            contract_sha256=runtime_state._canonical_sha256(changed),
            structure_sha256=changed["structure"]["sha256"],
            base_contract_sha256=relaxed_delta["fromContractSha256"],
            result_contract_sha256=relaxed_delta["toContractSha256"],
            delta_sha256=runtime_state._canonical_sha256(relaxed_delta),
        )
        replacement = runtime_state.start_session(
            self.root,
            "v3-relaxed",
            relaxed_path,
            structure_file=structure_path,
            supersedes_session_id="v3-authority",
            authority_receipt_file=relaxed_receipt,
        )
        self.assertIn("/outputs", replacement["lineage"]["contractDelta"]["changedPaths"])
        self.assertTrue(replacement["lineage"]["contractDelta"]["relaxations"])
        self.assertIn(
            "relax-contract",
            replacement["lineage"]["authorityReceipt"]["authorizedActions"],
        )
        replacement_state_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / "v3-relaxed"
            / "state.json"
        )
        canonical_replacement = json.loads(
            replacement_state_path.read_text(encoding="utf-8")
        )
        tampered_replacement = json.loads(json.dumps(canonical_replacement))
        tampered_replacement["lineage"]["contractDelta"]["relaxations"] = []
        runtime_state.atomic_write_json(replacement_state_path, tampered_replacement)
        with self.assertRaisesRegex(runtime_state.StateError, "canonical predecessor delta"):
            runtime_state.load_state(self.root, "v3-relaxed")
        runtime_state.atomic_write_json(replacement_state_path, canonical_replacement)

    def test_v3_batch_rejects_duplicate_outputs_and_render_budget_is_enforced(self) -> None:
        contract_path, structure_path = self.write_v3_contract(
            session_suffix="budget",
            artifact_kind="imagegen",
            visual_artifact_policy="runnable",
            render_budget={
                "maxCallsTotal": 1,
                "maxAttemptsPerOutput": 1,
                "maxConceptResets": 0,
            },
        )
        session_id = "v3-render-budget"
        state = runtime_state.start_session(
            self.root,
            session_id,
            contract_path,
            structure_file=structure_path,
        )
        state = self.confirm_v3(session_id, state)
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        render_brief = self.render_brief(session_id, state, "O01")
        duplicate = self.root / "v3-duplicate-batch.json"
        duplicate.write_text(
            json.dumps(
                [
                    {"outputId": "O01", "status": "generating"},
                    {"outputId": "O01", "status": "pending"},
                ]
            ),
            encoding="utf-8",
        )
        revision = state["revision"]
        with self.assertRaisesRegex(runtime_state.StateError, "duplicate outputId"):
            runtime_state.batch_mark(
                self.root,
                session_id,
                revision,
                duplicate,
            )
        _, unchanged = runtime_state.load_state(self.root, session_id)
        self.assertEqual(unchanged["revision"], revision)
        self.assertEqual(unchanged["renderUsage"]["callsTotal"], 0)

        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "generating",
            state["revision"],
            render_brief=render_brief,
        )
        self.assertEqual(state["renderUsage"]["callsTotal"], 1)
        self.assertEqual(state["renderUsage"]["attemptsByOutput"], {"O01": 1})
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "pending",
            state["revision"],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "render budget"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "generating",
                state["revision"],
                render_brief=render_brief,
            )
        with self.assertRaisesRegex(runtime_state.StateError, "concept reset"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "generating",
                state["revision"],
                concept_reset=True,
                render_brief=render_brief,
            )

        reset_contract, reset_structure = self.write_v3_contract(
            session_suffix="concept-reset",
            artifact_kind="imagegen",
            render_budget={
                "maxCallsTotal": 2,
                "maxAttemptsPerOutput": 2,
                "maxConceptResets": 1,
            },
        )
        reset_id = "v3-concept-reset"
        reset_state = runtime_state.start_session(
            self.root,
            reset_id,
            reset_contract,
            structure_file=reset_structure,
        )
        reset_state = self.confirm_v3(reset_id, reset_state)
        reset_state = runtime_state.lock_visual_direction(
            self.root,
            reset_id,
            reset_state["revision"],
            self.write_visual_direction(),
        )
        reset_render_brief = self.render_brief(reset_id, reset_state, "O01")
        reset_state = runtime_state.mark_output(
            self.root,
            reset_id,
            "O01",
            "generating",
            reset_state["revision"],
            render_brief=reset_render_brief,
        )
        reset_state = runtime_state.mark_output(
            self.root,
            reset_id,
            "O01",
            "blocked",
            reset_state["revision"],
            code="REVISE_DIRECTION",
            retryable=True,
            next_action="Return to Product Design before another render.",
        )
        reset_receipt = self.write_authority_receipt(
            "concept-reset",
            ["reset-concept"],
            session_id=reset_id,
            contract_sha256=runtime_state._canonical_sha256(
                reset_state["contract"]
            ),
            structure_sha256=reset_state["contract"]["structure"]["sha256"],
        )
        reset_state = runtime_state.mark_output(
            self.root,
            reset_id,
            "O01",
            "generating",
            reset_state["revision"],
            concept_reset=True,
            authority_receipt_file=reset_receipt,
            render_brief=reset_render_brief,
        )
        self.assertEqual(reset_state["renderUsage"]["callsTotal"], 2)
        self.assertEqual(reset_state["renderUsage"]["conceptResets"], 1)

    def test_v3_direction_only_runtime_qa_does_not_require_design_artifact(self) -> None:
        contract_path, structure_path = self.write_v3_contract(
            session_suffix="direction-only",
            design_evidence_required=False,
            runtime_evidence_required=True,
            artifact_kind="none",
        )
        session_id = "v3-direction-only"
        state = runtime_state.start_session(
            self.root,
            session_id,
            contract_path,
            structure_file=structure_path,
        )
        state = self.confirm_v3(session_id, state)
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        self.assertEqual(state["outputs"][0]["status"], "pending")
        with self.assertRaisesRegex(runtime_state.StateError, "implementation plan"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
            )
        plan = self.write_implementation_plan(session_id, state)
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_plan_file=plan,
        )
        direction_sha = state["visualDirection"]["sha256"]
        self.write_product_target("direction-only implementation")
        screenshot = self.qa_screenshot(
            session_id,
            "direction-only.png",
            self.png_bytes(800, 600),
        )
        manifest = self.fidelity_manifest(
            session_id,
            "direction-only.json",
            output_id="O01",
            accepted_sha256=None,
            result="pass",
            screenshot=screenshot,
            pixel_width=800,
            pixel_height=600,
            comparison_mode="direction-only",
            visual_direction_sha256=direction_sha,
            implementation_plan_sha256=state["implementation"]["planSha256"],
        )
        state = self.record_fidelity_qa(
            self.root,
            session_id,
            "O01",
            state["revision"],
            accepted_artifact_sha256=None,
            evidence_artifact=manifest,
            result="pass",
        )
        receipt = state["implementation"]["fidelityQaReceipts"][-1]
        self.assertEqual(receipt["comparisonMode"], "direction-only")
        self.assertIsNone(receipt["acceptedArtifactSha256"])
        self.assertEqual(receipt["visualDirectionSha256"], direction_sha)
        self.assertEqual(
            receipt["implementationPlanSha256"],
            state["implementation"]["planSha256"],
        )
        state_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / "state.json"
        )
        canonical_state = json.loads(state_path.read_text(encoding="utf-8"))
        tampered_plan_receipt = json.loads(json.dumps(canonical_state))
        tampered_plan_receipt["implementation"]["fidelityQaReceipts"][-1][
            "implementationPlanSha256"
        ] = "0" * 64
        runtime_state.atomic_write_json(state_path, tampered_plan_receipt)
        with self.assertRaisesRegex(runtime_state.StateError, "differs from active plan"):
            runtime_state.load_state(self.root, session_id)
        runtime_state.atomic_write_json(state_path, canonical_state)
        state = runtime_state.complete_implementation(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(state["status"], "awaiting-user-review")
        completed_state = json.loads(state_path.read_text(encoding="utf-8"))
        tampered_gallery = json.loads(json.dumps(completed_state))
        tampered_gallery["implementation"]["fidelityQaReceipts"][-1]["route"] = "/tampered"
        runtime_state.atomic_write_json(state_path, tampered_gallery)
        with self.assertRaisesRegex(runtime_state.StateError, "differs from its manifest"):
            runtime_state.accept_delivery(
                self.root,
                session_id,
                state["revision"],
                delivery_digest=state["deliveryReview"]["deliveryDigest"],
                user_authorized=True,
            )
        runtime_state.atomic_write_json(state_path, completed_state)

    def test_v3_imagegen_provenance_follows_artifact_kind_and_anchor_is_bound(self) -> None:
        contract_path, structure_path = self.write_v3_contract(
            session_suffix="anchor",
            artifact_kind="imagegen",
            two_outputs=True,
            anchor_second=True,
            visual_artifact_policy="runnable",
        )
        session_id = "v3-imagegen-anchor"
        state = runtime_state.start_session(
            self.root,
            session_id,
            contract_path,
            structure_file=structure_path,
        )
        state = self.confirm_v3(session_id, state)
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        anchor = self.artifact_bytes(session_id, "anchor.png", self.png_bytes(3, 2))
        with self.assertRaisesRegex(runtime_state.StateError, "requires --render-brief"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "generating",
                state["revision"],
            )
        anchor_render_brief = self.render_brief(session_id, state, "O01")
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "generating",
            state["revision"],
            render_brief=anchor_render_brief,
        )
        render_brief_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / anchor_render_brief
        )
        original_render_brief = render_brief_path.read_bytes()
        render_brief_path.write_bytes(original_render_brief + b"\n")
        with self.assertRaisesRegex(runtime_state.StateError, "render brief.*changed"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "reviewing",
                state["revision"],
                artifact=anchor,
            )
        render_brief_path.write_bytes(original_render_brief)
        with self.assertRaisesRegex(runtime_state.StateError, "provenance receipt"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O01",
                "reviewing",
                state["revision"],
                artifact=anchor,
            )
        anchor_provenance, _, _ = self.imagegen_provenance(session_id, "O01", anchor)
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "reviewing",
            state["revision"],
            artifact=anchor,
            provenance_receipt=anchor_provenance,
        )
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=anchor,
        )
        anchor_sha = state["outputs"][0]["sha256"]
        child_render_brief = self.render_brief(session_id, state, "O02")
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O02",
            "generating",
            state["revision"],
            render_brief=child_render_brief,
        )
        self.assertEqual(state["outputs"][1]["anchorArtifactSha256"], anchor_sha)
        child = self.artifact_bytes(session_id, "child.png", self.png_bytes(2, 3))
        child_provenance, _, _ = self.imagegen_provenance(session_id, "O02", child)
        anchor_path = (
            self.root
            / ".frontend-workbench"
            / "sessions"
            / session_id
            / anchor
        )
        original = anchor_path.read_bytes()
        anchor_path.write_bytes(original + b"tampered")
        with self.assertRaisesRegex(runtime_state.StateError, "anchor artifact"):
            runtime_state.mark_output(
                self.root,
                session_id,
                "O02",
                "reviewing",
                state["revision"],
                artifact=child,
                provenance_receipt=child_provenance,
            )
        anchor_path.write_bytes(original)
        state = runtime_state.mark_output(
            self.root,
            session_id,
            "O02",
            "reviewing",
            state["revision"],
            artifact=child,
            provenance_receipt=child_provenance,
        )
        self.assertEqual(state["outputs"][1]["anchorArtifactSha256"], anchor_sha)

    def test_v3_implementation_plan_covers_capabilities_targets_and_outputs(self) -> None:
        contract_path, structure_path = self.write_v3_contract(
            session_suffix="implementation-plan",
            design_evidence_required=False,
            runtime_evidence_required=True,
            artifact_kind="none",
            capability_complexity="foundational",
        )
        session_id = "v3-implementation-plan"
        state = runtime_state.start_session(
            self.root,
            session_id,
            contract_path,
            structure_file=structure_path,
        )
        state = self.confirm_v3(session_id, state)
        state = runtime_state.lock_visual_direction(
            self.root,
            session_id,
            state["revision"],
            self.write_visual_direction(),
        )
        state, errors = runtime_state.validate_session(
            self.root,
            session_id,
            state["revision"],
        )
        self.assertEqual(errors, [])
        weak_decision = {
            "requirementId": "cap-core",
            "selectedApproach": "project-owned",
            "existingOwner": None,
            "candidates": [
                {
                        "name": "new local owner",
                        "kind": "project-owned",
                    "evidenceRef": "repo:architecture/new-local-owner.md",
                }
            ],
            "selectedCandidate": "new local owner",
            "gap": "No existing owner covers the capability.",
            "lifetimeRationale": "The project must own the lifecycle.",
            "obligations": ["Maintain the capability"],
            "validation": ["Run integration checks"],
        }
        weak_plan = self.write_implementation_plan(
            session_id,
            state,
            decisions=[weak_decision],
        )
        with self.assertRaisesRegex(runtime_state.StateError, "at least two candidates"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_plan_file=weak_plan,
            )
        strong_decision = json.loads(json.dumps(weak_decision))
        strong_decision["candidates"].append(
            {
                "name": "external lifecycle owner",
                "kind": "external-dependency",
                "evidenceRef": "repo:research/external-lifecycle-owner.md",
            }
        )
        plan = self.write_implementation_plan(
            session_id,
            state,
            decisions=[strong_decision],
        )
        strong_plan_payload = json.loads(plan.read_text(encoding="utf-8"))
        evidence_ref = strong_plan_payload["capabilityDecisions"][0]["candidates"][0][
            "evidenceRef"
        ]
        evidence_path = self.root / evidence_ref.removeprefix("repo:")
        evidence_bytes = evidence_path.read_bytes()
        evidence_path.unlink()
        with self.assertRaisesRegex(runtime_state.StateError, "existing regular file"):
            runtime_state.begin_implementation(
                self.root,
                session_id,
                state["revision"],
                implementation_plan_file=plan,
            )
        evidence_path.write_bytes(evidence_bytes)
        state = runtime_state.begin_implementation(
            self.root,
            session_id,
            state["revision"],
            implementation_plan_file=plan,
        )
        implementation = state["implementation"]
        self.assertEqual(implementation["planPath"], "implementation/plan.json")
        self.assertRegex(implementation["planSha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            [item["path"] for item in implementation["targetFingerprints"]],
            ["src/product.txt"],
        )

    def test_v3_relaxations_detect_product_ownership_and_complexity_drift(self) -> None:
        contract_path, _ = self.write_v3_contract(
            session_suffix="ownership-relaxation",
            capability_complexity="foundational",
        )
        base = json.loads(contract_path.read_text(encoding="utf-8"))
        base["productModel"]["objects"].append(
            {
                "id": "technical-detail",
                "role": "implementation-detail",
                "parentId": "product",
                "evidenceForObjectIds": [],
            }
        )

        mutations = {
            "primaryObjectId": lambda item: item["surfaces"][0].update(
                primaryObjectId="technical-detail"
            ),
            "role changed": lambda item: item["productModel"]["objects"][1].update(
                role="primary"
            ),
            "parent ownership": lambda item: item["productModel"]["objects"][1].update(
                parentId=None
            ),
            "evidence ownership": lambda item: item["productModel"]["objects"][1].update(
                evidenceForObjectIds=["product"]
            ),
            "complexity demoted": lambda item: item["capabilityRequirements"][0].update(
                complexity="bounded"
            ),
            "ownerObjectId changed": lambda item: item["capabilityRequirements"][0].update(
                ownerObjectId="technical-detail"
            ),
            "capability label changed": lambda item: item["capabilityRequirements"][0].update(
                capability="A renamed capability"
            ),
            "constraints changed": lambda item: item["capabilityRequirements"][0].update(
                constraints=["A different constraint"]
            ),
            "surfaceIds changed": lambda item: item["capabilityRequirements"][0].update(
                surfaceIds=[]
            ),
        }
        for expected, mutate in mutations.items():
            with self.subTest(expected=expected):
                candidate = json.loads(json.dumps(base))
                mutate(candidate)
                relaxations = runtime_state._contract_relaxations(base, candidate)
                self.assertTrue(
                    any(expected in relaxation for relaxation in relaxations),
                    relaxations,
                )

    def test_v3_protected_capabilities_exact_match_required_capability_names(self) -> None:
        contract_path, _ = self.write_v3_contract(
            session_suffix="protected-capability",
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual(runtime_state.validate_contract(contract), [])

        implementation_primary = json.loads(json.dumps(contract))
        implementation_primary["productModel"]["objects"].append(
            {
                "id": "implementation-detail",
                "role": "implementation-detail",
                "parentId": "product",
                "evidenceForObjectIds": [],
            }
        )
        implementation_primary["surfaces"][0]["primaryObjectId"] = (
            "implementation-detail"
        )
        errors = runtime_state.validate_contract(implementation_primary)
        self.assertTrue(
            any("implementation-detail object" in error for error in errors),
            errors,
        )

        mismatched = json.loads(json.dumps(contract))
        mismatched["productIntent"]["protectedCapabilities"] = [
            "render and verify the product surface"
        ]
        errors = runtime_state.validate_contract(mismatched)
        self.assertTrue(
            any("exact-match" in error for error in errors),
            errors,
        )

        optionalized = json.loads(json.dumps(contract))
        optionalized["capabilityRequirements"][0]["required"] = False
        errors = runtime_state.validate_contract(optionalized)
        self.assertTrue(
            any("exact-match" in error for error in errors),
            errors,
        )

        duplicated_owner = json.loads(json.dumps(contract))
        duplicated_owner["capabilityRequirements"].append(
            {
                **duplicated_owner["capabilityRequirements"][0],
                "id": "cap-core-duplicate",
            }
        )
        errors = runtime_state.validate_contract(duplicated_owner)
        self.assertTrue(
            any("exactly one" in error for error in errors),
            errors,
        )

    def test_v3_complex_plan_rejects_ceremonial_candidate_evidence(self) -> None:
        contract_path, _ = self.write_v3_contract(
            session_suffix="plan-evidence",
            capability_complexity="foundational",
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        valid_decision = {
            "requirementId": "cap-core",
            "selectedApproach": "project-owned",
            "existingOwner": None,
            "candidates": [
                {
                    "name": "Project-owned lifecycle owner",
                    "kind": "project-owned",
                    "evidenceRef": "repo:architecture/lifecycle-owner.md",
                },
                {
                    "name": "Framework lifecycle adapter",
                    "kind": "framework",
                    "evidenceRef": "repo:research/framework-adapter.md",
                },
            ],
            "selectedCandidate": "Project-owned lifecycle owner",
            "gap": "No existing owner binds lifecycle evidence to the product contract.",
            "lifetimeRationale": "Project ownership keeps the core evidence semantics stable over time.",
            "obligations": ["Maintain lifecycle compatibility across releases"],
            "validation": ["Exercise contract, runtime, and delivery evidence gates"],
        }
        plan = self.write_implementation_plan(
            "plan-evidence",
            {"contract": contract},
            decisions=[valid_decision],
        )
        valid_plan = json.loads(plan.read_text(encoding="utf-8"))
        self.assertEqual(
            runtime_state.validate_implementation_plan(contract, valid_plan),
            [],
        )

        mutations = {
            "duplicate names": lambda item: item["capabilityDecisions"][0][
                "candidates"
            ][1].update(name="Project-owned lifecycle owner"),
            "duplicate evidenceRef": lambda item: item["capabilityDecisions"][0][
                "candidates"
            ][1].update(evidenceRef="repo:architecture/lifecycle-owner.md"),
            "repo:<relative-path>": lambda item: item["capabilityDecisions"][0][
                "candidates"
            ][0].update(evidenceRef="TBD"),
            "non-project-owned alternative": lambda item: item["capabilityDecisions"][0][
                "candidates"
            ][1].update(kind="project-owned"),
            "selectedCandidate": lambda item: item["capabilityDecisions"][0].update(
                selectedCandidate="project-owned lifecycle owner"
            ),
            "evidence-specific": lambda item: item["capabilityDecisions"][0].update(
                gap="No owner"
            ),
            "lifetime tradeoffs": lambda item: item["capabilityDecisions"][0].update(
                lifetimeRationale="It works"
            ),
            "ceremonial entries": lambda item: item["capabilityDecisions"][0].update(
                obligations=["Maintain"], validation=["Test"]
            ),
        }
        for expected, mutate in mutations.items():
            with self.subTest(expected=expected):
                candidate = json.loads(json.dumps(valid_plan))
                mutate(candidate)
                errors = runtime_state.validate_implementation_plan(
                    contract,
                    candidate,
                )
                self.assertTrue(
                    any(expected in error for error in errors),
                    errors,
                )
        raw_url = json.loads(json.dumps(valid_plan))
        raw_url["capabilityDecisions"][0]["candidates"][0][
            "evidenceRef"
        ] = "https://example.com/unbound"
        errors = runtime_state.validate_implementation_plan(contract, raw_url)
        self.assertTrue(
            any("repo:<relative-path>" in error for error in errors),
            errors,
        )

    def test_v3_complex_external_dependency_allows_evidence_backed_known_fit_tier(self) -> None:
        contract_path, _ = self.write_v3_contract(
            session_suffix="known-fit-graph",
            capability_complexity="complex",
        )
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        decision = {
            "requirementId": "cap-core",
            "decisionTier": "known-fit",
            "selectedApproach": "external-dependency",
            "existingOwner": None,
            "candidates": [
                {
                    "name": "React Flow graph owner",
                    "kind": "external-dependency",
                    "evidenceRef": "repo:evidence/react-flow-fit.md",
                }
            ],
            "selectedCandidate": "React Flow graph owner",
            "gap": "The repository has no graph owner and React Flow covers the declared interactions.",
            "lifetimeRationale": "A maintained graph library avoids owning zoom, pan, selection, and accessibility behavior.",
            "obligations": ["Track compatibility and accessibility across upgrades"],
            "validation": ["Exercise graph selection, keyboard access, zoom, and pan in the browser"],
        }
        plan_path = self.write_implementation_plan(
            "known-fit-graph",
            {"contract": contract},
            decisions=[decision],
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(runtime_state.validate_implementation_plan(contract, plan), [])

        legacy_comparison = json.loads(json.dumps(plan))
        legacy_comparison["capabilityDecisions"][0].pop("decisionTier")
        errors = runtime_state.validate_implementation_plan(contract, legacy_comparison)
        self.assertTrue(any("at least two candidates" in error for error in errors), errors)

        foundational = json.loads(json.dumps(contract))
        foundational["capabilityRequirements"][0]["complexity"] = "foundational"
        foundational_plan = json.loads(json.dumps(plan))
        foundational_plan["contractSha256"] = runtime_state._canonical_sha256(foundational)
        errors = runtime_state.validate_implementation_plan(foundational, foundational_plan)
        self.assertTrue(any("must be comparative" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
