from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_evals  # noqa: E402
import validate_repo  # noqa: E402


def trace_bytes(case: dict[str, Any], variant: str) -> bytes:
    return (
        json.dumps(
            {
                "caseId": case["id"],
                "prompt": case["prompt"],
                "variant": variant,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


class SchemaAndEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry, cls.schemas = run_evals.build_registry(ROOT / "schemas")
        cls.cases, cls.case_errors = run_evals.load_cases(
            ROOT,
            ROOT / "evals" / "cases",
            cls.registry,
            cls.schemas,
        )

    def test_repository_privacy_gate_accepts_only_synthetic_portable_content(self) -> None:
        errors: list[str] = []
        validate_repo.validate_privacy(ROOT, errors)
        self.assertEqual(errors, [])

    def test_repository_privacy_gate_rejects_personal_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            email = "test.person" + "@" + "example.com"
            home_path = "/" + "Users" + "/example/private-project/"
            (root / "notes.txt").write_text(
                f"owner={email}\nworkspace={home_path}\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_repo.validate_privacy(root, errors)
        self.assertTrue(any("email-like" in error for error in errors), errors)
        self.assertTrue(any("home-directory" in error for error in errors), errors)

    @staticmethod
    def measured_result(
        case: dict[str, Any],
        variant: str,
        *,
        input_tokens: int = 100,
        output_tokens: int = 20,
        model_calls: int = 2,
        tool_calls: int = 3,
        duration_ms: int = 1000,
        with_defects: bool = False,
    ) -> dict[str, Any]:
        expected = case["expected"]
        outcome_defects: list[dict[str, str]] = []
        fidelity_defects: list[dict[str, str]] = []
        if with_defects:
            outcome_defects.append(
                {
                    "id": "wrong-outcome",
                    "severity": "major",
                    "summary": "The observed flow did not reach the requested outcome.",
                }
            )
            fidelity_defects.append(
                {
                    "id": "visual-drift",
                    "severity": "minor",
                    "summary": "The rendered output drifted from the accepted reference.",
                }
            )
        source_id = f"{variant}-run-{case['id']}"
        trace_path = f"traces/{variant}-{case['id']}.jsonl"
        return {
            "schemaVersion": 3,
            "caseId": case["id"],
            "variant": variant,
            "invokedSkills": expected["requiredSkills"],
            "plannedOutputIds": expected["plannedOutputIds"],
            "completedOutputIds": expected["completedOutputIds"],
            "missingOutputIds": expected["missingOutputIds"],
            "transformations": expected["requiredTransformations"],
            "finalStatus": expected["finalStatus"],
            "hostFilesOutsideRuntime": [],
            "usage": {
                "inputTokens": input_tokens,
                "cachedInputTokens": input_tokens // 2,
                "outputTokens": output_tokens,
                "reasoningTokens": output_tokens // 4,
                "modelCalls": model_calls,
                "toolCalls": tool_calls,
                "durationMs": duration_ms,
            },
            "defects": {
                "outcome": outcome_defects,
                "fidelity": fidelity_defects,
            },
            "evidence": {
                "captureStatus": "complete",
                "sourceKind": "harness-trace",
                "sourceId": source_id,
                "promptSha256": run_evals.prompt_sha256(case),
                "traceSha256": hashlib.sha256(trace_bytes(case, variant)).hexdigest(),
                "tracePath": trace_path,
            },
        }

    @staticmethod
    def v3_contract() -> dict[str, Any]:
        product_model = {
            "rootObjectId": "project",
            "objects": [
                {
                    "id": "project",
                    "role": "root",
                    "parentId": None,
                    "evidenceForObjectIds": [],
                },
                {
                    "id": "workflow",
                    "role": "primary",
                    "parentId": "project",
                    "evidenceForObjectIds": [],
                },
                {
                    "id": "automated-check",
                    "role": "downstream-evidence",
                    "parentId": "project",
                    "evidenceForObjectIds": ["workflow"],
                },
                {
                    "id": "runner-source",
                    "role": "implementation-detail",
                    "parentId": "automated-check",
                    "evidenceForObjectIds": [],
                },
            ],
            "relations": [
                {
                    "id": "automated-check-evidence",
                    "fromObjectId": "automated-check",
                    "toObjectId": "workflow",
                    "kind": "evidence-for",
                }
            ],
        }
        return {
            "schemaVersion": 3,
            "contractId": "sample-workspace-v3",
            "workflowProfile": "full",
            "implementationTargets": [
                {
                    "path": "web/src/App.tsx",
                    "surfaceIds": ["projects", "process"],
                    "sharedOwner": True,
                }
            ],
            "productIntent": {
                "problem": "Model workflows before attaching executable evidence.",
                "representativeScenarios": [
                    "Create a workflow",
                    "Attach an Automated check to a confirmed path",
                ],
                "requiredDomains": ["workflow-model"],
                "protectedCapabilities": [
                    "Render and inspect an ordered process graph"
                ],
                "antiGoals": ["browser runner-centered project navigation"],
                "successSignals": ["Workflows remain primary"],
            },
            "productModel": product_model,
            "structure": {
                "id": "sample-workspace-structure",
                "path": "structure.json",
                "sha256": "a" * 64,
            },
            "capabilityRequirements": [
                {
                    "id": "cap-process-graph",
                    "capability": "Render and inspect an ordered process graph",
                    "complexity": "foundational",
                    "constraints": ["Preserve typed process semantics"],
                    "ownerObjectId": "workflow",
                    "surfaceIds": ["process"],
                    "required": True,
                }
            ],
            "operationalMetadataPolicy": {
                "defaultVisibility": "hidden-unless-required",
                "requiredClaims": [],
            },
            "visualArtifactPolicy": "imagegen-required",
            "visualDirectionPolicy": "required",
            "checkpointMode": "review-before-implementation",
            "renderBudget": {
                "maxCallsTotal": 4,
                "maxAttemptsPerOutput": 2,
                "maxConceptResets": 1,
            },
            "authority": {
                "pageStructure": "locked",
                "interactionModel": "locked",
                "contentRepartition": "within-surface-only",
            },
            "surfaces": [
                {
                    "id": "projects",
                    "kind": "page",
                    "route": "/projects",
                    "userJob": "Enter a workflow-model project",
                    "primaryObjectId": "project",
                    "shellIds": ["global-shell"],
                    "referenceBindingIds": [],
                },
                {
                    "id": "process",
                    "kind": "page",
                    "route": "/projects/:projectId/processes/:processId",
                    "userJob": "Understand and evolve one workflow",
                    "primaryObjectId": "workflow",
                    "shellIds": ["global-shell", "project-shell"],
                    "referenceBindingIds": ["process-reference"],
                },
            ],
            "edges": [
                {"from": "projects", "to": "process", "trigger": "Open process"}
            ],
            "outputs": [
                {
                    "id": "P01",
                    "surfaceId": "projects",
                    "state": "populated",
                    "viewport": "wide",
                    "scrollPosition": "full-page",
                    "approvalRequired": True,
                    "dependsOn": [],
                    "promotionRequired": False,
                    "promotionTarget": None,
                    "designEvidenceRequired": True,
                    "runtimeEvidenceRequired": True,
                    "artifactKind": "imagegen",
                    "anchorOutputId": None,
                },
                {
                    "id": "P02",
                    "surfaceId": "process",
                    "state": "model-ready",
                    "viewport": "wide",
                    "scrollPosition": "full-page",
                    "approvalRequired": True,
                    "dependsOn": ["P01"],
                    "promotionRequired": False,
                    "promotionTarget": None,
                    "designEvidenceRequired": True,
                    "runtimeEvidenceRequired": True,
                    "artifactKind": "imagegen",
                    "anchorOutputId": "P01",
                },
            ],
        }

    @staticmethod
    def v3_structure(contract: dict[str, Any]) -> dict[str, Any]:
        structure = {
            "schemaVersion": 3,
            "contractId": contract["structure"]["id"],
            "surfaces": [
                {
                    "id": "projects",
                    "route": "/projects",
                    "scenarioIds": ["model-process"],
                    "domainIds": ["workflow-model"],
                },
                {
                    "id": "process",
                    "route": "/projects/:projectId/processes/:processId",
                    "scenarioIds": ["model-process"],
                    "domainIds": ["workflow-model"],
                },
            ],
            "scenarios": [
                {
                    "id": "model-process",
                    "job": "Create and review a workflow",
                    "objectIds": ["project", "workflow", "automated-check"],
                    "entrySurfaceId": "projects",
                    "completionSurfaceId": "process",
                    "recoverySurfaceIds": [],
                }
            ],
            "shells": [
                {
                    "id": "global-shell",
                    "parentShellId": None,
                    "slots": ["brand", "global-navigation", "content"],
                    "invariants": ["Exactly Workspaces and Automated checks are global"],
                },
                {
                    "id": "project-shell",
                    "parentShellId": "global-shell",
                    "slots": ["breadcrumb", "project-navigation"],
                    "invariants": ["Process pages remain inside the project shell"],
                },
            ],
            "objectBindings": [
                {
                    "id": "objects-projects",
                    "surfaceId": "projects",
                    "primaryObjectId": "project",
                    "supportingObjectIds": ["workflow"],
                    "forbiddenDominantObjectIds": ["runner-source"],
                },
                {
                    "id": "objects-process",
                    "surfaceId": "process",
                    "primaryObjectId": "workflow",
                    "supportingObjectIds": ["project", "automated-check"],
                    "forbiddenDominantObjectIds": ["runner-source"],
                },
            ],
            "referenceBindings": [
                {
                    "id": "process-reference",
                    "sourceRef": "references/process-network.png",
                    "sourceSha256": "b" * 64,
                    "roles": ["functional-reference"],
                    "surfaceIds": ["process"],
                    "aspects": ["network-layout"],
                    "constraints": ["Use only for relationship topology"],
                    "mustNotInfluence": ["product-hierarchy", "global-shell"],
                }
            ],
        }
        contract["structure"]["sha256"] = canonical_sha256(structure)
        return structure

    @staticmethod
    def v3_implementation_plan(contract: dict[str, Any]) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "contractId": contract["contractId"],
            "contractSha256": canonical_sha256(contract),
            "structureSha256": contract["structure"]["sha256"],
            "capabilityDecisions": [
                {
                    "requirementId": "cap-process-graph",
                    "selectedApproach": "project-owned",
                    "existingOwner": None,
                    "candidates": [
                        {
                            "name": "React Flow",
                            "kind": "framework",
                            "evidenceRef": "repo:package-recon/react-flow.md",
                            "evidenceSha256": "e" * 64,
                        },
                        {
                            "name": "Project-owned SVG graph",
                            "kind": "project-owned",
                            "evidenceRef": "repo:architecture/process-graph.md",
                            "evidenceSha256": "f" * 64,
                        },
                    ],
                    "selectedCandidate": "Project-owned SVG graph",
                    "gap": "No existing process-graph owner is available.",
                    "lifetimeRationale": "The graph semantics are core product behavior.",
                    "obligations": ["Own keyboard navigation and layout stability"],
                    "validation": ["Exercise selection, branches, and recovery paths"],
                }
            ],
            "targetBindings": [
                {
                    "path": "web/src/App.tsx",
                    "surfaceIds": ["projects", "process"],
                    "capabilityRequirementIds": ["cap-process-graph"],
                }
            ],
            "outputBindings": [
                {
                    "outputId": "P01",
                    "targetPaths": ["web/src/App.tsx"],
                    "capabilityRequirementIds": ["cap-process-graph"],
                },
                {
                    "outputId": "P02",
                    "targetPaths": ["web/src/App.tsx"],
                    "capabilityRequirementIds": ["cap-process-graph"],
                },
            ],
        }

    @staticmethod
    def v3_runtime_state(contract: dict[str, Any]) -> dict[str, Any]:
        state_outputs: list[dict[str, Any]] = []
        for contract_output in contract["outputs"]:
            state_outputs.append(
                {
                    "id": contract_output["id"],
                    "approvalRequired": contract_output["approvalRequired"],
                    "promotionRequired": contract_output["promotionRequired"],
                    "status": "pending",
                    "artifact": None,
                    "sha256": None,
                    "reason": None,
                    "userAuthorized": False,
                    "problem": None,
                    "promotionPath": None,
                    "promotionSha256": None,
                    "visualDirectionSha256": None,
                    "designEvidenceRequired": contract_output[
                        "designEvidenceRequired"
                    ],
                    "runtimeEvidenceRequired": contract_output[
                        "runtimeEvidenceRequired"
                    ],
                    "artifactKind": contract_output["artifactKind"],
                    "anchorOutputId": contract_output["anchorOutputId"],
                    "anchorArtifactSha256": None,
                    "renderBriefPath": None,
                    "renderBriefSha256": None,
                }
            )
        return {
            "schemaVersion": 3,
            "sessionId": "schema-v3-session",
            "revision": 1,
            "status": "active",
            "createdAt": "2026-08-27T00:00:00Z",
            "updatedAt": "2026-08-27T00:00:00Z",
            "contractSha256": canonical_sha256(contract),
            "structureIdentity": contract["structure"],
            "renderUsage": {
                "callsTotal": 0,
                "conceptResets": 0,
                "attemptsByOutput": {output["id"]: 0 for output in contract["outputs"]},
            },
            "contract": contract,
            "outputs": state_outputs,
            "validationErrors": [],
            "promotedAt": None,
            "visualDirection": {
                "status": "pending",
                "path": None,
                "sha256": None,
                "lockedAt": None,
                "userAuthorized": False,
                "authorizedAt": None,
            },
            "implementation": {
                "status": "not-started",
                "startedAt": None,
                "completedAt": None,
                "planPath": None,
                "planSha256": None,
                "fidelityQaReceipts": [],
                "targetFingerprints": [],
            },
            "intentConfirmation": {
                "productIntentSha256": canonical_sha256(contract["productIntent"]),
                "lifecyclePlanSha256": "c" * 64,
                "contractSha256": canonical_sha256(contract),
                "structureSha256": contract["structure"]["sha256"],
                "authorityReceipt": None,
                "teachBack": None,
                "confirmedAt": None,
                "userAuthorized": False,
            },
            "qualityGates": {
                "intent": "pending",
                "coverage": "pending",
                "runtime": "pending",
                "fidelity": "pending",
                "userAcceptance": "pending",
            },
            "deliveryReview": {
                "status": "not-ready",
                "deliveryDigest": None,
                "acceptedAt": None,
                "rejectedAt": None,
                "reason": None,
                "userAuthorized": False,
            },
            "lineage": {
                "parentSessionId": None,
                "supersedesSessionId": None,
                "supersededBySessionId": None,
                "contractDelta": None,
                "visualDirectionDelta": None,
                "authorityReceipt": None,
            },
        }

    def write_result_set(
        self,
        root: Path,
        variant: str,
        *,
        skip_case: str | None = None,
        with_defects: bool = False,
        input_tokens: int = 100,
        output_tokens: int = 20,
        model_calls: int = 2,
        tool_calls: int = 3,
        duration_ms: int = 1000,
        write_traces: bool = True,
    ) -> None:
        root.mkdir(parents=True)
        for case_id, case in self.cases.items():
            if case_id == skip_case:
                continue
            result = self.measured_result(
                case,
                variant,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model_calls=model_calls,
                tool_calls=tool_calls,
                duration_ms=duration_ms,
                with_defects=with_defects,
            )
            if write_traces:
                trace_path = root / result["evidence"]["tracePath"]
                trace_path.parent.mkdir(parents=True, exist_ok=True)
                trace_path.write_bytes(trace_bytes(case, variant))
            (root / f"{case_id}.json").write_text(
                json.dumps(result),
                encoding="utf-8",
            )

    def test_all_eval_cases_and_contract_fixtures_validate(self) -> None:
        self.assertEqual(self.case_errors, [])
        expected_ids = {path.stem for path in (ROOT / "evals" / "cases").glob("*.json")}
        self.assertEqual(set(self.cases), expected_ids)

    def test_score_result_accepts_exact_hard_invariants(self) -> None:
        case = self.cases["locked-route-preservation"]
        result = self.measured_result(case, "workbench")
        schema_errors = run_evals.validate_instance(
            result,
            self.schemas["eval-result.schema.json"],
            self.registry,
            "result",
        )
        self.assertEqual(schema_errors, [])
        self.assertEqual(run_evals.score_result(case, result), [])

    def test_score_result_catches_false_completion_and_stray_file(self) -> None:
        case = self.cases["partial-renderer-failure"]
        result = self.measured_result(case, "workbench")
        result["finalStatus"] = "complete"
        result["hostFilesOutsideRuntime"] = ["design-output.png"]
        failures = run_evals.score_result(case, result)
        self.assertTrue(any("finalStatus" in failure for failure in failures))
        self.assertTrue(any("outside .frontend-workbench" in failure for failure in failures))

    def test_result_schema_requires_measurements_and_defect_assessment(self) -> None:
        result = self.measured_result(
            self.cases["locked-route-preservation"],
            "workbench",
        )
        del result["usage"]
        del result["defects"]
        del result["evidence"]
        errors = run_evals.validate_instance(
            result,
            self.schemas["eval-result.schema.json"],
            self.registry,
            "result",
        )
        self.assertTrue(any("usage" in error for error in errors))
        self.assertTrue(any("defects" in error for error in errors))
        self.assertTrue(any("evidence" in error for error in errors))

    def test_result_semantics_reject_impossible_token_breakdown(self) -> None:
        result = self.measured_result(
            self.cases["locked-route-preservation"],
            "workbench",
        )
        result["usage"]["cachedInputTokens"] = result["usage"]["inputTokens"] + 1
        result["usage"]["reasoningTokens"] = result["usage"]["outputTokens"] + 1
        errors = run_evals.validate_result_semantics(
            result,
            "result",
            self.cases["locked-route-preservation"],
        )
        self.assertTrue(any("cachedInputTokens" in error for error in errors))
        self.assertTrue(any("reasoningTokens" in error for error in errors))

    def test_failed_capture_allows_zero_tokens_only_with_explicit_outcome_defect(self) -> None:
        case = self.cases["locked-route-preservation"]
        result = self.measured_result(
            case,
            "workbench",
            input_tokens=0,
            output_tokens=0,
            model_calls=1,
            duration_ms=1,
            with_defects=True,
        )
        result["evidence"]["captureStatus"] = "failed"
        result["finalStatus"] = "blocked"
        schema_errors = run_evals.validate_instance(
            result,
            self.schemas["eval-result.schema.json"],
            self.registry,
            "result",
        )
        semantic_errors = run_evals.validate_result_semantics(result, "result", case)
        self.assertEqual(schema_errors, [])
        self.assertEqual(semantic_errors, [])

        result["defects"]["outcome"] = []
        semantic_errors = run_evals.validate_result_semantics(result, "result", case)
        self.assertTrue(
            any("requires an explicit outcome defect" in error for error in semantic_errors)
        )

    def test_complete_capture_requires_positive_usage_and_runtime(self) -> None:
        case = self.cases["locked-route-preservation"]
        result = self.measured_result(
            case,
            "workbench",
            input_tokens=0,
            output_tokens=0,
            model_calls=0,
            duration_ms=0,
        )
        schema_errors = run_evals.validate_instance(
            result,
            self.schemas["eval-result.schema.json"],
            self.registry,
            "result",
        )
        semantic_errors = run_evals.validate_result_semantics(result, "result", case)
        for field in ("inputTokens", "outputTokens", "modelCalls", "durationMs"):
            self.assertTrue(any(field in error for error in schema_errors))
            self.assertTrue(any(field in error for error in semantic_errors))

    def test_evidence_receipt_must_match_case_and_cannot_be_reused(self) -> None:
        case = self.cases["locked-route-preservation"]
        baseline = self.measured_result(case, "baseline")
        workbench = self.measured_result(case, "workbench")
        workbench["evidence"] = dict(baseline["evidence"])
        receipt_errors = run_evals.validate_evidence_receipts(
            {case["id"]: baseline},
            {case["id"]: workbench},
        )
        self.assertTrue(any("duplicate evidence source" in error for error in receipt_errors))
        self.assertTrue(any("duplicate traceSha256" in error for error in receipt_errors))
        self.assertTrue(any("duplicate tracePath" in error for error in receipt_errors))

        workbench["evidence"]["promptSha256"] = "1" * 64
        semantic_errors = run_evals.validate_result_semantics(workbench, "result", case)
        self.assertTrue(any("does not match eval case" in error for error in semantic_errors))

        workbench["evidence"]["sourceId"] = "synthetic"
        workbench["evidence"]["traceSha256"] = "0" * 64
        semantic_errors = run_evals.validate_result_semantics(workbench, "result", case)
        self.assertTrue(any("sourceId cannot be a placeholder" in error for error in semantic_errors))
        self.assertTrue(any("placeholder digest" in error for error in semantic_errors))

    def test_trace_receipt_requires_safe_nonsymlink_file_with_matching_digest(self) -> None:
        case = self.cases["locked-route-preservation"]
        result = self.measured_result(case, "workbench")
        with tempfile.TemporaryDirectory() as temp_value:
            results_root = Path(temp_value)
            errors = run_evals.validate_trace_evidence(result, results_root, "result")
            self.assertTrue(any("does not exist" in error for error in errors))

            trace_path = results_root / result["evidence"]["tracePath"]
            trace_path.parent.mkdir(parents=True)
            trace_path.write_bytes(b"tampered trace\n")
            errors = run_evals.validate_trace_evidence(result, results_root, "result")
            self.assertTrue(any("does not match" in error for error in errors))

            trace_path.write_bytes(trace_bytes(case, "workbench"))
            self.assertEqual(
                run_evals.validate_trace_evidence(result, results_root, "result"),
                [],
            )

            outside_trace = results_root / "outside.jsonl"
            outside_trace.write_bytes(trace_bytes(case, "workbench"))
            symlink_path = results_root / "traces" / "linked.jsonl"
            symlink_path.symlink_to(outside_trace)
            result["evidence"]["tracePath"] = "traces/linked.jsonl"
            errors = run_evals.validate_trace_evidence(result, results_root, "result")
            self.assertTrue(any("symlink" in error for error in errors))

            result["evidence"]["tracePath"] = "traces/../outside.jsonl"
            errors = run_evals.validate_trace_evidence(result, results_root, "result")
            self.assertTrue(any("canonical relative path" in error for error in errors))

    def test_fixture_mode_states_that_it_did_not_score_behavior(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = run_evals.main(["--mode", "fixtures", "--cases", "evals/cases"])
        self.assertEqual(status, 0)
        self.assertIn("NO behavioral results were scored", stdout.getvalue())

    def test_cli_requires_an_explicit_mode(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            run_evals.main(["--cases", "evals/cases"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("--mode", stderr.getvalue())

    def test_paired_mode_requires_both_result_sets_and_scorecard(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            run_evals.main(["--mode", "paired", "--cases", "evals/cases"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("requires --baseline-results", stderr.getvalue())

    def test_repository_raw_results_are_confined_to_ignored_runtime_path(self) -> None:
        errors = run_evals.result_location_errors(
            ROOT,
            ROOT / "evals" / "cases",
            "baseline",
        )
        self.assertTrue(any("must be under ignored" in error for error in errors))
        self.assertEqual(
            run_evals.result_location_errors(
                ROOT,
                ROOT / "evals" / "results" / "baseline",
                "baseline",
            ),
            [],
        )

    def test_paired_mode_emits_valid_compact_scorecard(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root = temp_root / "baseline"
            workbench_root = temp_root / "workbench"
            scorecard_path = temp_root / "scorecard.json"
            self.write_result_set(baseline_root, "baseline", with_defects=True)
            self.write_result_set(
                workbench_root,
                "workbench",
                input_tokens=150,
                output_tokens=30,
                model_calls=3,
                tool_calls=4,
                duration_ms=800,
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_evals.main(
                    [
                        "--mode",
                        "paired",
                        "--cases",
                        "evals/cases",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertIn("Paired behavioral eval passed", stderr.getvalue())
            payload = scorecard_path.read_text(encoding="utf-8")
            self.assertNotIn("\n  ", payload)
            scorecard = json.loads(payload)
            schema_errors = run_evals.validate_instance(
                scorecard,
                self.schemas["eval-scorecard.schema.json"],
                self.registry,
                "scorecard",
            )
            self.assertEqual(schema_errors, [])
            case_count = len(self.cases)
            self.assertEqual(scorecard["caseCount"], case_count)
            self.assertEqual(scorecard["variants"]["baseline"]["behavioralPasses"], 0)
            self.assertEqual(
                scorecard["variants"]["workbench"]["behavioralPasses"], case_count
            )
            self.assertEqual(scorecard["change"]["behavioralPassRatePoints"], 100.0)
            self.assertEqual(scorecard["change"]["outcomeDefects"], -case_count)
            self.assertEqual(scorecard["change"]["fidelityDefects"], -case_count)
            self.assertEqual(scorecard["change"]["totalTokensPercent"], 50.0)
            self.assertEqual(scorecard["change"]["outcomeDefectsPercent"], -100.0)
            self.assertEqual(scorecard["change"]["fidelityDefectsPercent"], -100.0)
            self.assertEqual(scorecard["change"]["durationMsPercent"], -20.0)
            self.assertEqual(
                scorecard["cases"][0]["workbench"]["evidence"]["sourceKind"],
                "harness-trace",
            )

    def test_paired_mode_fails_when_one_measured_result_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root = temp_root / "baseline"
            workbench_root = temp_root / "workbench"
            scorecard_path = temp_root / "scorecard.json"
            missing_case = sorted(self.cases)[0]
            self.write_result_set(baseline_root, "baseline")
            self.write_result_set(
                workbench_root,
                "workbench",
                skip_case=missing_case,
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_evals.main(
                    [
                        "--mode",
                        "paired",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn(
                f"missing workbench eval result for case {missing_case}",
                stderr.getvalue(),
            )
            self.assertFalse(scorecard_path.exists())

    def test_paired_mode_writes_scorecard_but_fails_on_workbench_defect(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root = temp_root / "baseline"
            workbench_root = temp_root / "workbench"
            scorecard_path = temp_root / "scorecard.json"
            self.write_result_set(baseline_root, "baseline")
            self.write_result_set(workbench_root, "workbench", with_defects=True)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_evals.main(
                    [
                        "--mode",
                        "paired",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertTrue(scorecard_path.is_file())
            self.assertIn("Paired behavioral eval failed", stderr.getvalue())

    def test_paired_mode_rejects_all_zero_copied_expected_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root = temp_root / "baseline"
            workbench_root = temp_root / "workbench"
            scorecard_path = temp_root / "scorecard.json"
            self.write_result_set(
                baseline_root,
                "baseline",
                input_tokens=0,
                output_tokens=0,
                model_calls=0,
                tool_calls=0,
                duration_ms=0,
            )
            self.write_result_set(
                workbench_root,
                "workbench",
                input_tokens=0,
                output_tokens=0,
                model_calls=0,
                tool_calls=0,
                duration_ms=0,
            )
            result_paths = list(baseline_root.glob("*.json"))
            result_paths.extend(workbench_root.glob("*.json"))
            for result_path in result_paths:
                copied_result = json.loads(result_path.read_text(encoding="utf-8"))
                copied_result["schemaVersion"] = 2
                del copied_result["evidence"]
                result_path.write_text(json.dumps(copied_result), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_evals.main(
                    [
                        "--mode",
                        "paired",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("Paired behavioral scoring failed", stderr.getvalue())
            self.assertFalse(scorecard_path.exists())

    def test_paired_mode_rejects_fabricated_receipts_without_trace_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root = temp_root / "baseline"
            workbench_root = temp_root / "workbench"
            scorecard_path = temp_root / "scorecard.json"
            self.write_result_set(baseline_root, "baseline", write_traces=False)
            self.write_result_set(workbench_root, "workbench", write_traces=False)
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_evals.main(
                    [
                        "--mode",
                        "paired",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("trace", stderr.getvalue().lower())
            self.assertFalse(scorecard_path.exists())

    def test_planner_regression_cases_encode_lifecycle_fail_closed_gates(self) -> None:
        expected_gates = {
            "planner-unconfirmed-multidomain-intent": (
                "intent-confirmation-gate",
                "narrow-to-inspections-only",
            ),
            "planner-imagegen-stage-required": (
                "imagegen-stage-gate",
                "implementation-before-required-artifact",
            ),
            "planner-agent-only-acceptance": (
                "awaiting-user-approval",
                "agent-self-acceptance",
            ),
            "planner-qa-invalid-fidelity-binding": (
                "reject-unbound-fidelity-receipt",
                "accept-context-mismatch",
            ),
            "planner-qa-duplicate-state-evidence": (
                "reject-duplicate-semantic-evidence",
                "reuse-screenshot-without-equivalence",
            ),
            "planner-terminal-session-completion": (
                "honor-user-rejection",
                "reopen-rejected-session",
            ),
        }
        self.assertEqual(
            set(expected_gates),
            {case_id for case_id in self.cases if case_id.startswith("planner-")},
        )
        for case_id, (required_gate, forbidden_bypass) in expected_gates.items():
            with self.subTest(case_id=case_id):
                case = self.cases[case_id]
                expected = case["expected"]
                self.assertIn(required_gate, expected["requiredTransformations"])
                self.assertIn(forbidden_bypass, expected["forbiddenTransformations"])
                if case_id == "planner-qa-invalid-fidelity-binding":
                    self.assertIn(
                        "match-state-viewport-scroll",
                        expected["requiredTransformations"],
                    )
                if case_id == "planner-terminal-session-completion":
                    self.assertIn(
                        "honor-session-lineage",
                        expected["requiredTransformations"],
                    )
                    self.assertIn(
                        "complete-superseded-session",
                        expected["forbiddenTransformations"],
                    )

                valid_result = self.measured_result(case, "workbench")
                self.assertEqual(run_evals.score_result(case, valid_result), [])

                bypass_result = self.measured_result(case, "workbench")
                bypass_result["transformations"] = [
                    *bypass_result["transformations"],
                    forbidden_bypass,
                ]
                bypass_result["finalStatus"] = "complete"
                failures = run_evals.score_result(case, bypass_result)
                self.assertTrue(
                    any("forbidden transformations" in failure for failure in failures)
                )
                self.assertTrue(any("finalStatus" in failure for failure in failures))

    def test_copy_regression_cases_fail_closed_on_operational_metadata(self) -> None:
        default_hidden = self.cases[
            "frontend-copy-operational-metadata-default-hidden"
        ]["expected"]
        self.assertIn(
            "omit-undeclared-operational-metadata",
            default_hidden["requiredTransformations"],
        )
        self.assertIn(
            "self-authorized-trust-copy",
            default_hidden["forbiddenTransformations"],
        )
        self.assertIn(
            "backend-field-as-visibility-authority",
            default_hidden["forbiddenTransformations"],
        )

        declared = self.cases[
            "frontend-copy-declared-operational-boundary"
        ]["expected"]
        self.assertIn(
            "honor-declared-operational-claim",
            declared["requiredTransformations"],
        )
        self.assertIn(
            "omit-undeclared-operational-metadata",
            declared["requiredTransformations"],
        )
        self.assertIn(
            "hide-declared-operational-claim",
            declared["forbiddenTransformations"],
        )

        for case_id in (
            "frontend-copy-operational-metadata-default-hidden",
            "frontend-copy-declared-operational-boundary",
        ):
            with self.subTest(case_id=case_id):
                case = self.cases[case_id]
                valid_result = self.measured_result(case, "workbench")
                self.assertEqual(run_evals.score_result(case, valid_result), [])
                bypass = self.measured_result(case, "workbench")
                bypass["transformations"] = [
                    *bypass["transformations"],
                    "self-authorized-trust-copy",
                ]
                self.assertTrue(
                    any(
                        "forbidden transformations" in failure
                        for failure in run_evals.score_result(case, bypass)
                    )
                )

    def test_planner_full_contract_fixtures_freeze_intent_and_visual_policy(self) -> None:
        fixture_names = (
            "planner-multidomain-contract.json",
            "planner-fidelity-contract.json",
        )
        for fixture_name in fixture_names:
            with self.subTest(fixture=fixture_name):
                fixture = json.loads(
                    (ROOT / "evals" / "fixtures" / fixture_name).read_text(
                        encoding="utf-8"
                    )
                )
                errors = run_evals.validate_instance(
                    fixture,
                    self.schemas["deliverable-coverage.schema.json"],
                    self.registry,
                    fixture_name,
                )
                self.assertEqual(errors, [])
                self.assertEqual(fixture["workflowProfile"], "full")
                self.assertEqual(fixture["visualArtifactPolicy"], "imagegen-required")
                self.assertEqual(
                    fixture["checkpointMode"], "review-before-implementation"
                )
                self.assertTrue(fixture["implementationTargets"])
                self.assertGreaterEqual(
                    len(fixture["productIntent"]["representativeScenarios"]), 2
                )
                self.assertTrue(fixture["productIntent"]["requiredDomains"])
                self.assertEqual(
                    fixture["operationalMetadataPolicy"]["defaultVisibility"],
                    "hidden-unless-required",
                )
                self.assertTrue(
                    all(output["approvalRequired"] for output in fixture["outputs"])
                )

        multidomain = json.loads(
            (
                ROOT
                / "evals"
                / "fixtures"
                / "planner-multidomain-contract.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            set(multidomain["productIntent"]["requiredDomains"]),
            {"inspections", "inventory", "staffing", "logistics"},
        )
        self.assertEqual(
            multidomain["operationalMetadataPolicy"]["requiredClaims"],
            [],
        )

        fidelity = json.loads(
            (
                ROOT
                / "evals"
                / "fixtures"
                / "planner-fidelity-contract.json"
            ).read_text(encoding="utf-8")
        )
        output_contexts = {
            (
                output["state"],
                output["viewport"],
                output["scrollPosition"],
            )
            for output in fidelity["outputs"]
        }
        self.assertEqual(
            output_contexts,
            {
                ("populated", "mobile-390x844", "top"),
                ("offline", "mobile-390x844", "top"),
            },
        )
        self.assertEqual(
            fidelity["operationalMetadataPolicy"]["requiredClaims"][0]["states"],
            ["offline"],
        )

    def test_v3_contract_structure_plan_and_authority_receipt_validate(self) -> None:
        for schema_name in (
            "frontend-structure.schema.json",
            "implementation-plan.schema.json",
            "authority-receipt.schema.json",
            "render-brief.schema.json",
        ):
            self.assertIn(schema_name, self.schemas)

        contract = self.v3_contract()
        structure = self.v3_structure(contract)
        plan = self.v3_implementation_plan(contract)
        receipt = {
            "schemaVersion": 1,
            "kind": "user-message",
            "sessionId": "schema-v3-session",
            "contractSha256": canonical_sha256(contract),
            "structureSha256": contract["structure"]["sha256"],
            "baseContractSha256": "e" * 64,
            "resultContractSha256": canonical_sha256(contract),
            "deltaSha256": "f" * 64,
            "sourceRef": "thread/turn-42",
            "messageSha256": "d" * 64,
            "authorizedActions": ["confirm-intent", "supersede-contract"],
            "statement": "Proceed with the confirmed business-first contract.",
        }
        render_brief = {
            "schemaVersion": 1,
            "outputId": "P02",
            "visualDirectionSha256": "d" * 64,
            "shellIds": ["global-shell", "project-shell"],
            "referenceBindingIds": ["process-reference"],
            "anchorOutputId": "P01",
            "anchorArtifactSha256": "c" * 64,
            "preserve": ["Preserve the accepted project shell"],
            "changeOnly": ["Render only the declared process state"],
        }
        instances = (
            (contract, "deliverable-coverage.schema.json", "v3-contract"),
            (structure, "frontend-structure.schema.json", "v3-structure"),
            (plan, "implementation-plan.schema.json", "v3-plan"),
            (receipt, "authority-receipt.schema.json", "authority-receipt"),
            (render_brief, "render-brief.schema.json", "render-brief"),
        )
        for instance, schema_name, label in instances:
            with self.subTest(schema=schema_name):
                self.assertEqual(
                    run_evals.validate_instance(
                        instance,
                        self.schemas[schema_name],
                        self.registry,
                        label,
                    ),
                    [],
                )
        self.assertEqual(
            validate_repo.validate_v3_bundle_semantics(contract, structure, plan),
            [],
        )

    def test_v3_full_contract_requires_semantic_and_render_fields(self) -> None:
        required_fields = (
            "productModel",
            "structure",
            "capabilityRequirements",
            "implementationTargets",
            "operationalMetadataPolicy",
            "renderBudget",
        )
        for field in required_fields:
            with self.subTest(field=field):
                contract = self.v3_contract()
                del contract[field]
                errors = run_evals.validate_instance(
                    contract,
                    self.schemas["deliverable-coverage.schema.json"],
                    self.registry,
                    "v3-contract",
                )
                self.assertTrue(any(field in error for error in errors), errors)

        for field in (
            "designEvidenceRequired",
            "runtimeEvidenceRequired",
            "artifactKind",
            "anchorOutputId",
        ):
            with self.subTest(output_field=field):
                contract = self.v3_contract()
                del contract["outputs"][0][field]
                errors = run_evals.validate_instance(
                    contract,
                    self.schemas["deliverable-coverage.schema.json"],
                    self.registry,
                    "v3-contract",
                )
                self.assertTrue(any(field in error for error in errors), errors)

        contract = self.v3_contract()
        contract["implementationTargets"] = ["web/src/App.tsx"]
        errors = run_evals.validate_instance(
            contract,
            self.schemas["deliverable-coverage.schema.json"],
            self.registry,
            "v3-contract",
        )
        self.assertTrue(any("implementationTargets" in error for error in errors))

        contract = self.v3_contract()
        contract["outputs"][0]["required"] = True
        errors = run_evals.validate_instance(
            contract,
            self.schemas["deliverable-coverage.schema.json"],
            self.registry,
            "v3-contract",
        )
        self.assertTrue(any("required" in error for error in errors))

        contract = self.v3_contract()
        contract["outputs"][0].update(
            designEvidenceRequired=False,
            runtimeEvidenceRequired=False,
            artifactKind="none",
            approvalRequired=False,
        )
        errors = run_evals.validate_instance(
            contract,
            self.schemas["deliverable-coverage.schema.json"],
            self.registry,
            "v3-contract",
        )
        self.assertTrue(any("not valid under any" in error for error in errors), errors)

    def test_v3_design_only_contract_allows_empty_implementation_targets(self) -> None:
        contract = self.v3_contract()
        contract["implementationTargets"] = []
        errors = run_evals.validate_instance(
            contract,
            self.schemas["deliverable-coverage.schema.json"],
            self.registry,
            "v3-design-only-contract",
        )
        self.assertEqual(errors, [])

    def test_v3_runtime_snapshot_requires_contract_structure_and_output_bindings(self) -> None:
        contract = self.v3_contract()
        state = self.v3_runtime_state(contract)
        self.assertEqual(
            run_evals.validate_instance(
                state,
                self.schemas["runtime-state.schema.json"],
                self.registry,
                "v3-state",
            ),
            [],
        )

        for field in ("contractSha256", "structureIdentity", "renderUsage"):
            with self.subTest(state_field=field):
                malformed = json.loads(json.dumps(state))
                del malformed[field]
                errors = run_evals.validate_instance(
                    malformed,
                    self.schemas["runtime-state.schema.json"],
                    self.registry,
                    "v3-state",
                )
                self.assertTrue(any(field in error for error in errors), errors)

        malformed = json.loads(json.dumps(state))
        del malformed["outputs"][0]["anchorArtifactSha256"]
        errors = run_evals.validate_instance(
            malformed,
            self.schemas["runtime-state.schema.json"],
            self.registry,
            "v3-state",
        )
        self.assertTrue(any("anchorArtifactSha256" in error for error in errors))

    def test_v3_bundle_semantics_rejects_drift_and_weak_capability_plan(self) -> None:
        contract = self.v3_contract()
        structure = self.v3_structure(contract)
        plan = self.v3_implementation_plan(contract)
        structure["surfaces"][1]["domainIds"] = []
        structure["surfaces"][0]["domainIds"] = []
        structure["scenarios"][0]["objectIds"] = ["unknown-object"]
        plan["capabilityDecisions"][0]["candidates"] = [
            plan["capabilityDecisions"][0]["candidates"][0]
        ]
        plan["capabilityDecisions"][0]["obligations"] = []
        errors = validate_repo.validate_v3_bundle_semantics(contract, structure, plan)
        self.assertTrue(any("required domains" in error for error in errors))
        self.assertTrue(any("unknown object" in error for error in errors))
        self.assertTrue(any("two credible candidates" in error for error in errors))
        self.assertTrue(any("lifecycle obligations" in error for error in errors))

        direct_contract = self.v3_contract()
        direct_contract["capabilityRequirements"][0]["complexity"] = "complex"
        direct_structure = self.v3_structure(direct_contract)
        direct_plan = self.v3_implementation_plan(direct_contract)
        decision = direct_plan["capabilityDecisions"][0]
        decision["decisionTier"] = "direct"
        decision["selectedApproach"] = "external-dependency"
        decision["candidates"] = [
            {
                "name": "React Flow",
                "kind": "external-dependency",
                "evidenceRef": "repo:package-recon/react-flow.md",
                "evidenceSha256": "e" * 64,
            }
        ]
        decision["selectedCandidate"] = "React Flow"
        direct_plan["contractSha256"] = canonical_sha256(direct_contract)
        errors = validate_repo.validate_v3_bundle_semantics(
            direct_contract,
            direct_structure,
            direct_plan,
        )
        self.assertTrue(any("direct tier" in error for error in errors), errors)

    def test_authority_receipt_rejects_unrecognized_action(self) -> None:
        receipt = {
            "schemaVersion": 1,
            "kind": "user-message",
            "sessionId": "schema-v3-session",
            "contractSha256": "c" * 64,
            "structureSha256": "a" * 64,
            "sourceRef": "thread/turn-42",
            "messageSha256": "d" * 64,
            "authorizedActions": ["agent-inferred-approval"],
            "statement": "Proceed.",
        }
        errors = run_evals.validate_instance(
            receipt,
            self.schemas["authority-receipt.schema.json"],
            self.registry,
            "authority-receipt",
        )
        self.assertTrue(any("agent-inferred-approval" in error for error in errors))

    def test_contract_schema_requires_target_for_promotable_output(self) -> None:
        contract = json.loads(
            (ROOT / "evals" / "fixtures" / "promotable-contract.json").read_text(
                encoding="utf-8"
            )
        )
        del contract["outputs"][0]["promotionTarget"]
        errors = run_evals.validate_instance(
            contract,
            self.schemas["deliverable-coverage.schema.json"],
            self.registry,
            "contract",
        )
        self.assertTrue(any("promotionTarget" in error for error in errors))

    def test_runtime_snapshot_schema_accepts_atomic_state_shape(self) -> None:
        contract = json.loads(
            (ROOT / "evals" / "fixtures" / "promotable-contract.json").read_text(
                encoding="utf-8"
            )
        )
        state = {
            "schemaVersion": 2,
            "sessionId": "schema-session",
            "revision": 1,
            "status": "active",
            "createdAt": "2026-08-18T00:00:00Z",
            "updatedAt": "2026-08-18T00:00:00Z",
            "contract": contract,
            "outputs": [
                {
                    "id": "O01",
                    "required": True,
                    "approvalRequired": False,
                    "promotionRequired": True,
                    "status": "pending",
                    "artifact": None,
                    "sha256": None,
                    "reason": None,
                    "userAuthorized": False,
                    "problem": None,
                    "promotionPath": None,
                    "promotionSha256": None,
                    "visualDirectionSha256": None,
                }
            ],
            "validationErrors": [],
            "promotedAt": None,
            "visualDirection": {
                "status": "not-required",
                "path": None,
                "sha256": None,
                "lockedAt": None,
                "userAuthorized": False,
                "authorizedAt": None,
            },
        }
        errors = run_evals.validate_instance(
            state,
            self.schemas["runtime-state.schema.json"],
            self.registry,
            "state",
        )
        self.assertEqual(errors, [])

        legacy = json.loads(json.dumps(state))
        legacy["schemaVersion"] = 1
        legacy["contract"]["schemaVersion"] = 1
        legacy.pop("visualDirection")
        legacy["outputs"][0].pop("visualDirectionSha256")
        legacy_errors = run_evals.validate_instance(
            legacy,
            self.schemas["runtime-state.schema.json"],
            self.registry,
            "legacy-state",
        )
        self.assertEqual(legacy_errors, [])

        del legacy["contract"]["authority"]
        malformed_errors = run_evals.validate_instance(
            legacy,
            self.schemas["runtime-state.schema.json"],
            self.registry,
            "legacy-state",
        )
        self.assertTrue(any("authority" in error for error in malformed_errors))

    def test_runtime_probe_schema_requires_state_scroll_source_and_transition_evidence(self) -> None:
        trace = {
            "schemaVersion": 1,
            "producer": "frontend-workbench/browser-runtime-probe",
            "adapter": "agent-browser",
            "adapterVersion": "0.33.2",
            "generatedAt": "2026-08-30T00:00:00Z",
            "specPath": "qa/O01.runtime-probe-spec.json",
            "specSha256": "a" * 64,
            "implementationSnapshotSha256": "b" * 64,
            "outputId": "O01",
            "route": "/dashboard",
            "state": "default",
            "viewport": "desktop",
            "scrollPosition": "top",
            "directNavigation": True,
            "page": {
                "finalUrl": "http://127.0.0.1:4173/dashboard",
                "title": "Dashboard",
                "rootSelector": "#root",
                "rootFound": True,
                "rootIsDocumentShell": False,
                "rootVisible": True,
                "rootEffectiveOpacity": 1.0,
                "rootViewportIntersectionPixels": 480000,
                "rootChildElementCount": 1,
                "visibleTextCharacters": 40,
                "visibleLandmarkCount": 1,
                "interactiveElementCount": 1,
                "rootWidth": 800,
                "rootHeight": 600,
            },
            "stateVerification": {
                "id": "default-state",
                "kind": "visible-text",
                "result": "pass",
                "observed": "Dashboard is visible",
            },
            "scroll": {
                "kind": "top",
                "x": 0,
                "y": 0,
                "maxY": 300,
                "verified": True,
                "captureFullPage": False,
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
                    "id": "open-detail",
                    "action": "click role=button name=Open",
                    "beforeSha256": "c" * 64,
                    "afterSha256": "d" * 64,
                    "stateChanged": True,
                    "assertions": [
                        {
                            "id": "detail-visible",
                            "kind": "visible-text",
                            "result": "pass",
                            "observed": "before=False; after=True",
                        }
                    ],
                    "result": "pass",
                }
            ],
            "screenshot": {
                "path": "qa/O01.png",
                "sha256": "e" * 64,
                "pixelWidth": 800,
                "pixelHeight": 600,
            },
            "verdict": "pass",
        }
        errors = run_evals.validate_instance(
            trace,
            self.schemas["runtime-probe.schema.json"],
            self.registry,
            "runtime-probe",
        )
        self.assertEqual(errors, [])

        forged = json.loads(json.dumps(trace))
        forged["page"]["rootIsDocumentShell"] = True
        forged["page"]["rootVisible"] = False
        forged["interactions"][0]["stateChanged"] = False
        forged["scroll"]["verified"] = False
        errors = run_evals.validate_instance(
            forged,
            self.schemas["runtime-probe.schema.json"],
            self.registry,
            "runtime-probe",
        )
        self.assertTrue(any("False was expected" in error for error in errors), errors)
        self.assertTrue(any("True was expected" in error for error in errors), errors)

if __name__ == "__main__":
    unittest.main()
