#!/usr/bin/env python3
"""Safe snapshot state for Frontend Workbench runtime sessions.

The helper is intentionally dependency-free and stores one atomic JSON snapshot per
session. It does not keep an event log and never edits a host project's ignore files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA_VERSION = 1
IGNORE_LINE = "/.frontend-workbench/"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
SESSION_STATUSES = {"active", "blocked", "validated", "promoted", "deferred", "cancelled"}
OUTPUT_STATUSES = {
    "pending",
    "generating",
    "reviewing",
    "awaiting-approval",
    "accepted",
    "blocked",
    "deferred",
    "promoted",
}
SETTLED_OUTPUT_STATUSES = {"accepted", "deferred", "promoted"}
TERMINAL_SESSION_STATUSES = {"promoted", "deferred", "cancelled"}
TRANSITIONS = {
    "pending": {"generating", "blocked", "deferred"},
    "generating": {"reviewing", "blocked", "pending"},
    "reviewing": {"awaiting-approval", "accepted", "blocked", "pending", "deferred"},
    "awaiting-approval": {"accepted", "blocked", "pending", "deferred"},
    "blocked": {"pending", "generating", "deferred"},
    "accepted": set(),
    "deferred": set(),
    "promoted": set(),
}


class StateError(RuntimeError):
    """A user-correctable runtime-state error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise StateError(message)
    return result


def _validate_id(value: str, label: str) -> str:
    if ID_RE.fullmatch(value) is None:
        raise StateError(f"{label} must match {ID_RE.pattern}")
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _relative_path(value: str, label: str) -> PurePosixPath:
    if not value or "\\" in value:
        raise StateError(f"{label} must be a non-empty POSIX-style relative path")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise StateError(f"{label} must stay inside its allowed root")
    return candidate


def resolve_repo_root(value: str | Path) -> Path:
    requested = Path(value).expanduser().resolve()
    result = _git(requested, "rev-parse", "--show-toplevel")
    root = Path(result.stdout.strip()).resolve()
    if not root.is_dir():
        raise StateError("Git returned an invalid repository root")
    return root


def preflight(value: str | Path) -> Path:
    root = resolve_repo_root(value)
    ignore_file = root / ".gitignore"
    if not ignore_file.is_file() or ignore_file.is_symlink():
        raise StateError(f"{ignore_file} must be a regular file containing {IGNORE_LINE!r}")
    lines = ignore_file.read_text(encoding="utf-8").splitlines()
    if IGNORE_LINE not in lines:
        raise StateError(
            f"Refusing runtime writes: root .gitignore needs the exact line {IGNORE_LINE!r}"
        )

    tracked = _git(root, "ls-files", "--", ".frontend-workbench").stdout.strip()
    if tracked:
        raise StateError("Refusing runtime writes: .frontend-workbench contains tracked files")

    probe = ".frontend-workbench/.preflight"
    ignored = _git(root, "check-ignore", "--quiet", "--no-index", "--", probe, check=False)
    if ignored.returncode != 0:
        raise StateError(f"Git does not ignore {probe!r} despite the required .gitignore line")

    runtime_root = root / ".frontend-workbench"
    if runtime_root.is_symlink():
        raise StateError("Refusing a symlinked .frontend-workbench runtime root")
    sessions_root = runtime_root / "sessions"
    if sessions_root.is_symlink():
        raise StateError("Refusing a symlinked .frontend-workbench/sessions directory")
    return root


def session_directory(root: Path, session_id: str) -> Path:
    _validate_id(session_id, "session ID")
    runtime_root = root / ".frontend-workbench"
    sessions = runtime_root / "sessions"
    candidate = sessions / session_id
    for label, path in (
        ("runtime root", runtime_root),
        ("sessions directory", sessions),
        ("session directory", candidate),
    ):
        if path.is_symlink():
            raise StateError(f"Refusing a symlinked {label}")
    resolved_sessions = sessions.resolve()
    resolved_candidate = candidate.resolve()
    if not _is_within(resolved_candidate, resolved_sessions):
        raise StateError("Session path escapes .frontend-workbench/sessions")
    return resolved_candidate


