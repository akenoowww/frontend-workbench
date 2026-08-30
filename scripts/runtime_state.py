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
import struct
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit


SCHEMA_VERSION = 3
PREVIOUS_SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1
IGNORE_LINE = "/.frontend-workbench/"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
WORKFLOW_PROFILES = {"micro", "standard", "full"}
IMPLEMENTATION_STATUSES = {"not-started", "in-progress", "completed"}
FIDELITY_RESULTS = {"pass", "fail", "blocked"}
VISUAL_ARTIFACT_POLICIES = {"runnable", "imagegen-required", "no-imagegen"}
VISUAL_DIRECTION_POLICIES = {"required", "not-required"}
VISUAL_DIRECTION_STATUSES = {"pending", "locked", "not-required"}
OPERATIONAL_METADATA_DEFAULT_VISIBILITY = "hidden-unless-required"
OPERATIONAL_METADATA_AUTHORITIES = {
    "user-request",
    "product-requirement",
    "approved-design",
    "legal-safety",
}
CHECKPOINT_MODES = {
    "continuous",
    "review-before-artifact",
    "review-each-stage",
    "review-before-implementation",
}
QUALITY_GATE_STATUSES = {"pending", "pass", "fail", "blocked", "not-required"}
MAX_BATCH_TRANSITIONS = 50
ARTIFACT_KINDS = {
    "none",
    "specification",
    "runnable",
    "browser-screenshot",
    "imagegen",
}
PRODUCT_OBJECT_ROLES = {
    "root",
    "primary",
    "supporting",
    "downstream-evidence",
    "implementation-detail",
}
CAPABILITY_COMPLEXITIES = {"bounded", "complex", "foundational"}
IMPLEMENTATION_APPROACHES = {
    "reuse",
    "extend",
    "compose",
    "platform",
    "framework",
    "external-dependency",
    "project-owned",
}
CANDIDATE_KINDS = IMPLEMENTATION_APPROACHES | {
    "project-file",
    "existing-owner",
    "native",
}
AUTHORITY_ACTIONS = {
    "confirm-intent",
    "supersede-contract",
    "relax-contract",
    "reset-concept",
}
SESSION_STATUSES = {
    "active",
    "blocked",
    "validated",
    "promoted",
    "completed",
    "awaiting-user-review",
    "rejected",
    "superseded",
    "deferred",
    "cancelled",
}
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
TERMINAL_SESSION_STATUSES = {
    "promoted",
    "completed",
    "rejected",
    "superseded",
    "deferred",
    "cancelled",
}
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


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def product_intent_sha256(product_intent: dict[str, Any]) -> str:
    return _canonical_sha256(product_intent)


def visual_direction_sha256(visual_direction: dict[str, Any]) -> str:
    return _canonical_sha256(visual_direction)


def structure_sha256(structure: dict[str, Any]) -> str:
    return _canonical_sha256(structure)


def _is_v3_contract(contract: dict[str, Any]) -> bool:
    return contract.get("schemaVersion") == SCHEMA_VERSION


def _is_v3_state(state: dict[str, Any]) -> bool:
    return state.get("schemaVersion") == SCHEMA_VERSION


