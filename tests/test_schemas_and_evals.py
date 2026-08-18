from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_evals  # noqa: E402


class SchemaAndEvalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry, cls.schemas = run_evals.build_registry(ROOT / "schemas")

    def test_all_eval_cases_and_contract_fixtures_validate(self) -> None:
        cases, errors = run_evals.load_cases(
            ROOT,
            ROOT / "evals" / "cases",
            self.registry,
            self.schemas,
        )
        self.assertEqual(errors, [])
        expected_ids = {path.stem for path in (ROOT / "evals" / "cases").glob("*.json")}
        self.assertEqual(set(cases), expected_ids)

    def test_score_result_accepts_exact_hard_invariants(self) -> None:
        case = json.loads(
            (ROOT / "evals" / "cases" / "locked-route-preservation.json").read_text(
                encoding="utf-8"
            )
        )
        result = {
            "schemaVersion": 1,
            "caseId": case["id"],
            "invokedSkills": case["expected"]["requiredSkills"],
            "plannedOutputIds": ["O01", "O02", "O03"],
            "completedOutputIds": ["O01", "O02", "O03"],
            "missingOutputIds": [],
            "transformations": [],
            "finalStatus": "complete",
            "hostFilesOutsideRuntime": [],
        }
        schema_errors = run_evals.validate_instance(
            result,
            self.schemas["eval-result.schema.json"],
            self.registry,
            "result",
        )
        self.assertEqual(schema_errors, [])
        self.assertEqual(run_evals.score_result(case, result), [])

    def test_score_result_catches_false_completion_and_stray_file(self) -> None:
        case = json.loads(
            (ROOT / "evals" / "cases" / "partial-renderer-failure.json").read_text(
                encoding="utf-8"
            )
        )
        result = {
            "schemaVersion": 1,
            "caseId": case["id"],
            "invokedSkills": ["art-direct-imagegen"],
            "plannedOutputIds": ["O01", "O02", "O03"],
            "completedOutputIds": ["O01"],
            "missingOutputIds": ["O02", "O03"],
            "transformations": [],
            "finalStatus": "complete",
            "hostFilesOutsideRuntime": ["design-output.png"],
        }
        failures = run_evals.score_result(case, result)
        self.assertTrue(any("finalStatus" in failure for failure in failures))
        self.assertTrue(any("outside .frontend-workbench" in failure for failure in failures))

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
            "schemaVersion": 1,
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
                }
            ],
            "validationErrors": [],
            "promotedAt": None,
        }
        errors = run_evals.validate_instance(
            state,
            self.schemas["runtime-state.schema.json"],
            self.registry,
            "state",
        )
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