def state_path(root: Path, session_id: str) -> Path:
    return session_directory(root, session_id) / "state.json"


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise StateError(f"Refusing to replace symlinked state file: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise StateError(f"{label} must be a regular JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(f"Unable to read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateError(f"{label} must contain a JSON object")
    return value


def _unknown_keys(value: dict[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{label} contains unknown field {key!r}")


def validate_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        contract,
        {"schemaVersion", "contractId", "authority", "surfaces", "edges", "outputs"},
        "contract",
        errors,
    )
    if contract.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"contract.schemaVersion must be {SCHEMA_VERSION}")
    contract_id = contract.get("contractId")
    if not isinstance(contract_id, str) or ID_RE.fullmatch(contract_id) is None:
        errors.append("contract.contractId is invalid")

    authority = contract.get("authority")
    if not isinstance(authority, dict):
        errors.append("contract.authority must be an object")
    else:
        _unknown_keys(
            authority,
            {"pageStructure", "interactionModel", "contentRepartition"},
            "contract.authority",
            errors,
        )
        if authority.get("pageStructure") not in {"locked", "revisable"}:
            errors.append("contract.authority.pageStructure is invalid")
        if authority.get("interactionModel") not in {"locked", "revisable"}:
            errors.append("contract.authority.interactionModel is invalid")
        if authority.get("contentRepartition") not in {
            "within-surface-only",
            "authorized-across-surfaces",
        }:
            errors.append("contract.authority.contentRepartition is invalid")

    surfaces = contract.get("surfaces")
    surface_ids: set[str] = set()
    if not isinstance(surfaces, list) or not surfaces:
        errors.append("contract.surfaces must be a non-empty array")
    else:
        for index, surface in enumerate(surfaces):
            label = f"contract.surfaces[{index}]"
            if not isinstance(surface, dict):
                errors.append(f"{label} must be an object")
                continue
            _unknown_keys(surface, {"id", "kind", "route", "userJob"}, label, errors)
            surface_id = surface.get("id")
            if not isinstance(surface_id, str) or ID_RE.fullmatch(surface_id) is None:
                errors.append(f"{label}.id is invalid")
            elif surface_id in surface_ids:
                errors.append(f"duplicate surface ID {surface_id!r}")
            else:
                surface_ids.add(surface_id)
            if surface.get("kind") not in {"page", "flow-step", "screen", "overlay"}:
                errors.append(f"{label}.kind is invalid")
            if not isinstance(surface.get("userJob"), str) or not surface["userJob"].strip():
                errors.append(f"{label}.userJob must be non-empty")
            route = surface.get("route")
            if route is not None and (not isinstance(route, str) or not route.strip()):
                errors.append(f"{label}.route must be non-empty when present")

    edges = contract.get("edges")
    if not isinstance(edges, list):
        errors.append("contract.edges must be an array")
    else:
        for index, edge in enumerate(edges):
            label = f"contract.edges[{index}]"
            if not isinstance(edge, dict):
                errors.append(f"{label} must be an object")
                continue
            _unknown_keys(edge, {"from", "to", "trigger"}, label, errors)
            if edge.get("from") not in surface_ids:
                errors.append(f"{label}.from references an unknown surface")
            if edge.get("to") not in surface_ids:
                errors.append(f"{label}.to references an unknown surface")
            if not isinstance(edge.get("trigger"), str) or not edge["trigger"].strip():
                errors.append(f"{label}.trigger must be non-empty")

    outputs = contract.get("outputs")
    output_ids: set[str] = set()
    dependencies: dict[str, list[str]] = {}
    if not isinstance(outputs, list) or not outputs:
        errors.append("contract.outputs must be a non-empty array")
    else:
        for index, output in enumerate(outputs):
            label = f"contract.outputs[{index}]"
            if not isinstance(output, dict):
                errors.append(f"{label} must be an object")
                continue
            _unknown_keys(
                output,
                {
                    "id",
                    "surfaceId",
                    "state",
                    "viewport",
                    "scrollPosition",
                    "required",
                    "approvalRequired",
                    "dependsOn",
                    "promotionRequired",
                    "promotionTarget",
                },
                label,
                errors,
            )
            output_id = output.get("id")
            if not isinstance(output_id, str) or ID_RE.fullmatch(output_id) is None:
                errors.append(f"{label}.id is invalid")
                continue
            if output_id in output_ids:
                errors.append(f"duplicate output ID {output_id!r}")
            output_ids.add(output_id)
            if output.get("surfaceId") not in surface_ids:
                errors.append(f"{label}.surfaceId references an unknown surface")
            for field in ("state", "viewport"):
                if not isinstance(output.get(field), str) or not output[field].strip():
                    errors.append(f"{label}.{field} must be non-empty")
            scroll_position = output.get("scrollPosition")
            if scroll_position is not None and (
                not isinstance(scroll_position, str) or not scroll_position.strip()
            ):
                errors.append(f"{label}.scrollPosition must be non-empty when present")
            if not isinstance(output.get("required"), bool):
                errors.append(f"{label}.required must be a boolean")
            if not isinstance(output.get("approvalRequired"), bool):
                errors.append(f"{label}.approvalRequired must be a boolean")
            if not isinstance(output.get("promotionRequired"), bool):
                errors.append(f"{label}.promotionRequired must be a boolean")
            depends_on = output.get("dependsOn")
            if not isinstance(depends_on, list) or not all(isinstance(item, str) for item in depends_on):
                errors.append(f"{label}.dependsOn must be an array of output IDs")
                dependencies[output_id] = []
            else:
                if len(set(depends_on)) != len(depends_on):
                    errors.append(f"{label}.dependsOn contains duplicates")
                dependencies[output_id] = list(depends_on)
            target = output.get("promotionTarget")
            if output.get("promotionRequired") is True:
                if not isinstance(target, str):
                    errors.append(f"{label}.promotionTarget is required for promotion")
                else:
                    try:
                        relative = _relative_path(target, f"{label}.promotionTarget")
                        if relative.parts[0] == ".frontend-workbench":
                            errors.append(f"{label}.promotionTarget cannot be runtime state")
                    except StateError as exc:
                        errors.append(str(exc))
            elif target is not None:
                errors.append(f"{label}.promotionTarget requires promotionRequired=true")

    for output_id, depends_on in dependencies.items():
        for dependency in depends_on:
            if dependency not in output_ids:
                errors.append(f"output {output_id!r} depends on unknown output {dependency!r}")
            if dependency == output_id:
                errors.append(f"output {output_id!r} cannot depend on itself")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(output_id: str) -> None:
        if output_id in visited:
            return
        if output_id in visiting:
            errors.append(f"output dependency cycle includes {output_id!r}")
            return
        visiting.add(output_id)
        for dependency in dependencies.get(output_id, []):
            if dependency in dependencies:
                visit(dependency)
        visiting.remove(output_id)
        visited.add(output_id)

    for output_id in dependencies:
        visit(output_id)
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_path(session_dir: Path, value: str, *, require_file: bool = True) -> Path:
    relative = _relative_path(value, "artifact path")
    if not relative.parts or relative.parts[0] != "artifacts":
        raise StateError("Artifact paths must start with artifacts/")
    artifacts_path = session_dir / "artifacts"
    if artifacts_path.is_symlink():
        raise StateError("Refusing a symlinked session artifacts directory")
    artifacts = artifacts_path.resolve()
    candidate = (session_dir / relative.as_posix()).resolve()
    if not _is_within(candidate, artifacts):
        raise StateError("Artifact path escapes the session artifacts directory")
    if require_file and (not candidate.is_file() or candidate.is_symlink()):
        raise StateError(f"Artifact must be a regular non-symlink file: {candidate}")
    return candidate


def _state_output_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in state["outputs"]}


def validate_state_shape(state: dict[str, Any], expected_session_id: str) -> list[str]:
    errors: list[str] = []
    if state.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"state.schemaVersion must be {SCHEMA_VERSION}")
    if state.get("sessionId") != expected_session_id:
        errors.append("state.sessionId does not match the requested session")
    if not isinstance(state.get("revision"), int) or state["revision"] < 1:
        errors.append("state.revision must be a positive integer")
    if state.get("status") not in SESSION_STATUSES:
        errors.append("state.status is invalid")
    contract = state.get("contract")
    if not isinstance(contract, dict):
        errors.append("state.contract must be an object")
        return errors
    errors.extend(validate_contract(contract))
    contract_outputs = {item["id"]: item for item in contract.get("outputs", []) if isinstance(item, dict) and "id" in item}
    outputs = state.get("outputs")
    if not isinstance(outputs, list):
        errors.append("state.outputs must be an array")
        return errors
    seen: set[str] = set()
    in_progress: list[str] = []
    for index, output in enumerate(outputs):
        label = f"state.outputs[{index}]"
        if not isinstance(output, dict):
            errors.append(f"{label} must be an object")
            continue
        output_id = output.get("id")
        if output_id in seen:
            errors.append(f"duplicate state output ID {output_id!r}")
        if isinstance(output_id, str):
            seen.add(output_id)
        contract_output = contract_outputs.get(output_id)
        if contract_output is None:
            errors.append(f"{label}.id is not in the contract")
            continue
        if output.get("required") is not contract_output.get("required"):
            errors.append(f"{label}.required differs from the contract")
        if output.get("approvalRequired") is not contract_output.get("approvalRequired"):
            errors.append(f"{label}.approvalRequired differs from the contract")
        if output.get("promotionRequired") is not contract_output.get("promotionRequired"):
            errors.append(f"{label}.promotionRequired differs from the contract")
        status = output.get("status")
        if status not in OUTPUT_STATUSES:
            errors.append(f"{label}.status is invalid")
        elif status in {"generating", "reviewing", "awaiting-approval"} and isinstance(output_id, str):
            in_progress.append(output_id)
        sha256 = output.get("sha256")
        if sha256 is not None and (not isinstance(sha256, str) or HASH_RE.fullmatch(sha256) is None):
            errors.append(f"{label}.sha256 is invalid")
        if status in {"reviewing", "awaiting-approval", "accepted", "promoted"}:
            if not isinstance(output.get("artifact"), str) or sha256 is None:
                errors.append(f"{label} requires artifact and sha256")
        if status == "awaiting-approval" and not output.get("approvalRequired"):
            errors.append(f"{label} cannot await approval when the contract does not require it")
        if status == "blocked" and not isinstance(output.get("problem"), dict):
            errors.append(f"{label}.problem is required when blocked")
        if status == "deferred":
            if not output.get("userAuthorized") or not isinstance(output.get("reason"), str):
                errors.append(f"{label} deferred status requires explicit authority and reason")
        if status == "promoted" and output.get("promotionRequired"):
            if not isinstance(output.get("promotionPath"), str):
                errors.append(f"{label}.promotionPath is required when promoted")
            promotion_hash = output.get("promotionSha256")
            if not isinstance(promotion_hash, str) or HASH_RE.fullmatch(promotion_hash) is None:
                errors.append(f"{label}.promotionSha256 is invalid")
    if set(contract_outputs) != seen:
        errors.append("state.outputs must contain every contract output exactly once")
    if len(in_progress) > 1:
        errors.append(
            "only one output may be generating, reviewing, or awaiting approval at a time: "
            + ", ".join(sorted(in_progress))
        )
    if not isinstance(state.get("validationErrors"), list):
        errors.append("state.validationErrors must be an array")
    for field in ("createdAt", "updatedAt"):
        if not isinstance(state.get(field), str) or not state[field]:
            errors.append(f"state.{field} must be non-empty")
    return errors