def _contract_output_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in contract.get("outputs", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def _design_evidence_required(contract_output: dict[str, Any]) -> bool:
    if "designEvidenceRequired" in contract_output:
        return contract_output.get("designEvidenceRequired") is True
    return contract_output.get("required") is True


def _runtime_evidence_required(contract_output: dict[str, Any]) -> bool:
    if "runtimeEvidenceRequired" in contract_output:
        return contract_output.get("runtimeEvidenceRequired") is True
    return contract_output.get("required") is True


def _state_design_evidence_required(output: dict[str, Any]) -> bool:
    if "designEvidenceRequired" in output:
        return output.get("designEvidenceRequired") is True
    return output.get("required") is True


def _state_runtime_evidence_required(output: dict[str, Any]) -> bool:
    if "runtimeEvidenceRequired" in output:
        return output.get("runtimeEvidenceRequired") is True
    return output.get("required") is True


def _contract_implementation_target_paths(contract: dict[str, Any]) -> list[str]:
    targets = contract.get("implementationTargets", [])
    if _is_v3_contract(contract):
        return [
            item["path"]
            for item in targets
            if isinstance(item, dict) and isinstance(item.get("path"), str)
        ]
    return [item for item in targets if isinstance(item, str)]


def default_operational_metadata_policy() -> dict[str, Any]:
    return {
        "defaultVisibility": OPERATIONAL_METADATA_DEFAULT_VISIBILITY,
        "requiredClaims": [],
    }


def lifecycle_plan_digest(contract: dict[str, Any]) -> str:
    if _is_v3_contract(contract):
        # V3 confirmations bind the complete canonical contract. This deliberately
        # includes coverage, target ownership, evidence roles, anchors, authority,
        # and render budgets so a replacement cannot weaken an unbound subtree.
        return _canonical_sha256(contract)
    equivalences = sorted(
        [
            {
                "outputId": output.get("id"),
                "evidenceEquivalentTo": output.get("evidenceEquivalentTo"),
                "equivalenceJustification": output.get("equivalenceJustification"),
            }
            for output in contract.get("outputs", [])
            if isinstance(output, dict)
            and (
                "evidenceEquivalentTo" in output
                or "equivalenceJustification" in output
            )
        ],
        key=lambda item: str(item["outputId"]),
    )
    payload = {
        "productIntent": contract.get("productIntent"),
        "visualArtifactPolicy": contract.get("visualArtifactPolicy"),
        "checkpointMode": contract.get("checkpointMode"),
        "evidenceEquivalences": equivalences,
    }
    # Preserve legacy snapshot digests when coverage predates an explicit policy.
    # New sessions persist the policies before their lifecycle digest is created.
    if "visualDirectionPolicy" in contract:
        payload["visualDirectionPolicy"] = contract.get("visualDirectionPolicy")
    if "operationalMetadataPolicy" in contract:
        payload["operationalMetadataPolicy"] = contract.get(
            "operationalMetadataPolicy"
        )
    return _canonical_sha256(payload)


def _json_pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _changed_json_paths(before: Any, after: Any, path: str = "") -> list[str]:
    if type(before) is not type(after):
        return [path or "/"]
    if isinstance(before, dict):
        changed: list[str] = []
        for key in sorted(set(before) | set(after)):
            child = f"{path}/{_json_pointer_escape(str(key))}"
            if key not in before or key not in after:
                changed.append(child)
            else:
                changed.extend(_changed_json_paths(before[key], after[key], child))
        return changed
    if isinstance(before, list):
        if before == after:
            return []
        return [path or "/"]
    return [] if before == after else [path or "/"]


def _contract_relaxations(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    relaxations: list[str] = []
    if (
        before.get("visualArtifactPolicy") == "imagegen-required"
        and after.get("visualArtifactPolicy") != "imagegen-required"
    ):
        relaxations.append("visualArtifactPolicy no longer requires imagegen")
    before_checkpoint = before.get("checkpointMode")
    after_checkpoint = after.get("checkpointMode")
    if (
        before_checkpoint == "review-each-stage"
        and after_checkpoint != "review-each-stage"
    ) or (
        before_checkpoint
        in {"review-before-artifact", "review-before-implementation"}
        and after_checkpoint == "continuous"
    ):
        relaxations.append(
            f"checkpointMode relaxed from {before_checkpoint} to {after_checkpoint}"
        )
    if (
        before.get("visualDirectionPolicy") == "required"
        and after.get("visualDirectionPolicy") != "required"
    ):
        relaxations.append("visualDirectionPolicy no longer required")
    before_authority = before.get("authority", {})
    after_authority = after.get("authority", {})
    for field in ("pageStructure", "interactionModel"):
        if (
            before_authority.get(field) == "locked"
            and after_authority.get(field) != "locked"
        ):
            relaxations.append(f"authority.{field} no longer locked")
    if (
        before_authority.get("contentRepartition") == "within-surface-only"
        and after_authority.get("contentRepartition")
        != "within-surface-only"
    ):
        relaxations.append("authority.contentRepartition broadened")

    before_intent = before.get("productIntent", {})
    after_intent = after.get("productIntent", {})
    for field in ("requiredDomains", "protectedCapabilities"):
        removed = sorted(
            set(before_intent.get(field, [])) - set(after_intent.get(field, []))
        )
        if removed:
            relaxations.append(f"productIntent.{field} removed: " + ", ".join(removed))

    before_surface_map = {
        item.get("id"): item
        for item in before.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    after_surface_map = {
        item.get("id"): item
        for item in after.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    removed_surfaces = sorted(set(before_surface_map) - set(after_surface_map))
    if removed_surfaces:
        relaxations.append("surfaces removed: " + ", ".join(removed_surfaces))
    for surface_id in sorted(set(before_surface_map) & set(after_surface_map)):
        before_primary = before_surface_map[surface_id].get("primaryObjectId")
        after_primary = after_surface_map[surface_id].get("primaryObjectId")
        if before_primary != after_primary:
            relaxations.append(
                f"surface {surface_id} primaryObjectId changed from "
                f"{before_primary!r} to {after_primary!r}"
            )

    before_product_model = before.get("productModel", {})
    after_product_model = after.get("productModel", {})
    if before_product_model.get("rootObjectId") != after_product_model.get(
        "rootObjectId"
    ):
        relaxations.append("productModel.rootObjectId changed")
    before_objects = {
        item.get("id"): item
        for item in before_product_model.get("objects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    after_objects = {
        item.get("id"): item
        for item in after_product_model.get("objects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    removed_objects = sorted(set(before_objects) - set(after_objects))
    if removed_objects:
        relaxations.append("product objects removed: " + ", ".join(removed_objects))
    for object_id in sorted(set(before_objects) & set(after_objects)):
        prior = before_objects[object_id]
        current = after_objects[object_id]
        if prior.get("role") != current.get("role"):
            relaxations.append(
                f"product object {object_id} role changed from "
                f"{prior.get('role')!r} to {current.get('role')!r}"
            )
        if prior.get("parentId") != current.get("parentId"):
            relaxations.append(f"product object {object_id} parent ownership changed")
        if set(prior.get("evidenceForObjectIds", [])) != set(
            current.get("evidenceForObjectIds", [])
        ):
            relaxations.append(f"product object {object_id} evidence ownership changed")
    for object_id in sorted(set(after_objects) - set(before_objects)):
        if after_objects[object_id].get("role") in {"root", "primary"}:
            relaxations.append(
                f"new product object {object_id} promoted into primary hierarchy"
            )

    before_outputs = _contract_output_map(before)
    after_outputs = _contract_output_map(after)
    for output_id, prior in before_outputs.items():
        current = after_outputs.get(output_id)
        if current is None:
            if _design_evidence_required(prior) or _runtime_evidence_required(prior):
                relaxations.append(f"required output removed: {output_id}")
            continue
        if _design_evidence_required(prior) and not _design_evidence_required(current):
            relaxations.append(f"output {output_id} design evidence no longer required")
        if _runtime_evidence_required(prior) and not _runtime_evidence_required(current):
            relaxations.append(f"output {output_id} runtime evidence no longer required")
        if prior.get("approvalRequired") and not current.get("approvalRequired"):
            relaxations.append(f"output {output_id} approval no longer required")
        if (
            prior.get("artifactKind") == "imagegen"
            and current.get("artifactKind") != "imagegen"
            and _design_evidence_required(prior)
        ):
            relaxations.append(f"output {output_id} no longer requires imagegen evidence")
        if (
            prior.get("evidenceEquivalentTo") is None
            and current.get("evidenceEquivalentTo") is not None
        ):
            relaxations.append(f"output {output_id} now permits evidence equivalence")

    before_capabilities = {
        item.get("id"): item
        for item in before.get("capabilityRequirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    after_capabilities = {
        item.get("id"): item
        for item in after.get("capabilityRequirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for capability_id, prior in before_capabilities.items():
        current = after_capabilities.get(capability_id)
        if prior.get("required") and (
            current is None or current.get("required") is not True
        ):
            relaxations.append(f"required capability removed or weakened: {capability_id}")
            continue
        if current is not None and prior.get("required"):
            if prior.get("ownerObjectId") != current.get("ownerObjectId"):
                relaxations.append(
                    f"required capability {capability_id} ownerObjectId changed"
                )
            if prior.get("capability") != current.get("capability"):
                relaxations.append(
                    f"required capability {capability_id} capability label changed"
                )
            complexity_rank = {"bounded": 0, "complex": 1, "foundational": 2}
            prior_complexity = prior.get("complexity")
            current_complexity = current.get("complexity")
            if complexity_rank.get(current_complexity, -1) < complexity_rank.get(
                prior_complexity, -1
            ):
                relaxations.append(
                    f"required capability {capability_id} complexity demoted from "
                    f"{prior_complexity} to {current_complexity}"
                )
            if set(prior.get("surfaceIds", [])) != set(
                current.get("surfaceIds", [])
            ):
                relaxations.append(
                    f"required capability {capability_id} surfaceIds changed"
                )
            if set(prior.get("constraints", [])) != set(
                current.get("constraints", [])
            ):
                relaxations.append(
                    f"required capability {capability_id} constraints changed"
                )

    before_targets = set(_contract_implementation_target_paths(before))
    after_targets = set(_contract_implementation_target_paths(after))
    removed_targets = sorted(before_targets - after_targets)
    if removed_targets:
        relaxations.append("implementation targets removed: " + ", ".join(removed_targets))
    before_target_map = {
        item.get("path"): item
        for item in before.get("implementationTargets", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    after_target_map = {
        item.get("path"): item
        for item in after.get("implementationTargets", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    for path, prior in before_target_map.items():
        current = after_target_map.get(path)
        if current is None:
            continue
        removed_target_surfaces = sorted(
            set(prior.get("surfaceIds", [])) - set(current.get("surfaceIds", []))
        )
        if removed_target_surfaces:
            relaxations.append(
                f"implementation target {path} dropped surfaces: "
                + ", ".join(removed_target_surfaces)
            )
    before_claim_ids = {
        item.get("id")
        for item in before.get("operationalMetadataPolicy", {}).get(
            "requiredClaims", []
        )
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    after_claim_ids = {
        item.get("id")
        for item in after.get("operationalMetadataPolicy", {}).get(
            "requiredClaims", []
        )
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    removed_claims = sorted(before_claim_ids - after_claim_ids)
    if removed_claims:
        relaxations.append(
            "operational metadata requirements removed: " + ", ".join(removed_claims)
        )
    return relaxations


def _build_contract_delta(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    changed_paths = _changed_json_paths(before, after)
    return {
        "fromContractSha256": _canonical_sha256(before),
        "toContractSha256": _canonical_sha256(after),
        "changedPaths": changed_paths,
        "materialChanges": list(changed_paths),
        "relaxations": _contract_relaxations(before, after),
    }


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


def _implementation_relative_path(value: str, label: str) -> PurePosixPath:
    if not value.strip():
        raise StateError(f"{label} must be a non-empty implementation path")
    relative = _relative_path(value, label)
    if relative.parts[0] in {".frontend-workbench", ".git"}:
        raise StateError(f"{label} cannot target runtime or Git metadata")
    return relative


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


def authority_receipt_path(
    session_dir: Path,
    value: str,
    *,
    require_file: bool = True,
) -> Path:
    relative = _relative_path(value, "authority receipt path")
    if not relative.parts or relative.parts[0] != "authority":
        raise StateError("Authority receipt paths must start with authority/")
    authority_root_path = session_dir / "authority"
    if authority_root_path.is_symlink():
        raise StateError("Refusing a symlinked session authority directory")
    candidate_path = session_dir
    for part in relative.parts:
        candidate_path = candidate_path / part
        if candidate_path.is_symlink():
            raise StateError(f"Refusing symlinked authority receipt path: {value}")
    authority_root = authority_root_path.resolve()
    candidate = candidate_path.resolve()
    if not _is_within(candidate, authority_root):
        raise StateError("Authority receipt path escapes the session authority directory")
    if require_file and (not candidate.is_file() or candidate.is_symlink()):
        raise StateError(
            f"Authority receipt must be a regular non-symlink file: {candidate}"
        )
    return candidate


def validate_authority_receipt(
    receipt: dict[str, Any],
    required_actions: set[str],
    *,
    expected_session_id: str | None = None,
    expected_contract_sha256: str | None = None,
    expected_structure_sha256: str | None = None,
    expected_base_contract_sha256: str | None = None,
    expected_result_contract_sha256: str | None = None,
    expected_delta_sha256: str | None = None,
    enforce_context: bool = False,
) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        receipt,
        {
            "schemaVersion",
            "kind",
            "sessionId",
            "contractSha256",
            "structureSha256",
            "baseContractSha256",
            "resultContractSha256",
            "deltaSha256",
            "sourceRef",
            "messageSha256",
            "authorizedActions",
            "statement",
        },
        "authority receipt",
        errors,
    )
    if receipt.get("schemaVersion") != 1:
        errors.append("authority receipt.schemaVersion must be 1")
    if receipt.get("kind") != "user-message":
        errors.append("authority receipt.kind must be user-message")
    session_id = receipt.get("sessionId")
    if not isinstance(session_id, str) or ID_RE.fullmatch(session_id) is None:
        errors.append("authority receipt.sessionId is invalid")
    for field in ("contractSha256", "structureSha256"):
        value = receipt.get(field)
        if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
            errors.append(f"authority receipt.{field} is invalid")
    for field in (
        "baseContractSha256",
        "resultContractSha256",
        "deltaSha256",
    ):
        value = receipt.get(field)
        if value is not None and (
            not isinstance(value, str) or HASH_RE.fullmatch(value) is None
        ):
            errors.append(f"authority receipt.{field} is invalid")
    for field in ("sourceRef", "statement"):
        value = receipt.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"authority receipt.{field} must be non-empty")
    message_sha = receipt.get("messageSha256")
    if not isinstance(message_sha, str) or HASH_RE.fullmatch(message_sha) is None:
        errors.append("authority receipt.messageSha256 is invalid")
    actions = receipt.get("authorizedActions")
    if (
        not isinstance(actions, list)
        or not actions
        or any(not isinstance(action, str) or not action.strip() for action in actions)
    ):
        errors.append(
            "authority receipt.authorizedActions must be a non-empty array of strings"
        )
        action_set: set[str] = set()
    else:
        action_set = set(actions)
        if len(action_set) != len(actions):
            errors.append("authority receipt.authorizedActions contains duplicates")
        for action in sorted(action_set - AUTHORITY_ACTIONS):
            errors.append(
                f"authority receipt.authorizedActions contains invalid action {action!r}"
            )
    for action in sorted(required_actions - action_set):
        errors.append(f"authority receipt does not authorize {action!r}")
    if action_set & {"supersede-contract", "relax-contract"}:
        for field in (
            "baseContractSha256",
            "resultContractSha256",
            "deltaSha256",
        ):
            if not isinstance(receipt.get(field), str):
                errors.append(
                    f"authority receipt.{field} is required for contract supersession"
                )
    if enforce_context:
        expected = {
            "sessionId": expected_session_id,
            "contractSha256": expected_contract_sha256,
            "structureSha256": expected_structure_sha256,
            "baseContractSha256": expected_base_contract_sha256,
            "resultContractSha256": expected_result_contract_sha256,
            "deltaSha256": expected_delta_sha256,
        }
        for field, expected_value in expected.items():
            if receipt.get(field) != expected_value:
                errors.append(
                    f"authority receipt.{field} does not match the authorized lifecycle context"
                )
    return errors


def _authority_receipt_summary(
    path_value: str,
    path: Path,
    receipt: dict[str, Any],
) -> dict[str, Any]:
    return {
        "path": path_value,
        "sha256": sha256_file(path),
        "kind": receipt["kind"],
        "sessionId": receipt["sessionId"],
        "contractSha256": receipt["contractSha256"],
        "structureSha256": receipt["structureSha256"],
        "baseContractSha256": receipt.get("baseContractSha256"),
        "resultContractSha256": receipt.get("resultContractSha256"),
        "deltaSha256": receipt.get("deltaSha256"),
        "sourceRef": receipt["sourceRef"],
        "messageSha256": receipt["messageSha256"],
        "authorizedActions": list(receipt["authorizedActions"]),
    }


def _store_authority_receipt(
    session_dir: Path,
    source_value: str | Path | None,
    destination_value: str,
    required_actions: set[str],
    *,
    expected_session_id: str,
    expected_contract_sha256: str,
    expected_structure_sha256: str,
    expected_base_contract_sha256: str | None = None,
    expected_result_contract_sha256: str | None = None,
    expected_delta_sha256: str | None = None,
) -> dict[str, Any]:
    if source_value is None:
        raise StateError(
            "V3 user authorization requires a file-backed authority receipt"
        )
    source = Path(source_value).expanduser().resolve()
    receipt = load_json(source, "authority receipt")
    errors = validate_authority_receipt(
        receipt,
        required_actions,
        expected_session_id=expected_session_id,
        expected_contract_sha256=expected_contract_sha256,
        expected_structure_sha256=expected_structure_sha256,
        expected_base_contract_sha256=expected_base_contract_sha256,
        expected_result_contract_sha256=expected_result_contract_sha256,
        expected_delta_sha256=expected_delta_sha256,
        enforce_context=True,
    )
    if errors:
        raise StateError("Invalid authority receipt: " + "; ".join(errors))
    destination = authority_receipt_path(
        session_dir,
        destination_value,
        require_file=False,
    )
    atomic_write_json(destination, receipt)
    stored = load_json(destination, "stored authority receipt")
    stored_errors = validate_authority_receipt(
        stored,
        required_actions,
        expected_session_id=expected_session_id,
        expected_contract_sha256=expected_contract_sha256,
        expected_structure_sha256=expected_structure_sha256,
        expected_base_contract_sha256=expected_base_contract_sha256,
        expected_result_contract_sha256=expected_result_contract_sha256,
        expected_delta_sha256=expected_delta_sha256,
        enforce_context=True,
    )
    if stored_errors:
        raise StateError(
            "Invalid stored authority receipt: " + "; ".join(stored_errors)
        )
    return _authority_receipt_summary(destination_value, destination, stored)


def _verify_stored_authority_receipt(
    session_dir: Path,
    summary: Any,
    required_actions: set[str],
    *,
    expected_session_id: str,
    expected_contract_sha256: str,
    expected_structure_sha256: str,
    expected_base_contract_sha256: str | None = None,
    expected_result_contract_sha256: str | None = None,
    expected_delta_sha256: str | None = None,
) -> dict[str, Any]:
    if not isinstance(summary, dict):
        raise StateError("V3 authorization lacks a stored authority receipt")
    allowed = {
        "path",
        "sha256",
        "kind",
        "sessionId",
        "contractSha256",
        "structureSha256",
        "baseContractSha256",
        "resultContractSha256",
        "deltaSha256",
        "sourceRef",
        "messageSha256",
        "authorizedActions",
    }
    unknown = sorted(set(summary) - allowed)
    if unknown:
        raise StateError(
            "Stored authority receipt contains unknown field(s): "
            + ", ".join(unknown)
        )
    path_value = summary.get("path")
    expected_sha = summary.get("sha256")
    if not isinstance(path_value, str):
        raise StateError("Stored authority receipt path is invalid")
    if not isinstance(expected_sha, str) or HASH_RE.fullmatch(expected_sha) is None:
        raise StateError("Stored authority receipt SHA-256 is invalid")
    path = authority_receipt_path(session_dir, path_value)
    if sha256_file(path) != expected_sha:
        raise StateError("Stored authority receipt changed after authorization")
    receipt = load_json(path, "stored authority receipt")
    errors = validate_authority_receipt(
        receipt,
        required_actions,
        expected_session_id=expected_session_id,
        expected_contract_sha256=expected_contract_sha256,
        expected_structure_sha256=expected_structure_sha256,
        expected_base_contract_sha256=expected_base_contract_sha256,
        expected_result_contract_sha256=expected_result_contract_sha256,
        expected_delta_sha256=expected_delta_sha256,
        enforce_context=True,
    )
    if errors:
        raise StateError("Invalid stored authority receipt: " + "; ".join(errors))
    verified = _authority_receipt_summary(path_value, path, receipt)
    if verified != summary:
        raise StateError("Stored authority receipt summary differs from receipt bytes")
    return verified


def _reject_authority_receipt_replay(
    root: Path,
    target_session_id: str,
    receipt: dict[str, Any],
    required_actions: set[str],
    *,
    allow_same_session: bool = True,
) -> None:
    """Bind one user message/action to one lifecycle session.

    The public receipt schema intentionally stays small. The runtime makes the
    binding concrete by storing the receipt inside the session and rejecting a
    matching message/action already attached to any other session snapshot.
    """

    sessions_root = root / ".frontend-workbench" / "sessions"
    if not sessions_root.is_dir() or sessions_root.is_symlink():
        return
    message_sha = receipt.get("messageSha256")
    for state_file in sessions_root.glob("*/state.json"):
        if state_file.is_symlink() or not state_file.is_file():
            continue
        try:
            existing = json.loads(state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(existing, dict):
            continue
        existing_session_id = existing.get("sessionId")
        if existing_session_id == target_session_id and allow_same_session:
            continue
        summaries = [
            existing.get("intentConfirmation", {}).get("authorityReceipt"),
            existing.get("lineage", {}).get("authorityReceipt"),
        ]
        for summary in summaries:
            if not isinstance(summary, dict):
                continue
            if summary.get("messageSha256") != message_sha:
                continue
            authorized_actions = set(summary.get("authorizedActions", []))
            overlap = sorted(required_actions & authorized_actions)
            if overlap:
                raise StateError(
                    "Authority receipt replay is forbidden: user message already "
                    f"authorized {', '.join(overlap)} for session {existing_session_id!r}"
                )
    for receipt_file in sessions_root.glob("*/authority/*.json"):
        existing_session_id = receipt_file.parent.parent.name
        if existing_session_id == target_session_id and allow_same_session:
            continue
        if receipt_file.is_symlink() or not receipt_file.is_file():
            continue
        try:
            existing_receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(existing_receipt, dict):
            continue
        if existing_receipt.get("messageSha256") != message_sha:
            continue
        overlap = sorted(
            required_actions & set(existing_receipt.get("authorizedActions", []))
        )
        if overlap:
            raise StateError(
                "Authority receipt replay is forbidden: user message already "
                f"authorized {', '.join(overlap)} for session {existing_session_id!r}"
            )


def _unknown_keys(value: dict[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{label} contains unknown field {key!r}")


def validate_visual_direction_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scalar_fields = {
        "conceptThesis",
        "brandPosture",
        "visualTension",
        "signatureMove",
        "densityRhythm",
        "surfaceLanguage",
        "motionTone",
        "imageryRole",
    }
    list_fields = {
        "hierarchyPrinciples",
        "typographyRoles",
        "colorRoles",
        "preserveFromProjectDNA",
        "intentionalDepartures",
        "avoid",
    }
    _unknown_keys(
        contract,
        {"schemaVersion", "evidence", "redesignBoundary", "contentDistribution"}
        | scalar_fields
        | list_fields,
        "visualDirection",
        errors,
    )
    if contract.get("schemaVersion") != 1:
        errors.append("visualDirection.schemaVersion must be 1")
    for field in sorted(scalar_fields):
        value = contract.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"visualDirection.{field} must be non-empty")
    non_empty_lists = {
        "hierarchyPrinciples",
        "typographyRoles",
        "colorRoles",
        "avoid",
    }
    for field in sorted(list_fields):
        values = contract.get(field)
        if (
            not isinstance(values, list)
            or (field in non_empty_lists and not values)
            or any(not isinstance(item, str) or not item.strip() for item in values)
        ):
            qualifier = "a non-empty array" if field in non_empty_lists else "an array"
            errors.append(
                f"visualDirection.{field} must be {qualifier} of non-empty strings"
            )
        elif len(set(values)) != len(values):
            errors.append(f"visualDirection.{field} contains duplicates")
    evidence = contract.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("visualDirection.evidence must be a non-empty array")
    else:
        source_types = {
            "project-file",
            "screenshot",
            "brand-guide",
            "website",
            "user-input",
        }
        for index, item in enumerate(evidence):
            label = f"visualDirection.evidence[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            _unknown_keys(
                item,
                {"sourceType", "sourceRef", "observation", "sourceSha256"},
                label,
                errors,
            )
            if item.get("sourceType") not in source_types:
                errors.append(f"{label}.sourceType is invalid")
            for field in ("sourceRef", "observation"):
                value = item.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{label}.{field} must be non-empty")
            source_sha = item.get("sourceSha256")
            if source_sha is not None and (
                not isinstance(source_sha, str) or HASH_RE.fullmatch(source_sha) is None
            ):
                errors.append(f"{label}.sourceSha256 is invalid")
    redesign_boundary = contract.get("redesignBoundary")
    if redesign_boundary is not None:
        if not isinstance(redesign_boundary, dict):
            errors.append("visualDirection.redesignBoundary must be an object")
        else:
            _unknown_keys(
                redesign_boundary,
                {"mode", "preserveRegions", "replaceRegions", "forbiddenCarryover"},
                "visualDirection.redesignBoundary",
                errors,
            )
            mode = redesign_boundary.get("mode")
            if mode not in {"preserve-only", "restyle-within-structure", "greenfield"}:
                errors.append("visualDirection.redesignBoundary.mode is invalid")
            material_dimensions = {
                "macro-layout",
                "information-hierarchy",
                "module-topology",
                "typography-scale",
                "surface-language",
                "color-role-expression",
                "data-visualization-form",
                "spacing-density",
                "imagery-role",
            }
            preserve_regions = redesign_boundary.get("preserveRegions")
            replace_regions = redesign_boundary.get("replaceRegions")
            if not isinstance(preserve_regions, list):
                errors.append(
                    "visualDirection.redesignBoundary.preserveRegions must be an array"
                )
                preserve_regions = []
            if mode == "preserve-only" and not preserve_regions:
                errors.append(
                    "visualDirection.redesignBoundary preserve-only mode requires an exact preserved region"
                )
            if not isinstance(replace_regions, list) or not replace_regions:
                errors.append(
                    "visualDirection.redesignBoundary.replaceRegions must be a non-empty array"
                )
                replace_regions = []
            preserve_ids: set[str] = set()
            for index, region in enumerate(preserve_regions):
                label = f"visualDirection.redesignBoundary.preserveRegions[{index}]"
                if not isinstance(region, dict):
                    errors.append(f"{label} must be an object")
                    continue
                _unknown_keys(region, {"regionId", "sourceRef", "invariants"}, label, errors)
                region_id = region.get("regionId")
                if not isinstance(region_id, str) or ID_RE.fullmatch(region_id) is None:
                    errors.append(f"{label}.regionId is invalid")
                elif region_id in preserve_ids:
                    errors.append(f"{label}.regionId is duplicated")
                else:
                    preserve_ids.add(region_id)
                if not isinstance(region.get("sourceRef"), str) or not region["sourceRef"].strip():
                    errors.append(f"{label}.sourceRef must be non-empty")
                invariants = region.get("invariants")
                if (
                    not isinstance(invariants, list)
                    or not invariants
                    or any(not isinstance(item, str) or not item.strip() for item in invariants)
                ):
                    errors.append(f"{label}.invariants must be a non-empty string array")
                elif len(set(invariants)) != len(invariants):
                    errors.append(f"{label}.invariants contains duplicates")
            replace_ids: set[str] = set()
            for index, region in enumerate(replace_regions):
                label = f"visualDirection.redesignBoundary.replaceRegions[{index}]"
                if not isinstance(region, dict):
                    errors.append(f"{label} must be an object")
                    continue
                _unknown_keys(
                    region,
                    {"regionId", "sourceRef", "mustChange", "minimumChangedDimensions"},
                    label,
                    errors,
                )
                region_id = region.get("regionId")
                if not isinstance(region_id, str) or ID_RE.fullmatch(region_id) is None:
                    errors.append(f"{label}.regionId is invalid")
                elif region_id in replace_ids:
                    errors.append(f"{label}.regionId is duplicated")
                else:
                    replace_ids.add(region_id)
                if not isinstance(region.get("sourceRef"), str) or not region["sourceRef"].strip():
                    errors.append(f"{label}.sourceRef must be non-empty")
                must_change = region.get("mustChange")
                if (
                    not isinstance(must_change, list)
                    or len(must_change) < 2
                    or any(item not in material_dimensions for item in must_change)
                    or len(set(must_change)) != len(must_change)
                ):
                    errors.append(
                        f"{label}.mustChange must contain at least two unique material dimensions"
                    )
                    must_change = []
                minimum = region.get("minimumChangedDimensions")
                if (
                    not isinstance(minimum, int)
                    or isinstance(minimum, bool)
                    or minimum < 1
                    or minimum > len(must_change)
                ):
                    errors.append(
                        f"{label}.minimumChangedDimensions must be between 1 and the mustChange count"
                    )
            overlap = sorted(preserve_ids & replace_ids)
            if overlap:
                errors.append(
                    "visualDirection.redesignBoundary regions cannot be both preserved and replaced: "
                    + ", ".join(overlap)
                )
            forbidden = redesign_boundary.get("forbiddenCarryover")
            if (
                not isinstance(forbidden, list)
                or not forbidden
                or any(not isinstance(item, str) or not item.strip() for item in forbidden)
            ):
                errors.append(
                    "visualDirection.redesignBoundary.forbiddenCarryover must be a non-empty string array"
                )
            elif len(set(forbidden)) != len(forbidden):
                errors.append(
                    "visualDirection.redesignBoundary.forbiddenCarryover contains duplicates"
                )
    content_distribution = contract.get("contentDistribution")
    if content_distribution is not None:
        if not isinstance(content_distribution, dict):
            errors.append("visualDirection.contentDistribution must be an object")
        else:
            _unknown_keys(
                content_distribution,
                {
                    "strategy",
                    "firstViewportRule",
                    "bands",
                    "sharedContentIds",
                    "mustRemainReachable",
                },
                "visualDirection.contentDistribution",
                errors,
            )
            strategy = content_distribution.get("strategy")
            if strategy not in {
                "single-viewport",
                "progressive-scroll",
                "multi-surface",
                "on-demand",
            }:
                errors.append("visualDirection.contentDistribution.strategy is invalid")
            first_viewport_rule = content_distribution.get("firstViewportRule")
            if not isinstance(first_viewport_rule, str) or not first_viewport_rule.strip():
                errors.append(
                    "visualDirection.contentDistribution.firstViewportRule must be non-empty"
                )
            bands = content_distribution.get("bands")
            if not isinstance(bands, list) or not bands:
                errors.append(
                    "visualDirection.contentDistribution.bands must be a non-empty array"
                )
                bands = []
            band_ids: set[str] = set()
            placements: set[str] = set()
            content_id_bands: dict[str, set[str]] = {}
            for index, band in enumerate(bands):
                label = f"visualDirection.contentDistribution.bands[{index}]"
                if not isinstance(band, dict):
                    errors.append(f"{label} must be an object")
                    continue
                _unknown_keys(
                    band,
                    {"id", "placement", "responsibilities", "contentIds"},
                    label,
                    errors,
                )
                band_id = band.get("id")
                if not isinstance(band_id, str) or ID_RE.fullmatch(band_id) is None:
                    errors.append(f"{label}.id is invalid")
                elif band_id in band_ids:
                    errors.append(f"{label}.id is duplicated")
                else:
                    band_ids.add(band_id)
                placement = band.get("placement")
                if placement not in {"first-viewport", "continuation", "on-demand"}:
                    errors.append(f"{label}.placement is invalid")
                else:
                    placements.add(placement)
                responsibilities = band.get("responsibilities")
                if (
                    not isinstance(responsibilities, list)
                    or not responsibilities
                    or any(
                        not isinstance(item, str) or not item.strip()
                        for item in responsibilities
                    )
                ):
                    errors.append(
                        f"{label}.responsibilities must be a non-empty string array"
                    )
                elif len(set(responsibilities)) != len(responsibilities):
                    errors.append(f"{label}.responsibilities contains duplicates")
                content_ids = band.get("contentIds")
                if (
                    not isinstance(content_ids, list)
                    or not content_ids
                    or any(
                        not isinstance(item, str) or ID_RE.fullmatch(item) is None
                        for item in content_ids
                    )
                ):
                    errors.append(f"{label}.contentIds must be a non-empty ID array")
                elif len(set(content_ids)) != len(content_ids):
                    errors.append(f"{label}.contentIds contains duplicates")
                else:
                    for content_id in content_ids:
                        content_id_bands.setdefault(content_id, set()).add(
                            band_id if isinstance(band_id, str) else label
                        )
            if strategy == "progressive-scroll" and not {
                "first-viewport",
                "continuation",
            }.issubset(placements):
                errors.append(
                    "visualDirection.contentDistribution progressive-scroll requires first-viewport and continuation bands"
                )
            shared_content_ids = content_distribution.get("sharedContentIds")
            if not isinstance(shared_content_ids, list) or any(
                not isinstance(item, str) or ID_RE.fullmatch(item) is None
                for item in shared_content_ids
            ):
                errors.append(
                    "visualDirection.contentDistribution.sharedContentIds must be an ID array"
                )
                shared_content_ids = []
            elif len(set(shared_content_ids)) != len(shared_content_ids):
                errors.append(
                    "visualDirection.contentDistribution.sharedContentIds contains duplicates"
                )
            shared_set = set(shared_content_ids)
            for content_id, owning_bands in content_id_bands.items():
                if len(owning_bands) > 1 and content_id not in shared_set:
                    errors.append(
                        "visualDirection.contentDistribution content ID "
                        f"{content_id} appears in multiple bands without sharedContentIds"
                    )
            for content_id in shared_set:
                if len(content_id_bands.get(content_id, set())) < 2:
                    errors.append(
                        "visualDirection.contentDistribution shared content ID "
                        f"{content_id} must appear in at least two bands"
                    )
            reachable = content_distribution.get("mustRemainReachable")
            if (
                not isinstance(reachable, list)
                or not reachable
                or any(not isinstance(item, str) or not item.strip() for item in reachable)
            ):
                errors.append(
                    "visualDirection.contentDistribution.mustRemainReachable must be a non-empty string array"
                )
            elif len(set(reachable)) != len(reachable):
                errors.append(
                    "visualDirection.contentDistribution.mustRemainReachable contains duplicates"
                )
    return errors


def validate_operational_metadata_policy(
    policy: Any,
    surface_ids: set[str],
    output_contexts: set[tuple[str, str]],
) -> list[str]:
    errors: list[str] = []
    if policy is None:
        return errors
    if not isinstance(policy, dict):
        return ["contract.operationalMetadataPolicy must be an object"]
    _unknown_keys(
        policy,
        {"defaultVisibility", "requiredClaims"},
        "contract.operationalMetadataPolicy",
        errors,
    )
    if policy.get("defaultVisibility") != OPERATIONAL_METADATA_DEFAULT_VISIBILITY:
        errors.append(
            "contract.operationalMetadataPolicy.defaultVisibility must be "
            f"{OPERATIONAL_METADATA_DEFAULT_VISIBILITY!r}"
        )
    claims = policy.get("requiredClaims")
    if not isinstance(claims, list):
        errors.append(
            "contract.operationalMetadataPolicy.requiredClaims must be an array"
        )
        return errors
    seen_claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        label = f"contract.operationalMetadataPolicy.requiredClaims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            claim,
            {"id", "surfaceId", "states", "meaning", "authority", "sourceRef"},
            label,
            errors,
        )
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or ID_RE.fullmatch(claim_id) is None:
            errors.append(f"{label}.id is invalid")
        elif claim_id in seen_claim_ids:
            errors.append(f"duplicate operational metadata claim ID {claim_id!r}")
        else:
            seen_claim_ids.add(claim_id)
        surface_id = claim.get("surfaceId")
        if not isinstance(surface_id, str) or ID_RE.fullmatch(surface_id) is None:
            errors.append(f"{label}.surfaceId is invalid")
        elif surface_id not in surface_ids:
            errors.append(f"{label}.surfaceId references an unknown surface")
        states = claim.get("states")
        if (
            not isinstance(states, list)
            or not states
            or any(not isinstance(state, str) or not state.strip() for state in states)
        ):
            errors.append(f"{label}.states must be a non-empty array of state IDs")
        else:
            if len(set(states)) != len(states):
                errors.append(f"{label}.states contains duplicates")
            if isinstance(surface_id, str) and ID_RE.fullmatch(surface_id) is not None:
                for state in states:
                    if (surface_id, state) not in output_contexts:
                        errors.append(
                            f"{label}.states references uncovered context "
                            f"{surface_id!r}/{state!r}"
                        )
        for field in ("meaning", "sourceRef"):
            value = claim.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}.{field} must be non-empty")
        if claim.get("authority") not in OPERATIONAL_METADATA_AUTHORITIES:
            errors.append(f"{label}.authority is invalid")
    return errors


def _validate_non_empty_string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[str]:
    if (
        not isinstance(value, list)
        or (not allow_empty and not value)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        qualifier = "an array" if allow_empty else "a non-empty array"
        errors.append(f"{label} must be {qualifier} of non-empty strings")
        return []
    if len(set(value)) != len(value):
        errors.append(f"{label} contains duplicates")
    return list(value)


def validate_v3_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        contract,
        {
            "schemaVersion",
            "contractId",
            "workflowProfile",
            "structure",
            "productIntent",
            "productModel",
            "capabilityRequirements",
            "operationalMetadataPolicy",
            "visualArtifactPolicy",
            "visualDirectionPolicy",
            "checkpointMode",
            "authority",
            "surfaces",
            "edges",
            "outputs",
            "implementationTargets",
            "renderBudget",
        },
        "contract",
        errors,
    )
    if contract.get("workflowProfile", "standard") != "full":
        errors.append(
            "schemaVersion 3 durable runtime currently requires workflowProfile full; use schemaVersion 2 for standard"
        )

    # Reuse the stable v2 validation for shared lifecycle fields by projecting
    # only the compatible shape. V3-specific evidence and ownership semantics
    # are checked below without changing v1/v2 behavior.
    projection = json.loads(json.dumps(contract))
    projection["schemaVersion"] = PREVIOUS_SCHEMA_VERSION
    for field in ("structure", "productModel", "capabilityRequirements", "renderBudget"):
        projection.pop(field, None)
    projection["implementationTargets"] = [
        item.get("path") if isinstance(item, dict) else item
        for item in contract.get("implementationTargets", [])
    ]
    projection["surfaces"] = [
        {
            key: value
            for key, value in item.items()
            if key in {"id", "kind", "route", "userJob"}
        }
        if isinstance(item, dict)
        else item
        for item in contract.get("surfaces", [])
    ]
    projection["outputs"] = [
        {
            **{
                key: value
                for key, value in item.items()
                if key
                in {
                    "id",
                    "surfaceId",
                    "state",
                    "viewport",
                    "scrollPosition",
                    "approvalRequired",
                    "dependsOn",
                    "promotionRequired",
                    "promotionTarget",
                    "evidenceEquivalentTo",
                    "equivalenceJustification",
                }
            },
            "required": item.get("designEvidenceRequired"),
        }
        if isinstance(item, dict)
        else item
        for item in contract.get("outputs", [])
    ]
    errors.extend(validate_contract(projection))
    if contract.get("workflowProfile", "standard") == "full":
        for field in (
            "operationalMetadataPolicy",
            "productModel",
            "structure",
            "capabilityRequirements",
            "implementationTargets",
        ):
            if field not in contract:
                errors.append(f"contract.{field} is required for schemaVersion 3 full workflows")

    structure = contract.get("structure")
    if not isinstance(structure, dict):
        errors.append("contract.structure must be an object")
    else:
        _unknown_keys(structure, {"id", "path", "sha256"}, "contract.structure", errors)
        structure_id = structure.get("id")
        if not isinstance(structure_id, str) or ID_RE.fullmatch(structure_id) is None:
            errors.append("contract.structure.id is invalid")
        structure_path_value = structure.get("path")
        if structure_path_value != "structure.json":
            errors.append("contract.structure.path must be structure.json")
        structure_digest = structure.get("sha256")
        if (
            not isinstance(structure_digest, str)
            or HASH_RE.fullmatch(structure_digest) is None
        ):
            errors.append("contract.structure.sha256 is invalid")

    product_model = contract.get("productModel")
    object_ids: set[str] = set()
    object_parents: dict[str, str | None] = {}
    if not isinstance(product_model, dict):
        errors.append("contract.productModel must be an object")
    else:
        _unknown_keys(
            product_model,
            {"rootObjectId", "objects", "relations"},
            "contract.productModel",
            errors,
        )
        objects = product_model.get("objects")
        if not isinstance(objects, list) or not objects:
            errors.append("contract.productModel.objects must be a non-empty array")
        else:
            for index, item in enumerate(objects):
                label = f"contract.productModel.objects[{index}]"
                if not isinstance(item, dict):
                    errors.append(f"{label} must be an object")
                    continue
                _unknown_keys(
                    item,
                    {"id", "role", "parentId", "evidenceForObjectIds"},
                    label,
                    errors,
                )
                object_id = item.get("id")
                if not isinstance(object_id, str) or ID_RE.fullmatch(object_id) is None:
                    errors.append(f"{label}.id is invalid")
                    continue
                if object_id in object_ids:
                    errors.append(f"duplicate product object ID {object_id!r}")
                object_ids.add(object_id)
                if item.get("role") not in PRODUCT_OBJECT_ROLES:
                    errors.append(f"{label}.role is invalid")
                parent_id = item.get("parentId")
                if parent_id is not None and (
                    not isinstance(parent_id, str) or ID_RE.fullmatch(parent_id) is None
                ):
                    errors.append(f"{label}.parentId is invalid")
                object_parents[object_id] = parent_id
                _validate_non_empty_string_list(
                    item.get("evidenceForObjectIds"),
                    f"{label}.evidenceForObjectIds",
                    errors,
                    allow_empty=True,
                )
        root_object_id = product_model.get("rootObjectId")
        if root_object_id not in object_ids:
            errors.append("contract.productModel.rootObjectId references an unknown object")
        elif isinstance(objects, list):
            root_object = next(
                (
                    item
                    for item in objects
                    if isinstance(item, dict) and item.get("id") == root_object_id
                ),
                None,
            )
            if not isinstance(root_object, dict) or root_object.get("role") != "root":
                errors.append("contract.productModel.rootObjectId must reference role root")
        for object_id, parent_id in object_parents.items():
            if parent_id is not None and parent_id not in object_ids:
                errors.append(
                    f"product object {object_id!r} parentId references an unknown object"
                )
            if parent_id == object_id:
                errors.append(f"product object {object_id!r} cannot parent itself")
        for item in objects if isinstance(objects, list) else []:
            if not isinstance(item, dict):
                continue
            for referenced in item.get("evidenceForObjectIds", []):
                if referenced not in object_ids:
                    errors.append(
                        f"product object {item.get('id')!r} evidenceForObjectIds references unknown object {referenced!r}"
                    )
        relations = product_model.get("relations")
        if not isinstance(relations, list):
            errors.append("contract.productModel.relations must be an array")
        else:
            seen_relations: set[tuple[str, str, str]] = set()
            for index, relation in enumerate(relations):
                label = f"contract.productModel.relations[{index}]"
                if not isinstance(relation, dict):
                    errors.append(f"{label} must be an object")
                    continue
                _unknown_keys(
                    relation,
                    {"id", "fromObjectId", "toObjectId", "kind"},
                    label,
                    errors,
                )
                relation_id = relation.get("id")
                if not isinstance(relation_id, str) or ID_RE.fullmatch(relation_id) is None:
                    errors.append(f"{label}.id is invalid")
                source = relation.get("fromObjectId")
                target = relation.get("toObjectId")
                kind = relation.get("kind")
                if source not in object_ids:
                    errors.append(f"{label}.fromObjectId references an unknown object")
                if target not in object_ids:
                    errors.append(f"{label}.toObjectId references an unknown object")
                if kind not in {
                    "contains",
                    "supports",
                    "governs",
                    "evidence-for",
                    "implements",
                    "depends-on",
                    "relates-to",
                }:
                    errors.append(f"{label}.kind is invalid")
                elif isinstance(source, str) and isinstance(target, str):
                    identity = (source, target, kind)
                    if identity in seen_relations:
                        errors.append(f"{label} duplicates a product relation")
                    seen_relations.add(identity)

    surfaces = contract.get("surfaces", [])
    object_roles = {
        item.get("id"): item.get("role")
        for item in contract.get("productModel", {}).get("objects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    surface_ids = {
        item.get("id")
        for item in surfaces
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for index, surface in enumerate(surfaces if isinstance(surfaces, list) else []):
        label = f"contract.surfaces[{index}]"
        if not isinstance(surface, dict):
            continue
        _unknown_keys(
            surface,
            {
                "id",
                "kind",
                "route",
                "userJob",
                "primaryObjectId",
                "shellIds",
                "referenceBindingIds",
            },
            label,
            errors,
        )
        if surface.get("primaryObjectId") not in object_ids:
            errors.append(f"{label}.primaryObjectId references an unknown product object")
        elif object_roles.get(surface.get("primaryObjectId")) == "implementation-detail":
            errors.append(
                f"{label}.primaryObjectId cannot reference an implementation-detail object"
            )
        for field in ("shellIds", "referenceBindingIds"):
            _validate_non_empty_string_list(
                surface.get(field),
                f"{label}.{field}",
                errors,
                allow_empty=True,
            )

    capability_requirements = contract.get("capabilityRequirements")
    capability_ids: set[str] = set()
    required_capability_surfaces: set[str] = set()
    required_capability_name_counts: dict[str, int] = {}
    if not isinstance(capability_requirements, list) or not capability_requirements:
        errors.append("contract.capabilityRequirements must be a non-empty array")
    else:
        for index, requirement in enumerate(capability_requirements):
            label = f"contract.capabilityRequirements[{index}]"
            if not isinstance(requirement, dict):
                errors.append(f"{label} must be an object")
                continue
            _unknown_keys(
                requirement,
                {
                    "id",
                    "capability",
                    "complexity",
                    "ownerObjectId",
                    "surfaceIds",
                    "required",
                    "constraints",
                },
                label,
                errors,
            )
            requirement_id = requirement.get("id")
            if (
                not isinstance(requirement_id, str)
                or ID_RE.fullmatch(requirement_id) is None
            ):
                errors.append(f"{label}.id is invalid")
            elif requirement_id in capability_ids:
                errors.append(f"duplicate capability requirement ID {requirement_id!r}")
            else:
                capability_ids.add(requirement_id)
            capability = requirement.get("capability")
            if not isinstance(capability, str) or not capability.strip():
                errors.append(f"{label}.capability must be non-empty")
            if requirement.get("complexity") not in CAPABILITY_COMPLEXITIES:
                errors.append(f"{label}.complexity is invalid")
            if requirement.get("ownerObjectId") not in object_ids:
                errors.append(f"{label}.ownerObjectId references an unknown product object")
            covered_surfaces = _validate_non_empty_string_list(
                requirement.get("surfaceIds"),
                f"{label}.surfaceIds",
                errors,
            )
            for surface_id in covered_surfaces:
                if surface_id not in surface_ids:
                    errors.append(f"{label}.surfaceIds references unknown surface {surface_id!r}")
            if not isinstance(requirement.get("required"), bool):
                errors.append(f"{label}.required must be a boolean")
            elif requirement["required"]:
                required_capability_surfaces.update(covered_surfaces)
                if isinstance(capability, str) and capability.strip():
                    required_capability_name_counts[capability] = (
                        required_capability_name_counts.get(capability, 0) + 1
                    )
            _validate_non_empty_string_list(
                requirement.get("constraints"),
                f"{label}.constraints",
                errors,
            )

    protected_capabilities = contract.get("productIntent", {}).get(
        "protectedCapabilities", []
    )
    if isinstance(protected_capabilities, list):
        for protected_capability in protected_capabilities:
            if (
                isinstance(protected_capability, str)
                and required_capability_name_counts.get(protected_capability) != 1
            ):
                errors.append(
                    "contract.productIntent.protectedCapabilities entry must exact-match "
                    "exactly one required capabilityRequirement.capability: "
                    f"{protected_capability!r}"
                )

    implementation_targets = contract.get("implementationTargets")
    target_paths: set[str] = set()
    if not isinstance(implementation_targets, list):
        errors.append("contract.implementationTargets must be an array")
    else:
        for index, target in enumerate(implementation_targets):
            label = f"contract.implementationTargets[{index}]"
            if not isinstance(target, dict):
                errors.append(f"{label} must be an object")
                continue
            _unknown_keys(target, {"path", "surfaceIds", "sharedOwner"}, label, errors)
            path = target.get("path")
            if not isinstance(path, str):
                errors.append(f"{label}.path must be a string")
            else:
                try:
                    _implementation_relative_path(path, f"{label}.path")
                except StateError as exc:
                    errors.append(str(exc))
                if path in target_paths:
                    errors.append(f"duplicate implementation target path {path!r}")
                target_paths.add(path)
            target_surfaces = _validate_non_empty_string_list(
                target.get("surfaceIds"),
                f"{label}.surfaceIds",
                errors,
            )
            for surface_id in target_surfaces:
                if surface_id not in surface_ids:
                    errors.append(f"{label}.surfaceIds references unknown surface {surface_id!r}")
            if not isinstance(target.get("sharedOwner"), bool):
                errors.append(f"{label}.sharedOwner must be a boolean")

    outputs = contract.get("outputs", [])
    output_ids: set[str] = set()
    output_map: dict[str, dict[str, Any]] = {}
    runtime_surface_ids: set[str] = set()
    imagegen_output_count = 0
    for index, output in enumerate(outputs if isinstance(outputs, list) else []):
        label = f"contract.outputs[{index}]"
        if not isinstance(output, dict):
            continue
        _unknown_keys(
            output,
            {
                "id",
                "surfaceId",
                "state",
                "viewport",
                "scrollPosition",
                "designEvidenceRequired",
                "runtimeEvidenceRequired",
                "artifactKind",
                "anchorOutputId",
                "approvalRequired",
                "dependsOn",
                "promotionRequired",
                "promotionTarget",
                "evidenceEquivalentTo",
                "equivalenceJustification",
            },
            label,
            errors,
        )
        output_id = output.get("id")
        if isinstance(output_id, str):
            output_ids.add(output_id)
            output_map[output_id] = output
        design_required = output.get("designEvidenceRequired")
        runtime_required = output.get("runtimeEvidenceRequired")
        if not isinstance(design_required, bool):
            errors.append(f"{label}.designEvidenceRequired must be a boolean")
        if not isinstance(runtime_required, bool):
            errors.append(f"{label}.runtimeEvidenceRequired must be a boolean")
        if design_required is False and runtime_required is False:
            errors.append(f"{label} must require design or runtime evidence")
        artifact_kind = output.get("artifactKind")
        if artifact_kind not in ARTIFACT_KINDS:
            errors.append(f"{label}.artifactKind is invalid")
        if design_required is False and artifact_kind != "none":
            errors.append(f"{label}.artifactKind must be none without design evidence")
        if design_required is True and artifact_kind == "none":
            errors.append(f"{label}.artifactKind cannot be none when design evidence is required")
        if design_required is False and output.get("approvalRequired"):
            errors.append(f"{label}.approvalRequired requires design evidence")
        if design_required is False and output.get("promotionRequired"):
            errors.append(f"{label}.promotionRequired requires design evidence")
        if artifact_kind == "imagegen" and design_required is True:
            imagegen_output_count += 1
        if runtime_required is True and isinstance(output.get("surfaceId"), str):
            runtime_surface_ids.add(output["surfaceId"])
        if (
            runtime_required is True
            and design_required is False
            and contract.get("visualDirectionPolicy") != "required"
        ):
            errors.append(f"{label} direction-only runtime evidence requires visual direction")
    for output_id, output in output_map.items():
        anchor_id = output.get("anchorOutputId")
        if anchor_id is not None:
            if anchor_id not in output_ids:
                errors.append(f"output {output_id!r} anchorOutputId references unknown output")
            elif anchor_id == output_id:
                errors.append(f"output {output_id!r} cannot anchor itself")
            elif anchor_id not in output.get("dependsOn", []):
                errors.append(
                    f"output {output_id!r} anchorOutputId must also appear in dependsOn"
                )
            elif not _design_evidence_required(output_map[anchor_id]):
                errors.append(f"output {output_id!r} anchor must require design evidence")
    for surface_id in sorted(required_capability_surfaces - runtime_surface_ids):
        errors.append(
            f"required capability surface {surface_id!r} lacks runtimeEvidenceRequired output"
        )

    render_budget = contract.get("renderBudget")
    if imagegen_output_count and not isinstance(render_budget, dict):
        errors.append("contract.renderBudget is required for imagegen outputs")
    if render_budget is not None:
        if not isinstance(render_budget, dict):
            errors.append("contract.renderBudget must be an object")
        else:
            _unknown_keys(
                render_budget,
                {"maxCallsTotal", "maxAttemptsPerOutput", "maxConceptResets"},
                "contract.renderBudget",
                errors,
            )
            for field in ("maxCallsTotal", "maxAttemptsPerOutput"):
                value = render_budget.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    errors.append(f"contract.renderBudget.{field} must be a positive integer")
            resets = render_budget.get("maxConceptResets")
            if not isinstance(resets, int) or isinstance(resets, bool) or resets < 0:
                errors.append(
                    "contract.renderBudget.maxConceptResets must be a non-negative integer"
                )
            calls = render_budget.get("maxCallsTotal")
            if isinstance(calls, int) and not isinstance(calls, bool) and calls < imagegen_output_count:
                errors.append(
                    "contract.renderBudget.maxCallsTotal cannot cover every imagegen output"
                )
            if isinstance(calls, int) and calls > 100:
                errors.append("contract.renderBudget.maxCallsTotal must be at most 100")
            attempts = render_budget.get("maxAttemptsPerOutput")
            if isinstance(attempts, int) and attempts > 10:
                errors.append(
                    "contract.renderBudget.maxAttemptsPerOutput must be at most 10"
                )
            if isinstance(resets, int) and resets > 20:
                errors.append(
                    "contract.renderBudget.maxConceptResets must be at most 20"
                )
    if contract.get("visualArtifactPolicy") == "no-imagegen" and render_budget is not None:
        errors.append("contract.renderBudget is forbidden when imagegen is disabled")
    if contract.get("visualArtifactPolicy") == "imagegen-required":
        if not any(_design_evidence_required(output) for output in output_map.values()):
            errors.append(
                "imagegen-required schemaVersion 3 contract needs a design-required output"
            )
        for output_id, output in output_map.items():
            if not _design_evidence_required(output):
                continue
            if output.get("artifactKind") != "imagegen":
                errors.append(
                    f"output {output_id!r} artifactKind must be imagegen when imagegen is required"
                )
            if output.get("approvalRequired") is not True:
                errors.append(
                    f"output {output_id!r} approvalRequired must be true when imagegen is required"
                )
    return errors


def validate_v3_structure_contract(structure: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        structure,
        {
            "schemaVersion",
            "contractId",
            "surfaces",
            "scenarios",
            "shells",
            "objectBindings",
            "referenceBindings",
        },
        "structure",
        errors,
    )
    if structure.get("schemaVersion") != 3:
        errors.append("structure.schemaVersion must be 3")
    contract_id = structure.get("contractId")
    if not isinstance(contract_id, str) or ID_RE.fullmatch(contract_id) is None:
        errors.append("structure.contractId is invalid")

    surface_ids: set[str] = set()
    scenario_refs: dict[str, list[str]] = {}
    surfaces = structure.get("surfaces")
    if not isinstance(surfaces, list) or not surfaces:
        errors.append("structure.surfaces must be a non-empty array")
        surfaces = []
    for index, surface in enumerate(surfaces):
        label = f"structure.surfaces[{index}]"
        if not isinstance(surface, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(surface, {"id", "route", "scenarioIds", "domainIds"}, label, errors)
        surface_id = surface.get("id")
        if not isinstance(surface_id, str) or ID_RE.fullmatch(surface_id) is None:
            errors.append(f"{label}.id is invalid")
            continue
        if surface_id in surface_ids:
            errors.append(f"duplicate structure surface ID {surface_id!r}")
        surface_ids.add(surface_id)
        route = surface.get("route")
        if route is not None and (not isinstance(route, str) or not route.strip()):
            errors.append(f"{label}.route must be null or non-empty")
        scenario_refs[surface_id] = _validate_non_empty_string_list(
            surface.get("scenarioIds"),
            f"{label}.scenarioIds",
            errors,
            allow_empty=True,
        )
        _validate_non_empty_string_list(
            surface.get("domainIds"),
            f"{label}.domainIds",
            errors,
            allow_empty=True,
        )

    scenario_ids: set[str] = set()
    scenarios = structure.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("structure.scenarios must be a non-empty array")
        scenarios = []
    for index, scenario in enumerate(scenarios):
        label = f"structure.scenarios[{index}]"
        if not isinstance(scenario, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            scenario,
            {
                "id",
                "job",
                "objectIds",
                "entrySurfaceId",
                "completionSurfaceId",
                "recoverySurfaceIds",
            },
            label,
            errors,
        )
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or ID_RE.fullmatch(scenario_id) is None:
            errors.append(f"{label}.id is invalid")
        elif scenario_id in scenario_ids:
            errors.append(f"duplicate structure scenario ID {scenario_id!r}")
        else:
            scenario_ids.add(scenario_id)
        job = scenario.get("job")
        if not isinstance(job, str) or not job.strip():
            errors.append(f"{label}.job must be non-empty")
        _validate_non_empty_string_list(
            scenario.get("objectIds"),
            f"{label}.objectIds",
            errors,
        )
        for field in ("entrySurfaceId", "completionSurfaceId"):
            if scenario.get(field) not in surface_ids:
                errors.append(f"{label}.{field} references an unknown structure surface")
        for recovery in _validate_non_empty_string_list(
            scenario.get("recoverySurfaceIds"),
            f"{label}.recoverySurfaceIds",
            errors,
            allow_empty=True,
        ):
            if recovery not in surface_ids:
                errors.append(f"{label}.recoverySurfaceIds references unknown surface {recovery!r}")
    for surface_id, references in scenario_refs.items():
        for scenario_id in references:
            if scenario_id not in scenario_ids:
                errors.append(
                    f"structure surface {surface_id!r} references unknown scenario {scenario_id!r}"
                )

    shell_ids: set[str] = set()
    shells = structure.get("shells")
    if not isinstance(shells, list):
        errors.append("structure.shells must be an array")
        shells = []
    for index, shell in enumerate(shells):
        label = f"structure.shells[{index}]"
        if not isinstance(shell, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(shell, {"id", "parentShellId", "slots", "invariants"}, label, errors)
        shell_id = shell.get("id")
        if not isinstance(shell_id, str) or ID_RE.fullmatch(shell_id) is None:
            errors.append(f"{label}.id is invalid")
        elif shell_id in shell_ids:
            errors.append(f"duplicate structure shell ID {shell_id!r}")
        else:
            shell_ids.add(shell_id)
        _validate_non_empty_string_list(shell.get("slots"), f"{label}.slots", errors)
        _validate_non_empty_string_list(shell.get("invariants"), f"{label}.invariants", errors)
    for index, shell in enumerate(shells):
        if isinstance(shell, dict):
            parent = shell.get("parentShellId")
            if parent is not None and parent not in shell_ids:
                errors.append(
                    f"structure.shells[{index}].parentShellId references an unknown shell"
                )

    bindings = structure.get("objectBindings")
    if not isinstance(bindings, list):
        errors.append("structure.objectBindings must be an array")
        bindings = []
    for index, binding in enumerate(bindings):
        label = f"structure.objectBindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            binding,
            {
                "id",
                "surfaceId",
                "primaryObjectId",
                "supportingObjectIds",
                "forbiddenDominantObjectIds",
            },
            label,
            errors,
        )
        binding_id = binding.get("id")
        if not isinstance(binding_id, str) or ID_RE.fullmatch(binding_id) is None:
            errors.append(f"{label}.id is invalid")
        if binding.get("surfaceId") not in surface_ids:
            errors.append(f"{label}.surfaceId references an unknown structure surface")
        primary = binding.get("primaryObjectId")
        if not isinstance(primary, str) or ID_RE.fullmatch(primary) is None:
            errors.append(f"{label}.primaryObjectId is invalid")
        for field in ("supportingObjectIds", "forbiddenDominantObjectIds"):
            _validate_non_empty_string_list(
                binding.get(field),
                f"{label}.{field}",
                errors,
                allow_empty=True,
            )

    references = structure.get("referenceBindings")
    if not isinstance(references, list):
        errors.append("structure.referenceBindings must be an array")
        references = []
    reference_ids: set[str] = set()
    for index, binding in enumerate(references):
        label = f"structure.referenceBindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            binding,
            {
                "id",
                "sourceRef",
                "sourceSha256",
                "roles",
                "surfaceIds",
                "aspects",
                "constraints",
                "mustNotInfluence",
            },
            label,
            errors,
        )
        binding_id = binding.get("id")
        if not isinstance(binding_id, str) or ID_RE.fullmatch(binding_id) is None:
            errors.append(f"{label}.id is invalid")
        elif binding_id in reference_ids:
            errors.append(f"duplicate reference binding ID {binding_id!r}")
        else:
            reference_ids.add(binding_id)
        source_ref = binding.get("sourceRef")
        if not isinstance(source_ref, str) or not source_ref.strip():
            errors.append(f"{label}.sourceRef must be non-empty")
        source_sha = binding.get("sourceSha256")
        if source_sha is not None and (
            not isinstance(source_sha, str) or HASH_RE.fullmatch(source_sha) is None
        ):
            errors.append(f"{label}.sourceSha256 is invalid")
        roles = _validate_non_empty_string_list(binding.get("roles"), f"{label}.roles", errors)
        for role in roles:
            if role not in {
                "functional-reference",
                "style-reference",
                "visual-anchor",
                "edit-target",
                "constraint",
            }:
                errors.append(f"{label}.roles contains invalid role {role!r}")
        for surface_id in _validate_non_empty_string_list(
            binding.get("surfaceIds"), f"{label}.surfaceIds", errors
        ):
            if surface_id not in surface_ids:
                errors.append(f"{label}.surfaceIds references unknown surface {surface_id!r}")
        _validate_non_empty_string_list(binding.get("aspects"), f"{label}.aspects", errors)
        for field in ("constraints", "mustNotInfluence"):
            _validate_non_empty_string_list(
                binding.get(field), f"{label}.{field}", errors, allow_empty=True
            )
    return errors


def validate_v3_bundle_semantics(
    contract: dict[str, Any],
    structure: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    structure_ref = contract.get("structure")
    if not isinstance(structure_ref, dict):
        return ["contract.structure must be an object"]
    structure_id = structure.get("contractId", structure.get("id"))
    if structure_id != structure_ref.get("id"):
        errors.append("structure ID does not match contract.structure.id")
    actual_sha = structure_sha256(structure)
    if actual_sha != structure_ref.get("sha256"):
        errors.append("structure SHA-256 does not match contract.structure.sha256")

    contract_surface_ids = {
        item.get("id")
        for item in contract.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    contract_object_ids = {
        item.get("id")
        for item in contract.get("productModel", {}).get("objects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    object_map = {
        item["id"]: item
        for item in contract.get("productModel", {}).get("objects", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    root_object_id = contract.get("productModel", {}).get("rootObjectId")
    root_role_ids = {
        object_id
        for object_id, item in object_map.items()
        if item.get("role") == "root"
    }
    if root_role_ids != {root_object_id}:
        errors.append("productModel must contain exactly one root-role object")
    elif object_map.get(root_object_id, {}).get("parentId") is not None:
        errors.append("productModel root object must not have a parent")
    for object_id, item in object_map.items():
        if (
            item.get("role") == "downstream-evidence"
            and not item.get("evidenceForObjectIds")
        ):
            errors.append(
                f"downstream evidence object {object_id} requires an evidence target"
            )
    object_visiting: set[str] = set()
    object_visited: set[str] = set()

    def visit_object(object_id: str) -> None:
        if object_id in object_visited:
            return
        if object_id in object_visiting:
            errors.append(f"product object parent cycle includes {object_id}")
            return
        object_visiting.add(object_id)
        parent_id = object_map.get(object_id, {}).get("parentId")
        if isinstance(parent_id, str) and parent_id in object_map:
            visit_object(parent_id)
        object_visiting.remove(object_id)
        object_visited.add(object_id)

    for object_id in object_map:
        visit_object(object_id)
    relation_ids = [
        item.get("id")
        for item in contract.get("productModel", {}).get("relations", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    if len(set(relation_ids)) != len(relation_ids):
        errors.append("duplicate product relation IDs")
    structure_errors = validate_v3_structure_contract(structure)
    errors.extend(structure_errors)
    structure_surfaces = structure.get("surfaces")
    contract_surface_map = {
        item["id"]: item
        for item in contract.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if isinstance(structure_surfaces, list):
        structure_surface_ids = {
            item.get("id")
            for item in structure_surfaces
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        }
        if structure_surface_ids != contract_surface_ids:
            errors.append("structure surfaces do not match coverage contract surfaces")
        for index, surface in enumerate(structure_surfaces):
            if not isinstance(surface, dict):
                continue
            contract_surface = contract_surface_map.get(surface.get("id"))
            if isinstance(contract_surface, dict):
                if surface.get("route") != contract_surface.get("route"):
                    errors.append(
                        f"structure.surfaces[{index}].route differs from coverage surface"
                    )

    for index, scenario in enumerate(structure.get("scenarios", [])):
        if not isinstance(scenario, dict):
            continue
        for object_id in scenario.get("objectIds", []):
            if object_id not in contract_object_ids:
                errors.append(
                    f"structure.scenarios[{index}].objectIds references unknown product object {object_id!r}"
                )

    scenario_map = {
        item["id"]: item
        for item in structure.get("scenarios", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    structure_surface_map = {
        item["id"]: item
        for item in structure.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    domain_ids = {
        domain_id
        for surface in structure_surface_map.values()
        for domain_id in surface.get("domainIds", [])
    }
    missing_domains = set(
        contract.get("productIntent", {}).get("requiredDomains", [])
    ) - domain_ids
    if missing_domains:
        errors.append(
            "required domains lack structure surface coverage: "
            + ", ".join(sorted(missing_domains))
        )
    for scenario_id, scenario in scenario_map.items():
        involved = {
            scenario.get("entrySurfaceId"),
            scenario.get("completionSurfaceId"),
            *scenario.get("recoverySurfaceIds", []),
        }
        for surface_id in involved:
            if (
                surface_id in structure_surface_map
                and scenario_id
                not in structure_surface_map[surface_id].get("scenarioIds", [])
            ):
                errors.append(
                    f"scenario {scenario_id} is missing from surface {surface_id} scenarioIds"
                )
        for field in ("entrySurfaceId", "completionSurfaceId"):
            surface_id = scenario.get(field)
            if surface_id not in contract_surface_ids:
                errors.append(
                    f"structure.scenarios[{index}].{field} references an unknown surface"
                )
        for surface_id in scenario.get("recoverySurfaceIds", []):
            if surface_id not in contract_surface_ids:
                errors.append(
                    f"structure.scenarios[{index}].recoverySurfaceIds references unknown surface {surface_id!r}"
                )

    for index, binding in enumerate(structure.get("objectBindings", [])):
        if not isinstance(binding, dict):
            continue
        object_values: list[Any] = [binding.get("primaryObjectId")]
        object_values.extend(binding.get("supportingObjectIds", []))
        object_values.extend(binding.get("forbiddenDominantObjectIds", []))
        surface_values: list[Any] = [binding.get("surfaceId")]
        for object_id in object_values:
            if object_id not in contract_object_ids:
                errors.append(
                    f"structure.objectBindings[{index}] references unknown product object {object_id!r}"
                )
        if binding.get("primaryObjectId") in binding.get(
            "forbiddenDominantObjectIds", []
        ):
            errors.append(
                f"structure.objectBindings[{index}] forbids its own primary object"
            )
        for surface_id in surface_values:
            if surface_id not in contract_surface_ids:
                errors.append(
                    f"structure.objectBindings[{index}] references unknown surface {surface_id!r}"
                )
            elif isinstance(surface_id, str):
                coverage_surface = contract_surface_map.get(surface_id)
                if (
                    isinstance(coverage_surface, dict)
                    and binding.get("primaryObjectId")
                    != coverage_surface.get("primaryObjectId")
                ):
                    errors.append(
                        f"structure.objectBindings[{index}].primaryObjectId differs from coverage surface"
                    )
    shell_ids = {
        item.get("id")
        for item in structure.get("shells", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    shell_map = {
        item["id"]: item
        for item in structure.get("shells", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    shell_visiting: set[str] = set()
    shell_visited: set[str] = set()

    def visit_shell(shell_id: str) -> None:
        if shell_id in shell_visited:
            return
        if shell_id in shell_visiting:
            errors.append(f"shell parent cycle includes {shell_id}")
            return
        shell_visiting.add(shell_id)
        parent_id = shell_map.get(shell_id, {}).get("parentShellId")
        if isinstance(parent_id, str) and parent_id in shell_map:
            visit_shell(parent_id)
        shell_visiting.remove(shell_id)
        shell_visited.add(shell_id)

    for shell_id in shell_map:
        visit_shell(shell_id)
    reference_ids = {
        item.get("id")
        for item in structure.get("referenceBindings", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    reference_map = {
        item["id"]: item
        for item in structure.get("referenceBindings", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for reference_id, binding in reference_map.items():
        overlap = set(binding.get("aspects", [])) & set(
            binding.get("mustNotInfluence", [])
        )
        if overlap:
            errors.append(
                f"reference binding {reference_id} both applies to and forbids: "
                + ", ".join(sorted(overlap))
            )
    for surface_id, surface in contract_surface_map.items():
        for shell_id in surface.get("shellIds", []):
            if shell_id not in shell_ids:
                errors.append(
                    f"coverage surface {surface_id!r} shellIds references unknown shell {shell_id!r}"
                )
        for reference_id in surface.get("referenceBindingIds", []):
            if reference_id not in reference_ids:
                errors.append(
                    f"coverage surface {surface_id!r} referenceBindingIds references unknown binding {reference_id!r}"
                )
            elif surface_id not in reference_map[reference_id].get("surfaceIds", []):
                errors.append(
                    f"coverage surface {surface_id!r} is outside reference binding {reference_id!r} scope"
                )

    bound_object_ids = {
        object_id
        for scenario in structure.get("scenarios", [])
        if isinstance(scenario, dict)
        for object_id in scenario.get("objectIds", [])
        if isinstance(object_id, str)
    }
    for binding in structure.get("objectBindings", []):
        if not isinstance(binding, dict):
            continue
        primary = binding.get("primaryObjectId")
        if isinstance(primary, str):
            bound_object_ids.add(primary)
        bound_object_ids.update(binding.get("supportingObjectIds", []))
    required_object_ids = {
        object_id
        for object_id, item in object_map.items()
        if item.get("role") != "implementation-detail"
    }
    missing_objects = required_object_ids - bound_object_ids
    if missing_objects:
        errors.append(
            "product objects lack scenario/surface binding: "
            + ", ".join(sorted(missing_objects))
        )
    return errors


def _load_v3_structure(
    contract: dict[str, Any],
    structure_file: str | Path | None,
) -> dict[str, Any]:
    if structure_file is None:
        raise StateError("SchemaVersion 3 init requires --structure")
    structure = load_json(Path(structure_file).expanduser().resolve(), "structure contract")
    errors = validate_v3_bundle_semantics(contract, structure)
    if errors:
        raise StateError("Invalid v3 structure binding: " + "; ".join(errors))
    return structure


def _verify_v3_structure(session_dir: Path, state: dict[str, Any]) -> str:
    if not _is_v3_state(state):
        return ""
    structure_path = session_dir / "structure.json"
    structure = load_json(structure_path, "stored structure contract")
    errors = validate_v3_bundle_semantics(state["contract"], structure)
    if errors:
        raise StateError("Invalid stored v3 structure: " + "; ".join(errors))
    return structure_sha256(structure)


def validate_contract(
    contract: dict[str, Any],
    *,
    allow_legacy_schema_version: bool = False,
    allow_legacy_missing_visual_direction_policy: bool = False,
) -> list[str]:
    if contract.get("schemaVersion") == SCHEMA_VERSION:
        return validate_v3_contract(contract)
    errors: list[str] = []
    _unknown_keys(
        contract,
        {
            "schemaVersion",
            "contractId",
            "workflowProfile",
            "implementationTargets",
            "productIntent",
            "operationalMetadataPolicy",
            "visualArtifactPolicy",
            "visualDirectionPolicy",
            "checkpointMode",
            "authority",
            "surfaces",
            "edges",
            "outputs",
        },
        "contract",
        errors,
    )
    contract_schema_version = contract.get("schemaVersion")
    legacy_contract = (
        allow_legacy_schema_version
        and contract_schema_version == LEGACY_SCHEMA_VERSION
    )
    if (
        contract_schema_version not in {PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION}
        and not legacy_contract
    ):
        errors.append(
            f"contract.schemaVersion must be {PREVIOUS_SCHEMA_VERSION} or {SCHEMA_VERSION}"
        )
    contract_id = contract.get("contractId")
    if not isinstance(contract_id, str) or ID_RE.fullmatch(contract_id) is None:
        errors.append("contract.contractId is invalid")
    workflow_profile = contract.get("workflowProfile", "standard")
    if not isinstance(workflow_profile, str) or workflow_profile not in WORKFLOW_PROFILES:
        errors.append("contract.workflowProfile is invalid")
    product_intent = contract.get("productIntent")
    visual_artifact_policy = contract.get("visualArtifactPolicy")
    visual_direction_policy = contract.get("visualDirectionPolicy")
    checkpoint_mode = contract.get("checkpointMode")
    if workflow_profile == "full":
        if not isinstance(product_intent, dict):
            errors.append("contract.productIntent is required for full workflows")
        if visual_artifact_policy not in VISUAL_ARTIFACT_POLICIES:
            errors.append("contract.visualArtifactPolicy is required and invalid for full workflows")
        if (
            visual_direction_policy not in VISUAL_DIRECTION_POLICIES
            and not (
                legacy_contract
                and
                allow_legacy_missing_visual_direction_policy
                and visual_direction_policy is None
            )
        ):
            errors.append(
                "contract.visualDirectionPolicy is required and invalid for full workflows"
            )
        if checkpoint_mode not in CHECKPOINT_MODES:
            errors.append("contract.checkpointMode is required and invalid for full workflows")
    else:
        if visual_artifact_policy is not None and visual_artifact_policy not in VISUAL_ARTIFACT_POLICIES:
            errors.append("contract.visualArtifactPolicy is invalid")
        if visual_direction_policy is not None and visual_direction_policy not in VISUAL_DIRECTION_POLICIES:
            errors.append("contract.visualDirectionPolicy is invalid")
        if checkpoint_mode is not None and checkpoint_mode not in CHECKPOINT_MODES:
            errors.append("contract.checkpointMode is invalid")
    if product_intent is not None:
        if not isinstance(product_intent, dict):
            errors.append("contract.productIntent must be an object")
        else:
            intent_fields = {
                "problem",
                "representativeScenarios",
                "requiredDomains",
                "protectedCapabilities",
                "antiGoals",
                "successSignals",
            }
            _unknown_keys(product_intent, intent_fields, "contract.productIntent", errors)
            problem = product_intent.get("problem")
            if not isinstance(problem, str) or not problem.strip():
                errors.append("contract.productIntent.problem must be non-empty")
            for field in sorted(intent_fields - {"problem"}):
                values = product_intent.get(field)
                minimum = 2 if field == "representativeScenarios" else 1
                if (
                    not isinstance(values, list)
                    or len(values) < minimum
                    or any(not isinstance(item, str) or not item.strip() for item in values)
                ):
                    errors.append(
                        f"contract.productIntent.{field} must contain at least {minimum} non-empty string(s)"
                    )
                elif len(set(values)) != len(values):
                    errors.append(f"contract.productIntent.{field} contains duplicates")
    if (
        workflow_profile == "full"
        and visual_artifact_policy == "imagegen-required"
        and checkpoint_mode not in {"review-each-stage", "review-before-implementation"}
    ):
        errors.append(
            "contract.checkpointMode must be review-each-stage or review-before-implementation when imagegen is required"
        )
    implementation_targets = contract.get("implementationTargets", [])
    if not isinstance(implementation_targets, list):
        errors.append("contract.implementationTargets must be an array")
    else:
        seen_targets: set[str] = set()
        for index, target in enumerate(implementation_targets):
            label = f"contract.implementationTargets[{index}]"
            if not isinstance(target, str):
                errors.append(f"{label} must be a string")
                continue
            if target in seen_targets:
                errors.append(f"{label} duplicates implementation target {target!r}")
            seen_targets.add(target)
            try:
                _implementation_relative_path(target, label)
            except StateError as exc:
                errors.append(str(exc))

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
    output_contexts: set[tuple[str, str]] = set()
    dependencies: dict[str, list[str]] = {}
    evidence_equivalences: dict[str, str] = {}
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
                    "evidenceEquivalentTo",
                    "equivalenceJustification",
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
            if (
                isinstance(output.get("surfaceId"), str)
                and isinstance(output.get("state"), str)
                and output["state"].strip()
            ):
                output_contexts.add((output["surfaceId"], output["state"]))
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
            evidence_equivalent_to = output.get("evidenceEquivalentTo")
            equivalence_justification = output.get("equivalenceJustification")
            if (evidence_equivalent_to is None) != (equivalence_justification is None):
                errors.append(
                    f"{label}.evidenceEquivalentTo and equivalenceJustification must be provided together"
                )
            elif evidence_equivalent_to is not None:
                if (
                    not isinstance(evidence_equivalent_to, str)
                    or ID_RE.fullmatch(evidence_equivalent_to) is None
                ):
                    errors.append(f"{label}.evidenceEquivalentTo is invalid")
                else:
                    evidence_equivalences[output_id] = evidence_equivalent_to
                if (
                    not isinstance(equivalence_justification, str)
                    or not equivalence_justification.strip()
                ):
                    errors.append(f"{label}.equivalenceJustification must be non-empty")
            if (
                workflow_profile == "full"
                and visual_artifact_policy == "imagegen-required"
                and output.get("required") is True
                and output.get("approvalRequired") is not True
            ):
                errors.append(
                    f"{label}.approvalRequired must be true when imagegen is required"
                )

    for output_id, depends_on in dependencies.items():
        for dependency in depends_on:
            if dependency not in output_ids:
                errors.append(f"output {output_id!r} depends on unknown output {dependency!r}")
            if dependency == output_id:
                errors.append(f"output {output_id!r} cannot depend on itself")
    for output_id, equivalent_to in evidence_equivalences.items():
        if equivalent_to not in output_ids:
            errors.append(
                f"output {output_id!r} evidenceEquivalentTo references unknown output {equivalent_to!r}"
            )
        if equivalent_to == output_id:
            errors.append(f"output {output_id!r} cannot be evidence-equivalent to itself")

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
    errors.extend(
        validate_operational_metadata_policy(
            contract.get("operationalMetadataPolicy"),
            surface_ids,
            output_contexts,
        )
    )
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


def visual_direction_contract_path(
    session_dir: Path,
    value: str = "product-design/visual-direction.json",
    *,
    require_file: bool = True,
) -> Path:
    relative = _relative_path(value, "visual direction path")
    if relative.as_posix() != "product-design/visual-direction.json":
        raise StateError(
            "Visual direction path must be product-design/visual-direction.json"
        )
    product_design_path = session_dir / "product-design"
    if product_design_path.is_symlink():
        raise StateError("Refusing a symlinked session product-design directory")
    product_design = product_design_path.resolve()
    candidate = (session_dir / relative.as_posix()).resolve()
    if not _is_within(candidate, product_design):
        raise StateError("Visual direction path escapes the product-design directory")
    if require_file and (not candidate.is_file() or candidate.is_symlink()):
        raise StateError(
            f"Visual direction must be a regular non-symlink file: {candidate}"
        )
    return candidate


def _verify_visual_direction(
    session_dir: Path,
    state: dict[str, Any],
    *,
    require_authorized: bool = False,
) -> str | None:
    direction = state.get("visualDirection")
    # Snapshots created before the direction-lock feature remain readable and
    # explicitly unbound. They are never retroactively claimed as locked.
    if direction is None:
        return None
    if direction.get("status") == "not-required":
        return None
    if direction.get("status") != "locked":
        raise StateError(
            "Visual direction is not locked; run lock-visual-direction first"
        )
    path_value = direction.get("path")
    expected_sha = direction.get("sha256")
    if not isinstance(path_value, str) or not isinstance(expected_sha, str):
        raise StateError("Locked visual direction lacks a path or SHA-256")
    path = visual_direction_contract_path(session_dir, path_value)
    contract = load_json(path, "visual direction contract")
    errors = validate_visual_direction_contract(contract)
    if errors:
        raise StateError("Invalid locked visual direction: " + "; ".join(errors))
    actual_sha = visual_direction_sha256(contract)
    if actual_sha != expected_sha:
        raise StateError("Locked visual direction contract changed after locking")
    if require_authorized and not direction.get("userAuthorized"):
        raise StateError(
            "Visual direction requires separate user authorization at this checkpoint"
        )
    return actual_sha


def render_brief_path(session_dir: Path, value: str) -> Path:
    relative = _relative_path(value, "render brief path")
    if (
        len(relative.parts) != 3
        or relative.parts[:2] != ("art-direct-imagegen", "render-briefs")
        or relative.suffix.lower() != ".json"
    ):
        raise StateError(
            "Render brief paths must be art-direct-imagegen/render-briefs/<name>.json"
        )
    brief_root_path = session_dir / "art-direct-imagegen" / "render-briefs"
    if brief_root_path.is_symlink():
        raise StateError("Refusing a symlinked render-briefs directory")
    candidate = (session_dir / relative.as_posix()).resolve()
    if not _is_within(candidate, brief_root_path.resolve()):
        raise StateError("Render brief path escapes the session render-briefs directory")
    if not candidate.is_file() or candidate.is_symlink():
        raise StateError(
            f"Render brief must be a regular non-symlink JSON file: {candidate}"
        )
    return candidate


def validate_render_brief(
    state: dict[str, Any],
    output_id: str,
    brief: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        brief,
        {
            "schemaVersion",
            "outputId",
            "visualDirectionSha256",
            "shellIds",
            "referenceBindingIds",
            "anchorOutputId",
            "anchorArtifactSha256",
            "preserve",
            "changeOnly",
        },
        "render brief",
        errors,
    )
    if brief.get("schemaVersion") != 1:
        errors.append("render brief.schemaVersion must be 1")
    if brief.get("outputId") != output_id:
        errors.append("render brief.outputId does not match the output")
    direction_sha = state.get("visualDirection", {}).get("sha256")
    if brief.get("visualDirectionSha256") != direction_sha:
        errors.append(
            "render brief.visualDirectionSha256 does not match the locked direction"
        )
    contract_output = _contract_output_map(state["contract"]).get(output_id)
    if not isinstance(contract_output, dict):
        return errors + ["render brief output is not in the contract"]
    surface = next(
        (
            item
            for item in state["contract"].get("surfaces", [])
            if isinstance(item, dict)
            and item.get("id") == contract_output.get("surfaceId")
        ),
        None,
    )
    if not isinstance(surface, dict):
        return errors + ["render brief output surface is not in the contract"]
    for field in ("shellIds", "referenceBindingIds"):
        values = brief.get(field)
        if not isinstance(values, list) or any(
            not isinstance(item, str) or not item.strip() for item in values
        ):
            errors.append(f"render brief.{field} must be an array of IDs")
        elif values != surface.get(field, []):
            errors.append(f"render brief.{field} differs from the covered surface")
    if brief.get("anchorOutputId") != contract_output.get("anchorOutputId"):
        errors.append("render brief.anchorOutputId differs from the contract")
    runtime_output = _state_output_map(state).get(output_id, {})
    if brief.get("anchorArtifactSha256") != runtime_output.get(
        "anchorArtifactSha256"
    ):
        errors.append(
            "render brief.anchorArtifactSha256 differs from the bound anchor"
        )
    for field in ("preserve", "changeOnly"):
        values = _validate_non_empty_string_list(
            brief.get(field),
            f"render brief.{field}",
            errors,
        )
        if any(len(item.strip()) < 8 for item in values):
            errors.append(f"render brief.{field} contains a ceremonial entry")
    return errors


def _bind_output_render_brief(
    session_dir: Path,
    state: dict[str, Any],
    output_id: str,
    render_brief_value: str | None,
) -> tuple[str, str]:
    if not isinstance(render_brief_value, str):
        raise StateError(
            f"imagegen output {output_id} requires --render-brief before generating"
        )
    path = render_brief_path(session_dir, render_brief_value)
    brief = load_json(path, "render brief")
    errors = validate_render_brief(state, output_id, brief)
    if errors:
        raise StateError("Invalid render brief: " + "; ".join(errors))
    return render_brief_value, sha256_file(path)


def _verify_output_render_brief(
    session_dir: Path,
    state: dict[str, Any],
    output: dict[str, Any],
) -> None:
    if not _is_v3_state(state):
        return
    contract_output = _contract_output_map(state["contract"])[output["id"]]
    path_value = output.get("renderBriefPath")
    expected_sha = output.get("renderBriefSha256")
    if contract_output.get("artifactKind") != "imagegen":
        if path_value is not None or expected_sha is not None:
            raise StateError(
                f"non-imagegen output {output['id']} cannot bind a render brief"
            )
        return
    material_statuses = {
        "generating",
        "reviewing",
        "awaiting-approval",
        "accepted",
        "promoted",
    }
    if output.get("status") not in material_statuses and path_value is None:
        return
    if not isinstance(path_value, str) or not isinstance(expected_sha, str):
        raise StateError(f"imagegen output {output['id']} lacks a bound render brief")
    path = render_brief_path(session_dir, path_value)
    if sha256_file(path) != expected_sha:
        raise StateError(f"render brief for output {output['id']} changed after binding")
    brief = load_json(path, "bound render brief")
    errors = validate_render_brief(state, output["id"], brief)
    if errors:
        raise StateError("Invalid bound render brief: " + "; ".join(errors))


def qa_evidence_path(
    session_dir: Path,
    value: str,
    *,
    require_file: bool = True,
) -> Path:
    relative = _relative_path(value, "QA evidence path")
    if not relative.parts or relative.parts[0] != "qa":
        raise StateError("QA evidence paths must start with qa/")
    qa_root_path = session_dir / "qa"
    if qa_root_path.is_symlink():
        raise StateError("Refusing a symlinked session QA directory")
    qa_root = qa_root_path.resolve()
    candidate_path = session_dir
    for part in relative.parts:
        candidate_path = candidate_path / part
        if candidate_path.is_symlink():
            raise StateError(f"Refusing symlinked QA evidence path: {value}")
    candidate = candidate_path.resolve()
    if not _is_within(candidate, qa_root):
        raise StateError("QA evidence path escapes the session QA directory")
    if require_file and (not candidate.is_file() or candidate.is_symlink()):
        raise StateError(f"QA evidence must be a regular non-symlink file: {candidate}")
    if not require_file and candidate.exists() and (
        not candidate.is_file() or candidate.is_symlink()
    ):
        raise StateError(f"QA evidence destination must be a regular file: {candidate}")
    return candidate


def provenance_file_path(session_dir: Path, value: str, label: str) -> Path:
    relative = _relative_path(value, label)
    if not relative.parts or relative.parts[0] != "provenance":
        raise StateError(f"{label} must start with provenance/")
    provenance_root_path = session_dir / "provenance"
    if provenance_root_path.is_symlink():
        raise StateError("Refusing a symlinked session provenance directory")
    provenance_root = provenance_root_path.resolve()
    candidate_path = session_dir
    for part in relative.parts:
        candidate_path = candidate_path / part
        if candidate_path.is_symlink():
            raise StateError(f"Refusing symlinked {label}: {value}")
    candidate = candidate_path.resolve()
    if not _is_within(candidate, provenance_root):
        raise StateError(f"{label} escapes the session provenance directory")
    if not candidate.is_file() or candidate.is_symlink():
        raise StateError(f"{label} must be a regular non-symlink file: {candidate}")
    return candidate


def validate_screenshot_file(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    with path.open("rb") as handle:
        data = handle.read(1024 * 1024)
    header = data[:12]
    valid = (
        (suffix == ".png" and header.startswith(b"\x89PNG\r\n\x1a\n"))
        or (suffix in {".jpg", ".jpeg"} and header.startswith(b"\xff\xd8\xff"))
        or (
            suffix == ".webp"
            and len(header) >= 12
            and header[:4] == b"RIFF"
            and header[8:12] == b"WEBP"
        )
    )
    if not valid:
        raise StateError("QA screenshot must be a PNG, JPEG, or WebP with matching file magic")
    width = height = 0
    if suffix == ".png":
        if len(data) < 24 or data[12:16] != b"IHDR":
            raise StateError("QA PNG screenshot has no valid IHDR dimensions")
        width, height = struct.unpack(">II", data[16:24])
    elif suffix in {".jpg", ".jpeg"}:
        offset = 2
        sof_markers = {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }
        while offset + 3 < len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            offset += 2
            if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                continue
            if offset + 2 > len(data):
                break
            segment_length = int.from_bytes(data[offset : offset + 2], "big")
            if segment_length < 2 or offset + segment_length > len(data):
                break
            if marker in sof_markers and segment_length >= 7:
                height = int.from_bytes(data[offset + 3 : offset + 5], "big")
                width = int.from_bytes(data[offset + 5 : offset + 7], "big")
                break
            offset += segment_length
    else:
        if len(data) < 30:
            raise StateError("QA WebP screenshot has no readable dimensions")
        chunk = data[12:16]
        if chunk == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
        elif chunk == b"VP8L" and data[20] == 0x2F:
            b0, b1, b2, b3 = data[21:25]
            width = 1 + b0 + ((b1 & 0x3F) << 8)
            height = 1 + (b1 >> 6) + (b2 << 2) + ((b3 & 0x0F) << 10)
        elif chunk == b"VP8 " and data[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(data[26:28], "little") & 0x3FFF
            height = int.from_bytes(data[28:30], "little") & 0x3FFF
    if width < 1 or height < 1:
        raise StateError("QA screenshot has no readable positive pixel dimensions")
    return width, height


def _output_requires_imagegen_provenance(
    state: dict[str, Any],
    output_id: str,
) -> bool:
    if _is_v3_state(state):
        output = _contract_output_map(state["contract"]).get(output_id)
        return isinstance(output, dict) and output.get("artifactKind") == "imagegen"
    return (
        state["contract"].get("workflowProfile", "standard") == "full"
        and state["contract"].get("visualArtifactPolicy") == "imagegen-required"
    )


def validate_imagegen_artifact(
    state: dict[str, Any],
    path: Path,
    output_id: str,
) -> None:
    if not _output_requires_imagegen_provenance(state, output_id):
        return
    try:
        validate_screenshot_file(path)
    except StateError as exc:
        policy_label = "imagegen" if _is_v3_state(state) else "imagegen-required"
        raise StateError(
            f"{policy_label} artifacts must be real non-symlink PNG/JPEG/WebP files: "
            + str(exc)
        ) from exc


def validate_declared_artifact_kind(
    state: dict[str, Any],
    path: Path,
    output_id: str,
) -> None:
    if not _is_v3_state(state):
        validate_imagegen_artifact(state, path, output_id)
        return
    contract_output = _contract_output_map(state["contract"])[output_id]
    artifact_kind = contract_output.get("artifactKind")
    if artifact_kind == "none":
        raise StateError(f"output {output_id} declares artifactKind none")
    if artifact_kind in {"browser-screenshot", "imagegen"}:
        try:
            validate_screenshot_file(path)
        except StateError as exc:
            raise StateError(
                f"{artifact_kind} artifact must be a real PNG/JPEG/WebP file: {exc}"
            ) from exc


def validate_imagegen_provenance(
    session_dir: Path,
    state: dict[str, Any],
    output_id: str,
    artifact: Path,
    receipt_value: str | None,
) -> dict[str, Any] | None:
    if not _output_requires_imagegen_provenance(state, output_id):
        if receipt_value is not None:
            raise StateError(
                "--provenance-receipt is valid only for imagegen outputs"
            )
        return None
    if not isinstance(receipt_value, str):
        raise StateError(
            "imagegen output review requires a provenance receipt via --provenance-receipt"
        )
    receipt_path = provenance_file_path(
        session_dir,
        receipt_value,
        "provenance receipt path",
    )
    if receipt_path.suffix.lower() != ".json":
        raise StateError("provenance receipt must be a JSON file")
    receipt = load_json(receipt_path, "image generation provenance receipt")
    errors: list[str] = []
    _unknown_keys(
        receipt,
        {
            "outputId",
            "artifactSha256",
            "sourceKind",
            "sourceId",
            "tracePath",
            "traceSha256",
        },
        "provenance receipt",
        errors,
    )
    if receipt.get("outputId") != output_id:
        errors.append("provenance receipt.outputId does not match the output")
    artifact_sha256 = sha256_file(artifact)
    if receipt.get("artifactSha256") != artifact_sha256:
        errors.append("provenance receipt.artifactSha256 does not match artifact bytes")
    if receipt.get("sourceKind") != "host-imagegen":
        errors.append("provenance receipt.sourceKind must be host-imagegen")
    source_id = receipt.get("sourceId")
    if not isinstance(source_id, str) or not source_id.strip():
        errors.append("provenance receipt.sourceId must be non-empty")
    trace_value = receipt.get("tracePath")
    declared_trace_sha = receipt.get("traceSha256")
    trace_sha256: str | None = None
    if not isinstance(trace_value, str):
        errors.append("provenance receipt.tracePath must be a string")
    else:
        try:
            trace_path = provenance_file_path(
                session_dir,
                trace_value,
                "provenance trace path",
            )
            if trace_path == receipt_path:
                errors.append("provenance receipt and trace must be distinct files")
            trace_sha256 = sha256_file(trace_path)
            if trace_sha256 != declared_trace_sha:
                errors.append(
                    "provenance receipt.traceSha256 does not match trace bytes"
                )
        except StateError as exc:
            errors.append(str(exc))
    if not isinstance(declared_trace_sha, str) or HASH_RE.fullmatch(declared_trace_sha) is None:
        errors.append("provenance receipt.traceSha256 is invalid")
    if errors:
        raise StateError("Invalid image generation provenance: " + "; ".join(errors))
    return {
        "receiptPath": receipt_value,
        "receiptSha256": sha256_file(receipt_path),
        "sourceKind": "host-imagegen",
        "sourceId": source_id,
        "tracePath": trace_value,
        "traceSha256": trace_sha256,
        "providerAuthenticity": "not-verified",
    }


def implementation_target_path(root: Path, value: str) -> Path:
    relative = _implementation_relative_path(value, "implementation target")
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise StateError(f"Refusing symlinked implementation target path: {value}")
    resolved = candidate.resolve()
    if not _is_within(resolved, root):
        raise StateError(f"Implementation target escapes the repository: {value}")
    if resolved.exists() and not resolved.is_file():
        raise StateError(f"Implementation target must be a regular file: {value}")
    return resolved


def implementation_target_sha256(root: Path, value: str) -> str | None:
    target = implementation_target_path(root, value)
    if not target.exists():
        return None
    return sha256_file(target)


def implementation_plan_path(
    session_dir: Path,
    value: str = "implementation/plan.json",
    *,
    require_file: bool = True,
) -> Path:
    relative = _relative_path(value, "implementation plan path")
    if relative.as_posix() != "implementation/plan.json":
        raise StateError("Implementation plan path must be implementation/plan.json")
    implementation_root_path = session_dir / "implementation"
    if implementation_root_path.is_symlink():
        raise StateError("Refusing a symlinked session implementation directory")
    candidate = (session_dir / relative.as_posix()).resolve()
    if not _is_within(candidate, implementation_root_path.resolve()):
        raise StateError("Implementation plan path escapes the implementation directory")
    if require_file and (not candidate.is_file() or candidate.is_symlink()):
        raise StateError(
            f"Implementation plan must be a regular non-symlink file: {candidate}"
        )
    return candidate


def validate_implementation_plan(
    contract: dict[str, Any],
    plan: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        plan,
        {
            "schemaVersion",
            "contractId",
            "contractSha256",
            "structureSha256",
            "capabilityDecisions",
            "targetBindings",
            "outputBindings",
        },
        "implementation plan",
        errors,
    )
    if plan.get("schemaVersion") != 1:
        errors.append("implementation plan.schemaVersion must be 1")
    if plan.get("contractId") != contract.get("contractId"):
        errors.append("implementation plan.contractId does not match the contract")
    if plan.get("contractSha256") != _canonical_sha256(contract):
        errors.append("implementation plan.contractSha256 does not match the contract")
    if plan.get("structureSha256") != contract.get("structure", {}).get("sha256"):
        errors.append("implementation plan.structureSha256 does not match the contract")

    requirements = {
        item["id"]: item
        for item in contract.get("capabilityRequirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    decisions = plan.get("capabilityDecisions")
    decision_ids: set[str] = set()
    if not isinstance(decisions, list):
        errors.append("implementation plan.capabilityDecisions must be an array")
        decisions = []
    for index, decision in enumerate(decisions):
        label = f"implementation plan.capabilityDecisions[{index}]"
        if not isinstance(decision, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            decision,
            {
                "requirementId",
                "decisionTier",
                "selectedApproach",
                "existingOwner",
                "candidates",
                "selectedCandidate",
                "gap",
                "lifetimeRationale",
                "obligations",
                "validation",
            },
            label,
            errors,
        )
        requirement_id = decision.get("requirementId")
        requirement = requirements.get(requirement_id)
        if requirement is None:
            errors.append(f"{label}.requirementId references an unknown capability")
            continue
        if requirement_id in decision_ids:
            errors.append(f"duplicate capability decision {requirement_id!r}")
        decision_ids.add(requirement_id)
        approach = decision.get("selectedApproach")
        if approach not in IMPLEMENTATION_APPROACHES:
            errors.append(f"{label}.selectedApproach is invalid")
        declared_tier = decision.get("decisionTier")
        if declared_tier is not None and declared_tier not in {
            "direct",
            "known-fit",
            "comparative",
        }:
            errors.append(f"{label}.decisionTier is invalid")
        complexity = requirement.get("complexity")
        guarded_decision = (
            complexity in {"complex", "foundational"}
            and approach in {"project-owned", "external-dependency"}
        )
        effective_tier = declared_tier or (
            "comparative" if guarded_decision else "direct"
        )
        if complexity == "foundational" and effective_tier != "comparative":
            errors.append(f"{label}.decisionTier must be comparative for foundational work")
        if (
            complexity in {"complex", "foundational"}
            and approach == "project-owned"
            and effective_tier != "comparative"
        ):
            errors.append(
                f"{label}.decisionTier must be comparative for a complex project-owned primitive"
            )
        if effective_tier == "known-fit" and approach not in {
            "reuse",
            "extend",
            "compose",
            "platform",
            "framework",
            "external-dependency",
        }:
            errors.append(
                f"{label}.decisionTier known-fit requires a proven non-project-owned capability"
            )
        if effective_tier == "direct" and guarded_decision:
            errors.append(
                f"{label}.decisionTier direct cannot own a complex project-owned or external capability"
            )
        existing_owner = decision.get("existingOwner")
        if existing_owner is not None and (
            not isinstance(existing_owner, str) or not existing_owner.strip()
        ):
            errors.append(f"{label}.existingOwner must be null or non-empty")
        candidates = decision.get("candidates")
        candidate_names: list[str] = []
        candidate_evidence_refs: list[str] = []
        candidate_kinds: list[str] = []
        candidate_by_name: dict[str, dict[str, Any]] = {}
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"{label}.candidates must be a non-empty array")
            candidates = []
        for candidate_index, candidate in enumerate(candidates):
            candidate_label = f"{label}.candidates[{candidate_index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{candidate_label} must be an object")
                continue
            _unknown_keys(
                candidate,
                {"name", "kind", "evidenceRef", "evidenceSha256"},
                candidate_label,
                errors,
            )
            for field in ("name", "kind", "evidenceRef"):
                value = candidate.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{candidate_label}.{field} must be non-empty")
            name = candidate.get("name")
            kind = candidate.get("kind")
            evidence_ref = candidate.get("evidenceRef")
            evidence_sha = candidate.get("evidenceSha256")
            if (
                not isinstance(evidence_sha, str)
                or HASH_RE.fullmatch(evidence_sha) is None
            ):
                errors.append(f"{candidate_label}.evidenceSha256 is invalid")
            if isinstance(name, str):
                candidate_names.append(name)
                candidate_by_name[name] = candidate
                if len(name.strip()) < 3:
                    errors.append(f"{candidate_label}.name is too short to identify a candidate")
            if isinstance(kind, str):
                candidate_kinds.append(kind)
                if kind not in CANDIDATE_KINDS:
                    errors.append(f"{candidate_label}.kind is not a credible implementation class")
            if isinstance(evidence_ref, str):
                candidate_evidence_refs.append(evidence_ref)
                valid_evidence_ref = False
                if evidence_ref.startswith("repo:"):
                    try:
                        _implementation_relative_path(
                            evidence_ref.removeprefix("repo:"),
                            f"{candidate_label}.evidenceRef",
                        )
                        valid_evidence_ref = True
                    except StateError:
                        pass
                elif evidence_ref.startswith("session:implementation/evidence/"):
                    try:
                        session_relative = evidence_ref.removeprefix("session:")
                        relative = _relative_path(
                            session_relative,
                            f"{candidate_label}.evidenceRef",
                        )
                        if relative.parts[:2] == ("implementation", "evidence"):
                            valid_evidence_ref = True
                    except StateError:
                        pass
                if not valid_evidence_ref:
                    errors.append(
                        f"{candidate_label}.evidenceRef must be repo:<relative-path> or session:implementation/evidence/<file>"
                    )
        if len({name.strip().casefold() for name in candidate_names}) != len(candidate_names):
            errors.append(f"{label}.candidates contains duplicate names")
        if len({ref.strip().casefold() for ref in candidate_evidence_refs}) != len(
            candidate_evidence_refs
        ):
            errors.append(f"{label}.candidates contains duplicate evidenceRef values")
        selected_candidate = decision.get("selectedCandidate")
        if selected_candidate not in candidate_names:
            errors.append(f"{label}.selectedCandidate must name a declared candidate")
        for field in ("gap", "lifetimeRationale"):
            value = decision.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{label}.{field} must be non-empty")
        obligations = _validate_non_empty_string_list(
            decision.get("obligations"),
            f"{label}.obligations",
            errors,
            allow_empty=True,
        )
        validation = _validate_non_empty_string_list(
            decision.get("validation"),
            f"{label}.validation",
            errors,
        )
        if guarded_decision:
            requires_comparison = effective_tier == "comparative"
            if requires_comparison and len(set(candidate_names)) < 2:
                errors.append(f"{label} requires at least two candidates")
            gap = decision.get("gap")
            if (
                not isinstance(gap, str)
                or len(gap.strip()) < 24
                or len(gap.split()) < 4
            ):
                errors.append(f"{label}.gap must be concrete and evidence-specific")
            rationale = decision.get("lifetimeRationale")
            if (
                not isinstance(rationale, str)
                or len(rationale.strip()) < 24
                or len(rationale.split()) < 4
            ):
                errors.append(f"{label}.lifetimeRationale must describe lifetime tradeoffs")
            if not obligations:
                errors.append(f"{label}.obligations must be non-empty")
            elif any(
                len(item.strip()) < 12 or len(item.split()) < 2
                for item in obligations
            ):
                errors.append(f"{label}.obligations contain ceremonial entries")
            if not validation:
                errors.append(f"{label}.validation must be non-empty")
            elif any(
                len(item.strip()) < 12 or len(item.split()) < 2
                for item in validation
            ):
                errors.append(f"{label}.validation contains ceremonial entries")
            selected = candidate_by_name.get(selected_candidate)
            if isinstance(selected, dict) and selected.get("kind") != approach:
                errors.append(
                    f"{label}.selectedCandidate kind must exactly match selectedApproach"
                )
            if approach == "project-owned" and not any(
                kind in (IMPLEMENTATION_APPROACHES - {"project-owned"})
                for kind in candidate_kinds
            ):
                errors.append(
                    f"{label} project-owned selection requires a credible non-project-owned alternative"
                )
    missing_required = sorted(
        requirement_id
        for requirement_id, requirement in requirements.items()
        if requirement.get("required") and requirement_id not in decision_ids
    )
    if missing_required:
        errors.append(
            "implementation plan lacks required capability decisions: "
            + ", ".join(missing_required)
        )

    contract_targets = {
        item["path"]: item
        for item in contract.get("implementationTargets", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    target_bindings = plan.get("targetBindings")
    bound_target_paths: set[str] = set()
    if not isinstance(target_bindings, list):
        errors.append("implementation plan.targetBindings must be an array")
        target_bindings = []
    for index, binding in enumerate(target_bindings):
        label = f"implementation plan.targetBindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            binding,
            {"path", "surfaceIds", "capabilityRequirementIds"},
            label,
            errors,
        )
        path = binding.get("path")
        target = contract_targets.get(path)
        if target is None:
            errors.append(f"{label}.path is not a declared implementation target")
            continue
        if path in bound_target_paths:
            errors.append(f"duplicate target binding path {path!r}")
        bound_target_paths.add(path)
        surface_ids = _validate_non_empty_string_list(
            binding.get("surfaceIds"),
            f"{label}.surfaceIds",
            errors,
        )
        if sorted(surface_ids) != sorted(target.get("surfaceIds", [])):
            errors.append(f"{label}.surfaceIds differ from the contract target")
        capability_ids = _validate_non_empty_string_list(
            binding.get("capabilityRequirementIds"),
            f"{label}.capabilityRequirementIds",
            errors,
        )
        for capability_id in capability_ids:
            if capability_id not in decision_ids:
                errors.append(
                    f"{label}.capabilityRequirementIds references unknown decision {capability_id!r}"
                )
            else:
                requirement_surfaces = set(
                    requirements[capability_id].get("surfaceIds", [])
                )
                if not requirement_surfaces.intersection(surface_ids):
                    errors.append(
                        f"{label}.capabilityRequirementIds {capability_id!r} does not cover the bound target surfaces"
                    )
    if bound_target_paths != set(contract_targets):
        errors.append("implementation plan.targetBindings must cover every exact target path")

    contract_outputs = _contract_output_map(contract)
    output_bindings = plan.get("outputBindings")
    bound_output_ids: set[str] = set()
    if not isinstance(output_bindings, list):
        errors.append("implementation plan.outputBindings must be an array")
        output_bindings = []
    for index, binding in enumerate(output_bindings):
        label = f"implementation plan.outputBindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            binding,
            {"outputId", "targetPaths", "capabilityRequirementIds"},
            label,
            errors,
        )
        output_id = binding.get("outputId")
        output = contract_outputs.get(output_id)
        if output is None:
            errors.append(f"{label}.outputId references an unknown output")
            continue
        if output_id in bound_output_ids:
            errors.append(f"duplicate output binding {output_id!r}")
        bound_output_ids.add(output_id)
        target_paths = _validate_non_empty_string_list(
            binding.get("targetPaths"),
            f"{label}.targetPaths",
            errors,
        )
        for path in target_paths:
            if path not in bound_target_paths:
                errors.append(f"{label}.targetPaths references unknown target {path!r}")
        capability_ids = _validate_non_empty_string_list(
            binding.get("capabilityRequirementIds"),
            f"{label}.capabilityRequirementIds",
            errors,
        )
        for capability_id in capability_ids:
            if capability_id not in decision_ids:
                errors.append(
                    f"{label}.capabilityRequirementIds references unknown decision {capability_id!r}"
                )
        output_surface = output.get("surfaceId")
        if not any(
            output_surface in contract_targets[path].get("surfaceIds", [])
            for path in target_paths
            if path in contract_targets
        ):
            errors.append(f"{label} has no target bound to the output surface")
    required_runtime_outputs = {
        output_id
        for output_id, output in contract_outputs.items()
        if _runtime_evidence_required(output)
    }
    if required_runtime_outputs != bound_output_ids:
        errors.append(
            "implementation plan.outputBindings must match runtime-required outputs exactly"
        )
    return errors


def validate_implementation_plan_repo_evidence(
    root: Path,
    plan: dict[str, Any],
    session_dir: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    for decision_index, decision in enumerate(plan.get("capabilityDecisions", [])):
        if not isinstance(decision, dict):
            continue
        for candidate_index, candidate in enumerate(decision.get("candidates", [])):
            if not isinstance(candidate, dict):
                continue
            evidence_ref = candidate.get("evidenceRef")
            declared_sha = candidate.get("evidenceSha256")
            if not isinstance(evidence_ref, str):
                continue
            label = (
                f"implementation plan.capabilityDecisions[{decision_index}]"
                f".candidates[{candidate_index}].evidenceRef"
            )
            try:
                if evidence_ref.startswith("repo:"):
                    relative = _implementation_relative_path(
                        evidence_ref.removeprefix("repo:"),
                        label,
                    )
                    candidate_path = root
                    allowed_root = root
                elif evidence_ref.startswith("session:implementation/evidence/"):
                    if session_dir is None:
                        raise StateError(
                            f"{label} session evidence requires an active session"
                        )
                    relative = _relative_path(
                        evidence_ref.removeprefix("session:"),
                        label,
                    )
                    if relative.parts[:2] != ("implementation", "evidence"):
                        raise StateError(
                            f"{label} must stay under implementation/evidence"
                        )
                    candidate_path = session_dir
                    allowed_root = (session_dir / "implementation" / "evidence").resolve()
                else:
                    continue
                for part in relative.parts:
                    candidate_path = candidate_path / part
                    if candidate_path.is_symlink():
                        raise StateError(f"{label} resolves through a symlink")
                resolved = candidate_path.resolve()
                if not _is_within(resolved, allowed_root):
                    raise StateError(f"{label} escapes its allowed evidence root")
                if not resolved.is_file() or resolved.is_symlink():
                    raise StateError(f"{label} must reference an existing regular file")
                if sha256_file(resolved) != declared_sha:
                    raise StateError(
                        f"{label} evidenceSha256 does not match evidence bytes"
                    )
            except StateError as exc:
                errors.append(str(exc))
    return errors


def _store_implementation_plan(
    session_dir: Path,
    contract: dict[str, Any],
    source_value: str | Path | None,
) -> tuple[str, str]:
    if source_value is None:
        raise StateError("SchemaVersion 3 full implementation requires --implementation-plan")
    source = Path(source_value).expanduser().resolve()
    plan = load_json(source, "implementation plan")
    errors = validate_implementation_plan(contract, plan)
    if errors:
        raise StateError("Invalid implementation plan: " + "; ".join(errors))
    path_value = "implementation/plan.json"
    destination = implementation_plan_path(
        session_dir,
        path_value,
        require_file=False,
    )
    atomic_write_json(destination, plan)
    stored = load_json(destination, "stored implementation plan")
    stored_errors = validate_implementation_plan(contract, stored)
    if stored_errors:
        raise StateError(
            "Invalid stored implementation plan: " + "; ".join(stored_errors)
        )
    return path_value, sha256_file(destination)


def _verify_implementation_plan(session_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    implementation = state.get("implementation", {})
    path_value = implementation.get("planPath")
    expected_sha = implementation.get("planSha256")
    if path_value != "implementation/plan.json" or not isinstance(expected_sha, str):
        raise StateError("SchemaVersion 3 implementation lacks a bound implementation plan")
    path = implementation_plan_path(session_dir, path_value)
    if sha256_file(path) != expected_sha:
        raise StateError("Implementation plan changed after begin-implementation")
    plan = load_json(path, "stored implementation plan")
    errors = validate_implementation_plan(state["contract"], plan)
    errors.extend(
        validate_implementation_plan_repo_evidence(
            session_dir.parents[2],
            plan,
            session_dir,
        )
    )
    if errors:
        raise StateError("Invalid stored implementation plan: " + "; ".join(errors))
    return plan


def _state_output_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in state["outputs"]}


def validate_state_shape(state: dict[str, Any], expected_session_id: str) -> list[str]:
    errors: list[str] = []
    state_schema_version = state.get("schemaVersion")
    common_state_fields = {
        "schemaVersion",
        "sessionId",
        "revision",
        "status",
        "createdAt",
        "updatedAt",
        "contract",
        "outputs",
        "validationErrors",
        "promotedAt",
        "implementation",
        "intentConfirmation",
        "visualDirection",
        "qualityGates",
        "deliveryReview",
        "lineage",
    }
    if state_schema_version == SCHEMA_VERSION:
        common_state_fields.update(
            {"contractSha256", "structureIdentity", "renderUsage"}
        )
    _unknown_keys(state, common_state_fields, "state", errors)
    if state_schema_version not in {
        LEGACY_SCHEMA_VERSION,
        PREVIOUS_SCHEMA_VERSION,
        SCHEMA_VERSION,
    }:
        errors.append(
            "state.schemaVersion must be 1, 2, or 3"
        )
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
    legacy_unbound_direction = state_schema_version == LEGACY_SCHEMA_VERSION
    previous_schema = state_schema_version == PREVIOUS_SCHEMA_VERSION
    v3_schema = state_schema_version == SCHEMA_VERSION
    if legacy_unbound_direction:
        if contract.get("schemaVersion") != LEGACY_SCHEMA_VERSION:
            errors.append("legacy state must contain a schemaVersion 1 contract")
        if "visualDirection" in state:
            errors.append("legacy state cannot claim a visual direction lock")
        if "visualDirectionPolicy" in contract:
            errors.append("legacy contract cannot claim a visual direction policy")
    elif previous_schema and contract.get("schemaVersion") != PREVIOUS_SCHEMA_VERSION:
        errors.append("schemaVersion 2 state must contain a schemaVersion 2 contract")
    elif v3_schema and contract.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("schemaVersion 3 state must contain a schemaVersion 3 contract")
    errors.extend(
        validate_contract(
            contract,
            allow_legacy_schema_version=legacy_unbound_direction,
            allow_legacy_missing_visual_direction_policy=legacy_unbound_direction,
        )
    )
    if v3_schema:
        if state.get("contractSha256") != _canonical_sha256(contract):
            errors.append("state.contractSha256 differs from the full contract")
        if state.get("structureIdentity") != contract.get("structure"):
            errors.append("state.structureIdentity differs from contract.structure")
    workflow_profile = contract.get("workflowProfile", "standard")
    if workflow_profile == "micro":
        errors.append("state.contract.workflowProfile micro cannot use durable runtime state")
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
        allowed_output_fields = {
            "id",
            "approvalRequired",
            "promotionRequired",
            "status",
            "artifact",
            "sha256",
            "reason",
            "userAuthorized",
            "problem",
            "promotionPath",
            "promotionSha256",
            "provenance",
            "visualDirectionSha256",
        }
        if v3_schema:
            allowed_output_fields.update(
                {
                    "designEvidenceRequired",
                    "runtimeEvidenceRequired",
                    "artifactKind",
                    "anchorOutputId",
                    "anchorArtifactSha256",
                    "renderBriefPath",
                    "renderBriefSha256",
                }
            )
        else:
            allowed_output_fields.add("required")
        _unknown_keys(output, allowed_output_fields, label, errors)
        output_id = output.get("id")
        if output_id in seen:
            errors.append(f"duplicate state output ID {output_id!r}")
        if isinstance(output_id, str):
            seen.add(output_id)
        contract_output = contract_outputs.get(output_id)
        if contract_output is None:
            errors.append(f"{label}.id is not in the contract")
            continue
        if v3_schema:
            for field in (
                "designEvidenceRequired",
                "runtimeEvidenceRequired",
                "artifactKind",
                "anchorOutputId",
            ):
                if field not in output:
                    errors.append(f"{label}.{field} is required in schemaVersion 3")
                elif output.get(field) != contract_output.get(field):
                    errors.append(f"{label}.{field} differs from the contract")
            if "required" in output:
                errors.append(f"{label}.required is invalid in schemaVersion 3")
            anchor_sha = output.get("anchorArtifactSha256")
            if "anchorArtifactSha256" not in output:
                errors.append(
                    f"{label}.anchorArtifactSha256 is required in schemaVersion 3"
                )
            for field in ("renderBriefPath", "renderBriefSha256"):
                if field not in output:
                    errors.append(
                        f"{label}.{field} is required in schemaVersion 3"
                    )
            if anchor_sha is not None and (
                not isinstance(anchor_sha, str) or HASH_RE.fullmatch(anchor_sha) is None
            ):
                errors.append(f"{label}.anchorArtifactSha256 is invalid")
            if contract_output.get("anchorOutputId") is None and anchor_sha is not None:
                errors.append(f"{label}.anchorArtifactSha256 requires anchorOutputId")
            if (
                isinstance(contract_output.get("anchorOutputId"), str)
                and output.get("status")
                in {
                    "generating",
                    "reviewing",
                    "awaiting-approval",
                    "accepted",
                    "promoted",
                }
                and anchor_sha is None
            ):
                errors.append(
                    f"{label}.anchorArtifactSha256 is required after anchored generation begins"
                )
            render_brief_value = output.get("renderBriefPath")
            render_brief_sha = output.get("renderBriefSha256")
            if render_brief_value is not None and not isinstance(
                render_brief_value, str
            ):
                errors.append(f"{label}.renderBriefPath is invalid")
            if render_brief_sha is not None and (
                not isinstance(render_brief_sha, str)
                or HASH_RE.fullmatch(render_brief_sha) is None
            ):
                errors.append(f"{label}.renderBriefSha256 is invalid")
            material_statuses = {
                "generating",
                "reviewing",
                "awaiting-approval",
                "accepted",
                "promoted",
            }
            if contract_output.get("artifactKind") == "imagegen":
                if output.get("status") in material_statuses and (
                    not isinstance(render_brief_value, str)
                    or not isinstance(render_brief_sha, str)
                ):
                    errors.append(f"{label} requires a bound render brief")
            elif render_brief_value is not None or render_brief_sha is not None:
                errors.append(f"{label} non-imagegen output cannot bind a render brief")
        elif output.get("required") is not contract_output.get("required"):
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
        direction_sha256 = output.get("visualDirectionSha256")
        if not legacy_unbound_direction and "visualDirectionSha256" not in output:
            errors.append(
                f"{label}.visualDirectionSha256 is required in schemaVersion {state_schema_version}"
            )
        if legacy_unbound_direction and "visualDirectionSha256" in output:
            errors.append(
                f"{label}.visualDirectionSha256 is invalid in legacy schemaVersion 1"
            )
        if direction_sha256 is not None and (
            not isinstance(direction_sha256, str)
            or HASH_RE.fullmatch(direction_sha256) is None
        ):
            errors.append(f"{label}.visualDirectionSha256 is invalid")
        if status in {"reviewing", "awaiting-approval", "accepted", "promoted"}:
            if not isinstance(output.get("artifact"), str) or sha256 is None:
                errors.append(f"{label} requires artifact and sha256")
            if v3_schema and not _design_evidence_required(contract_output):
                errors.append(f"{label} cannot contain design artifact state when design evidence is optional")
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
        provenance = output.get("provenance")
        if provenance is not None:
            if not isinstance(provenance, dict):
                errors.append(f"{label}.provenance must be an object or null")
            else:
                _unknown_keys(
                    provenance,
                    {
                        "receiptPath",
                        "receiptSha256",
                        "sourceKind",
                        "sourceId",
                        "tracePath",
                        "traceSha256",
                        "providerAuthenticity",
                    },
                    f"{label}.provenance",
                    errors,
                )
                for field in ("receiptSha256", "traceSha256"):
                    value = provenance.get(field)
                    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
                        errors.append(f"{label}.provenance.{field} is invalid")
                for field in ("receiptPath", "tracePath", "sourceId"):
                    value = provenance.get(field)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(
                            f"{label}.provenance.{field} must be non-empty"
                        )
                for field in ("receiptPath", "tracePath"):
                    value = provenance.get(field)
                    if isinstance(value, str):
                        try:
                            relative = _relative_path(
                                value,
                                f"{label}.provenance.{field}",
                            )
                            if not relative.parts or relative.parts[0] != "provenance":
                                errors.append(
                                    f"{label}.provenance.{field} must start with provenance/"
                                )
                        except StateError as exc:
                            errors.append(str(exc))
                if provenance.get("sourceKind") != "host-imagegen":
                    errors.append(
                        f"{label}.provenance.sourceKind must be host-imagegen"
                    )
                if provenance.get("providerAuthenticity") != "not-verified":
                    errors.append(
                        f"{label}.provenance.providerAuthenticity must be not-verified"
                    )
                if not _output_requires_imagegen_provenance(
                    state,
                    output_id if isinstance(output_id, str) else "",
                ):
                    errors.append(
                        f"{label}.provenance is valid only for imagegen outputs"
                    )
        if (
            v3_schema
            and status in {"reviewing", "awaiting-approval", "accepted", "promoted"}
            and contract_output.get("artifactKind") == "imagegen"
            and provenance is None
        ):
            errors.append(f"{label}.provenance is required for imagegen artifact state")
    if set(contract_outputs) != seen:
        errors.append("state.outputs must contain every contract output exactly once")
    if len(in_progress) > 1:
        errors.append(
            "only one output may be generating, reviewing, or awaiting approval at a time: "
            + ", ".join(sorted(in_progress))
        )
    if not isinstance(state.get("validationErrors"), list):
        errors.append("state.validationErrors must be an array")
    direction = state.get("visualDirection")
    if direction is None:
        if not legacy_unbound_direction:
            errors.append("state.visualDirection is required for non-legacy sessions")
    elif not isinstance(direction, dict):
        errors.append("state.visualDirection must be an object")
    else:
        _unknown_keys(
            direction,
            {
                "status",
                "path",
                "sha256",
                "lockedAt",
                "userAuthorized",
                "authorizedAt",
            },
            "state.visualDirection",
            errors,
        )
        direction_status = direction.get("status")
        if direction_status not in VISUAL_DIRECTION_STATUSES:
            errors.append("state.visualDirection.status is invalid")
        if not isinstance(direction.get("userAuthorized"), bool):
            errors.append("state.visualDirection.userAuthorized must be a boolean")
        policy = contract.get("visualDirectionPolicy")
        if policy == "required" and direction_status not in {"pending", "locked"}:
            errors.append(
                "required visual direction policy cannot have not-required state"
            )
        if policy == "not-required" and direction_status != "not-required":
            errors.append(
                "not-required visual direction policy must have not-required state"
            )
        if direction_status == "locked":
            if direction.get("path") != "product-design/visual-direction.json":
                errors.append("locked visual direction path is invalid")
            direction_sha = direction.get("sha256")
            if not isinstance(direction_sha, str) or HASH_RE.fullmatch(direction_sha) is None:
                errors.append("locked visual direction sha256 is invalid")
            if not isinstance(direction.get("lockedAt"), str):
                errors.append("locked visual direction requires lockedAt")
            if direction.get("userAuthorized"):
                if not isinstance(direction.get("authorizedAt"), str):
                    errors.append(
                        "authorized visual direction requires authorizedAt"
                    )
            elif direction.get("authorizedAt") is not None:
                errors.append(
                    "visual direction authorizedAt must be null without authorization"
                )
        else:
            for field in ("path", "sha256", "lockedAt", "authorizedAt"):
                if direction.get(field) is not None:
                    errors.append(
                        f"unlocked visual direction {field} must be null"
                    )
            if direction.get("userAuthorized"):
                errors.append("unlocked visual direction cannot be user-authorized")
        if direction_status == "locked":
            direction_sha = direction.get("sha256")
            for index, output in enumerate(outputs):
                if not isinstance(output, dict):
                    continue
                if output.get("status") in {
                    "reviewing",
                    "awaiting-approval",
                    "accepted",
                    "promoted",
                } and output.get("visualDirectionSha256") != direction_sha:
                    errors.append(
                        f"state.outputs[{index}].visualDirectionSha256 differs from the locked direction"
                    )
        elif policy == "required":
            for index, output in enumerate(outputs):
                if (
                    isinstance(output, dict)
                    and output.get("status")
                    in {"reviewing", "awaiting-approval", "accepted", "promoted"}
                ):
                    errors.append(
                        f"state.outputs[{index}] cannot contain a material artifact before direction lock"
                    )
        if policy == "not-required":
            for index, output in enumerate(outputs):
                if (
                    isinstance(output, dict)
                    and output.get("visualDirectionSha256") is not None
                ):
                    errors.append(
                        f"state.outputs[{index}].visualDirectionSha256 must be null when direction is not required"
                    )
    implementation = state.get("implementation")
    if implementation is not None:
        if not isinstance(implementation, dict):
            errors.append("state.implementation must be an object")
        else:
            _unknown_keys(
                implementation,
                {
                    "status",
                    "startedAt",
                    "completedAt",
                    "fidelityQaReceipts",
                    "targetFingerprints",
                    *( {"planPath", "planSha256"} if v3_schema else set() ),
                },
                "state.implementation",
                errors,
            )
            if v3_schema:
                for field in ("planPath", "planSha256"):
                    if field not in implementation:
                        errors.append(
                            f"state.implementation.{field} is required in schemaVersion 3"
                        )
                plan_path = implementation.get("planPath")
                plan_sha = implementation.get("planSha256")
                if plan_path is not None and plan_path != "implementation/plan.json":
                    errors.append("state.implementation.planPath is invalid")
                if plan_sha is not None and (
                    not isinstance(plan_sha, str) or HASH_RE.fullmatch(plan_sha) is None
                ):
                    errors.append("state.implementation.planSha256 is invalid")
                if implementation.get("status") == "not-started" and (
                    plan_path is not None or plan_sha is not None
                ):
                    errors.append(
                        "not-started schemaVersion 3 implementation plan binding must be null"
                    )
                if implementation.get("status") in {"in-progress", "completed"} and (
                    plan_path != "implementation/plan.json"
                    or not isinstance(plan_sha, str)
                ):
                    errors.append(
                        "active schemaVersion 3 implementation requires planPath and planSha256"
                    )
            implementation_status = implementation.get("status")
            if (
                not isinstance(implementation_status, str)
                or implementation_status not in IMPLEMENTATION_STATUSES
            ):
                errors.append("state.implementation.status is invalid")
            started_at = implementation.get("startedAt")
            completed_at = implementation.get("completedAt")
            if (
                isinstance(implementation_status, str)
                and implementation_status in {"in-progress", "completed"}
                and not isinstance(started_at, str)
            ):
                errors.append(
                    "state.implementation.startedAt is required after implementation starts"
                )
            if implementation_status == "not-started" and started_at is not None:
                errors.append("state.implementation.startedAt must be null before implementation starts")
            if implementation_status == "completed" and not isinstance(completed_at, str):
                errors.append("state.implementation.completedAt is required when completed")
            if implementation_status != "completed" and completed_at is not None:
                errors.append("state.implementation.completedAt must be null until completed")
            receipts = implementation.get("fidelityQaReceipts")
            if not isinstance(receipts, list):
                errors.append("state.implementation.fidelityQaReceipts must be an array")
            else:
                for index, receipt in enumerate(receipts):
                    label = f"state.implementation.fidelityQaReceipts[{index}]"
                    if not isinstance(receipt, dict):
                        errors.append(f"{label} must be an object")
                        continue
                    _unknown_keys(
                        receipt,
                        {
                            "outputId",
                            "acceptedArtifactSha256",
                            "manifestPath",
                            "manifestSha256",
                            "screenshotPath",
                            "screenshotSha256",
                            "result",
                            "route",
                            "state",
                            "viewport",
                            "scrollPosition",
                            "pixelWidth",
                            "pixelHeight",
                            "evidenceEquivalentTo",
                            "equivalenceJustification",
                            "reason",
                            "recordedAt",
                            *( {"comparisonMode", "visualDirectionSha256", "implementationPlanSha256"} if v3_schema else set() ),
                        },
                        label,
                        errors,
                    )
                    receipt_output_id = receipt.get("outputId")
                    if (
                        not isinstance(receipt_output_id, str)
                        or receipt_output_id not in contract_outputs
                    ):
                        errors.append(f"{label}.outputId is not in the contract")
                    for field in ("manifestSha256",):
                        value = receipt.get(field)
                        if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
                            errors.append(f"{label}.{field} is invalid")
                    accepted_digest = receipt.get("acceptedArtifactSha256")
                    if accepted_digest is not None and (
                        not isinstance(accepted_digest, str)
                        or HASH_RE.fullmatch(accepted_digest) is None
                    ):
                        errors.append(f"{label}.acceptedArtifactSha256 is invalid")
                    if not v3_schema and accepted_digest is None:
                        errors.append(f"{label}.acceptedArtifactSha256 is invalid")
                    if v3_schema:
                        comparison_mode = receipt.get("comparisonMode")
                        if comparison_mode not in {"accepted-design", "direction-only"}:
                            errors.append(f"{label}.comparisonMode is invalid")
                        direction_digest = receipt.get("visualDirectionSha256")
                        if (
                            not isinstance(direction_digest, str)
                            or HASH_RE.fullmatch(direction_digest) is None
                        ):
                            errors.append(f"{label}.visualDirectionSha256 is invalid")
                        plan_digest = receipt.get("implementationPlanSha256")
                        if (
                            not isinstance(plan_digest, str)
                            or HASH_RE.fullmatch(plan_digest) is None
                        ):
                            errors.append(f"{label}.implementationPlanSha256 is invalid")
                        elif plan_digest != implementation.get("planSha256"):
                            errors.append(
                                f"{label}.implementationPlanSha256 differs from active plan"
                            )
                        if comparison_mode == "direction-only" and accepted_digest is not None:
                            errors.append(
                                f"{label}.acceptedArtifactSha256 must be null for direction-only"
                            )
                        if comparison_mode == "accepted-design" and accepted_digest is None:
                            errors.append(
                                f"{label}.acceptedArtifactSha256 is required for accepted-design"
                            )
                    manifest_path = receipt.get("manifestPath")
                    if not isinstance(manifest_path, str):
                        errors.append(f"{label}.manifestPath must be a string")
                    else:
                        try:
                            relative = _relative_path(manifest_path, f"{label}.manifestPath")
                            if not relative.parts or relative.parts[0] != "qa":
                                errors.append(f"{label}.manifestPath must start with qa/")
                            if PurePosixPath(manifest_path).suffix.lower() != ".json":
                                errors.append(f"{label}.manifestPath must end with .json")
                        except StateError as exc:
                            errors.append(str(exc))
                    receipt_result = receipt.get("result")
                    if not isinstance(receipt_result, str) or receipt_result not in FIDELITY_RESULTS:
                        errors.append(f"{label}.result is invalid")
                    for field in ("route", "state", "viewport", "scrollPosition"):
                        value = receipt.get(field)
                        if not isinstance(value, str) or not value.strip():
                            errors.append(f"{label}.{field} must be a non-empty string")
                    for field in ("pixelWidth", "pixelHeight"):
                        value = receipt.get(field)
                        if value is not None and (
                            not isinstance(value, int)
                            or isinstance(value, bool)
                            or value < 1
                        ):
                            errors.append(f"{label}.{field} must be a positive integer")
                    equivalence = receipt.get("equivalenceJustification")
                    evidence_equivalent_to = receipt.get("evidenceEquivalentTo")
                    if (evidence_equivalent_to is None) != (equivalence is None):
                        errors.append(
                            f"{label}.evidenceEquivalentTo and equivalenceJustification must be provided together"
                        )
                    elif evidence_equivalent_to is not None:
                        if (
                            not isinstance(evidence_equivalent_to, str)
                            or evidence_equivalent_to not in contract_outputs
                        ):
                            errors.append(
                                f"{label}.evidenceEquivalentTo is not in the contract"
                            )
                        if not isinstance(equivalence, str) or not equivalence.strip():
                            errors.append(
                                f"{label}.equivalenceJustification must be non-empty when present"
                            )
                    screenshot_path = receipt.get("screenshotPath")
                    screenshot_sha = receipt.get("screenshotSha256")
                    if screenshot_path is None:
                        if screenshot_sha is not None:
                            errors.append(
                                f"{label}.screenshotSha256 requires screenshotPath"
                            )
                        if receipt.get("pixelWidth") is not None or receipt.get("pixelHeight") is not None:
                            errors.append(
                                f"{label} pixel dimensions must be null without screenshotPath"
                            )
                    elif not isinstance(screenshot_path, str):
                        errors.append(f"{label}.screenshotPath must be a string or null")
                    else:
                        try:
                            relative = _relative_path(
                                screenshot_path,
                                f"{label}.screenshotPath",
                            )
                            if not relative.parts or relative.parts[0] != "qa":
                                errors.append(f"{label}.screenshotPath must start with qa/")
                        except StateError as exc:
                            errors.append(str(exc))
                        if (
                            not isinstance(screenshot_sha, str)
                            or HASH_RE.fullmatch(screenshot_sha) is None
                        ):
                            errors.append(f"{label}.screenshotSha256 is invalid")
                        for field in ("pixelWidth", "pixelHeight"):
                            value = receipt.get(field)
                            if (
                                not isinstance(value, int)
                                or isinstance(value, bool)
                                or value < 1
                            ):
                                errors.append(
                                    f"{label}.{field} is required with screenshotPath"
                                )
                    reason = receipt.get("reason")
                    if reason is not None and (
                        not isinstance(reason, str) or not reason.strip()
                    ):
                        errors.append(f"{label}.reason must be non-empty when present")
                    if receipt_result == "pass" and not isinstance(screenshot_path, str):
                        errors.append(f"{label} PASS receipt requires screenshotPath")
                    if (
                        isinstance(receipt_result, str)
                        and receipt_result in {"fail", "blocked"}
                        and screenshot_path is None
                        and not isinstance(reason, str)
                    ):
                        errors.append(
                            f"{label} FAIL/BLOCKED receipt without screenshot requires reason"
                        )
                    if not isinstance(receipt.get("recordedAt"), str):
                        errors.append(f"{label}.recordedAt must be a string")
            fingerprints = implementation.get("targetFingerprints", [])
            fingerprint_paths: list[str] = []
            if not isinstance(fingerprints, list):
                errors.append("state.implementation.targetFingerprints must be an array")
            else:
                for index, fingerprint in enumerate(fingerprints):
                    label = f"state.implementation.targetFingerprints[{index}]"
                    if not isinstance(fingerprint, dict):
                        errors.append(f"{label} must be an object")
                        continue
                    _unknown_keys(
                        fingerprint,
                        {"path", "baselineSha256", "completionSha256"},
                        label,
                        errors,
                    )
                    target = fingerprint.get("path")
                    if not isinstance(target, str):
                        errors.append(f"{label}.path must be a string")
                    else:
                        fingerprint_paths.append(target)
                        try:
                            _implementation_relative_path(target, f"{label}.path")
                        except StateError as exc:
                            errors.append(str(exc))
                    for field in ("baselineSha256", "completionSha256"):
                        value = fingerprint.get(field)
                        if value is not None and (
                            not isinstance(value, str) or HASH_RE.fullmatch(value) is None
                        ):
                            errors.append(f"{label}.{field} is invalid")
                if len(set(fingerprint_paths)) != len(fingerprint_paths):
                    errors.append("state.implementation.targetFingerprints contains duplicate paths")
            if (
                workflow_profile == "full"
                and isinstance(implementation_status, str)
                and implementation_status in {"in-progress", "completed"}
            ):
                declared_targets = _contract_implementation_target_paths(contract)
                if not fingerprint_paths:
                    errors.append(
                        "full implementation requires non-empty targetFingerprints"
                    )
                elif declared_targets and fingerprint_paths != declared_targets:
                    errors.append(
                        "state.implementation.targetFingerprints must match contract.implementationTargets"
                    )
                if v3_schema and (
                    implementation.get("planPath") != "implementation/plan.json"
                    or not isinstance(implementation.get("planSha256"), str)
                ):
                    errors.append(
                        "schemaVersion 3 full implementation requires a bound implementation plan"
                    )
                if (
                    implementation_status == "completed"
                    and isinstance(fingerprints, list)
                    and not any(
                        fingerprint.get("completionSha256") is not None
                        and fingerprint.get("completionSha256")
                        != fingerprint.get("baselineSha256")
                        for fingerprint in fingerprints
                        if isinstance(fingerprint, dict)
                    )
                ):
                    errors.append(
                        "completed full workflow requires a changed implementation target fingerprint"
                    )
    confirmation = state.get("intentConfirmation")
    if confirmation is not None:
        if not isinstance(confirmation, dict):
            errors.append("state.intentConfirmation must be an object")
        else:
            _unknown_keys(
                confirmation,
                {
                    "productIntentSha256",
                    "lifecyclePlanSha256",
                    "teachBack",
                    "confirmedAt",
                    "userAuthorized",
                    *( {"contractSha256", "structureSha256", "authorityReceipt"} if v3_schema else set() ),
                },
                "state.intentConfirmation",
                errors,
            )
            expected_intent = contract.get("productIntent")
            expected_digest = (
                product_intent_sha256(expected_intent)
                if isinstance(expected_intent, dict)
                else None
            )
            if confirmation.get("productIntentSha256") != expected_digest:
                errors.append("state.intentConfirmation.productIntentSha256 differs from contract")
            expected_lifecycle_digest = (
                lifecycle_plan_digest(contract)
                if contract.get("workflowProfile", "standard") == "full"
                else None
            )
            if confirmation.get("lifecyclePlanSha256") not in {
                None,
                expected_lifecycle_digest,
            }:
                errors.append(
                    "state.intentConfirmation.lifecyclePlanSha256 differs from contract"
                )
            if not isinstance(confirmation.get("userAuthorized"), bool):
                errors.append("state.intentConfirmation.userAuthorized must be a boolean")
            if v3_schema:
                for field in ("contractSha256", "structureSha256", "authorityReceipt"):
                    if field not in confirmation:
                        errors.append(
                            f"state.intentConfirmation.{field} is required in schemaVersion 3"
                        )
                contract_digest = _canonical_sha256(contract)
                if confirmation.get("contractSha256") != contract_digest:
                    errors.append(
                        "state.intentConfirmation.contractSha256 differs from contract"
                    )
                structure_digest = contract.get("structure", {}).get("sha256")
                if confirmation.get("structureSha256") != structure_digest:
                    errors.append(
                        "state.intentConfirmation.structureSha256 differs from contract"
                    )
            if confirmation.get("userAuthorized"):
                if not isinstance(confirmation.get("teachBack"), str) or not confirmation["teachBack"].strip():
                    errors.append("confirmed intent requires a non-empty teachBack")
                if not isinstance(confirmation.get("confirmedAt"), str):
                    errors.append("confirmed intent requires confirmedAt")
                if v3_schema:
                    if not isinstance(confirmation.get("authorityReceipt"), dict):
                        errors.append(
                            "confirmed v3 intent requires authorityReceipt"
                        )
            elif v3_schema and confirmation.get("authorityReceipt") is not None:
                errors.append(
                    "unconfirmed v3 intent authorityReceipt must be null"
                )

    quality_gates = state.get("qualityGates")
    if quality_gates is not None:
        expected_gate_keys = {"intent", "coverage", "runtime", "fidelity", "userAcceptance"}
        if not isinstance(quality_gates, dict):
            errors.append("state.qualityGates must be an object")
        else:
            _unknown_keys(quality_gates, expected_gate_keys, "state.qualityGates", errors)
            for gate in sorted(expected_gate_keys):
                if quality_gates.get(gate) not in QUALITY_GATE_STATUSES:
                    errors.append(f"state.qualityGates.{gate} is invalid")

    lineage = state.get("lineage")
    if lineage is not None:
        if not isinstance(lineage, dict):
            errors.append("state.lineage must be an object")
        else:
            _unknown_keys(
                lineage,
                {
                    "parentSessionId",
                    "supersedesSessionId",
                    "supersededBySessionId",
                    "contractDelta",
                    "visualDirectionDelta",
                    *( {"authorityReceipt"} if v3_schema else set() ),
                },
                "state.lineage",
                errors,
            )
            for field in ("parentSessionId", "supersedesSessionId", "supersededBySessionId"):
                value = lineage.get(field)
                if value is not None and (
                    not isinstance(value, str) or ID_RE.fullmatch(value) is None
                ):
                    errors.append(f"state.lineage.{field} is invalid")
            if v3_schema:
                if "authorityReceipt" not in lineage:
                    errors.append(
                        "state.lineage.authorityReceipt is required in schemaVersion 3"
                    )
                elif isinstance(lineage.get("supersedesSessionId"), str):
                    if not isinstance(lineage.get("authorityReceipt"), dict):
                        errors.append(
                            "schemaVersion 3 supersession requires lineage.authorityReceipt"
                        )
                elif lineage.get("authorityReceipt") is not None:
                    errors.append(
                        "lineage.authorityReceipt requires supersedesSessionId"
                    )
            delta = lineage.get("contractDelta")
            if delta is not None:
                if not isinstance(delta, dict):
                    errors.append("state.lineage.contractDelta must be an object")
                else:
                    _unknown_keys(
                        delta,
                        {
                            "fromContractSha256",
                            "toContractSha256",
                            "changedPaths",
                            *( {"materialChanges", "relaxations"} if v3_schema else set() ),
                        },
                        "state.lineage.contractDelta",
                        errors,
                    )
                    for field in ("fromContractSha256", "toContractSha256"):
                        value = delta.get(field)
                        if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
                            errors.append(f"state.lineage.contractDelta.{field} is invalid")
                    paths = delta.get("changedPaths")
                    if not isinstance(paths, list) or any(
                        not isinstance(item, str) or not item.startswith("/") for item in paths
                    ):
                        errors.append("state.lineage.contractDelta.changedPaths is invalid")
                    if v3_schema:
                        material_changes = delta.get("materialChanges", [])
                        if not isinstance(material_changes, list) or any(
                            not isinstance(item, str) or not item.strip()
                            for item in material_changes
                        ):
                            errors.append(
                                "state.lineage.contractDelta.materialChanges is invalid"
                            )
                        relaxations = delta.get("relaxations", [])
                        if not isinstance(relaxations, list) or any(
                            not isinstance(item, str) or not item.strip()
                            for item in relaxations
                        ):
                            errors.append(
                                "state.lineage.contractDelta.relaxations is invalid"
                            )
            direction_delta = lineage.get("visualDirectionDelta")
            if direction_delta is not None:
                if not isinstance(direction_delta, dict):
                    errors.append("state.lineage.visualDirectionDelta must be an object")
                else:
                    _unknown_keys(
                        direction_delta,
                        {"fromSha256", "toSha256"},
                        "state.lineage.visualDirectionDelta",
                        errors,
                    )
                    from_sha = direction_delta.get("fromSha256")
                    if from_sha is not None and (
                        not isinstance(from_sha, str)
                        or HASH_RE.fullmatch(from_sha) is None
                    ):
                        errors.append(
                            "state.lineage.visualDirectionDelta.fromSha256 is invalid"
                        )
                    to_sha = direction_delta.get("toSha256")
                    if not isinstance(to_sha, str) or HASH_RE.fullmatch(to_sha) is None:
                        errors.append(
                            "state.lineage.visualDirectionDelta.toSha256 is invalid"
                        )

    delivery_review = state.get("deliveryReview")
    if delivery_review is not None:
        if not isinstance(delivery_review, dict):
            errors.append("state.deliveryReview must be an object")
        else:
            _unknown_keys(
                delivery_review,
                {"status", "deliveryDigest", "acceptedAt", "rejectedAt", "reason", "userAuthorized"},
                "state.deliveryReview",
                errors,
            )
            if delivery_review.get("status") not in {
                "not-ready",
                "awaiting-user-review",
                "accepted",
                "rejected",
            }:
                errors.append("state.deliveryReview.status is invalid")
            digest = delivery_review.get("deliveryDigest")
            if digest is not None and (
                not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None
            ):
                errors.append("state.deliveryReview.deliveryDigest is invalid")
            if not isinstance(delivery_review.get("userAuthorized"), bool):
                errors.append("state.deliveryReview.userAuthorized must be a boolean")

    if v3_schema:
        usage = state.get("renderUsage")
        if not isinstance(usage, dict):
            errors.append("state.renderUsage must be an object in schemaVersion 3")
        else:
            _unknown_keys(
                usage,
                {"callsTotal", "conceptResets", "attemptsByOutput"},
                "state.renderUsage",
                errors,
            )
            for field in ("callsTotal", "conceptResets"):
                value = usage.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"state.renderUsage.{field} must be a non-negative integer")
            attempts = usage.get("attemptsByOutput")
            if not isinstance(attempts, dict):
                errors.append("state.renderUsage.attemptsByOutput must be an object")
            else:
                attempt_total = 0
                for output_id, count in attempts.items():
                    if output_id not in contract_outputs:
                        errors.append(
                            f"state.renderUsage.attemptsByOutput references unknown output {output_id!r}"
                        )
                    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                        errors.append(
                            f"state.renderUsage.attemptsByOutput[{output_id!r}] must be a non-negative integer"
                        )
                    else:
                        attempt_total += count
                        contract_output = contract_outputs.get(output_id)
                        if (
                            isinstance(contract_output, dict)
                            and contract_output.get("artifactKind") != "imagegen"
                            and count
                        ):
                            errors.append(
                                f"state.renderUsage records attempts for non-imagegen output {output_id!r}"
                            )
                if isinstance(usage.get("callsTotal"), int) and usage.get("callsTotal") != attempt_total:
                    errors.append(
                        "state.renderUsage.callsTotal must equal attemptsByOutput total"
                    )
            budget = contract.get("renderBudget")
            if (
                isinstance(usage.get("callsTotal"), int)
                and isinstance(usage.get("conceptResets"), int)
                and usage["conceptResets"] > usage["callsTotal"]
            ):
                errors.append(
                    "state.renderUsage.conceptResets cannot exceed callsTotal"
                )
            if isinstance(budget, dict):
                max_calls = budget.get("maxCallsTotal")
                max_resets = budget.get("maxConceptResets")
                max_attempts = budget.get("maxAttemptsPerOutput")
                if (
                    isinstance(usage.get("callsTotal"), int)
                    and isinstance(max_calls, int)
                    and usage["callsTotal"] > max_calls
                ):
                    errors.append("state.renderUsage.callsTotal exceeds renderBudget")
                if (
                    isinstance(usage.get("conceptResets"), int)
                    and isinstance(max_resets, int)
                    and usage["conceptResets"] > max_resets
                ):
                    errors.append("state.renderUsage.conceptResets exceeds renderBudget")
                if isinstance(attempts, dict):
                    for output_id, count in attempts.items():
                        if (
                            isinstance(count, int)
                            and isinstance(max_attempts, int)
                            and count > max_attempts
                        ):
                            errors.append(
                                f"state.renderUsage attempt count for {output_id!r} exceeds renderBudget"
                            )
            elif usage.get("callsTotal") or usage.get("conceptResets") or usage.get("attemptsByOutput"):
                errors.append("state.renderUsage must remain empty without renderBudget")

    for field in ("createdAt", "updatedAt"):
        if not isinstance(state.get(field), str) or not state[field]:
            errors.append(f"state.{field} must be non-empty")
    return errors


def _verify_v3_lineage(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
) -> None:
    lineage = state.get("lineage", {})
    supersedes_session_id = lineage.get("supersedesSessionId")
    if not isinstance(supersedes_session_id, str):
        if lineage.get("authorityReceipt") is not None:
            raise StateError("V3 lineage authority receipt lacks supersedesSessionId")
        return
    predecessor_dir = session_directory(root, supersedes_session_id)
    predecessor = load_json(
        predecessor_dir / "state.json",
        "superseded runtime state",
    )
    predecessor_errors = validate_state_shape(predecessor, supersedes_session_id)
    if predecessor_errors:
        raise StateError(
            "Invalid superseded runtime state: " + "; ".join(predecessor_errors)
        )
    expected_delta = _build_contract_delta(
        predecessor["contract"],
        state["contract"],
    )
    if lineage.get("contractDelta") != expected_delta:
        raise StateError(
            "V3 lineage contractDelta differs from the canonical predecessor delta"
        )
    if predecessor.get("status") != "superseded" or predecessor.get(
        "lineage", {}
    ).get("supersededBySessionId") != state["sessionId"]:
        raise StateError(
            "V3 successor is not atomically reconciled with its superseded predecessor"
        )
    required_actions = {"supersede-contract"}
    if expected_delta["relaxations"]:
        required_actions.add("relax-contract")
    _verify_stored_authority_receipt(
        session_dir,
        lineage.get("authorityReceipt"),
        required_actions,
        expected_session_id=state["sessionId"],
        expected_contract_sha256=_canonical_sha256(state["contract"]),
        expected_structure_sha256=state["contract"]["structure"]["sha256"],
        expected_base_contract_sha256=expected_delta["fromContractSha256"],
        expected_result_contract_sha256=expected_delta["toContractSha256"],
        expected_delta_sha256=_canonical_sha256(expected_delta),
    )


def _verify_v3_concept_reset_receipts(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
) -> list[str]:
    reset_count = state.get("renderUsage", {}).get("conceptResets", 0)
    if not isinstance(reset_count, int) or reset_count < 0:
        raise StateError("V3 concept reset usage is invalid")
    hashes: list[str] = []
    for index in range(1, reset_count + 1):
        path_value = f"authority/reset-concept-{index}.json"
        path = authority_receipt_path(session_dir, path_value)
        receipt = load_json(path, "stored concept reset authority receipt")
        errors = validate_authority_receipt(
            receipt,
            {"reset-concept"},
            expected_session_id=state["sessionId"],
            expected_contract_sha256=_canonical_sha256(state["contract"]),
            expected_structure_sha256=state["contract"]["structure"]["sha256"],
            enforce_context=True,
        )
        if errors:
            raise StateError(
                "Invalid stored concept reset authority receipt: "
                + "; ".join(errors)
            )
        _reject_authority_receipt_replay(
            root,
            state["sessionId"],
            receipt,
            {"reset-concept"},
        )
        hashes.append(sha256_file(path))
    return hashes


def load_state(root: Path, session_id: str) -> tuple[Path, dict[str, Any]]:
    session_dir = session_directory(root, session_id)
    if session_dir.is_symlink():
        raise StateError("Refusing a symlinked session directory")
    state = load_json(session_dir / "state.json", "runtime state")
    errors = validate_state_shape(state, session_id)
    if errors:
        raise StateError("Invalid runtime state: " + "; ".join(errors))
    schema_version = state.get("schemaVersion")
    bound_direction_schema = schema_version in {
        PREVIOUS_SCHEMA_VERSION,
        SCHEMA_VERSION,
    }
    v3_schema = schema_version == SCHEMA_VERSION
    state["contract"].setdefault("workflowProfile", "standard")
    state["contract"].setdefault("implementationTargets", [])
    if bound_direction_schema:
        state["contract"].setdefault("visualDirectionPolicy", "not-required")
    state.setdefault("implementation", _new_implementation_state(schema_version))
    state["implementation"].setdefault("targetFingerprints", [])
    for output in state.get("outputs", []):
        if isinstance(output, dict):
            output.setdefault("provenance", None)
            if bound_direction_schema:
                output.setdefault("visualDirectionSha256", None)
    state.setdefault("intentConfirmation", _new_intent_confirmation(state["contract"]))
    expected_lifecycle_plan = (
        lifecycle_plan_digest(state["contract"])
        if state["contract"].get("workflowProfile", "standard") == "full"
        else None
    )
    lifecycle_plan_needs_reapproval = (
        state["intentConfirmation"].get("lifecyclePlanSha256")
        != expected_lifecycle_plan
    )
    state["intentConfirmation"]["lifecyclePlanSha256"] = expected_lifecycle_plan
    state.setdefault("qualityGates", _new_quality_gates(state["contract"]))
    if (
        lifecycle_plan_needs_reapproval
        and state["contract"].get("workflowProfile", "standard") == "full"
        and state["intentConfirmation"].get("userAuthorized")
    ):
        state["intentConfirmation"].update(
            teachBack=None,
            confirmedAt=None,
            userAuthorized=False,
        )
        state["qualityGates"]["intent"] = "pending"
    state.setdefault("deliveryReview", _new_delivery_review())
    state.setdefault("lineage", _new_lineage())
    if bound_direction_schema:
        state["lineage"].setdefault("visualDirectionDelta", None)
    if v3_schema:
        _verify_v3_structure(session_dir, state)
        confirmation = state.get("intentConfirmation", {})
        if confirmation.get("userAuthorized"):
            _verify_stored_authority_receipt(
                session_dir,
                confirmation.get("authorityReceipt"),
                {"confirm-intent"},
                expected_session_id=state["sessionId"],
                expected_contract_sha256=_canonical_sha256(state["contract"]),
                expected_structure_sha256=state["contract"]["structure"]["sha256"],
            )
        _verify_v3_lineage(root, session_dir, state)
        _verify_v3_concept_reset_receipts(root, session_dir, state)
        for output in state.get("outputs", []):
            if isinstance(output, dict):
                _verify_output_render_brief(session_dir, state, output)
        if state.get("implementation", {}).get("status") in {"in-progress", "completed"}:
            _verify_implementation_plan(session_dir, state)
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


def _new_implementation_state(schema_version: int = PREVIOUS_SCHEMA_VERSION) -> dict[str, Any]:
    state = {
        "status": "not-started",
        "startedAt": None,
        "completedAt": None,
        "fidelityQaReceipts": [],
        "targetFingerprints": [],
    }
    if schema_version == SCHEMA_VERSION:
        state.update(planPath=None, planSha256=None)
    return state


def _new_intent_confirmation(contract: dict[str, Any]) -> dict[str, Any]:
    intent = contract.get("productIntent")
    confirmation = {
        "productIntentSha256": (
            product_intent_sha256(intent) if isinstance(intent, dict) else None
        ),
        "lifecyclePlanSha256": (
            lifecycle_plan_digest(contract)
            if contract.get("workflowProfile", "standard") == "full"
            else None
        ),
        "teachBack": None,
        "confirmedAt": None,
        "userAuthorized": False,
    }
    if _is_v3_contract(contract):
        confirmation.update(
            contractSha256=_canonical_sha256(contract),
            structureSha256=contract.get("structure", {}).get("sha256"),
            authorityReceipt=None,
        )
    return confirmation


def _new_visual_direction_state(contract: dict[str, Any]) -> dict[str, Any]:
    required = contract.get("visualDirectionPolicy") == "required"
    return {
        "status": "pending" if required else "not-required",
        "path": None,
        "sha256": None,
        "lockedAt": None,
        "userAuthorized": False,
        "authorizedAt": None,
    }


def _new_quality_gates(contract: dict[str, Any]) -> dict[str, str]:
    full = contract.get("workflowProfile", "standard") == "full"
    return {
        "intent": "pending" if full else "not-required",
        "coverage": "pending",
        "runtime": "pending",
        "fidelity": "pending" if full else "not-required",
        "userAcceptance": "pending" if full else "not-required",
    }


def _new_delivery_review() -> dict[str, Any]:
    return {
        "status": "not-ready",
        "deliveryDigest": None,
        "acceptedAt": None,
        "rejectedAt": None,
        "reason": None,
        "userAuthorized": False,
    }


def _new_lineage(
    *,
    parent_session_id: str | None = None,
    supersedes_session_id: str | None = None,
    contract_delta: dict[str, Any] | None = None,
    authority_receipt: dict[str, Any] | None = None,
    schema_version: int = PREVIOUS_SCHEMA_VERSION,
) -> dict[str, Any]:
    lineage = {
        "parentSessionId": parent_session_id,
        "supersedesSessionId": supersedes_session_id,
        "supersededBySessionId": None,
        "contractDelta": contract_delta,
        "visualDirectionDelta": None,
    }
    if schema_version == SCHEMA_VERSION:
        lineage["authorityReceipt"] = authority_receipt
    return lineage


def start_session(
    root_value: str | Path,
    session_id: str,
    contract_file: str | Path,
    structure_file: str | Path | None = None,
    *,
    parent_session_id: str | None = None,
    supersedes_session_id: str | None = None,
    user_authorized_supersession: bool = False,
    authority_receipt_file: str | Path | None = None,
) -> dict[str, Any]:
    _validate_id(session_id, "session ID")
    contract = load_json(Path(contract_file).expanduser().resolve(), "coverage contract")
    errors = validate_contract(contract)
    if errors:
        raise StateError("Invalid coverage contract: " + "; ".join(errors))
    contract_schema_version = contract.get("schemaVersion")
    if contract_schema_version not in {PREVIOUS_SCHEMA_VERSION, SCHEMA_VERSION}:
        raise StateError("New sessions require a schemaVersion 2 or 3 contract")
    v3_contract = contract_schema_version == SCHEMA_VERSION
    contract.setdefault("workflowProfile", "standard")
    contract.setdefault("implementationTargets", [])
    contract.setdefault("visualDirectionPolicy", "not-required")
    if contract["workflowProfile"] == "full":
        contract.setdefault(
            "operationalMetadataPolicy",
            default_operational_metadata_policy(),
        )
    if contract["workflowProfile"] == "micro":
        raise StateError("Micro workflow does not create durable runtime state; do not run init")
    root = preflight(root_value)
    if parent_session_id is not None:
        _validate_id(parent_session_id, "parent session ID")
    if supersedes_session_id is not None:
        _validate_id(supersedes_session_id, "superseded session ID")
        if not v3_contract and not user_authorized_supersession:
            raise StateError("--supersedes-session-id requires explicit user-authorized supersession")
        if v3_contract and authority_receipt_file is None:
            raise StateError(
                "SchemaVersion 3 supersession requires a file-backed authority receipt"
            )
    elif user_authorized_supersession or authority_receipt_file is not None:
        raise StateError("--user-authorized-supersession requires --supersedes-session-id")
    superseded_state: dict[str, Any] | None = None
    superseded_dir: Path | None = None
    contract_delta: dict[str, Any] | None = None
    supersession_required_actions: set[str] = set()
    if supersedes_session_id is not None:
        superseded_dir, superseded_state = load_state(root, supersedes_session_id)
        if superseded_state["status"] == "superseded":
            raise StateError(f"Session {supersedes_session_id} is already superseded")
        if superseded_state.get("lineage", {}).get("supersededBySessionId") is not None:
            raise StateError(f"Session {supersedes_session_id} already has a successor")
        if parent_session_id is None:
            parent_session_id = supersedes_session_id
        elif parent_session_id != supersedes_session_id:
            _, parent_state = load_state(root, parent_session_id)
            if parent_state["status"] in {"rejected", "superseded", "cancelled"}:
                raise StateError(
                    f"Session {parent_session_id} cannot be used as a parent while {parent_state['status']}"
                )
        contract_delta = {
            "fromContractSha256": _canonical_sha256(superseded_state["contract"]),
            "toContractSha256": _canonical_sha256(contract),
            "changedPaths": _changed_json_paths(superseded_state["contract"], contract),
        }
        if v3_contract:
            contract_delta = _build_contract_delta(
                superseded_state["contract"],
                contract,
            )
            relaxations = contract_delta["relaxations"]
            supersession_required_actions = {"supersede-contract"}
            if relaxations:
                supersession_required_actions.add("relax-contract")
            source_receipt = load_json(
                Path(authority_receipt_file).expanduser().resolve(),
                "authority receipt",
            )
            receipt_errors = validate_authority_receipt(
                source_receipt,
                supersession_required_actions,
                expected_session_id=session_id,
                expected_contract_sha256=_canonical_sha256(contract),
                expected_structure_sha256=contract["structure"]["sha256"],
                expected_base_contract_sha256=contract_delta[
                    "fromContractSha256"
                ],
                expected_result_contract_sha256=contract_delta[
                    "toContractSha256"
                ],
                expected_delta_sha256=_canonical_sha256(contract_delta),
                enforce_context=True,
            )
            if receipt_errors:
                raise StateError(
                    "Invalid authority receipt: " + "; ".join(receipt_errors)
                )
            _reject_authority_receipt_replay(
                root,
                session_id,
                source_receipt,
                supersession_required_actions,
            )
    elif parent_session_id is not None:
        _, parent_state = load_state(root, parent_session_id)
        if parent_state["status"] in {"rejected", "superseded", "cancelled"}:
            raise StateError(
                f"Session {parent_session_id} cannot be used as a parent while {parent_state['status']}"
            )
    structure = None
    if v3_contract:
        structure = _load_v3_structure(contract, structure_file)
    elif structure_file is not None:
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
    supersession_authority: dict[str, Any] | None = None
    if v3_contract and supersedes_session_id is not None:
        (staging / "authority").mkdir()
        try:
            supersession_authority = _store_authority_receipt(
                staging,
                authority_receipt_file,
                "authority/supersession.json",
                supersession_required_actions,
                expected_session_id=session_id,
                expected_contract_sha256=_canonical_sha256(contract),
                expected_structure_sha256=contract["structure"]["sha256"],
                expected_base_contract_sha256=contract_delta[
                    "fromContractSha256"
                ],
                expected_result_contract_sha256=contract_delta[
                    "toContractSha256"
                ],
                expected_delta_sha256=_canonical_sha256(contract_delta),
            )
        except Exception:
            shutil.rmtree(staging)
            raise
    state: dict[str, Any] = {
        "schemaVersion": contract_schema_version,
        "sessionId": session_id,
        "revision": 1,
        "status": "active",
        "createdAt": now,
        "updatedAt": now,
        "contract": contract,
        "outputs": [],
        "validationErrors": [],
        "promotedAt": None,
        "implementation": _new_implementation_state(contract_schema_version),
        "intentConfirmation": _new_intent_confirmation(contract),
        "visualDirection": _new_visual_direction_state(contract),
        "qualityGates": _new_quality_gates(contract),
        "deliveryReview": _new_delivery_review(),
        "lineage": _new_lineage(
            parent_session_id=parent_session_id,
            supersedes_session_id=supersedes_session_id,
            contract_delta=contract_delta,
            authority_receipt=supersession_authority,
            schema_version=contract_schema_version,
        ),
    }
    for output in contract["outputs"]:
        state_output = {
            "id": output["id"],
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
            "provenance": None,
            "visualDirectionSha256": None,
        }
        if v3_contract:
            state_output.update(
                designEvidenceRequired=output["designEvidenceRequired"],
                runtimeEvidenceRequired=output["runtimeEvidenceRequired"],
                artifactKind=output["artifactKind"],
                anchorOutputId=output["anchorOutputId"],
                anchorArtifactSha256=None,
                renderBriefPath=None,
                renderBriefSha256=None,
            )
        else:
            state_output["required"] = output["required"]
        state["outputs"].append(state_output)
    if v3_contract:
        state["contractSha256"] = _canonical_sha256(contract)
        state["structureIdentity"] = json.loads(json.dumps(contract["structure"]))
        state["renderUsage"] = {
            "callsTotal": 0,
            "conceptResets": 0,
            "attemptsByOutput": {},
        }
    try:
        (staging / "artifacts").mkdir()
        (staging / "qa").mkdir()
        (staging / "provenance").mkdir()
        (staging / "product-design").mkdir()
        (staging / "implementation").mkdir()
        (staging / "implementation" / "evidence").mkdir()
        (staging / "art-direct-imagegen" / "render-briefs").mkdir(
            parents=True
        )
        if not (staging / "authority").exists():
            (staging / "authority").mkdir()
        atomic_write_json(staging / "coverage.json", contract)
        if structure is not None:
            atomic_write_json(staging / "structure.json", structure)
        atomic_write_json(staging / "state.json", state)
        os.replace(staging, session_dir)
        _fsync_directory(sessions_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    if superseded_state is not None and superseded_dir is not None:
        superseded_state["status"] = "superseded"
        superseded_state["lineage"]["supersededBySessionId"] = session_id
        superseded_state["validationErrors"] = []
        try:
            _commit_state(superseded_dir, superseded_state)
        except Exception:
            if session_dir.is_dir() and not session_dir.is_symlink():
                shutil.rmtree(session_dir)
            raise
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
        provenance=None,
        visualDirectionSha256=None,
    )


def _require_confirmed_intent(
    state: dict[str, Any],
    session_dir: Path | None = None,
) -> None:
    if state["contract"].get("workflowProfile", "standard") != "full":
        return
    confirmation = state.get("intentConfirmation", {})
    intent = state["contract"].get("productIntent")
    expected_digest = product_intent_sha256(intent) if isinstance(intent, dict) else None
    expected_lifecycle_digest = lifecycle_plan_digest(state["contract"])
    if (
        confirmation.get("productIntentSha256") != expected_digest
        or confirmation.get("lifecyclePlanSha256") != expected_lifecycle_digest
        or not confirmation.get("userAuthorized")
        or not isinstance(confirmation.get("teachBack"), str)
        or not confirmation["teachBack"].strip()
    ):
        raise StateError(
            "Full workflow lifecycle plan is not confirmed; run confirm-intent with the exact product-intent and lifecycle-plan digests plus --user-authorized"
        )
    if _is_v3_state(state):
        if confirmation.get("contractSha256") != _canonical_sha256(state["contract"]):
            raise StateError("V3 intent confirmation is not bound to the full contract digest")
        structure_digest = state["contract"].get("structure", {}).get("sha256")
        if confirmation.get("structureSha256") != structure_digest:
            raise StateError("V3 intent confirmation is not bound to the structure digest")
        if session_dir is None:
            raise StateError("V3 intent confirmation requires stored authority verification")
        _verify_stored_authority_receipt(
            session_dir,
            confirmation.get("authorityReceipt"),
            {"confirm-intent"},
            expected_session_id=state["sessionId"],
            expected_contract_sha256=_canonical_sha256(state["contract"]),
            expected_structure_sha256=structure_digest,
        )


def confirm_intent(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    *,
    product_intent_sha256: str,
    lifecycle_plan_sha256: str,
    teach_back: str,
    user_authorized: bool,
    authority_receipt_file: str | Path | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] in TERMINAL_SESSION_STATUSES:
        raise StateError(f"Cannot confirm intent for terminal session status {state['status']!r}")
    if state["contract"].get("workflowProfile", "standard") != "full":
        raise StateError("confirm-intent is supported only for full workflows")
    if not user_authorized:
        raise StateError("confirm-intent requires --user-authorized")
    if not isinstance(teach_back, str) or not teach_back.strip():
        raise StateError("confirm-intent requires a non-empty --teach-back")
    expected_digest = state["intentConfirmation"]["productIntentSha256"]
    if (
        not isinstance(product_intent_sha256, str)
        or HASH_RE.fullmatch(product_intent_sha256) is None
        or product_intent_sha256 != expected_digest
    ):
        raise StateError("Product intent digest does not match the current contract")
    expected_lifecycle_digest = state["intentConfirmation"]["lifecyclePlanSha256"]
    if (
        not isinstance(lifecycle_plan_sha256, str)
        or HASH_RE.fullmatch(lifecycle_plan_sha256) is None
        or lifecycle_plan_sha256 != expected_lifecycle_digest
    ):
        raise StateError("lifecycle plan digest does not match the current contract")
    confirmation = state["intentConfirmation"]
    if confirmation.get("userAuthorized"):
        if confirmation.get("teachBack") != teach_back:
            raise StateError("Product intent is already confirmed with a different teach-back")
        if _is_v3_state(state):
            _verify_stored_authority_receipt(
                session_dir,
                confirmation.get("authorityReceipt"),
                {"confirm-intent"},
                expected_session_id=session_id,
                expected_contract_sha256=_canonical_sha256(state["contract"]),
                expected_structure_sha256=state["contract"]["structure"]["sha256"],
            )
        return state
    authority_summary: dict[str, Any] | None = None
    if _is_v3_state(state):
        _verify_v3_structure(session_dir, state)
        authority_summary = _store_authority_receipt(
            session_dir,
            authority_receipt_file,
            "authority/intent.json",
            {"confirm-intent"},
            expected_session_id=session_id,
            expected_contract_sha256=_canonical_sha256(state["contract"]),
            expected_structure_sha256=state["contract"]["structure"]["sha256"],
        )
        stored_receipt = load_json(
            authority_receipt_path(session_dir, "authority/intent.json"),
            "stored authority receipt",
        )
        _reject_authority_receipt_replay(
            root,
            session_id,
            stored_receipt,
            {"confirm-intent"},
        )
    confirmation.update(
        teachBack=teach_back.strip(),
        confirmedAt=utc_now(),
        userAuthorized=True,
    )
    if _is_v3_state(state):
        confirmation.update(
            contractSha256=_canonical_sha256(state["contract"]),
            structureSha256=state["contract"]["structure"]["sha256"],
            authorityReceipt=authority_summary,
        )
    state["qualityGates"]["intent"] = "pass"
    return _commit_state(session_dir, state)


def lock_visual_direction(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    direction_contract_file: str | Path,
    *,
    user_authorized: bool = False,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] in TERMINAL_SESSION_STATUSES:
        raise StateError(
            f"Cannot lock visual direction for terminal session status {state['status']!r}"
        )
    direction = state.get("visualDirection")
    if direction is None:
        raise StateError(
            "Legacy-unbound session cannot be retroactively locked; create a superseding session"
        )
    if state["contract"].get("visualDirectionPolicy") != "required":
        raise StateError(
            "lock-visual-direction requires visualDirectionPolicy=required"
        )
    source = Path(direction_contract_file).expanduser()
    if source.is_symlink():
        raise StateError("Visual direction source must not be a symlink")
    contract = load_json(source.resolve(), "visual direction contract")
    errors = validate_visual_direction_contract(contract)
    if errors:
        raise StateError("Invalid visual direction contract: " + "; ".join(errors))
    incoming_sha = visual_direction_sha256(contract)

    if direction.get("status") == "locked":
        current_sha = _verify_visual_direction(session_dir, state)
        if incoming_sha != current_sha:
            raise StateError(
                "Visual direction is already locked to a different SHA; create a superseding session"
            )
        if user_authorized and not direction.get("userAuthorized"):
            direction["userAuthorized"] = True
            direction["authorizedAt"] = utc_now()
            return _commit_state(session_dir, state)
        return state
    if direction.get("status") != "pending":
        raise StateError("Visual direction is not in a lockable pending state")

    destination = visual_direction_contract_path(session_dir, require_file=False)
    atomic_write_json(destination, contract)
    stored = load_json(destination, "stored visual direction contract")
    stored_sha = visual_direction_sha256(stored)
    if stored_sha != incoming_sha:
        raise StateError("Stored visual direction digest differs from the source contract")
    now = utc_now()
    direction.update(
        status="locked",
        path="product-design/visual-direction.json",
        sha256=stored_sha,
        lockedAt=now,
        userAuthorized=user_authorized,
        authorizedAt=now if user_authorized else None,
    )

    parent_session_id = state.get("lineage", {}).get("parentSessionId")
    if isinstance(parent_session_id, str):
        _, parent_state = load_state(root, parent_session_id)
        parent_direction = parent_state.get("visualDirection")
        parent_sha = (
            parent_direction.get("sha256")
            if isinstance(parent_direction, dict)
            and parent_direction.get("status") == "locked"
            else None
        )
        state["lineage"]["visualDirectionDelta"] = {
            "fromSha256": parent_sha,
            "toSha256": stored_sha,
        }
    return _commit_state(session_dir, state)


def _verify_output_anchor(
    session_dir: Path,
    state: dict[str, Any],
    contract_output: dict[str, Any],
    output: dict[str, Any],
    *,
    bind: bool = False,
) -> str | None:
    if not _is_v3_state(state):
        return None
    anchor_id = contract_output.get("anchorOutputId")
    if anchor_id is None:
        if output.get("anchorArtifactSha256") is not None:
            raise StateError(f"output {output['id']} has an unexpected anchor SHA")
        return None
    anchor = _state_output_map(state).get(anchor_id)
    if anchor is None or anchor.get("status") not in {"accepted", "promoted"}:
        raise StateError(
            f"output {output['id']} requires accepted/promoted anchor {anchor_id}"
        )
    artifact_error = _verify_output_artifact(session_dir, anchor)
    if artifact_error:
        raise StateError(f"anchor artifact {anchor_id}: {artifact_error}")
    anchor_sha = anchor.get("sha256")
    if not isinstance(anchor_sha, str):
        raise StateError(f"anchor artifact {anchor_id} has no SHA-256")
    bound_sha = output.get("anchorArtifactSha256")
    if bind:
        output["anchorArtifactSha256"] = anchor_sha
    elif bound_sha != anchor_sha:
        raise StateError(
            f"output {output['id']} anchor artifact changed after generation began"
        )
    return anchor_sha


def _consume_render_budget(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
    output_id: str,
    *,
    concept_reset: bool,
    authority_receipt_file: str | Path | None,
) -> None:
    if not _is_v3_state(state):
        if concept_reset:
            raise StateError("--concept-reset is supported only for schemaVersion 3")
        return
    contract_output = _contract_output_map(state["contract"])[output_id]
    if contract_output.get("artifactKind") != "imagegen":
        if concept_reset:
            raise StateError("concept reset is valid only for imagegen outputs")
        return
    budget = state["contract"].get("renderBudget")
    usage = state.get("renderUsage")
    if not isinstance(budget, dict) or not isinstance(usage, dict):
        raise StateError("imagegen output lacks a valid render budget")
    runtime_output = _state_output_map(state)[output_id]
    if concept_reset:
        problem = runtime_output.get("problem")
        code = problem.get("code") if isinstance(problem, dict) else None
        normalized_code = (
            code.lower().replace("_", "-") if isinstance(code, str) else None
        )
        if runtime_output.get("status") != "blocked" or normalized_code != "revise-direction":
            raise StateError(
                "concept reset requires a Product Design REVISE_DIRECTION blocker"
            )
    if concept_reset and usage["conceptResets"] >= budget["maxConceptResets"]:
        raise StateError("concept reset exceeds the confirmed render budget")
    attempts = usage["attemptsByOutput"].get(output_id, 0)
    if concept_reset and attempts == 0:
        raise StateError("concept reset requires a prior imagegen attempt")
    if attempts >= budget["maxAttemptsPerOutput"]:
        raise StateError(f"output {output_id} exceeds its render budget")
    if usage["callsTotal"] >= budget["maxCallsTotal"]:
        raise StateError("imagegen call exceeds the total render budget")
    if concept_reset:
        reset_index = usage["conceptResets"] + 1
        if authority_receipt_file is None:
            raise StateError(
                "concept reset requires a file-backed reset-concept authority receipt"
            )
        receipt = load_json(
            Path(authority_receipt_file).expanduser().resolve(),
            "authority receipt",
        )
        receipt_errors = validate_authority_receipt(
            receipt,
            {"reset-concept"},
            expected_session_id=state["sessionId"],
            expected_contract_sha256=_canonical_sha256(state["contract"]),
            expected_structure_sha256=state["contract"]["structure"]["sha256"],
            enforce_context=True,
        )
        if receipt_errors:
            raise StateError(
                "Invalid authority receipt: " + "; ".join(receipt_errors)
            )
        _reject_authority_receipt_replay(
            root,
            state["sessionId"],
            receipt,
            {"reset-concept"},
            allow_same_session=False,
        )
        _store_authority_receipt(
            session_dir,
            authority_receipt_file,
            f"authority/reset-concept-{reset_index}.json",
            {"reset-concept"},
            expected_session_id=state["sessionId"],
            expected_contract_sha256=_canonical_sha256(state["contract"]),
            expected_structure_sha256=state["contract"]["structure"]["sha256"],
        )
    usage["callsTotal"] += 1
    usage["attemptsByOutput"][output_id] = attempts + 1
    if concept_reset:
        usage["conceptResets"] += 1


def _apply_output_transition(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
    output_id: str,
    status: str,
    *,
    artifact: str | None = None,
    reason: str | None = None,
    user_authorized: bool = False,
    code: str | None = None,
    retryable: bool = False,
    next_action: str | None = None,
    provenance_receipt: str | None = None,
    concept_reset: bool = False,
    authority_receipt_file: str | Path | None = None,
    render_brief: str | None = None,
) -> dict[str, Any]:
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
    if _is_v3_state(state) and not _design_evidence_required(contract_output):
        if status in {"generating", "reviewing", "awaiting-approval", "accepted"}:
            raise StateError(
                f"output {output_id} has no required design evidence lifecycle"
            )
    direction_sha: str | None = None
    if status in {"generating", "reviewing", "awaiting-approval", "accepted"}:
        _require_confirmed_intent(state, session_dir)
        direction_sha = _verify_visual_direction(
            session_dir,
            state,
            require_authorized=(
                status == "generating"
                and state["contract"].get("checkpointMode")
                in {"review-before-artifact", "review-each-stage"}
            ),
        )
    if status == current:
        if (
            status == "accepted"
            and user_authorized
            and not output.get("userAuthorized")
        ):
            _require_confirmed_intent(state, session_dir)
            if artifact != output.get("artifact"):
                raise StateError(
                    "user authorization must use the same accepted artifact"
                )
            accepted_path = artifact_path(session_dir, artifact)
            validate_declared_artifact_kind(state, accepted_path, output_id)
            existing_provenance = output.get("provenance")
            validate_imagegen_provenance(
                session_dir,
                state,
                output_id,
                accepted_path,
                (
                    existing_provenance.get("receiptPath")
                    if isinstance(existing_provenance, dict)
                    else None
                ),
            )
            if sha256_file(accepted_path) != output.get("sha256"):
                raise StateError(
                    "accepted artifact changed before user authorization"
                )
            if output.get("visualDirectionSha256") != direction_sha:
                raise StateError(
                    "accepted artifact is not bound to the locked visual direction"
                )
            _verify_output_anchor(
                session_dir,
                state,
                contract_output,
                output,
            )
            _verify_output_render_brief(session_dir, state, output)
            output["userAuthorized"] = True
            state["status"] = "active"
            state["validationErrors"] = []
        return state
    if status not in TRANSITIONS[current]:
        raise StateError(f"Illegal output transition {current!r} -> {status!r}")

    if provenance_receipt is not None and status not in {
        "reviewing",
        "awaiting-approval",
        "accepted",
    }:
        raise StateError(
            "--provenance-receipt is valid only for reviewing, awaiting-approval, or accepted"
        )

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
        _verify_output_anchor(
            session_dir,
            state,
            contract_output,
            output,
            bind=True,
        )
        if _is_v3_state(state):
            if contract_output.get("artifactKind") == "imagegen":
                brief_path_value, brief_sha = _bind_output_render_brief(
                    session_dir,
                    state,
                    output_id,
                    render_brief,
                )
                output["renderBriefPath"] = brief_path_value
                output["renderBriefSha256"] = brief_sha
            elif render_brief is not None:
                raise StateError("--render-brief is valid only for imagegen outputs")
        elif render_brief is not None:
            raise StateError("--render-brief requires schemaVersion 3")
        _consume_render_budget(
            root,
            session_dir,
            state,
            output_id,
            concept_reset=concept_reset,
            authority_receipt_file=authority_receipt_file,
        )
    elif concept_reset:
        raise StateError("--concept-reset is valid only when entering generating")
    elif authority_receipt_file is not None:
        raise StateError("--authority-receipt is valid only with --concept-reset")
    elif render_brief is not None:
        raise StateError("--render-brief is valid only when entering generating")

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

    previous_provenance = output.get("provenance")
    previous_anchor_sha = output.get("anchorArtifactSha256")
    previous_render_brief_path = output.get("renderBriefPath")
    previous_render_brief_sha = output.get("renderBriefSha256")
    _clear_output(output)
    output["status"] = status
    if _is_v3_state(state):
        output["anchorArtifactSha256"] = (
            previous_anchor_sha
            if status in {"generating", "reviewing", "awaiting-approval", "accepted", "blocked"}
            else None
        )
        output["renderBriefPath"] = (
            previous_render_brief_path
            if status in {"generating", "reviewing", "awaiting-approval", "accepted", "blocked"}
            else None
        )
        output["renderBriefSha256"] = (
            previous_render_brief_sha
            if status in {"generating", "reviewing", "awaiting-approval", "accepted", "blocked"}
            else None
        )
    if status in {"reviewing", "awaiting-approval", "accepted"}:
        if artifact is None:
            raise StateError(f"{status} requires --artifact")
        path = artifact_path(session_dir, artifact)
        _verify_output_anchor(
            session_dir,
            state,
            contract_output,
            output,
        )
        _verify_output_render_brief(session_dir, state, output)
        validate_declared_artifact_kind(state, path, output_id)
        selected_provenance_receipt = provenance_receipt
        if selected_provenance_receipt is None and isinstance(previous_provenance, dict):
            selected_provenance_receipt = previous_provenance.get("receiptPath")
        provenance = validate_imagegen_provenance(
            session_dir,
            state,
            output_id,
            path,
            selected_provenance_receipt,
        )
        output["artifact"] = artifact
        output["sha256"] = sha256_file(path)
        output["provenance"] = provenance
        output["visualDirectionSha256"] = direction_sha
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
        _state_design_evidence_required(item) and item["status"] == "blocked"
        for item in state["outputs"]
    ) else "active"
    state["validationErrors"] = []
    return state


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
    provenance_receipt: str | None = None,
    concept_reset: bool = False,
    authority_receipt_file: str | Path | None = None,
    render_brief: str | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    original_status = _state_output_map(state).get(output_id, {}).get("status")
    original_user_authorized = _state_output_map(state).get(output_id, {}).get(
        "userAuthorized"
    )
    state = _apply_output_transition(
        root,
        session_dir,
        state,
        output_id,
        status,
        artifact=artifact,
        reason=reason,
        user_authorized=user_authorized,
        code=code,
        retryable=retryable,
        next_action=next_action,
        provenance_receipt=provenance_receipt,
        concept_reset=concept_reset,
        authority_receipt_file=authority_receipt_file,
        render_brief=render_brief,
    )
    if (
        original_status == status
        and original_user_authorized
        == _state_output_map(state).get(output_id, {}).get("userAuthorized")
    ):
        return state
    return _commit_state(session_dir, state)


def batch_mark(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    transitions_file: str | Path,
) -> dict[str, Any]:
    path = Path(transitions_file).expanduser().resolve()
    if not path.is_file() or path.is_symlink():
        raise StateError(f"Batch transitions must be a regular JSON file: {path}")
    try:
        transitions = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateError(f"Unable to read batch transitions: {exc}") from exc
    if not isinstance(transitions, list) or not transitions:
        raise StateError("Batch transitions must be a non-empty JSON array")
    if len(transitions) > MAX_BATCH_TRANSITIONS:
        raise StateError(f"Batch transitions may contain at most {MAX_BATCH_TRANSITIONS} entries")

    root = preflight(root_value)
    session_dir, persisted = load_state(root, session_id)
    require_revision(persisted, expected_revision)
    if _is_v3_state(persisted):
        batch_ids = [
            transition.get("outputId")
            for transition in transitions
            if isinstance(transition, dict)
            and isinstance(transition.get("outputId"), str)
        ]
        duplicate_ids = sorted(
            {output_id for output_id in batch_ids if batch_ids.count(output_id) > 1}
        )
        if duplicate_ids:
            raise StateError(
                "Batch transitions contain duplicate outputId(s): "
                + ", ".join(duplicate_ids)
            )
    state = json.loads(json.dumps(persisted))
    allowed = {
        "outputId",
        "status",
        "artifact",
        "reason",
        "userAuthorized",
        "code",
        "retryable",
        "nextAction",
        "provenanceReceipt",
        "conceptReset",
        "authorityReceipt",
        "renderBrief",
    }
    for index, transition in enumerate(transitions):
        if not isinstance(transition, dict):
            raise StateError(f"Batch transition {index} must be an object")
        unknown = sorted(set(transition) - allowed)
        if unknown:
            raise StateError(
                f"Batch transition {index} contains unknown field(s): " + ", ".join(unknown)
            )
        output_id = transition.get("outputId")
        status = transition.get("status")
        if not isinstance(output_id, str) or not isinstance(status, str):
            raise StateError(f"Batch transition {index} requires string outputId and status")
        user_authorized = transition.get("userAuthorized", False)
        retryable = transition.get("retryable", False)
        concept_reset = transition.get("conceptReset", False)
        if (
            not isinstance(user_authorized, bool)
            or not isinstance(retryable, bool)
            or not isinstance(concept_reset, bool)
        ):
            raise StateError(
                f"Batch transition {index} userAuthorized, retryable, and conceptReset must be booleans"
            )
        state = _apply_output_transition(
            root,
            session_dir,
            state,
            output_id,
            status,
            artifact=transition.get("artifact"),
            reason=transition.get("reason"),
            user_authorized=user_authorized,
            code=transition.get("code"),
            retryable=retryable,
            next_action=transition.get("nextAction"),
            provenance_receipt=transition.get("provenanceReceipt"),
            concept_reset=concept_reset,
            authority_receipt_file=transition.get("authorityReceipt"),
            render_brief=transition.get("renderBrief"),
        )
    return _commit_state(session_dir, state)


def _execution_envelope(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
) -> dict[str, Any]:
    implementation_status = state["implementation"]["status"]
    latest_receipts = {
        receipt["outputId"]: receipt
        for receipt in state["implementation"]["fidelityQaReceipts"]
    }
    implementation_snapshot = None
    if implementation_status in {"in-progress", "completed"}:
        implementation_snapshot = implementation_snapshot_sha256(root, state)
    redesign_boundary = None
    direction_path_value = state.get("visualDirection", {}).get("path")
    if isinstance(direction_path_value, str):
        direction_contract = load_json(
            visual_direction_contract_path(session_dir, direction_path_value),
            "visual direction contract",
        )
        redesign_boundary = direction_contract.get("redesignBoundary")
    if state["qualityGates"]["intent"] == "pending":
        stage = "intent-confirmation"
        stage_owner = "frontend-product-design"
    elif state.get("visualDirection", {}).get("status") == "pending":
        stage = "visual-direction"
        stage_owner = "frontend-product-design"
    elif state["qualityGates"]["coverage"] != "pass":
        stage = "design-evidence"
        stage_owner = (
            "art-direct-imagegen"
            if any(
                output.get("artifactKind") == "imagegen"
                and output["status"] not in SETTLED_OUTPUT_STATUSES
                for output in state["outputs"]
            )
            else "frontend-product-design"
        )
    elif implementation_status == "not-started":
        stage = "implementation-planning"
        stage_owner = "frontend-project-fit"
    elif implementation_status == "in-progress":
        missing_runtime = any(
            _runtime_evidence_required(contract_output)
            and latest_receipts.get(output_id, {}).get("result") != "pass"
            for output_id, contract_output in _contract_output_map(state["contract"]).items()
        )
        stage = "runtime-qa" if missing_runtime else "implementation-completion"
        stage_owner = "frontend-runtime-qa" if missing_runtime else "frontend-project-fit"
    elif state["status"] == "awaiting-user-review":
        stage = "delivery-review"
        stage_owner = "frontend-runtime-qa"
    else:
        stage = "terminal"
        stage_owner = None

    references: list[str] = []
    if stage_owner == "frontend-product-design":
        references.append("skills/frontend-product-design/references/visual-direction.md")
    elif stage_owner == "art-direct-imagegen":
        references.extend(
            [
                "skills/art-direct-imagegen/references/output-contract.md",
                "skills/art-direct-imagegen/references/prompt-and-review.md",
            ]
        )
    elif stage_owner == "frontend-project-fit":
        references.append(
            "skills/frontend-project-fit/references/project-discovery-and-reuse.md"
        )
        if any(
            requirement.get("complexity") in {"complex", "foundational"}
            for requirement in state["contract"].get("capabilityRequirements", [])
            if isinstance(requirement, dict)
        ):
            references.append(
                "skills/frontend-project-fit/references/capability-and-dependency-selection.md"
            )
    elif stage_owner == "frontend-runtime-qa":
        references.append("skills/frontend-runtime-qa/references/runtime-checks.md")
    if state["contract"].get("workflowProfile", "standard") == "full" and stage not in {
        "terminal",
        "delivery-review",
    }:
        references.append("skills/frontend-product-design/references/full-lifecycle.md")

    plan: dict[str, Any] | None = None
    plan_path_value = state["implementation"].get("planPath")
    if isinstance(plan_path_value, str):
        plan = load_json(
            implementation_plan_path(session_dir, plan_path_value),
            "implementation plan",
        )
    plan_decisions = {
        decision["requirementId"]: decision
        for decision in (plan or {}).get("capabilityDecisions", [])
        if isinstance(decision, dict) and isinstance(decision.get("requirementId"), str)
    }
    plan_output_bindings = {
        binding["outputId"]: binding
        for binding in (plan or {}).get("outputBindings", [])
        if isinstance(binding, dict) and isinstance(binding.get("outputId"), str)
    }
    surfaces = {
        surface["id"]: surface
        for surface in state["contract"].get("surfaces", [])
        if isinstance(surface, dict) and isinstance(surface.get("id"), str)
    }
    runtime_probes: list[dict[str, Any]] = []
    for contract_output in state["contract"]["outputs"]:
        if not _runtime_evidence_required(contract_output):
            continue
        surface = surfaces[contract_output["surfaceId"]]
        binding = plan_output_bindings.get(contract_output["id"], {})
        capability_validation: list[dict[str, Any]] = []
        for requirement_id in binding.get("capabilityRequirementIds", []):
            decision = plan_decisions.get(requirement_id)
            if decision is None:
                continue
            capability_validation.append(
                {
                    "requirementId": requirement_id,
                    "selectedApproach": decision.get("selectedApproach"),
                    "selectedCandidate": decision.get("selectedCandidate"),
                    "validation": decision.get("validation", []),
                }
            )
        runtime_probes.append(
            {
                "outputId": contract_output["id"],
                "route": surface.get("route"),
                "state": contract_output["state"],
                "viewport": contract_output["viewport"],
                "scrollPosition": contract_output.get("scrollPosition", "top"),
                "adapter": "agent-browser",
                "specPath": f"qa/{contract_output['id']}.runtime-probe-spec.json",
                "tracePath": f"qa/{contract_output['id']}.runtime-probe.json",
                "capabilityValidation": capability_validation,
            }
        )

    decision_tiers = []
    for requirement in state["contract"].get("capabilityRequirements", []):
        if not isinstance(requirement, dict):
            continue
        complexity = requirement.get("complexity")
        if complexity == "foundational":
            minimum_tier = "comparative"
        elif complexity == "complex":
            minimum_tier = "known-fit-or-comparative"
        else:
            minimum_tier = "direct"
        decision_tiers.append(
            {
                "requirementId": requirement.get("id"),
                "complexity": complexity,
                "minimumTier": minimum_tier,
            }
        )

    allowed_tools = ["repository-read", "project-native-checks"]
    if stage_owner == "frontend-project-fit":
        allowed_tools.append("project-dependency-inspection")
    if runtime_probes and stage_owner == "frontend-runtime-qa":
        allowed_tools.append("agent-browser")
    if stage_owner == "art-direct-imagegen":
        allowed_tools.append("image_gen")
    required_claims = state["contract"].get(
        "operationalMetadataPolicy",
        default_operational_metadata_policy(),
    ).get("requiredClaims", [])
    envelope: dict[str, Any] = {
        "schemaVersion": 1,
        "sessionId": state["sessionId"],
        "stateRevision": state["revision"],
        "contractSha256": _canonical_sha256(state["contract"]),
        "stage": stage,
        "stageOwner": stage_owner,
        "selectedReferenceSlices": list(dict.fromkeys(references)),
        "allowedTools": list(dict.fromkeys(allowed_tools)),
        "runtimeProbePolicy": {
            "schemaVersion": 1,
            "adapter": "agent-browser",
            "requiredAssertions": [
                "direct target navigation and page identity",
                "declared state and scroll position",
                "non-document app root with visible geometry and meaningful content",
                "target interaction with a changed before/after state and postcondition",
                "empty console, page-error, and failed-request lists",
                "zero critical or serious accessibility violations",
                "current implementation snapshot and a distinct screenshot of at least 320x200 pixels",
            ],
        },
        "runtimeProbes": runtime_probes,
        "capabilityDecisionTiers": decision_tiers,
        "authorizedOperationalClaims": required_claims,
        "implementationSnapshotSha256": implementation_snapshot,
        "redesignBoundary": redesign_boundary,
        "renderAttemptPolicy": {
            "maxCallsPerUserTurn": (
                None
                if state["contract"].get("workflowProfile", "standard") == "full"
                else 1
            ),
            "fullRetryAuthority": (
                "helper-reservation-only"
                if state["contract"].get("workflowProfile", "standard") == "full"
                else "not-applicable"
            ),
            "autonomousRetryAllowed": False,
            "retryMustEditPreviousArtifact": True,
            "inputRolesImmutable": True,
            "renderBudget": state["contract"].get("renderBudget"),
            "renderUsage": state.get("renderUsage"),
        },
        "forbiddenSubstitutions": [
            "Do not substitute build or source inspection for rendered browser proof.",
            "Do not navigate through a search engine or an invented URL; open only the declared target.",
            "Do not replace a selected mature complex capability with custom SVG, canvas, or bespoke controls.",
            "Do not install a browser runner or package inside an isolated fixture without explicit authorization; mark the dependency or runtime path blocked.",
            "Do not let the implementing agent set completion without helper-validated runtime receipts.",
            "Do not issue a second from-scratch ImageGen call for the same output or reclassify a supplied style/functional reference as an edit target.",
        ],
        "completionAuthority": "scripts/runtime_state.py complete-implementation",
        "tokenPolicy": "Load only the stage owner and selectedReferenceSlices; do not preload every bundled skill or reference.",
    }
    envelope["sha256"] = _canonical_sha256(envelope)
    return envelope


def compact_handoff(root_value: str | Path, session_id: str) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    next_actions: list[str] = []
    if state["qualityGates"]["intent"] == "pending":
        next_actions.append("confirm-intent")
    direction = state.get("visualDirection")
    if direction is None:
        direction_summary = {
            "status": "legacy-unbound",
            "path": None,
            "sha256": None,
            "lockedAt": None,
            "userAuthorized": False,
            "authorizedAt": None,
        }
    else:
        direction_summary = dict(direction)
        if direction.get("status") == "pending":
            next_actions.append("lock-visual-direction")
        elif direction.get("status") == "locked":
            _verify_visual_direction(session_dir, state)
            if (
                state["contract"].get("checkpointMode") != "continuous"
                and not direction.get("userAuthorized")
            ):
                next_actions.append(
                    "authorize the locked visual direction with lock-visual-direction --user-authorized"
                )
    active = [
        output["id"]
        for output in state["outputs"]
        if output["status"] in {"generating", "reviewing", "awaiting-approval", "blocked"}
    ]
    if active:
        next_actions.append("resolve outputs: " + ", ".join(active))
    elif state["qualityGates"]["coverage"] != "pass":
        next_actions.append("settle required outputs and validate")
    if state["status"] == "awaiting-user-review":
        next_actions.append("accept-delivery or reject-delivery with the current delivery digest")
    handoff = {
        "sessionId": state["sessionId"],
        "revision": state["revision"],
        "status": state["status"],
        "contractId": state["contract"]["contractId"],
        "workflowProfile": state["contract"].get("workflowProfile", "standard"),
        "visualArtifactPolicy": state["contract"].get("visualArtifactPolicy"),
        "checkpointMode": state["contract"].get("checkpointMode"),
        "operationalMetadataPolicy": state["contract"].get(
            "operationalMetadataPolicy",
            default_operational_metadata_policy(),
        ),
        "visualDirection": direction_summary,
        "intentConfirmation": state["intentConfirmation"],
        "qualityGates": state["qualityGates"],
        "outputs": [
            {
                "id": output["id"],
                "status": output["status"],
                "sha256": output["sha256"],
                "userAuthorized": output["userAuthorized"],
                "provenance": output.get("provenance"),
                "visualDirectionSha256": output.get("visualDirectionSha256"),
            }
            for output in state["outputs"]
        ],
        "implementationStatus": state["implementation"]["status"],
        "deliveryReview": state["deliveryReview"],
        "lineage": state["lineage"],
        "provenanceBoundary": (
            "Receipt and trace integrity are verified; provider authenticity is not verified."
        ),
        "executionEnvelope": _execution_envelope(root, session_dir, state),
        "nextActions": next_actions,
    }
    if _is_v3_state(state):
        handoff.update(
            contractSha256=_canonical_sha256(state["contract"]),
            structure=state["contract"].get("structure"),
            renderBudget=state["contract"].get("renderBudget"),
            renderUsage=state.get("renderUsage"),
            implementationPlan={
                "path": state["implementation"].get("planPath"),
                "sha256": state["implementation"].get("planSha256"),
            },
        )
        for item, state_output in zip(handoff["outputs"], state["outputs"]):
            item.update(
                designEvidenceRequired=state_output["designEvidenceRequired"],
                runtimeEvidenceRequired=state_output["runtimeEvidenceRequired"],
                artifactKind=state_output["artifactKind"],
                anchorOutputId=state_output["anchorOutputId"],
                anchorArtifactSha256=state_output["anchorArtifactSha256"],
                renderBriefPath=state_output["renderBriefPath"],
                renderBriefSha256=state_output["renderBriefSha256"],
            )
    return handoff


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


def _full_design_gate_errors(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    direction_sha: str | None = None
    try:
        _require_confirmed_intent(state, session_dir)
    except StateError as exc:
        errors.append(str(exc))
    try:
        direction_sha = _verify_visual_direction(
            session_dir,
            state,
            require_authorized=(
                state["contract"].get("checkpointMode") != "continuous"
            ),
        )
    except StateError as exc:
        errors.append(str(exc))
    if state["status"] not in {"validated", "promoted"}:
        errors.append("session must be validated before implementation starts")
    contract_outputs = _contract_output_map(state["contract"])
    for output in state["outputs"]:
        contract_output = contract_outputs[output["id"]]
        if not _design_evidence_required(contract_output):
            continue
        status = output["status"]
        imagegen_requires_approval = (
            state["contract"].get("visualArtifactPolicy") == "imagegen-required"
        )
        checkpoint_requires_approval = state["contract"].get("checkpointMode") in {
            "review-each-stage",
            "review-before-implementation",
        }
        if imagegen_requires_approval and (
            status not in {"accepted", "promoted"} or not output.get("userAuthorized")
        ):
            errors.append(
                f"required imagegen output {output['id']} must be accepted and user-authorized"
            )
        elif checkpoint_requires_approval and (
            status not in {"accepted", "promoted"} or not output.get("userAuthorized")
        ):
            errors.append(
                f"required checkpoint output {output['id']} must be accepted and user-authorized"
            )
        if output["promotionRequired"]:
            if status != "promoted":
                errors.append(f"required design output {output['id']} must be promoted")
                continue
        elif status not in {"accepted", "promoted"}:
            errors.append(f"required design output {output['id']} must be accepted")
            continue

        if output.get("visualDirectionSha256") != direction_sha:
            errors.append(
                f"required design output {output['id']} is not bound to the locked visual direction"
            )

        artifact_error = _verify_output_artifact(session_dir, output)
        if artifact_error:
            errors.append(artifact_error)
        elif _is_v3_state(state):
            try:
                _verify_output_anchor(
                    session_dir,
                    state,
                    contract_output,
                    output,
                )
                _verify_output_render_brief(session_dir, state, output)
            except StateError as exc:
                errors.append(str(exc))
        if not artifact_error and _output_requires_imagegen_provenance(state, output["id"]):
            try:
                imagegen_artifact = artifact_path(session_dir, output["artifact"])
                validate_imagegen_artifact(state, imagegen_artifact, output["id"])
                provenance = output.get("provenance")
                verified_provenance = validate_imagegen_provenance(
                    session_dir,
                    state,
                    output["id"],
                    imagegen_artifact,
                    (
                        provenance.get("receiptPath")
                        if isinstance(provenance, dict)
                        else None
                    ),
                )
                if verified_provenance != provenance:
                    errors.append(
                        f"required imagegen output {output['id']} provenance state differs from verified receipt"
                    )
            except StateError as exc:
                errors.append(f"required imagegen output {output['id']}: {exc}")
        if status == "promoted":
            promotion_error = _verify_promoted_destination(root, state, output)
            if promotion_error:
                errors.append(promotion_error)
    return errors


def _effective_implementation_targets(
    state: dict[str, Any],
    supplied_targets: list[str] | None,
) -> list[str]:
    predeclared = _contract_implementation_target_paths(state["contract"])
    if _is_v3_state(state):
        if supplied_targets:
            raise StateError(
                "SchemaVersion 3 implementation targets come only from the bound implementation plan"
            )
        if supplied_targets == []:
            raise StateError(
                "SchemaVersion 3 does not accept --implementation-target; use --implementation-plan"
            )
        if not predeclared:
            raise StateError("Durable implementation requires a non-empty implementation target set")
        return list(predeclared)
    if supplied_targets is None:
        effective = list(predeclared)
    else:
        if not supplied_targets:
            raise StateError("Durable implementation requires a non-empty implementation target set")
        effective = []
        seen: set[str] = set()
        for index, target in enumerate(supplied_targets):
            label = f"implementation target {index + 1}"
            if not isinstance(target, str):
                raise StateError(f"{label} must be a string")
            _implementation_relative_path(target, label)
            if target in seen:
                raise StateError(f"Duplicate implementation target: {target}")
            seen.add(target)
            effective.append(target)
        if predeclared and effective != predeclared:
            raise StateError(
                "Explicit implementation targets conflict with predeclared contract targets"
            )
    if not effective:
        raise StateError("Durable implementation requires a non-empty implementation target set")
    return effective


def _capture_target_fingerprints(
    root: Path,
    targets: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "path": target,
            "baselineSha256": implementation_target_sha256(root, target),
            "completionSha256": None,
        }
        for target in targets
    ]


def implementation_snapshot_sha256(root: Path, state: dict[str, Any]) -> str:
    root = root.expanduser().resolve()
    fingerprints = state.get("implementation", {}).get("targetFingerprints")
    if (
        not isinstance(fingerprints, list)
        or not fingerprints
        or any(not isinstance(item, dict) for item in fingerprints)
    ):
        raise StateError("implementation snapshot requires declared target fingerprints")
    targets: list[dict[str, Any]] = []
    for fingerprint in fingerprints:
        target = fingerprint.get("path")
        if not isinstance(target, str):
            raise StateError("implementation snapshot contains an invalid target path")
        targets.append(
            {
                "path": target,
                "sha256": implementation_target_sha256(root, target),
            }
        )
    return _canonical_sha256(
        {
            "contractSha256": _canonical_sha256(state["contract"]),
            "implementationPlanSha256": state.get("implementation", {}).get(
                "planSha256"
            ),
            "targets": targets,
        }
    )


def _implementation_change_errors(
    root: Path,
    state: dict[str, Any],
    session_dir: Path | None = None,
) -> list[str]:
    implementation = state["implementation"]
    fingerprints = implementation.get("targetFingerprints", [])
    predeclared = _contract_implementation_target_paths(state["contract"])
    if (
        not isinstance(fingerprints, list)
        or not fingerprints
        or any(not isinstance(item, dict) for item in fingerprints)
    ):
        return ["implementation target baselines are missing or do not match the contract"]
    fingerprint_paths = [
        item.get("path") for item in fingerprints
    ]
    if predeclared and fingerprint_paths != predeclared:
        return ["implementation target baselines conflict with predeclared contract targets"]

    errors: list[str] = []
    if _is_v3_state(state):
        if session_dir is None:
            errors.append("schemaVersion 3 implementation plan cannot be verified")
        else:
            try:
                _verify_implementation_plan(session_dir, state)
            except StateError as exc:
                errors.append(str(exc))
    changed_targets: list[str] = []
    for fingerprint in fingerprints:
        target = fingerprint["path"]
        try:
            completion_sha = implementation_target_sha256(root, target)
        except StateError as exc:
            errors.append(f"implementation target {target}: {exc}")
            continue
        fingerprint["completionSha256"] = completion_sha
        if completion_sha is not None and completion_sha != fingerprint.get("baselineSha256"):
            changed_targets.append(target)
    if not changed_targets:
        errors.append("no declared implementation target changed after begin-implementation")
    return errors


def begin_implementation(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    *,
    implementation_targets: list[str] | None = None,
    implementation_plan_file: str | Path | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    implementation = state["implementation"]
    if implementation["status"] == "completed":
        raise StateError("Implementation is already completed")
    if implementation["status"] == "in-progress":
        if implementation_targets is not None:
            effective_targets = _effective_implementation_targets(
                state,
                implementation_targets,
            )
            persisted_targets = [
                item["path"] for item in implementation.get("targetFingerprints", [])
            ]
            if effective_targets != persisted_targets:
                raise StateError(
                    "Explicit implementation targets conflict with the active implementation"
                )
        if _is_v3_state(state):
            _verify_implementation_plan(session_dir, state)
        return state

    profile = state["contract"].get("workflowProfile", "standard")
    errors: list[str] = []
    target_fingerprints: list[dict[str, Any]] = []
    validated_plan_source: str | Path | None = None
    if profile == "standard":
        if state["status"] not in {"validated", "promoted"}:
            errors.append("standard workflow requires a validated session")
        try:
            direction_sha = _verify_visual_direction(
                session_dir,
                state,
                require_authorized=(
                    state["contract"].get("checkpointMode") != "continuous"
                ),
            )
            for output in state["outputs"]:
                if (
                    _state_design_evidence_required(output)
                    and output["status"] in {"accepted", "promoted"}
                    and output.get("visualDirectionSha256") != direction_sha
                ):
                    errors.append(
                        f"required design output {output['id']} is not bound to the locked visual direction"
                    )
        except StateError as exc:
            errors.append(str(exc))
        try:
            effective_targets = _effective_implementation_targets(
                state,
                implementation_targets,
            )
            target_fingerprints = _capture_target_fingerprints(root, effective_targets)
        except StateError as exc:
            errors.append(
                "standard durable implementation requires explicit affected targets: "
                + str(exc)
            )
        if implementation_plan_file is not None:
            errors.append("--implementation-plan is supported only for schemaVersion 3 full workflows")
    elif profile == "full":
        errors.extend(_full_design_gate_errors(root, session_dir, state))
        if _is_v3_state(state):
            if implementation_plan_file is None:
                errors.append(
                    "schemaVersion 3 full implementation requires an implementation plan"
                )
            else:
                try:
                    candidate_plan = load_json(
                        Path(implementation_plan_file).expanduser().resolve(),
                        "implementation plan",
                    )
                    plan_errors = validate_implementation_plan(
                        state["contract"],
                        candidate_plan,
                    )
                    plan_errors.extend(
                        validate_implementation_plan_repo_evidence(
                            root,
                            candidate_plan,
                            session_dir,
                        )
                    )
                    if plan_errors:
                        errors.extend(plan_errors)
                    else:
                        validated_plan_source = implementation_plan_file
                except StateError as exc:
                    errors.append(str(exc))
        elif implementation_plan_file is not None:
            errors.append("--implementation-plan requires schemaVersion 3")
        try:
            effective_targets = _effective_implementation_targets(
                state,
                implementation_targets,
            )
            target_fingerprints = _capture_target_fingerprints(root, effective_targets)
        except StateError as exc:
            errors.append(str(exc))
    if errors:
        raise StateError("Implementation gate failed: " + "; ".join(errors))

    if _is_v3_state(state):
        plan_path, plan_sha = _store_implementation_plan(
            session_dir,
            state["contract"],
            validated_plan_source,
        )
        implementation["planPath"] = plan_path
        implementation["planSha256"] = plan_sha

    implementation["status"] = "in-progress"
    implementation["startedAt"] = utc_now()
    implementation["completedAt"] = None
    implementation["targetFingerprints"] = target_fingerprints
    return _commit_state(session_dir, state)


def _validate_runtime_probe(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
    output: dict[str, Any],
    manifest_path: Path,
    runtime_probe: dict[str, Any],
    *,
    result: str,
    screenshot_path: str | None,
    screenshot_sha256: str | None,
    pixel_width: int | None,
    pixel_height: int | None,
) -> None:
    errors: list[str] = []
    _unknown_keys(
        runtime_probe,
        {"path", "sha256"},
        "fidelity QA manifest.runtimeProbe",
        errors,
    )
    probe_value = runtime_probe.get("path")
    declared_probe_sha = runtime_probe.get("sha256")
    if not isinstance(probe_value, str):
        errors.append("manifest.runtimeProbe.path must be a string")
    if (
        not isinstance(declared_probe_sha, str)
        or HASH_RE.fullmatch(declared_probe_sha) is None
    ):
        errors.append("manifest.runtimeProbe.sha256 is invalid")
    if errors:
        raise StateError("Invalid runtime probe: " + "; ".join(errors))

    probe_path = qa_evidence_path(session_dir, probe_value)
    if probe_path == manifest_path:
        errors.append("runtime probe and fidelity manifest must be distinct files")
    if probe_path.suffix.lower() != ".json":
        errors.append("runtime probe must be a JSON file under qa/")
    actual_probe_sha = sha256_file(probe_path)
    if actual_probe_sha != declared_probe_sha:
        errors.append("manifest.runtimeProbe.sha256 does not match runtime probe bytes")
    trace = load_json(probe_path, "runtime probe")
    _unknown_keys(
        trace,
        {
            "schemaVersion",
            "producer",
            "adapter",
            "adapterVersion",
            "generatedAt",
            "specPath",
            "specSha256",
            "implementationSnapshotSha256",
            "outputId",
            "route",
            "state",
            "viewport",
            "scrollPosition",
            "directNavigation",
            "page",
            "stateVerification",
            "scroll",
            "runtimeHealth",
            "accessibility",
            "interactions",
            "screenshot",
            "verdict",
            "reason",
        },
        "runtime probe",
        errors,
    )
    if trace.get("schemaVersion") != 1:
        errors.append("runtime probe.schemaVersion must be 1")
    if trace.get("producer") != "frontend-workbench/browser-runtime-probe":
        errors.append("runtime probe.producer is not the canonical helper")
    if trace.get("adapter") != "agent-browser":
        errors.append("runtime probe.adapter must be agent-browser")
    if not isinstance(trace.get("adapterVersion"), str) or not trace["adapterVersion"].strip():
        errors.append("runtime probe.adapterVersion must be non-empty")
    if not isinstance(trace.get("generatedAt"), str) or not trace["generatedAt"].strip():
        errors.append("runtime probe.generatedAt must be non-empty")
    else:
        try:
            datetime.fromisoformat(trace["generatedAt"].replace("Z", "+00:00"))
        except ValueError:
            errors.append("runtime probe.generatedAt must be an ISO-8601 timestamp")
    if trace.get("outputId") != output["id"]:
        errors.append("runtime probe.outputId does not match the requested output")

    contract_output = _contract_output_map(state["contract"])[output["id"]]
    surface = next(
        item
        for item in state["contract"]["surfaces"]
        if item["id"] == contract_output["surfaceId"]
    )
    expected_route = surface.get("route")
    expected_state = contract_output["state"]
    expected_viewport = contract_output["viewport"]
    expected_scroll_position = contract_output.get("scrollPosition", "top")
    expected_implementation_snapshot = implementation_snapshot_sha256(root, state)
    if trace.get("route") != expected_route:
        errors.append("runtime probe.route does not match the covered surface")
    if trace.get("state") != expected_state:
        errors.append("runtime probe.state does not match the covered output")
    if trace.get("viewport") != expected_viewport:
        errors.append("runtime probe.viewport does not match the covered output")
    if trace.get("scrollPosition") != expected_scroll_position:
        errors.append("runtime probe.scrollPosition does not match the covered output")
    if trace.get("implementationSnapshotSha256") != expected_implementation_snapshot:
        errors.append("runtime probe is not bound to the current implementation snapshot")
    if trace.get("directNavigation") is not True:
        errors.append("runtime probe must navigate directly to the target URL")

    spec_value = trace.get("specPath")
    spec_sha = trace.get("specSha256")
    probe_spec: dict[str, Any] = {}
    if not isinstance(spec_value, str):
        errors.append("runtime probe.specPath must be a string")
    if not isinstance(spec_sha, str) or HASH_RE.fullmatch(spec_sha) is None:
        errors.append("runtime probe.specSha256 is invalid")
    if isinstance(spec_value, str):
        try:
            spec_path = qa_evidence_path(session_dir, spec_value)
            if spec_path.suffix.lower() != ".json":
                errors.append("runtime probe spec must be JSON")
            if spec_path in {manifest_path, probe_path}:
                errors.append("runtime probe spec must be distinct from trace and manifest")
            if sha256_file(spec_path) != spec_sha:
                errors.append("runtime probe.specSha256 does not match spec bytes")
            probe_spec = load_json(spec_path, "runtime probe spec")
            if probe_spec.get("outputId") != output["id"]:
                errors.append("runtime probe spec.outputId does not match the output")
            if probe_spec.get("route") != expected_route:
                errors.append("runtime probe spec.route does not match the surface")
            if probe_spec.get("state") != expected_state:
                errors.append("runtime probe spec.state does not match the output")
            if probe_spec.get("scrollPosition") != expected_scroll_position:
                errors.append("runtime probe spec.scrollPosition does not match the output")
            if probe_spec.get("implementationSnapshotSha256") != expected_implementation_snapshot:
                errors.append(
                    "runtime probe spec is not bound to the current implementation snapshot"
                )
            spec_viewport = probe_spec.get("viewport")
            if not isinstance(spec_viewport, dict) or spec_viewport.get("label") != expected_viewport:
                errors.append("runtime probe spec.viewport does not match the output")
            if probe_spec.get("tracePath") != probe_value:
                errors.append("runtime probe spec.tracePath does not match the trace")
            if probe_spec.get("screenshotPath") != screenshot_path:
                errors.append("runtime probe spec.screenshotPath does not match the manifest")
        except StateError as exc:
            errors.append(str(exc))

    verdict = trace.get("verdict")
    if verdict not in FIDELITY_RESULTS:
        errors.append("runtime probe.verdict is invalid")
    if result == "pass" and verdict != "pass":
        errors.append("PASS fidelity manifest requires a PASS runtime probe")
    if verdict in {"fail", "blocked"} and (
        not isinstance(trace.get("reason"), str) or not trace["reason"].strip()
    ):
        errors.append("FAIL/BLOCKED runtime probe requires a reason")

    page = trace.get("page")
    if not isinstance(page, dict):
        errors.append("runtime probe.page must be an object")
        page = {}
    else:
        _unknown_keys(
            page,
            {
                "finalUrl",
                "title",
                "rootSelector",
                "rootFound",
                "rootIsDocumentShell",
                "rootVisible",
                "rootEffectiveOpacity",
                "rootViewportIntersectionPixels",
                "rootChildElementCount",
                "visibleTextCharacters",
                "visibleLandmarkCount",
                "interactiveElementCount",
                "rootWidth",
                "rootHeight",
            },
            "runtime probe.page",
            errors,
        )
    final_url = page.get("finalUrl")
    title = page.get("title")
    root_selector = page.get("rootSelector")
    if not isinstance(final_url, str) or not final_url.strip():
        errors.append("runtime probe.page.finalUrl must be non-empty")
    elif probe_spec and final_url != probe_spec.get("url"):
        errors.append("runtime probe.page.finalUrl does not match the exact probe URL")
    elif (
        isinstance(expected_route, str)
        and expected_route.startswith("/")
        and not any(marker in expected_route for marker in (":", "*", "{", "["))
        and urlsplit(final_url).path != expected_route
    ):
        errors.append("runtime probe.page.finalUrl path does not match the covered route")
    if not isinstance(title, str):
        errors.append("runtime probe.page.title must be a string")
    if not isinstance(root_selector, str) or not root_selector.strip():
        errors.append("runtime probe.page.rootSelector must be non-empty")
    elif (
        root_selector.strip().casefold() in {"html", "body", ":root", "*"}
        or re.search(
            r"(^|[\s,>+~:(])(?:html|body)(?=$|[\s,>+~.#\[:)])",
            root_selector,
            flags=re.IGNORECASE,
        )
    ):
        errors.append("runtime probe app root cannot be the document shell")
    if probe_spec and root_selector != probe_spec.get("rootSelector"):
        errors.append("runtime probe.page.rootSelector differs from the probe spec")
    if not isinstance(page.get("rootIsDocumentShell"), bool):
        errors.append("runtime probe.page.rootIsDocumentShell must be a boolean")
    if not isinstance(page.get("rootVisible"), bool):
        errors.append("runtime probe.page.rootVisible must be a boolean")

    if result == "pass":
        if not isinstance(title, str) or not title.strip():
            errors.append("PASS runtime probe requires a non-empty page title")
        if page.get("rootFound") is not True:
            errors.append("PASS runtime probe did not find the declared app root")
        if page.get("rootIsDocumentShell") is not False:
            errors.append("PASS runtime probe app root resolves to the document shell")
        if page.get("rootVisible") is not True:
            errors.append("PASS runtime probe app root is not visibly intersecting the viewport")
        numeric_minimums = {
            "rootChildElementCount": 1,
            "visibleTextCharacters": 8,
            "rootWidth": 0,
            "rootHeight": 0,
            "rootEffectiveOpacity": 0.05,
            "rootViewportIntersectionPixels": 0,
        }
        for field, minimum in numeric_minimums.items():
            value = page.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"runtime probe.page.{field} must be numeric")
            elif field in {
                "rootWidth",
                "rootHeight",
                "rootEffectiveOpacity",
                "rootViewportIntersectionPixels",
            } and value <= minimum:
                errors.append(f"PASS runtime probe.page.{field} must be positive")
            elif field not in {"rootWidth", "rootHeight"} and value < minimum:
                errors.append(
                    f"PASS runtime probe.page.{field} must be at least {minimum}"
                )
        landmark_count = page.get("visibleLandmarkCount")
        interactive_count = page.get("interactiveElementCount")
        if (
            not isinstance(landmark_count, int)
            or isinstance(landmark_count, bool)
            or landmark_count < 0
            or not isinstance(interactive_count, int)
            or isinstance(interactive_count, bool)
            or interactive_count < 0
        ):
            errors.append("runtime probe semantic counts must be non-negative integers")
        elif landmark_count + interactive_count < 1:
            errors.append("PASS runtime probe requires a landmark or interactive element")

    state_verification = trace.get("stateVerification")
    if not isinstance(state_verification, dict):
        errors.append("runtime probe.stateVerification must be an object")
    else:
        _unknown_keys(
            state_verification,
            {"id", "kind", "result", "observed"},
            "runtime probe.stateVerification",
            errors,
        )
        for field in ("id", "kind", "observed"):
            value = state_verification.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"runtime probe.stateVerification.{field} must be non-empty")
        if state_verification.get("result") not in {"pass", "fail"}:
            errors.append("runtime probe.stateVerification.result is invalid")
        elif result == "pass" and state_verification["result"] != "pass":
            errors.append("PASS runtime probe requires a passing stateVerification")
        spec_state_assertion = probe_spec.get("stateAssertion") if probe_spec else None
        if isinstance(spec_state_assertion, dict) and (
            state_verification.get("id") != spec_state_assertion.get("id")
            or state_verification.get("kind") != spec_state_assertion.get("kind")
        ):
            errors.append("runtime probe.stateVerification differs from the probe spec")

    scroll = trace.get("scroll")
    if not isinstance(scroll, dict):
        errors.append("runtime probe.scroll must be an object")
    else:
        _unknown_keys(
            scroll,
            {"kind", "x", "y", "maxY", "verified", "captureFullPage"},
            "runtime probe.scroll",
            errors,
        )
        scroll_kind = scroll.get("kind")
        if scroll_kind not in {"top", "bottom", "full-page", "selector"}:
            errors.append("runtime probe.scroll.kind is invalid")
        if expected_scroll_position in {"top", "bottom", "full-page"} and (
            scroll_kind != expected_scroll_position
        ):
            errors.append("runtime probe.scroll.kind does not match scrollPosition")
        spec_scroll = probe_spec.get("scroll") if probe_spec else None
        if isinstance(spec_scroll, dict) and scroll_kind != spec_scroll.get("kind"):
            errors.append("runtime probe.scroll.kind differs from the probe spec")
        for field in ("x", "y", "maxY"):
            value = scroll.get(field)
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value < 0
            ):
                errors.append(f"runtime probe.scroll.{field} must be non-negative")
        if not isinstance(scroll.get("verified"), bool):
            errors.append("runtime probe.scroll.verified must be a boolean")
        elif result == "pass" and scroll["verified"] is not True:
            errors.append("PASS runtime probe requires verified scroll position")
        if not isinstance(scroll.get("captureFullPage"), bool):
            errors.append("runtime probe.scroll.captureFullPage must be a boolean")
        elif expected_scroll_position == "full-page" and scroll["captureFullPage"] is not True:
            errors.append("full-page runtime probe requires full-page capture")

    runtime_health = trace.get("runtimeHealth")
    if not isinstance(runtime_health, dict):
        errors.append("runtime probe.runtimeHealth must be an object")
        runtime_health = {}
    else:
        _unknown_keys(
            runtime_health,
            {"consoleErrors", "pageErrors", "failedRequests"},
            "runtime probe.runtimeHealth",
            errors,
        )
    for field in ("consoleErrors", "pageErrors", "failedRequests"):
        value = runtime_health.get(field)
        if not isinstance(value, list):
            errors.append(f"runtime probe.runtimeHealth.{field} must be an array")
        elif result == "pass" and value:
            errors.append(f"PASS runtime probe requires empty runtimeHealth.{field}")

    accessibility = trace.get("accessibility")
    if not isinstance(accessibility, dict):
        errors.append("runtime probe.accessibility must be an object")
        accessibility = {}
    else:
        _unknown_keys(
            accessibility,
            {"criticalViolations", "seriousViolations", "otherViolations"},
            "runtime probe.accessibility",
            errors,
        )
    for field in ("criticalViolations", "seriousViolations"):
        value = accessibility.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"runtime probe.accessibility.{field} must be a non-negative integer")
        elif result == "pass" and value != 0:
            errors.append(f"PASS runtime probe requires zero accessibility.{field}")
    if not isinstance(accessibility.get("otherViolations"), list):
        errors.append("runtime probe.accessibility.otherViolations must be an array")

    interactions = trace.get("interactions")
    if not isinstance(interactions, list):
        errors.append("runtime probe.interactions must be an array")
        interactions = []
    if result == "pass" and not interactions:
        errors.append("PASS runtime probe requires a target interaction")
    spec_interactions = probe_spec.get("interactions") if probe_spec else None
    if isinstance(spec_interactions, list):
        trace_ids = [
            item.get("id") for item in interactions if isinstance(item, dict)
        ]
        spec_ids = [
            item.get("id") for item in spec_interactions if isinstance(item, dict)
        ]
        if trace_ids != spec_ids:
            errors.append("runtime probe interactions differ from the probe spec")
    interaction_ids: set[str] = set()
    for index, interaction in enumerate(interactions):
        label = f"runtime probe.interactions[{index}]"
        if not isinstance(interaction, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(
            interaction,
            {
                "id",
                "action",
                "beforeSha256",
                "afterSha256",
                "stateChanged",
                "assertions",
                "result",
            },
            label,
            errors,
        )
        interaction_id = interaction.get("id")
        if not isinstance(interaction_id, str) or ID_RE.fullmatch(interaction_id) is None:
            errors.append(f"{label}.id is invalid")
        elif interaction_id in interaction_ids:
            errors.append(f"{label}.id is duplicated")
        else:
            interaction_ids.add(interaction_id)
        if not isinstance(interaction.get("action"), str) or not interaction["action"].strip():
            errors.append(f"{label}.action must be non-empty")
        for field in ("beforeSha256", "afterSha256"):
            value = interaction.get(field)
            if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
                errors.append(f"{label}.{field} is invalid")
        state_changed = interaction.get("stateChanged")
        if not isinstance(state_changed, bool):
            errors.append(f"{label}.stateChanged must be a boolean")
        elif result == "pass" and state_changed is not True:
            errors.append(f"PASS runtime probe requires {label}.stateChanged true")
        if (
            isinstance(interaction.get("beforeSha256"), str)
            and interaction.get("beforeSha256") == interaction.get("afterSha256")
        ):
            errors.append(f"{label} before/after state fingerprints must differ")
        if interaction.get("result") not in {"pass", "fail"}:
            errors.append(f"{label}.result is invalid")
        elif result == "pass" and interaction["result"] != "pass":
            errors.append(f"PASS runtime probe requires {label}.result pass")
        assertions = interaction.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(f"{label}.assertions must be non-empty")
            continue
        for assertion_index, assertion in enumerate(assertions):
            assertion_label = f"{label}.assertions[{assertion_index}]"
            if not isinstance(assertion, dict):
                errors.append(f"{assertion_label} must be an object")
                continue
            _unknown_keys(
                assertion,
                {"id", "kind", "result", "observed"},
                assertion_label,
                errors,
            )
            for field in ("id", "kind", "observed"):
                value = assertion.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{assertion_label}.{field} must be non-empty")
            if assertion.get("result") not in {"pass", "fail"}:
                errors.append(f"{assertion_label}.result is invalid")
            elif result == "pass" and assertion["result"] != "pass":
                errors.append(f"PASS runtime probe requires {assertion_label}.result pass")

    trace_screenshot = trace.get("screenshot")
    if not isinstance(trace_screenshot, dict):
        errors.append("runtime probe.screenshot must be an object")
    else:
        _unknown_keys(
            trace_screenshot,
            {"path", "sha256", "pixelWidth", "pixelHeight"},
            "runtime probe.screenshot",
            errors,
        )
        expected_screenshot = {
            "path": screenshot_path,
            "sha256": screenshot_sha256,
            "pixelWidth": pixel_width,
            "pixelHeight": pixel_height,
        }
        for field, expected in expected_screenshot.items():
            if trace_screenshot.get(field) != expected:
                errors.append(
                    f"runtime probe.screenshot.{field} does not match the fidelity manifest"
                )
        if result == "pass" and (
            not isinstance(pixel_width, int)
            or pixel_width < 320
            or not isinstance(pixel_height, int)
            or pixel_height < 200
        ):
            errors.append("PASS runtime screenshot must be at least 320x200 pixels")

    if errors:
        raise StateError("Invalid runtime probe: " + "; ".join(errors))


def _validate_fidelity_manifest(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
    output: dict[str, Any],
    manifest_value: str,
    accepted_artifact_sha256: str | None,
    result: str,
) -> dict[str, Any]:
    manifest_path = qa_evidence_path(session_dir, manifest_value)
    manifest_sha256 = sha256_file(manifest_path)
    accepted_design_hashes = {
        item["sha256"]
        for item in state["outputs"]
        if item["status"] in {"accepted", "promoted"}
        and isinstance(item.get("sha256"), str)
    }
    if manifest_sha256 in accepted_design_hashes:
        raise StateError("Fidelity QA evidence cannot reuse an accepted design artifact digest")
    if manifest_path.suffix.lower() != ".json":
        raise StateError("Fidelity QA evidence must be a JSON manifest under qa/")
    manifest = load_json(manifest_path, "fidelity QA manifest")
    errors: list[str] = []
    v3_state = _is_v3_state(state)
    _unknown_keys(
        manifest,
        {
            "outputId",
            "acceptedArtifactSha256",
            "result",
            "route",
            "state",
            "viewport",
            "scrollPosition",
            "pixelWidth",
            "pixelHeight",
            "evidenceEquivalentTo",
            "equivalenceJustification",
            "screenshot",
            "runtimeProbe",
            "reason",
            *( {"comparisonMode", "visualDirectionSha256", "implementationPlanSha256"} if v3_state else set() ),
        },
        "fidelity QA manifest",
        errors,
    )
    if manifest.get("outputId") != output["id"]:
        errors.append("manifest.outputId does not match the requested output")
    if manifest.get("acceptedArtifactSha256") != accepted_artifact_sha256:
        errors.append("manifest.acceptedArtifactSha256 does not match the accepted artifact")
    if manifest.get("result") != result:
        errors.append("manifest.result does not match --result")

    contract_output = next(
        item for item in state["contract"]["outputs"] if item["id"] == output["id"]
    )
    direction_sha = _verify_visual_direction(session_dir, state)
    if v3_state:
        expected_mode = (
            "accepted-design"
            if _design_evidence_required(contract_output)
            else "direction-only"
        )
        if manifest.get("comparisonMode") != expected_mode:
            errors.append(
                f"manifest.comparisonMode must be {expected_mode!r} for this output"
            )
        if manifest.get("visualDirectionSha256") != direction_sha:
            errors.append(
                "manifest.visualDirectionSha256 does not match the locked direction"
            )
        if manifest.get("implementationPlanSha256") != state.get(
            "implementation", {}
        ).get("planSha256"):
            errors.append(
                "manifest.implementationPlanSha256 does not match the active implementation plan"
            )
        if expected_mode == "direction-only" and accepted_artifact_sha256 is not None:
            errors.append(
                "direction-only manifest acceptedArtifactSha256 must be null"
            )
        if expected_mode == "accepted-design" and not isinstance(
            accepted_artifact_sha256, str
        ):
            errors.append(
                "accepted-design manifest requires acceptedArtifactSha256"
            )
    surface = next(
        item
        for item in state["contract"]["surfaces"]
        if item["id"] == contract_output["surfaceId"]
    )
    route = manifest.get("route")
    covered_state = manifest.get("state")
    viewport = manifest.get("viewport")
    scroll_position = manifest.get("scrollPosition")
    if not isinstance(route, str) or not route.strip():
        errors.append("manifest.route must be a non-empty string")
    elif isinstance(surface.get("route"), str) and route != surface["route"]:
        errors.append("manifest.route does not match the covered surface")
    if not isinstance(covered_state, str) or not covered_state.strip():
        errors.append("manifest.state must be a non-empty string")
    elif covered_state != contract_output["state"]:
        errors.append("manifest.state does not match the covered output")
    if not isinstance(viewport, str) or not viewport.strip():
        errors.append("manifest.viewport must be a non-empty string")
    elif viewport != contract_output["viewport"]:
        errors.append("manifest.viewport does not match the covered output")
    expected_scroll_position = contract_output.get("scrollPosition", "top")
    if not isinstance(scroll_position, str) or not scroll_position.strip():
        errors.append("manifest.scrollPosition must be a non-empty string")
    elif scroll_position != expected_scroll_position:
        errors.append("manifest.scrollPosition does not match the covered output")

    pixel_width = manifest.get("pixelWidth")
    pixel_height = manifest.get("pixelHeight")
    evidence_equivalent_to = manifest.get("evidenceEquivalentTo")
    equivalence_justification = manifest.get("equivalenceJustification")
    if (evidence_equivalent_to is None) != (equivalence_justification is None):
        errors.append(
            "manifest evidenceEquivalentTo and equivalenceJustification must be provided together"
        )
    elif evidence_equivalent_to is not None:
        if (
            evidence_equivalent_to != contract_output.get("evidenceEquivalentTo")
            or equivalence_justification
            != contract_output.get("equivalenceJustification")
        ):
            errors.append(
                "manifest equivalence does not match the lifecycle-confirmed contract"
            )

    reason = manifest.get("reason")
    if reason is not None and (not isinstance(reason, str) or not reason.strip()):
        errors.append("manifest.reason must be a non-empty string when present")

    screenshot = manifest.get("screenshot")
    screenshot_value: str | None = None
    screenshot_sha256: str | None = None
    if screenshot is None:
        if result == "pass":
            errors.append("PASS fidelity manifest requires a screenshot")
        elif not isinstance(reason, str) or not reason.strip():
            errors.append("FAIL/BLOCKED fidelity manifest without screenshot requires a reason")
        if pixel_width is not None or pixel_height is not None:
            errors.append("manifest pixel dimensions must be null without a screenshot")
    elif not isinstance(screenshot, dict):
        errors.append("manifest.screenshot must be an object")
    else:
        _unknown_keys(
            screenshot,
            {"path", "sha256"},
            "fidelity QA manifest.screenshot",
            errors,
        )
        screenshot_value = screenshot.get("path")
        declared_screenshot_sha = screenshot.get("sha256")
        if not isinstance(screenshot_value, str):
            errors.append("manifest.screenshot.path must be a string")
        if (
            not isinstance(declared_screenshot_sha, str)
            or HASH_RE.fullmatch(declared_screenshot_sha) is None
        ):
            errors.append("manifest.screenshot.sha256 is invalid")
        if isinstance(screenshot_value, str):
            try:
                screenshot_path = qa_evidence_path(session_dir, screenshot_value)
                if screenshot_path == manifest_path:
                    errors.append("manifest and screenshot must be distinct files")
                screenshot_sha256 = sha256_file(screenshot_path)
                if screenshot_sha256 != declared_screenshot_sha:
                    errors.append("manifest.screenshot.sha256 does not match screenshot bytes")
                if screenshot_sha256 in accepted_design_hashes:
                    errors.append("QA screenshot bytes match an accepted design artifact")
                actual_width, actual_height = validate_screenshot_file(screenshot_path)
                if (
                    not isinstance(pixel_width, int)
                    or isinstance(pixel_width, bool)
                    or pixel_width < 1
                ):
                    errors.append("manifest.pixelWidth must be a positive integer")
                elif pixel_width != actual_width:
                    errors.append("manifest.pixelWidth does not match the actual screenshot")
                if (
                    not isinstance(pixel_height, int)
                    or isinstance(pixel_height, bool)
                    or pixel_height < 1
                ):
                    errors.append("manifest.pixelHeight must be a positive integer")
                elif pixel_height != actual_height:
                    errors.append("manifest.pixelHeight does not match the actual screenshot")
                latest_receipts: dict[str, dict[str, Any]] = {}
                for receipt in state["implementation"]["fidelityQaReceipts"]:
                    latest_receipts[receipt["outputId"]] = receipt
                duplicates = sorted(
                    receipt["outputId"]
                    for receipt in latest_receipts.values()
                    if receipt.get("screenshotSha256") == screenshot_sha256
                    and receipt.get("outputId") != output["id"]
                )
                if duplicates:
                    if duplicates != [evidence_equivalent_to]:
                        errors.append(
                            "duplicate screenshot SHA requires an exact lifecycle-confirmed evidence-equivalent output pair"
                        )
                elif evidence_equivalent_to is not None:
                    errors.append(
                        "manifest declares evidence equivalence but screenshot SHA is not duplicated by that output"
                    )
            except StateError as exc:
                errors.append(str(exc))

    runtime_probe = manifest.get("runtimeProbe")
    if runtime_probe is None:
        if result == "pass":
            errors.append("PASS fidelity manifest requires a browser runtime probe")
    elif not isinstance(runtime_probe, dict):
        errors.append("manifest.runtimeProbe must be an object")
    else:
        try:
            _validate_runtime_probe(
                root,
                session_dir,
                state,
                output,
                manifest_path,
                runtime_probe,
                result=result,
                screenshot_path=screenshot_value,
                screenshot_sha256=screenshot_sha256,
                pixel_width=pixel_width,
                pixel_height=pixel_height,
            )
        except StateError as exc:
            errors.append(str(exc))

    if errors:
        raise StateError("Invalid fidelity QA manifest: " + "; ".join(errors))
    receipt = {
        "outputId": output["id"],
        "acceptedArtifactSha256": accepted_artifact_sha256,
        "manifestPath": manifest_value,
        "manifestSha256": manifest_sha256,
        "screenshotPath": screenshot_value,
        "screenshotSha256": screenshot_sha256,
        "result": result,
        "route": route,
        "state": covered_state,
        "viewport": viewport,
        "scrollPosition": scroll_position,
        "pixelWidth": pixel_width,
        "pixelHeight": pixel_height,
        "evidenceEquivalentTo": evidence_equivalent_to,
        "equivalenceJustification": equivalence_justification,
        "reason": reason,
    }
    if v3_state:
        receipt.update(
            comparisonMode=manifest.get("comparisonMode"),
            visualDirectionSha256=manifest.get("visualDirectionSha256"),
            implementationPlanSha256=manifest.get("implementationPlanSha256"),
        )
    return receipt


def _record_fidelity_qa(
    root_value: str | Path,
    session_id: str,
    output_id: str,
    expected_revision: int,
    *,
    accepted_artifact_sha256: str | None,
    evidence_artifact: str,
    result: str,
    _canonical_probe_executed: bool,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    implementation = state["implementation"]
    if implementation["status"] != "in-progress":
        raise StateError("Fidelity QA can be recorded only while implementation is in progress")
    if not isinstance(result, str) or result not in FIDELITY_RESULTS:
        raise StateError("Fidelity QA result must be pass, fail, or blocked")
    if result == "pass" and not _canonical_probe_executed:
        raise StateError(
            "PASS runtime evidence must be captured and recorded atomically through run-runtime-qa"
        )
    if (
        not _is_v3_state(state)
        and (
            not isinstance(accepted_artifact_sha256, str)
            or HASH_RE.fullmatch(accepted_artifact_sha256) is None
        )
    ):
        raise StateError("--accepted-artifact-sha256 must be a lowercase SHA-256 digest")

    output = _state_output_map(state).get(output_id)
    if output is None:
        raise StateError(f"Unknown output ID: {output_id}")
    contract_output = _contract_output_map(state["contract"])[output_id]
    direction_sha = _verify_visual_direction(session_dir, state)
    if _design_evidence_required(contract_output):
        if output["status"] not in {"accepted", "promoted"}:
            raise StateError("Fidelity QA requires an accepted or promoted design output")
        if output.get("visualDirectionSha256") != direction_sha:
            raise StateError(
                "Fidelity QA output is not bound to the locked visual direction"
            )
        if output.get("sha256") != accepted_artifact_sha256:
            raise StateError("Fidelity QA digest does not match the accepted artifact")
        artifact_error = _verify_output_artifact(session_dir, output)
        if artifact_error:
            raise StateError(artifact_error)
        if output["status"] == "promoted":
            promotion_error = _verify_promoted_destination(root, state, output)
            if promotion_error:
                raise StateError(promotion_error)
    else:
        if not _is_v3_state(state):
            raise StateError("Direction-only fidelity QA requires schemaVersion 3")
        if accepted_artifact_sha256 is not None:
            raise StateError(
                "Direction-only fidelity QA requires null accepted artifact SHA-256"
            )

    if isinstance(output.get("artifact"), str) and evidence_artifact == output.get("artifact"):
        raise StateError("Fidelity QA evidence cannot be the accepted design artifact")
    if result == "pass":
        implementation_errors = _implementation_change_errors(root, state, session_dir)
        if implementation_errors:
            raise StateError(
                "Runtime QA gate failed before evidence capture: "
                + "; ".join(implementation_errors)
            )
    receipt = _validate_fidelity_manifest(
        root,
        session_dir,
        state,
        output,
        evidence_artifact,
        accepted_artifact_sha256,
        result,
    )
    receipt["recordedAt"] = utc_now()
    implementation["fidelityQaReceipts"].append(receipt)
    if result == "fail":
        state["qualityGates"]["fidelity"] = "fail"
    elif result == "blocked":
        state["qualityGates"]["fidelity"] = "blocked"
    return _commit_state(session_dir, state)


def record_fidelity_qa(
    root_value: str | Path,
    session_id: str,
    output_id: str,
    expected_revision: int,
    *,
    accepted_artifact_sha256: str | None,
    evidence_artifact: str,
    result: str,
) -> dict[str, Any]:
    return _record_fidelity_qa(
        root_value,
        session_id,
        output_id,
        expected_revision,
        accepted_artifact_sha256=accepted_artifact_sha256,
        evidence_artifact=evidence_artifact,
        result=result,
        _canonical_probe_executed=False,
    )


def run_runtime_qa(
    root_value: str | Path,
    session_id: str,
    output_id: str,
    expected_revision: int,
    *,
    accepted_artifact_sha256: str | None,
    probe_spec: str,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["implementation"]["status"] != "in-progress":
        raise StateError("Runtime QA can run only while implementation is in progress")
    output = _state_output_map(state).get(output_id)
    if output is None:
        raise StateError(f"Unknown output ID: {output_id}")
    spec_path = qa_evidence_path(session_dir, probe_spec)
    if spec_path.suffix.lower() != ".json":
        raise StateError("Runtime probe spec must be JSON under qa/")
    spec = load_json(spec_path, "runtime probe spec")
    if spec.get("outputId") != output_id:
        raise StateError("Runtime probe spec.outputId does not match --output-id")

    probe_script = Path(__file__).resolve().with_name("browser_runtime_probe.py")
    completed = subprocess.run(
        [
            sys.executable,
            str(probe_script),
            "--session-dir",
            str(session_dir),
            "--spec",
            str(spec_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        trace_value = spec.get("tracePath")
        if isinstance(trace_value, str):
            try:
                trace = load_json(
                    qa_evidence_path(session_dir, trace_value),
                    "failed runtime probe",
                )
                if isinstance(trace.get("reason"), str):
                    detail = trace["reason"]
            except StateError:
                pass
        raise StateError("Canonical browser runtime probe did not PASS: " + (detail or "unknown failure"))

    trace_value = spec.get("tracePath")
    if not isinstance(trace_value, str):
        raise StateError("Runtime probe spec.tracePath is invalid")
    trace_path = qa_evidence_path(session_dir, trace_value)
    trace = load_json(trace_path, "runtime probe")
    if trace.get("verdict") != "pass":
        raise StateError("Canonical browser runtime probe did not produce PASS")
    screenshot = trace.get("screenshot")
    if not isinstance(screenshot, dict):
        raise StateError("Canonical browser runtime probe lacks screenshot evidence")

    contract_output = _contract_output_map(state["contract"])[output_id]
    manifest: dict[str, Any] = {
        "outputId": output_id,
        "acceptedArtifactSha256": accepted_artifact_sha256,
        "result": "pass",
        "route": trace.get("route"),
        "state": trace.get("state"),
        "viewport": trace.get("viewport"),
        "scrollPosition": trace.get("scrollPosition"),
        "pixelWidth": screenshot.get("pixelWidth"),
        "pixelHeight": screenshot.get("pixelHeight"),
        "screenshot": {
            "path": screenshot.get("path"),
            "sha256": screenshot.get("sha256"),
        },
        "runtimeProbe": {
            "path": trace_value,
            "sha256": sha256_file(trace_path),
        },
    }
    if contract_output.get("evidenceEquivalentTo") is not None:
        manifest["evidenceEquivalentTo"] = contract_output["evidenceEquivalentTo"]
        manifest["equivalenceJustification"] = contract_output[
            "equivalenceJustification"
        ]
    if _is_v3_state(state):
        manifest.update(
            comparisonMode=(
                "accepted-design"
                if _design_evidence_required(contract_output)
                else "direction-only"
            ),
            visualDirectionSha256=state["visualDirection"]["sha256"],
            implementationPlanSha256=state["implementation"]["planSha256"],
        )
    manifest_value = f"qa/{output_id}.fidelity.json"
    manifest_path = qa_evidence_path(session_dir, manifest_value, require_file=False)
    if manifest_path in {spec_path, trace_path}:
        raise StateError("Runtime QA manifest path conflicts with probe evidence")
    atomic_write_json(manifest_path, manifest)
    return _record_fidelity_qa(
        root,
        session_id,
        output_id,
        expected_revision,
        accepted_artifact_sha256=accepted_artifact_sha256,
        evidence_artifact=manifest_value,
        result="pass",
        _canonical_probe_executed=True,
    )


def _current_delivery_digest(
    root: Path,
    session_dir: Path,
    state: dict[str, Any],
) -> str:
    direction_sha = _verify_visual_direction(session_dir, state)
    latest_receipts = {
        receipt["outputId"]: receipt
        for receipt in state["implementation"]["fidelityQaReceipts"]
    }
    gallery: list[dict[str, Any]] = []
    contract_outputs = _contract_output_map(state["contract"])
    for output in sorted(state["outputs"], key=lambda item: item["id"]):
        contract_output = contract_outputs[output["id"]]
        if not _runtime_evidence_required(contract_output):
            continue
        if _design_evidence_required(contract_output):
            artifact_error = _verify_output_artifact(session_dir, output)
            if artifact_error:
                raise StateError(artifact_error)
            if _is_v3_state(state):
                _verify_output_render_brief(session_dir, state, output)
            if output["status"] == "promoted":
                promotion_error = _verify_promoted_destination(root, state, output)
                if promotion_error:
                    raise StateError(promotion_error)
        receipt = latest_receipts.get(output["id"])
        if receipt is None:
            raise StateError(f"Runtime gallery lacks required output {output['id']}")
        if receipt.get("result") != "pass":
            raise StateError(
                f"Runtime gallery receipt for {output['id']} is not PASS"
            )
        verified_receipt = _validate_fidelity_manifest(
            root,
            session_dir,
            state,
            output,
            receipt["manifestPath"],
            receipt.get("acceptedArtifactSha256"),
            receipt["result"],
        )
        receipt_fields = [
            "acceptedArtifactSha256",
            "manifestSha256",
            "screenshotPath",
            "screenshotSha256",
            "result",
            "route",
            "state",
            "viewport",
            "scrollPosition",
            "pixelWidth",
            "pixelHeight",
            "evidenceEquivalentTo",
            "equivalenceJustification",
            "reason",
        ]
        if _is_v3_state(state):
            receipt_fields.extend(
                [
                    "comparisonMode",
                    "visualDirectionSha256",
                    "implementationPlanSha256",
                ]
            )
        for field in receipt_fields:
            if verified_receipt.get(field) != receipt.get(field):
                raise StateError(
                    f"Runtime gallery receipt for {output['id']} {field} differs from its manifest"
                )
        manifest_path = qa_evidence_path(session_dir, receipt["manifestPath"])
        if sha256_file(manifest_path) != receipt["manifestSha256"]:
            raise StateError(f"Runtime gallery manifest changed for {output['id']}")
        screenshot_path_value = receipt.get("screenshotPath")
        if not isinstance(screenshot_path_value, str):
            raise StateError(f"Runtime gallery lacks a screenshot for {output['id']}")
        screenshot_path = qa_evidence_path(session_dir, screenshot_path_value)
        screenshot_sha = sha256_file(screenshot_path)
        if screenshot_sha != receipt.get("screenshotSha256"):
            raise StateError(f"Runtime gallery screenshot changed for {output['id']}")
        width, height = validate_screenshot_file(screenshot_path)
        if width != receipt.get("pixelWidth") or height != receipt.get("pixelHeight"):
            raise StateError(f"Runtime gallery dimensions changed for {output['id']}")
        gallery_fields = [
            "outputId",
            "acceptedArtifactSha256",
            "manifestSha256",
            "screenshotSha256",
            "route",
            "state",
            "viewport",
            "scrollPosition",
            "pixelWidth",
            "pixelHeight",
            "evidenceEquivalentTo",
            "equivalenceJustification",
            "result",
        ]
        if _is_v3_state(state):
            gallery_fields.extend(
                [
                    "comparisonMode",
                    "visualDirectionSha256",
                    "implementationPlanSha256",
                ]
            )
        gallery_item = {field: receipt.get(field) for field in gallery_fields}
        if _is_v3_state(state):
            gallery_item.update(
                renderBriefPath=output.get("renderBriefPath"),
                renderBriefSha256=output.get("renderBriefSha256"),
            )
        gallery.append(gallery_item)
    fingerprints = state["implementation"].get("targetFingerprints", [])
    concept_reset_receipt_hashes: list[str] = []
    if _is_v3_state(state):
        _verify_implementation_plan(session_dir, state)
        concept_reset_receipt_hashes = _verify_v3_concept_reset_receipts(
            root,
            session_dir,
            state,
        )
    for fingerprint in fingerprints:
        current = implementation_target_sha256(root, fingerprint["path"])
        if current != fingerprint.get("completionSha256"):
            raise StateError(
                f"Implementation target changed after completion: {fingerprint['path']}"
            )
    delivery_payload = {
        "contractSha256": _canonical_sha256(state["contract"]),
        "productIntentSha256": state["intentConfirmation"].get(
            "productIntentSha256"
        ),
        "visualDirectionSha256": direction_sha,
        "completedAt": state["implementation"].get("completedAt"),
        "targetFingerprints": fingerprints,
        "runtimeGallery": gallery,
    }
    if _is_v3_state(state):
        delivery_payload.update(
            structureSha256=state["contract"].get("structure", {}).get("sha256"),
            implementationPlanSha256=state["implementation"].get("planSha256"),
            conceptResetAuthorityReceiptSha256=concept_reset_receipt_hashes,
        )
    return _canonical_sha256(delivery_payload)


def complete_implementation(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    implementation = state["implementation"]
    if implementation["status"] == "completed":
        return state
    if implementation["status"] != "in-progress":
        raise StateError("Implementation must be started before it can be completed")

    direction_sha = _verify_visual_direction(session_dir, state)
    contract_outputs = _contract_output_map(state["contract"])
    for output in state["outputs"]:
        contract_output = contract_outputs[output["id"]]
        if (
            _design_evidence_required(contract_output)
            and output["status"] in {"accepted", "promoted"}
            and output.get("visualDirectionSha256") != direction_sha
        ):
            raise StateError(
                f"Completion gate failed: required design output {output['id']} is not bound to the locked visual direction"
            )

    full_workflow = state["contract"].get("workflowProfile", "standard") == "full"
    errors: list[str] = []
    if full_workflow or implementation.get("targetFingerprints"):
        errors.extend(_implementation_change_errors(root, state, session_dir))
    if full_workflow:
        errors = _full_design_gate_errors(root, session_dir, state) + errors
    latest_receipts = {
        receipt["outputId"]: receipt
        for receipt in implementation["fidelityQaReceipts"]
    }
    for output in state["outputs"]:
        contract_output = contract_outputs[output["id"]]
        if not _runtime_evidence_required(contract_output):
            continue
        receipt = latest_receipts.get(output["id"])
        if receipt is None:
            errors.append(
                f"runtime-required output {output['id']} has no fidelity QA receipt"
            )
            continue
        expected_artifact_sha = (
            output.get("sha256")
            if _design_evidence_required(contract_output)
            else None
        )
        if receipt["acceptedArtifactSha256"] != expected_artifact_sha:
            errors.append(
                f"fidelity QA receipt for {output['id']} is not bound to the accepted artifact"
            )
        if (
            _is_v3_state(state)
            and receipt.get("visualDirectionSha256") != direction_sha
        ):
            errors.append(
                f"fidelity QA receipt for {output['id']} is not bound to the locked direction"
            )
        if receipt["result"] != "pass":
            errors.append(
                f"latest fidelity QA receipt for {output['id']} is {receipt['result']}"
            )
        try:
            manifest_path = qa_evidence_path(session_dir, receipt["manifestPath"])
            manifest_matches = sha256_file(manifest_path) == receipt["manifestSha256"]
            if not manifest_matches:
                errors.append(
                    f"fidelity QA receipt for {output['id']} manifest hash mismatch"
                )
            screenshot_matches = True
            if isinstance(receipt.get("screenshotPath"), str):
                screenshot_path = qa_evidence_path(
                    session_dir,
                    receipt["screenshotPath"],
                )
                screenshot_matches = sha256_file(screenshot_path) == receipt["screenshotSha256"]
                if not screenshot_matches:
                    errors.append(
                        f"fidelity QA receipt for {output['id']} screenshot hash mismatch"
                    )
            if manifest_matches and screenshot_matches:
                verified = _validate_fidelity_manifest(
                    root,
                    session_dir,
                    state,
                    output,
                    receipt["manifestPath"],
                    receipt["acceptedArtifactSha256"],
                    receipt["result"],
                )
                for field in (
                    "manifestSha256",
                    "screenshotPath",
                    "screenshotSha256",
                    "route",
                    "state",
                    "viewport",
                    "scrollPosition",
                    "pixelWidth",
                    "pixelHeight",
                    "evidenceEquivalentTo",
                    "equivalenceJustification",
                    "reason",
                    *( ("comparisonMode", "visualDirectionSha256", "implementationPlanSha256") if _is_v3_state(state) else () ),
                ):
                    if verified[field] != receipt.get(field):
                        errors.append(
                            f"fidelity QA receipt for {output['id']} {field} mismatch"
                        )
        except StateError as exc:
            errors.append(f"fidelity QA receipt for {output['id']}: {exc}")
    if errors:
        raise StateError("Completion gate failed: " + "; ".join(errors))

    implementation["status"] = "completed"
    implementation["completedAt"] = utc_now()
    state["qualityGates"]["runtime"] = "pass"
    if full_workflow:
        state["qualityGates"]["fidelity"] = "pass"
        digest = _current_delivery_digest(root, session_dir, state)
        state["deliveryReview"].update(
            status="awaiting-user-review",
            deliveryDigest=digest,
            acceptedAt=None,
            rejectedAt=None,
            reason=None,
            userAuthorized=False,
        )
        state["status"] = "awaiting-user-review"
    else:
        state["status"] = "completed"
    return _commit_state(session_dir, state)


def _review_delivery(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    *,
    delivery_digest: str,
    user_authorized: bool,
    accepted: bool,
    reason: str | None = None,
) -> dict[str, Any]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] != "awaiting-user-review":
        raise StateError("Delivery review requires awaiting-user-review status")
    if not user_authorized:
        raise StateError("Delivery review requires --user-authorized")
    if not isinstance(delivery_digest, str) or HASH_RE.fullmatch(delivery_digest) is None:
        raise StateError("--delivery-digest must be a lowercase SHA-256 digest")
    expected = state["deliveryReview"].get("deliveryDigest")
    current = _current_delivery_digest(root, session_dir, state)
    if delivery_digest != expected or current != expected:
        raise StateError("The supplied delivery digest does not match the current runtime gallery")
    if not accepted and (not isinstance(reason, str) or not reason.strip()):
        raise StateError("reject-delivery requires a non-empty --reason")
    now = utc_now()
    state["deliveryReview"].update(
        status="accepted" if accepted else "rejected",
        acceptedAt=now if accepted else None,
        rejectedAt=None if accepted else now,
        reason=None if accepted else reason.strip(),
        userAuthorized=True,
    )
    state["qualityGates"]["userAcceptance"] = "pass" if accepted else "fail"
    state["status"] = "completed" if accepted else "rejected"
    return _commit_state(session_dir, state)


def accept_delivery(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    *,
    delivery_digest: str,
    user_authorized: bool,
) -> dict[str, Any]:
    return _review_delivery(
        root_value,
        session_id,
        expected_revision,
        delivery_digest=delivery_digest,
        user_authorized=user_authorized,
        accepted=True,
    )


def reject_delivery(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
    *,
    delivery_digest: str,
    reason: str,
    user_authorized: bool,
) -> dict[str, Any]:
    return _review_delivery(
        root_value,
        session_id,
        expected_revision,
        delivery_digest=delivery_digest,
        user_authorized=user_authorized,
        accepted=False,
        reason=reason,
    )


def validate_session(
    root_value: str | Path,
    session_id: str,
    expected_revision: int,
) -> tuple[dict[str, Any], list[str]]:
    root = preflight(root_value)
    session_dir, state = load_state(root, session_id)
    require_revision(state, expected_revision)
    if state["status"] in TERMINAL_SESSION_STATUSES or state["status"] == "awaiting-user-review":
        raise StateError(f"Cannot validate terminal session status {state['status']!r}")
    contract_outputs = {item["id"]: item for item in state["contract"]["outputs"]}
    outputs = _state_output_map(state)
    intent_errors: list[str] = []
    coverage_errors: list[str] = []
    try:
        _require_confirmed_intent(state, session_dir)
    except StateError as exc:
        intent_errors.append(str(exc))
    direction_sha: str | None = None
    try:
        direction_sha = _verify_visual_direction(session_dir, state)
    except StateError as exc:
        coverage_errors.append(str(exc))
    if _is_v3_state(state):
        try:
            _verify_v3_structure(session_dir, state)
        except StateError as exc:
            coverage_errors.append(str(exc))
    for output_id, output in outputs.items():
        contract_output = contract_outputs[output_id]
        status = output["status"]
        if status in {"reviewing", "awaiting-approval", "accepted"}:
            error = _verify_output_artifact(session_dir, output)
            if error:
                coverage_errors.append(error)
        elif status == "promoted":
            error = _verify_promoted_destination(root, state, output)
            if error:
                coverage_errors.append(error)
        if (
            _design_evidence_required(contract_output)
            and status not in SETTLED_OUTPUT_STATUSES
        ):
            coverage_errors.append(f"required output {output_id} is {status}")
        if (
            status in {"reviewing", "awaiting-approval", "accepted", "promoted"}
            and output.get("visualDirectionSha256") != direction_sha
        ):
            coverage_errors.append(
                f"output {output_id} is not bound to the locked visual direction"
            )
        if _is_v3_state(state) and status in {
            "generating",
            "reviewing",
            "awaiting-approval",
            "accepted",
            "promoted",
        }:
            try:
                _verify_output_anchor(
                    session_dir,
                    state,
                    contract_output,
                    output,
                )
                _verify_output_render_brief(session_dir, state, output)
            except StateError as exc:
                coverage_errors.append(str(exc))
        if (
            status in {"reviewing", "awaiting-approval", "accepted", "promoted"}
            and _output_requires_imagegen_provenance(state, output_id)
        ):
            try:
                image_path = artifact_path(session_dir, output["artifact"])
                validate_imagegen_artifact(state, image_path, output_id)
                provenance = output.get("provenance")
                verified = validate_imagegen_provenance(
                    session_dir,
                    state,
                    output_id,
                    image_path,
                    provenance.get("receiptPath") if isinstance(provenance, dict) else None,
                )
                if verified != provenance:
                    coverage_errors.append(
                        f"output {output_id} provenance differs from its receipt"
                    )
            except StateError as exc:
                coverage_errors.append(str(exc))
        if status == "deferred" and (not output["userAuthorized"] or not output["reason"]):
            coverage_errors.append(f"deferred output {output_id} lacks explicit authority")
        for dependency in contract_output["dependsOn"]:
            if status in SETTLED_OUTPUT_STATUSES and outputs[dependency]["status"] not in SETTLED_OUTPUT_STATUSES:
                coverage_errors.append(f"output {output_id} settled before dependency {dependency}")

    errors = intent_errors + coverage_errors
    state["validationErrors"] = sorted(set(errors))
    state["status"] = "blocked" if errors else "validated"
    state["qualityGates"]["coverage"] = "blocked" if coverage_errors else "pass"
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
        and (
            not _state_design_evidence_required(item)
            or item["status"] in SETTLED_OUTPUT_STATUSES
        )
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
    contract_outputs = _contract_output_map(state["contract"])
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
            if error is None and _is_v3_state(state):
                try:
                    _verify_output_anchor(
                        session_dir,
                        state,
                        contract_outputs[output["id"]],
                        output,
                    )
                    _verify_output_render_brief(session_dir, state, output)
                except StateError as exc:
                    error = str(exc)
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
            if error is None and _is_v3_state(state):
                try:
                    _verify_output_anchor(
                        session_dir,
                        state,
                        contract_outputs[output["id"]],
                        output,
                    )
                    _verify_output_render_brief(session_dir, state, output)
                except StateError as exc:
                    error = str(exc)
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
    if any(
        _state_design_evidence_required(item) and item["status"] == "blocked"
        for item in state["outputs"]
    ):
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
    direction_sha = _verify_visual_direction(session_dir, state)
    if output.get("visualDirectionSha256") != direction_sha:
        raise StateError(
            "Accepted output is not bound to the locked visual direction"
        )
    contract_output = next(item for item in state["contract"]["outputs"] if item["id"] == output_id)
    target = contract_output.get("promotionTarget")
    if not isinstance(target, str):
        raise StateError("Promotion target is missing from the contract")
    source = artifact_path(session_dir, output["artifact"])
    source_hash = sha256_file(source)
    if source_hash != output["sha256"]:
        raise StateError("Accepted source artifact failed SHA-256 verification")
    if _is_v3_state(state):
        _verify_output_anchor(
            session_dir,
            state,
            contract_output,
            output,
        )
        _verify_output_render_brief(session_dir, state, output)
    if _output_requires_imagegen_provenance(state, output_id):
        provenance = output.get("provenance")
        validate_imagegen_provenance(
            session_dir,
            state,
            output_id,
            source,
            provenance.get("receiptPath") if isinstance(provenance, dict) else None,
        )
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
    if (
        state["contract"].get("workflowProfile", "standard") == "full"
        and state["implementation"]["status"] == "in-progress"
        and not discard_unpromoted
    ):
        raise StateError(
            "Full workflow cleanup requires implementation completion or explicit "
            "--discard-unpromoted confirmation"
        )
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
    init.add_argument("--parent-session-id")
    init.add_argument("--supersedes-session-id")
    init.add_argument("--user-authorized-supersession", action="store_true")
    init.add_argument("--authority-receipt")

    common("status")
    common("handoff")

    confirm_intent_parser = common("confirm-intent")
    confirm_intent_parser.add_argument("--expected-revision", required=True, type=int)
    confirm_intent_parser.add_argument("--product-intent-sha256", required=True)
    confirm_intent_parser.add_argument("--lifecycle-plan-sha256", required=True)
    confirm_intent_parser.add_argument("--teach-back", required=True)
    confirm_intent_parser.add_argument("--user-authorized", action="store_true")
    confirm_intent_parser.add_argument("--authority-receipt")

    lock_direction_parser = common("lock-visual-direction")
    lock_direction_parser.add_argument("--expected-revision", required=True, type=int)
    lock_direction_parser.add_argument("--direction-contract", required=True)
    lock_direction_parser.add_argument("--user-authorized", action="store_true")

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
    mark.add_argument("--provenance-receipt")
    mark.add_argument("--concept-reset", action="store_true")
    mark.add_argument("--authority-receipt")
    mark.add_argument("--render-brief")

    batch = common("batch-mark")
    batch.add_argument("--expected-revision", required=True, type=int)
    batch.add_argument("--transitions", required=True)

    validate = common("validate")
    validate.add_argument("--expected-revision", required=True, type=int)

    resume = common("resume")
    resume.add_argument("--expected-revision", required=True, type=int)

    promote = common("promote")
    promote.add_argument("--output-id", required=True)
    promote.add_argument("--expected-revision", required=True, type=int)
    promote.add_argument("--replace", action="store_true")
    promote.add_argument("--expected-destination-sha256")

    begin_implementation_parser = common("begin-implementation")
    begin_implementation_parser.add_argument("--expected-revision", required=True, type=int)
    begin_implementation_parser.add_argument(
        "--implementation-target",
        action="append",
        dest="implementation_targets",
    )
    begin_implementation_parser.add_argument("--implementation-plan")

    fidelity = common("record-fidelity-qa")
    fidelity.add_argument("--output-id", required=True)
    fidelity.add_argument("--expected-revision", required=True, type=int)
    fidelity.add_argument("--accepted-artifact-sha256")
    fidelity.add_argument("--evidence-artifact", required=True)
    fidelity.add_argument("--result", required=True, choices=sorted(FIDELITY_RESULTS))

    runtime_qa = common("run-runtime-qa")
    runtime_qa.add_argument("--output-id", required=True)
    runtime_qa.add_argument("--expected-revision", required=True, type=int)
    runtime_qa.add_argument("--accepted-artifact-sha256")
    runtime_qa.add_argument("--probe-spec", required=True)

    complete_implementation_parser = common("complete-implementation")
    complete_implementation_parser.add_argument("--expected-revision", required=True, type=int)

    accept_delivery_parser = common("accept-delivery")
    accept_delivery_parser.add_argument("--expected-revision", required=True, type=int)
    accept_delivery_parser.add_argument("--delivery-digest", required=True)
    accept_delivery_parser.add_argument("--user-authorized", action="store_true")

    reject_delivery_parser = common("reject-delivery")
    reject_delivery_parser.add_argument("--expected-revision", required=True, type=int)
    reject_delivery_parser.add_argument("--delivery-digest", required=True)
    reject_delivery_parser.add_argument("--reason", required=True)
    reject_delivery_parser.add_argument("--user-authorized", action="store_true")

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
                parent_session_id=args.parent_session_id,
                supersedes_session_id=args.supersedes_session_id,
                user_authorized_supersession=args.user_authorized_supersession,
                authority_receipt_file=args.authority_receipt,
            )
        elif args.command == "status":
            root = preflight(args.root)
            _, result = load_state(root, args.session_id)
        elif args.command == "handoff":
            result = compact_handoff(args.root, args.session_id)
        elif args.command == "confirm-intent":
            result = confirm_intent(
                args.root,
                args.session_id,
                args.expected_revision,
                product_intent_sha256=args.product_intent_sha256,
                lifecycle_plan_sha256=args.lifecycle_plan_sha256,
                teach_back=args.teach_back,
                user_authorized=args.user_authorized,
                authority_receipt_file=args.authority_receipt,
            )
        elif args.command == "lock-visual-direction":
            result = lock_visual_direction(
                args.root,
                args.session_id,
                args.expected_revision,
                args.direction_contract,
                user_authorized=args.user_authorized,
            )
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
                provenance_receipt=args.provenance_receipt,
                concept_reset=args.concept_reset,
                authority_receipt_file=args.authority_receipt,
                render_brief=args.render_brief,
            )
        elif args.command == "batch-mark":
            result = batch_mark(
                args.root,
                args.session_id,
                args.expected_revision,
                args.transitions,
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
        elif args.command == "begin-implementation":
            result = begin_implementation(
                args.root,
                args.session_id,
                args.expected_revision,
                implementation_targets=args.implementation_targets,
                implementation_plan_file=args.implementation_plan,
            )
        elif args.command == "record-fidelity-qa":
            result = record_fidelity_qa(
                args.root,
                args.session_id,
                args.output_id,
                args.expected_revision,
                accepted_artifact_sha256=args.accepted_artifact_sha256,
                evidence_artifact=args.evidence_artifact,
                result=args.result,
            )
        elif args.command == "run-runtime-qa":
            result = run_runtime_qa(
                args.root,
                args.session_id,
                args.output_id,
                args.expected_revision,
                accepted_artifact_sha256=args.accepted_artifact_sha256,
                probe_spec=args.probe_spec,
            )
        elif args.command == "complete-implementation":
            result = complete_implementation(
                args.root,
                args.session_id,
                args.expected_revision,
            )
        elif args.command == "accept-delivery":
            result = accept_delivery(
                args.root,
                args.session_id,
                args.expected_revision,
                delivery_digest=args.delivery_digest,
                user_authorized=args.user_authorized,
            )
        elif args.command == "reject-delivery":
            result = reject_delivery(
                args.root,
                args.session_id,
                args.expected_revision,
                delivery_digest=args.delivery_digest,
                reason=args.reason,
                user_authorized=args.user_authorized,
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
