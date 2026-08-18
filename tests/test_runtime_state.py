from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
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
    ) -> Path:
        outputs = [
            {
                "id": "O01",
                "surfaceId": "P01",
                "state": "default",
                "viewport": "desktop",
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
                    "required": True,
                    "approvalRequired": False,
                    "dependsOn": ["O01"],
                    "promotionRequired": False,
                }
            )
        contract = {
            "schemaVersion": 1,
            "contractId": "test-contract",
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

    def artifact(self, session_id: str, name: str, contents: str) -> str:
        relative = f"artifacts/{name}"
        path = self.root / ".frontend-workbench" / "sessions" / session_id / relative
        path.write_text(contents, encoding="utf-8")
        return relative

    def settle_output(self, session_id: str, artifact: str) -> dict:
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
        return runtime_state.mark_output(
            self.root,
            session_id,
            "O01",
            "accepted",
            state["revision"],
            artifact=artifact,
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
        runtime_state.start_session(
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


if __name__ == "__main__":
    unittest.main()