def load_state(root: Path, session_id: str) -> tuple[Path, dict[str, Any]]:
    session_dir = session_directory(root, session_id)
    if session_dir.is_symlink():
        raise StateError("Refusing a symlinked session directory")
    state = load_json(session_dir / "state.json", "runtime state")
    errors = validate_state_shape(state, session_id)
    if errors:
        raise StateError("Invalid runtime state: " + "; ".join(errors))
    return session_dir, state


def require_revision(state: dict[str, Any], expected_revision: int) -> None:
    if state["revision"] != expected_revision:
        raise StateError(
            f"Revision conflict: expected {expected_revision}, current revision is {state['revision']}"
        )


def _commit_state(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    state["revision"] += 1
    state["updatedAt"] = utc_now()
    atomic_write_json(session_dir / "state.json", state)
    return state


def start_session(
    root_value: str | Path,
    session_id: str,
    contract_file: str | Path,
    structure_file: str | Path | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    _validate_id(session_id, "session ID")
    contract = load_json(Path(contract_file).expanduser().resolve(), "coverage contract")
    errors = validate_contract(contract)
    if errors:
        raise StateError("Invalid coverage contract: " + "; ".join(errors))
    structure = None
    if structure_file is not None:
        structure = load_json(Path(structure_file).expanduser().resolve(), "structure contract")
    session_dir = session_directory(root, session_id)
    if session_dir.exists():
        raise StateError(f"Session already exists: {session_id}")
    sessions_root = session_dir.parent
    if sessions_root.is_symlink():
        raise StateError("Refusing a symlinked sessions directory")
    sessions_root.mkdir(parents=True, exist_ok=True)
    staging = sessions_root / f".init-{session_id}-{uuid.uuid4().hex}"
    staging.mkdir(exist_ok=False)
    now = utc_now()
    state: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "sessionId": session_id,
        "revision": 1,
        "status": "active",
        "createdAt": now,
        "updatedAt": now,
        "contract": contract,
        "outputs": [
            {
                "id": output["id"],
                "required": output["required"],
                "approvalRequired": output["approvalRequired"],
                "promotionRequired": output["promotionRequired"],
                "status": "pending",
                "artifact": None,
                "sha256": None,
                "reason": None,
                "userAuthorized": False,
                "problem": None,
                "promotionPath": None,
                "promotionSha256": None,
            }
            for output in contract["outputs"]
        ],
        "validationErrors": [],
        "promotedAt": None,
    }
    try:
        (staging / "artifacts").mkdir()
        atomic_write_json(staging / "coverage.json", contract)
        if structure is not None:
            atomic_write_json(staging / "structure.json", structure)
        atomic_write_json(staging / "state.json", state)
        os.replace(staging, session_dir)
        _fsync_directory(sessions_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return state


def _clear_output(output: dict[str, Any]) -> None:
    output.update(
        artifact=None,
        sha256=None,
        reason=None,
        userAuthorized=False,
        problem=None,
        promotionPath=None,
        promotionSha256=None,
    )


def mark_output(
    root_value: str | Path,
    session_id: str,
    output_id: str,
    status: str,
    expected_revision: int,
    *,
    artifact: str | None = None,
    reason: str | None = None,
    user_authorized: bool = False,
    code: str | None = None,
    retryable: bool = False,
    next_action: str | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] in TERMINAL_SESSION_STATUSES:
        raise StateError(f"Cannot mutate terminal session status {state['status']!r}")
    if status not in OUTPUT_STATUSES - {"promoted"}:
        raise StateError("Output status must be pending, generating, reviewing, awaiting-approval, accepted, blocked, or deferred")
    outputs = _state_output_map(state)
    if output_id not in outputs:
        raise StateError(f"Unknown output ID: {output_id}")
    output = outputs[output_id]
    current = output["status"]
    contract_output = next(
        item for item in state["contract"]["outputs"] if item["id"] == output_id
    )
    if status == current:
        return state
    if status not in TRANSITIONS[current]:
        raise StateError(f"Illegal output transition {current!r} -> {status!r}")

    if status == "generating":
        active = [
            item["id"]
            for item in state["outputs"]
            if item["id"] != output_id
            and item["status"] in {"generating", "reviewing", "awaiting-approval"}
        ]
        if active:
            raise StateError(
                "Only one output may generate, review, or await approval at a time; active output: "
                + ", ".join(active)
            )
        unsettled = [
            dependency
            for dependency in contract_output["dependsOn"]
            if outputs[dependency]["status"] not in {"accepted", "promoted"}
        ]
        if unsettled:
            raise StateError(
                "Cannot generate before accepted/promoted dependencies: "
                + ", ".join(unsettled)
            )

    if status == "awaiting-approval" and not contract_output["approvalRequired"]:
        raise StateError("the coverage contract does not require approval for this output")
    if current == "reviewing" and status == "accepted" and contract_output["approvalRequired"]:
        raise StateError("approval-required output must enter awaiting-approval before acceptance")
    if current == "awaiting-approval" and status in {"accepted", "pending", "deferred"}:
        if not user_authorized:
            raise StateError("leaving awaiting-approval requires --user-authorized")
        if status == "pending" and not reason:
            raise StateError("rejecting an awaiting-approval output requires --reason")

    if current == "awaiting-approval" and status == "accepted":
        approved_artifact = output.get("artifact")
        approved_hash = output.get("sha256")
        if artifact != approved_artifact:
            raise StateError("acceptance must use the same reviewed artifact")
        if not isinstance(approved_hash, str) or HASH_RE.fullmatch(approved_hash) is None:
            raise StateError("awaiting-approval output has no valid reviewed artifact hash")
        approved_path = artifact_path(session_dir, artifact)
        if sha256_file(approved_path) != approved_hash:
            raise StateError("reviewed artifact changed while awaiting approval")

    _clear_output(output)
    output["status"] = status
    if status in {"reviewing", "awaiting-approval", "accepted"}:
        if artifact is None:
            raise StateError(f"{status} requires --artifact")
        path = artifact_path(session_dir, artifact)
        output["artifact"] = artifact
        output["sha256"] = sha256_file(path)
        if current == "awaiting-approval" and status == "accepted":
            output["userAuthorized"] = True
    elif status == "pending" and current == "awaiting-approval":
        output["reason"] = reason
        output["userAuthorized"] = True
    elif status == "blocked":
        if not code or ID_RE.fullmatch(code) is None or not next_action:
            raise StateError("blocked requires --code and --next-action")
        output["problem"] = {
            "code": code,
            "retryable": retryable,
            "nextAction": next_action,
        }
    elif status == "deferred":
        if not user_authorized or not reason:
            raise StateError("deferred requires --user-authorized and --reason")
        output["reason"] = reason
        output["userAuthorized"] = True

    state["status"] = "blocked" if any(
        item["required"] and item["status"] == "blocked" for item in state["outputs"]
    ) else "active"
    state["validationErrors"] = []
    return _commit_state(session_dir, state)


def _verify_output_artifact(session_dir: Path, output: dict[str, Any]) -> str | None:
    artifact = output.get("artifact")
    expected_hash = output.get("sha256")
    if not isinstance(artifact, str) or not isinstance(expected_hash, str):
        return f"output {output['id']} has no verified artifact"
    try:
        actual_hash = sha256_file(artifact_path(session_dir, artifact))
    except StateError as exc:
        return f"output {output['id']}: {exc}"
    if actual_hash != expected_hash:
        return f"output {output['id']} artifact hash mismatch"
    return None


def _verify_promoted_destination(
    root: Path,
    state: dict[str, Any],
    output: dict[str, Any],
) -> str | None:
    contract_output = next(
        item for item in state["contract"]["outputs"] if item["id"] == output["id"]
    )
    target = contract_output.get("promotionTarget")
    expected_hash = output.get("promotionSha256")
    if not isinstance(target, str) or not isinstance(expected_hash, str):
        return f"promoted output {output['id']} lacks promotion metadata"
    try:
        destination = _promotion_destination(root, target)
    except StateError as exc:
        return f"promoted output {output['id']}: {exc}"
    if not destination.is_file() or destination.is_symlink():
        return f"promoted output {output['id']} destination is missing"
    if sha256_file(destination) != expected_hash:
        return f"promoted output {output['id']} destination hash mismatch"
    return None


def validate_session(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
) -> tuple[dict[str, Any], list[str]]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] in {"promoted", "cancelled"}:
        raise StateError(f"Cannot validate terminal session status {state['status']!r}")
    contract_outputs = {item["id"]: item for item in state["contract"]["outputs"]}
    outputs = _state_output_map(state)
    errors: list[str] = []
    for output_id, output in outputs.items():
        status = output["status"]
        if status in {"reviewing", "awaiting-approval", "accepted"}:
            error = _verify_output_artifact(session_dir, output)
            if error:
                errors.append(error)
        elif status == "promoted":
            error = _verify_promoted_destination(root, state, output)
            if error:
                errors.append(error)
        if output["required"] and status not in SETTLED_OUTPUT_STATUSES:
            errors.append(f"required output {output_id} is {status}")
        if status == "deferred" and (not output["userAuthorized"] or not output["reason"]):
            errors.append(f"deferred output {output_id} lacks explicit authority")
        for dependency in contract_outputs[output_id]["dependsOn"]:
            if status in SETTLED_OUTPUT_STATUSES and outputs[dependency]["status"] not in SETTLED_OUTPUT_STATUSES:
                errors.append(f"output {output_id} settled before dependency {dependency}")

    state["validationErrors"] = sorted(set(errors))
    state["status"] = "blocked" if errors else "validated"
    return _commit_state(session_dir, state), state["validationErrors"]


def _blocked_problem(code: str, retryable: bool, next_action: str) -> dict[str, Any]:
    return {"code": code, "retryable": retryable, "nextAction": next_action}


def _promotion_destination(root: Path, target: str) -> Path:
    relative = _relative_path(target, "promotion target")
    if relative.parts[0] == ".frontend-workbench":
        raise StateError("Promotion target cannot be inside runtime state")
    candidate = (root / relative.as_posix()).resolve()
    if not _is_within(candidate, root):
        raise StateError("Promotion target escapes the repository")
    if not candidate.parent.is_dir() or candidate.parent.is_symlink():
        raise StateError("Promotion target parent must be an existing non-symlink directory")
    return candidate


def _reconcile_promotions(root: Path, state: dict[str, Any]) -> bool:
    contract_outputs = {item["id"]: item for item in state["contract"]["outputs"]}
    changed = False
    for output in state["outputs"]:
        contract_output = contract_outputs[output["id"]]
        if output["status"] != "accepted" or not output["promotionRequired"]:
            continue
        target = contract_output.get("promotionTarget")
        if not isinstance(target, str) or not isinstance(output.get("sha256"), str):
            continue
        destination = _promotion_destination(root, target)
        if destination.is_file() and not destination.is_symlink():
            actual_hash = sha256_file(destination)
            if actual_hash == output["sha256"]:
                output["status"] = "promoted"
                output["promotionPath"] = target
                output["promotionSha256"] = actual_hash
                changed = True
    return changed


def _promotion_complete(state: dict[str, Any]) -> bool:
    return all(
        (not item["promotionRequired"] or item["status"] in {"promoted", "deferred"})
        and (not item["required"] or item["status"] in SETTLED_OUTPUT_STATUSES)
        for item in state["outputs"]
    )


def resume_session(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] in TERMINAL_SESSION_STATUSES:
        raise StateError(f"Cannot resume terminal session status {state['status']!r}")
    changed = _reconcile_promotions(root, state)
    for output in state["outputs"]:
        if output["status"] == "generating":
            output["status"] = "blocked"
            output["problem"] = _blocked_problem(
                "unknown_outcome",
                True,
                "Inspect the renderer outcome before starting a bounded retry.",
            )
            changed = True
        elif output["status"] in {"reviewing", "awaiting-approval"}:
            error = _verify_output_artifact(session_dir, output)
            if error:
                output["status"] = "blocked"
                output["problem"] = _blocked_problem(
                    "unknown_outcome",
                    True,
                    "Recover or regenerate the review artifact before continuing.",
                )
                changed = True
        elif output["status"] == "accepted":
            error = _verify_output_artifact(session_dir, output)
            if error:
                output["status"] = "blocked"
                output["problem"] = _blocked_problem(
                    "artifact_integrity_mismatch",
                    False,
                    "Restore the accepted artifact from a trusted source before continuing.",
                )
                changed = True
        elif output["status"] == "promoted":
            error = _verify_promoted_destination(root, state, output)
            if error:
                output["status"] = "blocked"
                output["problem"] = _blocked_problem(
                    "promotion_integrity_mismatch",
                    False,
                    "Restore the promoted destination from its verified backup before continuing.",
                )
                changed = True

    if not changed:
        return state
    if any(item["required"] and item["status"] == "blocked" for item in state["outputs"]):
        state["status"] = "blocked"
    elif _promotion_complete(state) and any(
        item["promotionRequired"] for item in state["outputs"]
    ):
        state["status"] = "promoted"
        state["promotedAt"] = utc_now()
    state["validationErrors"] = []
    return _commit_state(session_dir, state)


def _copy_atomic_no_overwrite(source: Path, destination: Path) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".promote",
    )
    temporary = Path(temporary_name)
    try:
        with source.open("rb") as read_handle, os.fdopen(descriptor, "wb") as write_handle:
            shutil.copyfileobj(read_handle, write_handle)
            write_handle.flush()
            os.fsync(write_handle.fileno())
        os.link(temporary, destination)
        temporary.unlink()
        _fsync_directory(destination.parent)
    except FileExistsError as exc:
        raise StateError(f"Promotion target already exists: {destination}") from exc
    finally:
        if temporary.exists():
            temporary.unlink()


