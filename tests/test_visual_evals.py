from __future__ import annotations

import contextlib
import hashlib
import io
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_visual_evals  # noqa: E402


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)


def make_png(width: int, height: int, color: tuple[int, int, int]) -> bytes:
    row = b"\x00" + bytes(color) * width
    raw = row * height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        run_visual_evals.PNG_SIGNATURE
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", zlib.compress(raw, level=9))
        + png_chunk(b"IEND", b"")
    )


class VisualEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry, cls.schemas = run_visual_evals.build_registry(ROOT / "schemas")
        cls.bundles, cls.case_errors = run_visual_evals.load_cases(
            ROOT,
            ROOT / "evals" / "design-cases",
            cls.registry,
            cls.schemas,
        )

    def write_pair(
        self,
        root: Path,
        case_id: str = "brownfield-settings-dna",
    ) -> tuple[Path, Path]:
        bundle = self.bundles[case_id]
        case = bundle["case"]
        fixture = bundle["fixture"]
        baseline_root = root / "baseline"
        workbench_root = root / "workbench"
        pairing_inputs = {
            "modelConfig": ("model-config.json", b'{"model":"same-model","effort":"same"}\n'),
            "environment": ("environment.json", b'{"runtime":"same-environment"}\n'),
            "captureHarness": ("capture-harness.json", b'{"harness":"same-capture"}\n'),
            "taskBudget": ("task-budget.json", b'{"budget":"same-budget"}\n'),
        }
        shared = {
            "promptSha256": run_visual_evals.prompt_sha256(case),
            "modelConfigSha256": hashlib.sha256(pairing_inputs["modelConfig"][1]).hexdigest(),
            "environmentSha256": hashlib.sha256(pairing_inputs["environment"][1]).hexdigest(),
            "fixtureSha256": case["fixtureSha256"],
            "captureHarnessSha256": hashlib.sha256(
                pairing_inputs["captureHarness"][1]
            ).hexdigest(),
            "taskBudgetSha256": hashlib.sha256(pairing_inputs["taskBudget"][1]).hexdigest(),
        }
        for variant, result_root in (
            ("baseline", baseline_root),
            ("workbench", workbench_root),
        ):
            result_root.mkdir(parents=True)
            trace = (
                json.dumps({"caseId": case_id, "trialId": "trial-01", "variant": variant})
                + "\n"
            ).encode("utf-8")
            trace_path = result_root / "traces" / f"{variant}.jsonl"
            trace_path.parent.mkdir(parents=True)
            trace_path.write_bytes(trace)
            pairing_receipts: dict[str, dict[str, str]] = {}
            for receipt_name, (filename, payload) in pairing_inputs.items():
                relative = f"pairing/{filename}"
                receipt_path = result_root / relative
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_bytes(payload)
                pairing_receipts[receipt_name] = {
                    "path": relative,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            captures: list[dict[str, Any]] = []
            for index, target in enumerate(fixture["captureMatrix"]):
                viewport = target["viewport"]
                base = 30 if variant == "baseline" else 130
                color = ((base + index * 17) % 255, (70 + index * 29) % 255, 190)
                relative = f"screenshots/{target['captureId']}.png"
                screenshot_path = result_root / relative
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                screenshot_path.write_bytes(
                    make_png(viewport["width"], viewport["height"], color)
                )
                captures.append(
                    {
                        "captureId": target["captureId"],
                        "outputId": target["outputId"],
                        "surfaceId": target["surfaceId"],
                        "route": target["route"],
                        "state": target["state"],
                        "viewport": dict(viewport),
                        "scrollPosition": target["scrollPosition"],
                        "path": relative,
                        "sha256": run_visual_evals.sha256_file(screenshot_path),
                    }
                )
            result = {
                "schemaVersion": 1,
                "caseId": case_id,
                "trialId": "trial-01",
                "variant": variant,
                "pairing": {
                    "pairId": f"pair-{case_id}-01",
                    "treatment": (
                        "frontend-workbench-disabled"
                        if variant == "baseline"
                        else "frontend-workbench-enabled"
                    ),
                    "matchedDigests": dict(shared),
                    "receipts": pairing_receipts,
                },
                "evidence": {
                    "sourceKind": "harness-trace",
                    "sourceId": f"unit-run-{variant}-{case_id}-01",
                    "tracePath": f"traces/{variant}.jsonl",
                    "traceSha256": hashlib.sha256(trace).hexdigest(),
                },
                "captures": captures,
            }
            (result_root / f"{case_id}--trial-01.json").write_text(
                json.dumps(result),
                encoding="utf-8",
            )
        return baseline_root, workbench_root

    def make_blind_pack(
        self,
        root: Path,
        case_id: str = "brownfield-settings-dna",
    ) -> tuple[Path, Path, Path]:
        baseline_root, workbench_root = self.write_pair(root, case_id)
        blind_root = root / "blind"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = run_visual_evals.main(
                [
                    "--mode",
                    "blind-pack",
                    "--case-id",
                    case_id,
                    "--baseline-results",
                    str(baseline_root),
                    "--workbench-results",
                    str(workbench_root),
                    "--blind-root",
                    str(blind_root),
                ]
            )
        self.assertEqual(status, 0, stdout.getvalue())
        self.assertIn("NO visual quality was scored", stdout.getvalue())
        return baseline_root, workbench_root, blind_root

    def write_judgments(
        self,
        root: Path,
        blind_root: Path,
        *,
        prefer: str = "workbench",
    ) -> Path:
        judgments_root = root / "judgments"
        judgments_root.mkdir()
        packet_paths = sorted((blind_root / "packets").glob("*/packet.json"))
        for index, packet_path in enumerate(packet_paths, start=1):
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            mapping_path = blind_root / "private-mappings" / f"{packet['packetId']}.json"
            mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
            verdict = next(
                side for side, variant in mapping["assignment"].items() if variant == prefer
            )
            trace = (
                json.dumps({"packetId": packet["packetId"], "judgeSlot": index}) + "\n"
            ).encode("utf-8")
            trace_relative = f"judge-traces/{packet['packetId']}.jsonl"
            trace_path = judgments_root / trace_relative
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            trace_path.write_bytes(trace)
            capture_id = packet["sides"][verdict][0]["captureId"]
            dimension_value = {
                "verdict": verdict,
                "rationale": "The preferred side presents the declared job with clearer visible evidence.",
                "evidence": [
                    {
                        "side": verdict,
                        "captureId": capture_id,
                        "observation": "The primary job and required state are visibly easier to locate.",
                    }
                ],
            }
            judgment = {
                "schemaVersion": 1,
                "packetId": packet["packetId"],
                "packetSha256": run_visual_evals.sha256_file(packet_path),
                "rubricSha256": packet["task"]["rubricSha256"],
                "judgeReceipt": {
                    "sourceKind": "harness-trace",
                    "judgeId": f"unit-judge-{index:02d}",
                    "sourceId": f"unit-judge-source-{index:02d}-{packet['packetId']}",
                    "tracePath": trace_relative,
                    "traceSha256": hashlib.sha256(trace).hexdigest(),
                },
                "dimensions": {
                    dimension: dict(dimension_value)
                    for dimension in run_visual_evals.DIMENSIONS
                },
            }
            (judgments_root / f"{packet['packetId']}.json").write_text(
                json.dumps(judgment),
                encoding="utf-8",
            )
        return judgments_root

    def test_visual_runtime_artifacts_stay_under_ignored_results_root(self) -> None:
        self.assertTrue(
            run_visual_evals.runtime_location_errors(
                ROOT,
                ROOT / "visual-scorecard.json",
                "visual scorecard",
            )
        )
        self.assertEqual(
            run_visual_evals.runtime_location_errors(
                ROOT,
                ROOT / "evals" / "results" / "visual" / "scorecard.json",
                "visual scorecard",
            ),
            [],
        )
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(
                run_visual_evals.runtime_location_errors(
                    ROOT,
                    Path(temporary) / "scorecard.json",
                    "visual scorecard",
                ),
                [],
            )

    def test_eight_static_cases_and_exact_pairwise_rubric_validate(self) -> None:
        self.assertEqual(self.case_errors, [])
        self.assertEqual(
            set(self.bundles),
            {
                "brownfield-settings-dna",
                "complex-graph-capability-fit",
                "density-repartition-responsive",
                "operations-preserve-sidebar-redesign",
                "multiroute-project-coherence",
                "product-hierarchy-fidelity",
                "project-shell-reference-scope",
                "planner-state-clarity",
            },
        )
        rubric = self.bundles["brownfield-settings-dna"]["rubric"]
        self.assertEqual(tuple(rubric["dimensions"]), run_visual_evals.DIMENSIONS)
        self.assertEqual(
            run_visual_evals.DIMENSIONS[-4:],
            (
                "productHierarchyFidelity",
                "shellContinuity",
                "referenceScopeFidelity",
                "capabilityFit",
            ),
        )
        self.assertEqual(rubric["allowedVerdicts"], ["A", "B", "tie", "not-judgeable"])
        self.assertFalse(rubric["numericScoresAllowed"])

    def test_adversarial_visual_contexts_are_typed_and_scoped(self) -> None:
        hierarchy = self.bundles["product-hierarchy-fidelity"]["fixture"]["brief"][
            "evaluationContext"
        ]["productHierarchy"]
        self.assertEqual(hierarchy["primaryObject"], "Workflow")
        self.assertIn("Automated checks", hierarchy["supportingObjects"])
        self.assertIn("Runner source", hierarchy["executionMechanisms"])

        shell_context = self.bundles["project-shell-reference-scope"]["fixture"][
            "brief"
        ]["evaluationContext"]
        self.assertEqual(
            shell_context["shellContinuity"]["acceptedAnchorId"],
            "project-shell-anchor-v1",
        )
        references = {reference["id"]: reference for reference in shell_context["references"]}
        functional = references["force-graph-functional-ref"]
        self.assertEqual(functional["role"], "FUNCTIONAL_REFERENCE")
        self.assertIn("Global shell", functional["forbiddenInfluence"])
        self.assertIn("Community clustering", functional["allowedInfluence"])

        capability = self.bundles["complex-graph-capability-fit"]["fixture"]["brief"][
            "evaluationContext"
        ]["capabilityFit"]
        self.assertTrue(capability["comparisonRequired"])
        self.assertGreaterEqual(len(capability["establishedOptions"]), 2)
        self.assertIn("Equivalent relationship list", capability["requiredFallbacks"])

        operational_policy = self.bundles["brownfield-settings-dna"]["fixture"][
            "brief"
        ]["evaluationContext"]["operationalMetadataPolicy"]
        self.assertEqual(operational_policy["defaultVisibility"], "hidden-unless-required")
        self.assertEqual(operational_policy["requiredClaims"], [])

        redesign = self.bundles["operations-preserve-sidebar-redesign"]["fixture"][
            "brief"
        ]["evaluationContext"]["redesignBoundary"]
        self.assertEqual(redesign["mode"], "preserve-only")
        self.assertEqual(
            [item["regionId"] for item in redesign["preserveRegions"]],
            ["primary-sidebar"],
        )
        replace = redesign["replaceRegions"][0]
        self.assertEqual(replace["regionId"], "dashboard-main")
        self.assertGreaterEqual(replace["minimumChangedDimensions"], 5)
        self.assertIn("macro-layout", replace["mustChange"])
        self.assertIn("module-topology", replace["mustChange"])
        distribution = self.bundles["operations-preserve-sidebar-redesign"]["fixture"][
            "brief"
        ]["evaluationContext"]["contentDistribution"]
        self.assertEqual(distribution["strategy"], "progressive-scroll")
        self.assertEqual(
            {band["placement"] for band in distribution["bands"]},
            {"first-viewport", "continuation"},
        )
        self.assertEqual(distribution["sharedContentIds"], [])
        content_ids = [
            content_id
            for band in distribution["bands"]
            for content_id in band["contentIds"]
        ]
        self.assertEqual(len(content_ids), len(set(content_ids)))

    def test_adversarial_behavior_cases_and_contract_fixtures_validate(self) -> None:
        expected = {
            "custom-primitive-without-comparison",
            "design-optional-runtime-required",
            "duplicate-batch-transition",
            "empty-operational-policy-visible-claims",
            "implementation-scope-exceeds-surfaces",
            "missing-project-shell-anchor",
            "product-primary-object-drift",
            "scoped-functional-reference",
            "silent-artifact-policy-downgrade",
        }
        observed: set[str] = set()
        fixtures: dict[str, dict[str, Any]] = {}
        for case_id in expected:
            case_path = ROOT / "evals" / "cases" / f"{case_id}.json"
            case = run_visual_evals.load_object(case_path)
            observed.add(case["id"])
            self.assertEqual(case["id"], case_path.stem)
            self.assertEqual(
                run_visual_evals.validate_instance(
                    case,
                    self.schemas["eval-case.schema.json"],
                    self.registry,
                    str(case_path),
                ),
                [],
            )
            fixture_path = ROOT / case["contractFixture"]
            fixture = run_visual_evals.load_object(fixture_path)
            fixtures[case_id] = fixture
            self.assertEqual(
                run_visual_evals.validate_instance(
                    fixture,
                    self.schemas["deliverable-coverage.schema.json"],
                    self.registry,
                    str(fixture_path),
                ),
                [],
            )
        self.assertEqual(observed, expected)
        self.assertTrue(all(fixture["schemaVersion"] == 3 for fixture in fixtures.values()))

        hierarchy = fixtures["product-primary-object-drift"]["productModel"]
        roles = {item["id"]: item["role"] for item in hierarchy["objects"]}
        self.assertEqual(roles["workflow"], "primary")
        self.assertEqual(roles["automated-check"], "downstream-evidence")
        self.assertEqual(roles["runner-source"], "implementation-detail")

        optional_output = fixtures["design-optional-runtime-required"]["outputs"][0]
        self.assertFalse(optional_output["designEvidenceRequired"])
        self.assertTrue(optional_output["runtimeEvidenceRequired"])
        self.assertEqual(optional_output["artifactKind"], "none")

        policy_fixture = fixtures["silent-artifact-policy-downgrade"]
        self.assertEqual(policy_fixture["visualArtifactPolicy"], "imagegen-required")
        self.assertEqual(
            policy_fixture["checkpointMode"], "review-before-implementation"
        )
        self.assertTrue(policy_fixture["outputs"][0]["designEvidenceRequired"])

        shell_fixture = fixtures["missing-project-shell-anchor"]
        dependent_output = next(
            output for output in shell_fixture["outputs"] if output["id"] == "O02"
        )
        self.assertEqual(dependent_output["anchorOutputId"], "O01")
        self.assertIn(
            "force-graph-functional-ref",
            shell_fixture["surfaces"][1]["referenceBindingIds"],
        )

        graph_capability = fixtures["custom-primitive-without-comparison"][
            "capabilityRequirements"
        ][0]
        self.assertEqual(graph_capability["complexity"], "complex")
        self.assertTrue(
            any("Compare approved" in item for item in graph_capability["constraints"])
        )

        implementation_fixture = fixtures["implementation-scope-exceeds-surfaces"]
        self.assertEqual(
            implementation_fixture["implementationTargets"],
            [
                {
                    "path": "web/src/BusinessProcess.tsx",
                    "surfaceIds": ["P01"],
                    "sharedOwner": False,
                }
            ],
        )
        self.assertEqual(
            fixtures["empty-operational-policy-visible-claims"][
                "operationalMetadataPolicy"
            ]["requiredClaims"],
            [],
        )
        duplicate_case = run_visual_evals.load_object(
            ROOT / "evals" / "cases" / "duplicate-batch-transition.json"
        )
        self.assertIn(
            "reject-duplicate-batch-output",
            duplicate_case["expected"]["requiredTransformations"],
        )
        self.assertEqual(
            fixtures["duplicate-batch-transition"]["renderBudget"][
                "maxAttemptsPerOutput"
            ],
            1,
        )

    def test_fixture_mode_explicitly_scores_no_visual_quality(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = run_visual_evals.main(["--mode", "fixtures"])
        self.assertEqual(status, 0)
        self.assertIn("8 case(s)", stdout.getvalue())
        self.assertIn("NO visual quality was scored", stdout.getvalue())

    def test_png_receipt_enforces_magic_hash_dimensions_and_no_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            screenshot = root / "screenshots" / "screen.png"
            screenshot.parent.mkdir()
            screenshot.write_bytes(make_png(320, 480, (10, 20, 30)))
            receipt = {
                "path": "screenshots/screen.png",
                "sha256": run_visual_evals.sha256_file(screenshot),
            }
            _, errors = run_visual_evals.validate_png_receipt(
                root,
                receipt,
                "screenshots",
                "capture",
                320,
                480,
                reject_metadata_leaks=True,
            )
            self.assertEqual(errors, [])

            _, errors = run_visual_evals.validate_png_receipt(
                root,
                receipt,
                "screenshots",
                "capture",
                321,
                480,
                reject_metadata_leaks=True,
            )
            self.assertTrue(any("dimensions" in error for error in errors))

            bad_receipt = dict(receipt, sha256="0" * 64)
            _, errors = run_visual_evals.validate_png_receipt(
                root,
                bad_receipt,
                "screenshots",
                "capture",
                320,
                480,
                reject_metadata_leaks=True,
            )
            self.assertTrue(any("SHA-256" in error for error in errors))

            fake = root / "screenshots" / "fake.png"
            fake.write_bytes(b"not a png")
            fake_receipt = {
                "path": "screenshots/fake.png",
                "sha256": run_visual_evals.sha256_file(fake),
            }
            _, errors = run_visual_evals.validate_png_receipt(
                root,
                fake_receipt,
                "screenshots",
                "capture",
                320,
                480,
                reject_metadata_leaks=True,
            )
            self.assertTrue(any("invalid PNG" in error for error in errors))

            linked = root / "screenshots" / "linked.png"
            linked.symlink_to(screenshot)
            linked_receipt = {
                "path": "screenshots/linked.png",
                "sha256": receipt["sha256"],
            }
            _, errors = run_visual_evals.validate_png_receipt(
                root,
                linked_receipt,
                "screenshots",
                "capture",
                320,
                480,
                reject_metadata_leaks=True,
            )
            self.assertTrue(any("symlink" in error for error in errors))

    def test_blind_pack_rejects_mismatched_pairing_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root, workbench_root = self.write_pair(temp_root)
            result_path = next(workbench_root.glob("*.json"))
            result = json.loads(result_path.read_text(encoding="utf-8"))
            changed_environment = b'{"runtime":"changed-environment"}\n'
            environment_path = workbench_root / result["pairing"]["receipts"]["environment"]["path"]
            environment_path.write_bytes(changed_environment)
            changed_digest = hashlib.sha256(changed_environment).hexdigest()
            result["pairing"]["receipts"]["environment"]["sha256"] = changed_digest
            result["pairing"]["matchedDigests"]["environmentSha256"] = changed_digest
            result_path.write_text(json.dumps(result), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_visual_evals.main(
                    [
                        "--mode",
                        "blind-pack",
                        "--case-id",
                        "brownfield-settings-dna",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--blind-root",
                        str(temp_root / "blind"),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("matched pairing digests differ", stderr.getvalue())
            self.assertIn("validated pairing receipts differ", stderr.getvalue())
            self.assertFalse((temp_root / "blind").exists())

    def test_blind_pack_rejects_tampered_reused_or_symlinked_pairing_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root, workbench_root = self.write_pair(temp_root)
            result_path = next(workbench_root.glob("*.json"))
            result = json.loads(result_path.read_text(encoding="utf-8"))
            environment_receipt = result["pairing"]["receipts"]["environment"]
            (workbench_root / environment_receipt["path"]).write_bytes(b"tampered bytes\n")
            result["pairing"]["receipts"]["taskBudget"] = dict(
                result["pairing"]["receipts"]["modelConfig"]
            )
            capture_receipt = result["pairing"]["receipts"]["captureHarness"]
            capture_path = workbench_root / capture_receipt["path"]
            capture_path.unlink()
            capture_path.symlink_to(
                workbench_root / result["pairing"]["receipts"]["modelConfig"]["path"]
            )
            result_path.write_text(json.dumps(result), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_visual_evals.main(
                    [
                        "--mode",
                        "blind-pack",
                        "--case-id",
                        "brownfield-settings-dna",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--blind-root",
                        str(temp_root / "blind"),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("SHA-256 does not match file bytes", stderr.getvalue())
            self.assertIn("pairing receipt file is reused", stderr.getvalue())
            self.assertIn("symlink", stderr.getvalue())
            self.assertFalse((temp_root / "blind").exists())

    def test_blind_pack_copies_anonymized_assets_and_keeps_mapping_private(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            _, _, blind_root = self.make_blind_pack(temp_root)
            packet_paths = sorted((blind_root / "packets").glob("*/packet.json"))
            mapping_paths = sorted((blind_root / "private-mappings").glob("*.json"))
            self.assertEqual(len(packet_paths), 3)
            self.assertEqual(len(mapping_paths), 3)
            for packet_path in packet_paths:
                packet_text = packet_path.read_text(encoding="utf-8")
                self.assertNotIn("baseline", packet_text.lower())
                self.assertNotIn("workbench", packet_text.lower())
                packet = json.loads(packet_text)
                for side in ("A", "B"):
                    for capture in packet["sides"][side]:
                        asset = packet_path.parent / capture["path"]
                        self.assertTrue(asset.is_file())
                        self.assertFalse(asset.is_symlink())
                        self.assertEqual(run_visual_evals.sha256_file(asset), capture["sha256"])
            mapping = json.loads(mapping_paths[0].read_text(encoding="utf-8"))
            self.assertEqual(set(mapping["assignment"].values()), {"baseline", "workbench"})

    def test_visual_paired_aggregates_counts_without_causal_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root, workbench_root, blind_root = self.make_blind_pack(temp_root)
            judgments_root = self.write_judgments(temp_root, blind_root)
            scorecard_path = temp_root / "scorecard.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_visual_evals.main(
                    [
                        "--mode",
                        "visual-paired",
                        "--case-id",
                        "brownfield-settings-dna",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--blind-root",
                        str(blind_root),
                        "--judgments",
                        str(judgments_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 0, stderr.getvalue())
            scorecard = json.loads(scorecard_path.read_text(encoding="utf-8"))
            self.assertTrue(scorecard["visualQualityScored"])
            self.assertFalse(scorecard["causalUpliftClaimed"])
            self.assertIn("does not establish causal uplift", scorecard["statement"])
            self.assertEqual(scorecard["judgmentCount"], 3)
            for dimension in run_visual_evals.DIMENSIONS:
                counts = scorecard["dimensions"][dimension]
                self.assertEqual(counts["workbenchWins"], 3)
                self.assertEqual(counts["baselineWins"], 0)
                self.assertEqual(counts["disagreementTrials"], 0)

    def test_visual_paired_rejects_nonindependent_judge(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root, workbench_root, blind_root = self.make_blind_pack(temp_root)
            judgments_root = self.write_judgments(temp_root, blind_root)
            judgment_paths = sorted(judgments_root.glob("*.json"))
            first = json.loads(judgment_paths[0].read_text(encoding="utf-8"))
            second = json.loads(judgment_paths[1].read_text(encoding="utf-8"))
            second["judgeReceipt"]["judgeId"] = first["judgeReceipt"]["judgeId"]
            judgment_paths[1].write_text(json.dumps(second), encoding="utf-8")
            scorecard_path = temp_root / "scorecard.json"
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_visual_evals.main(
                    [
                        "--mode",
                        "visual-paired",
                        "--case-id",
                        "brownfield-settings-dna",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--blind-root",
                        str(blind_root),
                        "--judgments",
                        str(judgments_root),
                        "--scorecard",
                        str(scorecard_path),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("not independent", stderr.getvalue())
            self.assertFalse(scorecard_path.exists())

    def test_visual_paired_rejects_variant_alias_in_judgment(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root, workbench_root, blind_root = self.make_blind_pack(temp_root)
            judgments_root = self.write_judgments(temp_root, blind_root)
            judgment_path = sorted(judgments_root.glob("*.json"))[0]
            judgment = json.loads(judgment_path.read_text(encoding="utf-8"))
            judgment["dimensions"]["specificity"]["rationale"] = (
                "The workbench_enabled alias improperly reveals the treatment assignment."
            )
            judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_visual_evals.main(
                    [
                        "--mode",
                        "visual-paired",
                        "--case-id",
                        "brownfield-settings-dna",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--blind-root",
                        str(blind_root),
                        "--judgments",
                        str(judgments_root),
                        "--scorecard",
                        str(temp_root / "scorecard.json"),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("judgment leaks a variant label", stderr.getvalue())

    def test_visual_paired_rejects_variant_alias_in_verified_judge_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            temp_root = Path(temp_value)
            baseline_root, workbench_root, blind_root = self.make_blind_pack(temp_root)
            judgments_root = self.write_judgments(temp_root, blind_root)
            judgment_path = sorted(judgments_root.glob("*.json"))[0]
            judgment = json.loads(judgment_path.read_text(encoding="utf-8"))
            trace_path = judgments_root / judgment["judgeReceipt"]["tracePath"]
            trace_bytes = b'{"assignment_hint":"baseline_v1"}\n'
            trace_path.write_bytes(trace_bytes)
            judgment["judgeReceipt"]["traceSha256"] = hashlib.sha256(trace_bytes).hexdigest()
            judgment_path.write_text(json.dumps(judgment), encoding="utf-8")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                status = run_visual_evals.main(
                    [
                        "--mode",
                        "visual-paired",
                        "--case-id",
                        "brownfield-settings-dna",
                        "--baseline-results",
                        str(baseline_root),
                        "--workbench-results",
                        str(workbench_root),
                        "--blind-root",
                        str(blind_root),
                        "--judgments",
                        str(judgments_root),
                        "--scorecard",
                        str(temp_root / "scorecard.json"),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertIn("verified judge trace leaks a variant label", stderr.getvalue())

    def test_cli_does_not_expose_blind_assignment_seed(self) -> None:
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            run_visual_evals.main(["--mode", "fixtures", "--seed", "public-seed"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("unrecognized arguments: --seed", stderr.getvalue())

    def test_judgment_schema_rejects_numeric_score(self) -> None:
        judgment = {
            "schemaVersion": 1,
            "packetId": "packet-one",
            "packetSha256": "1" * 64,
            "rubricSha256": "2" * 64,
            "judgeReceipt": {
                "sourceKind": "human-review",
                "judgeId": "judge-one",
                "sourceId": "review-source-one",
                "tracePath": "judge-traces/review-one.jsonl",
                "traceSha256": "3" * 64,
            },
            "dimensions": {
                dimension: {
                    "verdict": "tie",
                    "rationale": "Both sides show materially equivalent visible evidence for this dimension.",
                    "evidence": [
                        {
                            "side": "both",
                            "captureId": "capture-one",
                            "observation": "Both sides present the same visible hierarchy and state clarity.",
                        }
                    ],
                }
                for dimension in run_visual_evals.DIMENSIONS
            },
        }
        judgment["dimensions"]["specificity"]["score"] = 3
        errors = run_visual_evals.validate_instance(
            judgment,
            self.schemas["eval-blind-judgment.schema.json"],
            self.registry,
            "judgment",
        )
        self.assertTrue(any("score" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