def _copy_atomic_replace(
    source: Path,
    destination: Path,
    expected_destination_hash: str,
    backup: Path,
) -> None:
    if not destination.is_file() or destination.is_symlink():
        raise StateError("--replace requires an existing regular non-symlink destination")
    if HASH_RE.fullmatch(expected_destination_hash) is None:
        raise StateError("--expected-destination-sha256 must be a lowercase SHA-256 digest")
    actual = sha256_file(destination)
    if actual != expected_destination_hash:
        raise StateError("Existing destination changed; expected SHA-256 does not match")
    backup.parent.mkdir(parents=True, exist_ok=True)
    if backup.exists():
        raise StateError(f"Refusing to overwrite promotion backup: {backup}")
    _copy_atomic_no_overwrite(destination, backup)

    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".promote",
    )
    temporary = Path(temporary_name)
    try:
        with source.open("rb") as read_handle, os.fdopen(descriptor, "wb") as write_handle:
            shutil.copyfileobj(read_handle, write_handle)
            write_handle.flush()
            os.fsync(write_handle.fileno())
        if sha256_file(destination) != expected_destination_hash:
            raise StateError("Existing destination changed during guarded replacement")
        os.replace(temporary, destination)
        _fsync_directory(destination.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def promote_output(
    root_value: str | Path,
    session_id: str,
    output_id: str,
    expected_revision: int,
    *,
    replace: bool = False,
    expected_destination_hash: str | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] != "validated":
        raise StateError("Promotion requires a validated session")
    outputs = _state_output_map(state)
    output = outputs.get(output_id)
    if output is None:
        raise StateError(f"Unknown output ID: {output_id}")
    if output["status"] != "accepted" or not output["promotionRequired"]:
        raise StateError("Promotion requires an accepted output with promotionRequired=true")
    contract_output = next(item for item in state["contract"]["outputs"] if item["id"] == output_id)
    target = contract_output.get("promotionTarget")
    if not isinstance(target, str):
        raise StateError("Promotion target is missing from the contract")
    source = artifact_path(session_dir, output["artifact"])
    source_hash = sha256_file(source)
    if source_hash != output["sha256"]:
        raise StateError("Accepted source artifact failed SHA-256 verification")
    destination = _promotion_destination(root, target)
    if replace:
        if expected_destination_hash is None:
            raise StateError("--replace requires --expected-destination-sha256")
        backup = session_dir / "backups" / f"{output_id}-{expected_destination_hash}"
        _copy_atomic_replace(source, destination, expected_destination_hash, backup)
    else:
        if expected_destination_hash is not None:
            raise StateError("--expected-destination-sha256 is valid only with --replace")
        _copy_atomic_no_overwrite(source, destination)
    readback_hash = sha256_file(destination)
    if readback_hash != source_hash:
        raise StateError("Promoted artifact failed readback verification")

    output["status"] = "promoted"
    output["promotionPath"] = target
    output["promotionSha256"] = readback_hash
    if _promotion_complete(state):
        state["status"] = "promoted"
        state["promotedAt"] = utc_now()
    return _commit_state(session_dir, state)


def cleanup_session(
    root_value: str | Path,
    session_id: str,
    confirm_session: str,
    expected_revision: int,
    *,
    discard_unpromoted: bool = False,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if confirm_session != session_id:
        raise StateError("--confirm-session must exactly match --session-id")
    unpromoted_accepted = [
        item["id"]
        for item in state["outputs"]
        if item["status"] == "accepted" and item["promotionRequired"]
    ]
    if unpromoted_accepted:
        raise StateError(
            "Cleanup would delete accepted artifacts that were not promoted: "
            + ", ".join(unpromoted_accepted)
        )
    if state["status"] not in TERMINAL_SESSION_STATUSES and not discard_unpromoted:
        raise StateError(
            "Cleanup requires a terminal session or explicit --discard-unpromoted confirmation"
        )
    if session_dir.is_symlink() or not session_dir.is_dir():
        raise StateError("Session directory is not a safe cleanup target")
    sessions_root = session_dir.parent.resolve()
    if not _is_within(session_dir.resolve(), sessions_root):
        raise StateError("Cleanup target escapes the sessions directory")
    quarantine = sessions_root / f".cleanup-{session_id}-{uuid.uuid4().hex}"
    os.replace(session_dir, quarantine)
    shutil.rmtree(quarantine)
    try:
        sessions_root.rmdir()
        sessions_root.parent.rmdir()
    except OSError:
        pass
    return {"sessionId": session_id, "status": "cleaned"}


def _print_json(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def common(name: str) -> argparse.ArgumentParser:
        command = subparsers.add_parser(name)
        command.add_argument("--root", required=True)
        command.add_argument("--session-id", required=True)
        return command

    init = common("init")
    init.add_argument("--contract", required=True)
    init.add_argument("--structure")

    common("status")

    mark = common("mark")
    mark.add_argument("--output-id", required=True)
    mark.add_argument("--status", required=True)
    mark.add_argument("--expected-revision", required=True, type=int)
    mark.add_argument("--artifact")
    mark.add_argument("--reason")
    mark.add_argument("--user-authorized", action="store_true")
    mark.add_argument("--code")
    mark.add_argument("--retryable", action="store_true")
    mark.add_argument("--next-action")

    validate = common("validate")
    validate.add_argument("--expected-revision", required=True, type=int)

    resume = common("resume")
    resume.add_argument("--expected-revision", required=True, type=int)

    promote = common("promote")
    promote.add_argument("--output-id", required=True)
    promote.add_argument("--expected-revision", required=True, type=int)
    promote.add_argument("--replace", action="store_true")
    promote.add_argument("--expected-destination-sha256")

    cleanup = common("cleanup")
    cleanup.add_argument("--confirm-session", required=True)
    cleanup.add_argument("--expected-revision", required=True, type=int)
    cleanup.add_argument("--discard-unpromoted", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            result = start_session(
                args.root,
                args.session_id,
                args.contract,
                structure_file=args.structure,
            )
        elif args.command == "status":
            root = preflight(args.root)
            _, result = load_state(root, args.session_id)
        elif args.command == "mark":
            result = mark_output(
                args.root,
                args.session_id,
                args.output_id,
                args.status,
                args.expected_revision,
                artifact=args.artifact,
                reason=args.reason,
                user_authorized=args.user_authorized,
                code=args.code,
                retryable=args.retryable,
                next_action=args.next_action,
            )
        elif args.command == "validate":
            result, errors = validate_session(
                args.root,
                args.session_id,
                args.expected_revision,
            )
            _print_json(result)
            return 2 if errors else 0
        elif args.command == "resume":
            result = resume_session(args.root, args.session_id, args.expected_revision)
        elif args.command == "promote":
            result = promote_output(
                args.root,
                args.session_id,
                args.output_id,
                args.expected_revision,
                replace=args.replace,
                expected_destination_hash=args.expected_destination_sha256,
            )
        elif args.command == "cleanup":
            result = cleanup_session(
                args.root,
                args.session_id,
                args.confirm_session,
                args.expected_revision,
                discard_unpromoted=args.discard_unpromoted,
            )
        else:
            raise AssertionError(args.command)
    except StateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _print_json(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
