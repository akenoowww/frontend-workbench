#!/usr/bin/env python3
"""Validate design fixtures, build blind packets, or score paired visual judgments."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import secrets
import shutil
import struct
import sys
import zlib
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as exc:  # pragma: no cover - exercised in clean environments
    print(
        "error: install development dependencies with "
        "`python3 -m pip install -r requirements-dev.txt`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


DIMENSIONS = (
    "specificity",
    "hierarchy",
    "uxCorrectness",
    "uiDnaPreservation",
    "responsiveness",
    "genericness",
    "productHierarchyFidelity",
    "shellContinuity",
    "referenceScopeFidelity",
    "capabilityFit",
)
VARIANTS = ("baseline", "workbench")
MATCHED_DIGESTS = (
    "promptSha256",
    "modelConfigSha256",
    "environmentSha256",
    "fixtureSha256",
    "captureHarnessSha256",
    "taskBudgetSha256",
)
PAIRING_RECEIPTS = {
    "modelConfig": "modelConfigSha256",
    "environment": "environmentSha256",
    "captureHarness": "captureHarnessSha256",
    "taskBudget": "taskBudgetSha256",
}
PLACEHOLDER_IDS = {"fixture", "none", "synthetic", "test", "unknown"}
VARIANT_LEAK_RE = re.compile(r"(?:baseline|workbench)", re.IGNORECASE)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
SCORECARD_STATEMENT = (
    "Blind pairwise visual preferences were aggregated; this scorecard does not "
    "establish causal uplift."
)


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


def json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prompt_sha256(case: dict[str, Any]) -> str:
    return sha256_bytes(case["prompt"].encode("utf-8"))


def build_registry(schema_root: Path) -> tuple[Registry, dict[str, dict[str, Any]]]:
    registry = Registry()
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_root.glob("*.schema.json")):
        schema = load_object(path)
        Draft202012Validator.check_schema(schema)
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            raise ValueError(f"{path}: schema needs $id")
        registry = registry.with_resource(schema_id, Resource.from_contents(schema))
        schemas[path.name] = schema
    return registry, schemas


def validate_instance(
    instance: dict[str, Any],
    schema: dict[str, Any],
    registry: Registry,
    label: str,
) -> list[str]:
    validator = Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    )
    errors: list[str] = []
    for failure in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in failure.absolute_path) or "$"
        errors.append(f"{label}:{location}: {failure.message}")
    return errors


def resolve_path(repo_root: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    return candidate.resolve() if candidate.is_absolute() else (repo_root / candidate).resolve()


def runtime_location_errors(repo_root: Path, path: Path, label: str) -> list[str]:
    """Keep raw visual-eval artifacts ignored when they live in this repository."""
    resolved_repo = repo_root.resolve()
    resolved_path = path.resolve()
    try:
        resolved_path.relative_to(resolved_repo)
    except ValueError:
        return []
    runtime_root = (resolved_repo / "evals" / "results").resolve()
    try:
        resolved_path.relative_to(runtime_root)
    except ValueError:
        return [
            f"{label} inside the repository must stay under ignored {runtime_root}"
        ]
    try:
        ignored = "/evals/results/" in (
            resolved_repo / ".gitignore"
        ).read_text(encoding="utf-8").splitlines()
    except OSError:
        ignored = False
    return [] if ignored else ["root .gitignore must contain the exact line '/evals/results/'"]


def contained_static_file(
    repo_root: Path,
    value: str,
    expected_root: Path,
    label: str,
) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        return None, [f"{label}: path must be canonical and relative"]
    candidate = repo_root.joinpath(*pure.parts)
    cursor = repo_root
    for part in pure.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            errors.append(f"{label}: path must not traverse a symlink: {value}")
            return None, errors
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(expected_root.resolve())
    except (OSError, RuntimeError, ValueError) as exc:
        errors.append(f"{label}: path escapes its allowed root or is missing: {value}: {exc}")
        return None, errors
    if not resolved.is_file() or resolved.is_symlink():
        errors.append(f"{label}: expected a regular non-symlink file: {value}")
        return None, errors
    return resolved, errors


def safe_runtime_file(
    root: Path,
    value: str,
    prefix: str,
    label: str,
) -> tuple[Path | None, list[str]]:
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or not pure.parts
        or pure.parts[0] != prefix
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() != value
    ):
        return None, [f"{label}: path must be canonical and under {prefix}/"]
    if root.is_symlink():
        return None, [f"{label}: runtime root must not be a symlink"]
    resolved_root = root.resolve()
    cursor = root
    for part in pure.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return None, [f"{label}: path must not traverse a symlink: {value}"]
    candidate = root.joinpath(*pure.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError) as exc:
        return None, [f"{label}: path escapes its runtime root or is missing: {value}: {exc}"]
    if not resolved.is_file() or resolved.is_symlink():
        return None, [f"{label}: expected a regular non-symlink file: {value}"]
    return resolved, []


def parse_png(path: Path) -> tuple[int, int, list[tuple[bytes, bytes]]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("PNG signature is invalid")
    position = len(PNG_SIGNATURE)
    chunks: list[tuple[bytes, bytes]] = []
    width = height = 0
    saw_idat = False
    saw_iend = False
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("PNG chunk header is truncated")
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        chunk_end = position + 12 + length
        if chunk_end > len(data):
            raise ValueError("PNG chunk payload is truncated")
        payload = data[position + 8 : position + 8 + length]
        expected_crc = struct.unpack(">I", data[position + 8 + length : chunk_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"PNG chunk {chunk_type!r} has an invalid CRC")
        if not chunks and chunk_type != b"IHDR":
            raise ValueError("PNG IHDR must be the first chunk")
        if chunk_type == b"IHDR":
            if chunks or length != 13:
                raise ValueError("PNG IHDR is invalid")
            width, height = struct.unpack(">II", payload[:8])
            if width < 1 or height < 1:
                raise ValueError("PNG dimensions must be positive")
        elif chunk_type == b"IDAT":
            saw_idat = True
        elif chunk_type == b"IEND":
            if length != 0 or chunk_end != len(data):
                raise ValueError("PNG IEND is invalid or trailing bytes are present")
            saw_iend = True
        chunks.append((chunk_type, payload))
        position = chunk_end
        if saw_iend:
            break
    if width < 1 or height < 1 or not saw_idat or not saw_iend:
        raise ValueError("PNG must contain IHDR, IDAT, and IEND chunks")
    return width, height, chunks


def png_metadata_leaks_variant(chunks: list[tuple[bytes, bytes]]) -> bool:
    for chunk_type, payload in chunks:
        if chunk_type in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
            text = payload.decode("latin-1", errors="ignore")
            if VARIANT_LEAK_RE.search(text):
                return True
    return False


def validate_file_receipt(
    root: Path,
    path_value: Any,
    digest_value: Any,
    prefix: str,
    label: str,
) -> tuple[Path | None, list[str]]:
    if not isinstance(path_value, str):
        return None, [f"{label}: path receipt is required"]
    path, errors = safe_runtime_file(root, path_value, prefix, label)
    if path is None:
        return None, errors
    try:
        if path.stat().st_size == 0:
            errors.append(f"{label}: file must not be empty")
        actual_digest = sha256_file(path)
    except OSError as exc:
        errors.append(f"{label}: could not read receipt file: {exc}")
        return path, errors
    if not isinstance(digest_value, str) or actual_digest != digest_value:
        errors.append(f"{label}: SHA-256 does not match file bytes")
    return path, errors


def validate_png_receipt(
    root: Path,
    capture: dict[str, Any],
    prefix: str,
    label: str,
    expected_width: int,
    expected_height: int,
    *,
    reject_metadata_leaks: bool,
) -> tuple[Path | None, list[str]]:
    path, errors = validate_file_receipt(
        root,
        capture.get("path"),
        capture.get("sha256"),
        prefix,
        label,
    )
    if path is None:
        return None, errors
    if path.suffix.lower() != ".png":
        errors.append(f"{label}: screenshot must use a .png extension")
        return path, errors
    try:
        width, height, chunks = parse_png(path)
    except (OSError, ValueError, struct.error) as exc:
        errors.append(f"{label}: invalid PNG: {exc}")
        return path, errors
    if (width, height) != (expected_width, expected_height):
        errors.append(
            f"{label}: PNG dimensions {(width, height)!r} do not match "
            f"declared dimensions {(expected_width, expected_height)!r}"
        )
    if reject_metadata_leaks and png_metadata_leaks_variant(chunks):
        errors.append(f"{label}: PNG metadata leaks a variant label")
    return path, errors


def object_leaks_variant(value: Any) -> bool:
    if isinstance(value, str):
        return VARIANT_LEAK_RE.search(value) is not None
    if isinstance(value, list):
        return any(object_leaks_variant(item) for item in value)
    if isinstance(value, dict):
        return any(object_leaks_variant(key) or object_leaks_variant(item) for key, item in value.items())
    return False


def bytes_leak_variant(value: bytes) -> bool:
    return b"baseline" in value.lower() or b"workbench" in value.lower()


def validate_pairing_receipts(
    results_root: Path,
    pairing: dict[str, Any],
    label: str,
) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    validated: dict[str, str] = {}
    matched = pairing.get("matchedDigests")
    receipts = pairing.get("receipts")
    if not isinstance(matched, dict) or not isinstance(receipts, dict):
        return validated, errors
    seen_paths: dict[Path, str] = {}
    seen_file_ids: dict[tuple[int, int], str] = {}
    for receipt_name, digest_field in PAIRING_RECEIPTS.items():
        receipt = receipts.get(receipt_name)
        if not isinstance(receipt, dict):
            continue
        receipt_label = f"{label}:pairing.receipts.{receipt_name}"
        path, receipt_errors = validate_file_receipt(
            results_root,
            receipt.get("path"),
            receipt.get("sha256"),
            "pairing",
            receipt_label,
        )
        errors.extend(receipt_errors)
        if path is None:
            continue
        previous = seen_paths.get(path)
        if previous is not None:
            errors.append(
                f"{receipt_label}: pairing receipt file is reused by {previous!r}"
            )
        seen_paths[path] = receipt_name
        try:
            stat = path.stat()
            file_id = (stat.st_dev, stat.st_ino)
            previous_identity = seen_file_ids.get(file_id)
            if previous_identity is not None and previous_identity != receipt_name:
                errors.append(
                    f"{receipt_label}: pairing receipt file identity is reused by "
                    f"{previous_identity!r}"
                )
            seen_file_ids[file_id] = receipt_name
            actual_digest = sha256_file(path)
        except OSError as exc:
            errors.append(f"{receipt_label}: could not hash receipt bytes: {exc}")
            continue
        validated[receipt_name] = actual_digest
        if actual_digest != matched.get(digest_field):
            errors.append(
                f"{receipt_label}: actual bytes do not bind to matchedDigests.{digest_field}"
            )
    return validated, errors


def load_cases(
    repo_root: Path,
    cases_root: Path,
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    bundles: dict[str, dict[str, Any]] = {}
    case_schema = schemas["eval-visual-case.schema.json"]
    fixture_schema = schemas["eval-visual-fixture.schema.json"]
    rubric_schema = schemas["eval-visual-rubric.schema.json"]
    for path in sorted(cases_root.glob("*.json")):
        try:
            case = load_object(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_instance(case, case_schema, registry, str(path)))
        case_id = case.get("id")
        if not isinstance(case_id, str):
            continue
        if path.stem != case_id:
            errors.append(f"{path}: case id must match its filename")
        if case_id in bundles:
            errors.append(f"duplicate visual eval case ID: {case_id}")
            continue
        fixture_value = case.get("fixtureManifest")
        rubric_value = case.get("rubric")
        if not isinstance(fixture_value, str) or not isinstance(rubric_value, str):
            continue
        fixture_path, fixture_path_errors = contained_static_file(
            repo_root,
            fixture_value,
            repo_root / "evals" / "design-fixtures",
            f"{path}:fixtureManifest",
        )
        rubric_path, rubric_path_errors = contained_static_file(
            repo_root,
            rubric_value,
            repo_root / "evals" / "rubrics",
            f"{path}:rubric",
        )
        errors.extend(fixture_path_errors)
        errors.extend(rubric_path_errors)
        if fixture_path is None or rubric_path is None:
            continue
        try:
            fixture = load_object(fixture_path)
            rubric = load_object(rubric_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_instance(fixture, fixture_schema, registry, str(fixture_path)))
        errors.extend(validate_instance(rubric, rubric_schema, registry, str(rubric_path)))
        actual_fixture_sha = sha256_file(fixture_path)
        actual_rubric_sha = sha256_file(rubric_path)
        if case.get("fixtureSha256") != actual_fixture_sha:
            errors.append(f"{path}: fixtureSha256 does not match fixture bytes")
        if case.get("rubricSha256") != actual_rubric_sha:
            errors.append(f"{path}: rubricSha256 does not match rubric bytes")
        if fixture.get("fixtureId") != case_id:
            errors.append(f"{path}: fixtureId must match the visual case id")
        capture_items = fixture.get("captureMatrix")
        capture_ids = [
            item.get("captureId")
            for item in capture_items
            if isinstance(item, dict) and isinstance(item.get("captureId"), str)
        ] if isinstance(capture_items, list) else []
        if len(capture_ids) != len(set(capture_ids)):
            errors.append(f"{fixture_path}: capture IDs must be unique")
        if set(capture_ids) != set(case.get("expectedCaptureIds", [])):
            errors.append(f"{path}: expectedCaptureIds must exactly match fixture captureMatrix")
        rubric_dimensions = rubric.get("dimensions")
        if not isinstance(rubric_dimensions, dict) or tuple(rubric_dimensions) != DIMENSIONS:
            errors.append(f"{rubric_path}: rubric dimensions must be exactly {DIMENSIONS!r}")
        if rubric.get("allowedVerdicts") != ["A", "B", "tie", "not-judgeable"]:
            errors.append(f"{rubric_path}: pairwise verdicts are invalid")
        source_id = fixture.get("provenance", {}).get("sourceId")
        if isinstance(source_id, str) and source_id.strip().lower() in PLACEHOLDER_IDS:
            errors.append(f"{fixture_path}: provenance sourceId cannot be a placeholder")
        bundles[case_id] = {"case": case, "fixture": fixture, "rubric": rubric}
    if not bundles:
        errors.append(f"no visual eval cases found under {cases_root}")
    return bundles, errors


def filter_cases(
    bundles: dict[str, dict[str, Any]],
    requested: list[str] | None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not requested:
        return bundles, []
    requested_set = set(requested)
    missing = sorted(requested_set - set(bundles))
    errors = [f"unknown visual eval case: {case_id}" for case_id in missing]
    return {case_id: bundles[case_id] for case_id in sorted(requested_set & set(bundles))}, errors


def validate_run_capture(
    result_root: Path,
    capture: dict[str, Any],
    target: dict[str, Any],
    label: str,
) -> list[str]:
    errors: list[str] = []
    for field in ("outputId", "surfaceId", "route", "state", "viewport", "scrollPosition"):
        if capture.get(field) != target.get(field):
            errors.append(
                f"{label}: {field} does not match fixture capture target "
                f"{target.get(field)!r}"
            )
    viewport = target["viewport"]
    _, png_errors = validate_png_receipt(
        result_root,
        capture,
        "screenshots",
        label,
        viewport["width"],
        viewport["height"],
        reject_metadata_leaks=False,
    )
    errors.extend(png_errors)
    return errors


def load_runs(
    results_root: Path,
    variant: str,
    all_case_ids: set[str],
    bundles: dict[str, dict[str, Any]],
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], list[str]]:
    errors: list[str] = []
    runs: dict[tuple[str, str], dict[str, Any]] = {}
    if not results_root.is_dir():
        return {}, [f"{variant} results directory does not exist: {results_root}"]
    for path in sorted(results_root.glob("*.json")):
        try:
            result = load_object(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_instance(
                result,
                schemas["eval-visual-run.schema.json"],
                registry,
                str(path),
            )
        )
        case_id = result.get("caseId")
        trial_id = result.get("trialId")
        if not isinstance(case_id, str) or not isinstance(trial_id, str):
            continue
        if case_id not in all_case_ids:
            errors.append(f"{path}: result references unknown visual case {case_id!r}")
            continue
        if case_id not in bundles:
            continue
        if result.get("variant") != variant:
            errors.append(f"{path}: expected variant {variant!r}")
        key = (case_id, trial_id)
        if key in runs:
            errors.append(f"duplicate {variant} visual result for {case_id}/{trial_id}")
            continue
        bundle = bundles[case_id]
        case = bundle["case"]
        fixture = bundle["fixture"]
        pairing = result.get("pairing")
        matched = pairing.get("matchedDigests") if isinstance(pairing, dict) else None
        if isinstance(matched, dict):
            if matched.get("promptSha256") != prompt_sha256(case):
                errors.append(f"{path}: promptSha256 does not match the visual case prompt")
            if matched.get("fixtureSha256") != case.get("fixtureSha256"):
                errors.append(f"{path}: fixtureSha256 does not match the visual case")
        if isinstance(pairing, dict):
            validated_receipts, receipt_errors = validate_pairing_receipts(
                results_root,
                pairing,
                str(path),
            )
            result["_validatedPairingReceipts"] = validated_receipts
            errors.extend(receipt_errors)
        evidence = result.get("evidence")
        if isinstance(evidence, dict):
            source_id = evidence.get("sourceId")
            if isinstance(source_id, str) and source_id.strip().lower() in PLACEHOLDER_IDS:
                errors.append(f"{path}: evidence sourceId cannot be a placeholder")
            _, trace_errors = validate_file_receipt(
                results_root,
                evidence.get("tracePath"),
                evidence.get("traceSha256"),
                "traces",
                f"{path}:trace",
            )
            errors.extend(trace_errors)
        targets = {
            item["captureId"]: item
            for item in fixture["captureMatrix"]
            if isinstance(item, dict)
        }
        captures = result.get("captures")
        seen_ids: set[str] = set()
        seen_paths: set[str] = set()
        seen_digests: set[str] = set()
        if isinstance(captures, list):
            for index, capture in enumerate(captures):
                if not isinstance(capture, dict):
                    continue
                capture_id = capture.get("captureId")
                label = f"{path}:captures[{index}]"
                if not isinstance(capture_id, str) or capture_id not in targets:
                    errors.append(f"{label}: unknown captureId {capture_id!r}")
                    continue
                if capture_id in seen_ids:
                    errors.append(f"{label}: duplicate captureId {capture_id!r}")
                seen_ids.add(capture_id)
                capture_path = capture.get("path")
                if isinstance(capture_path, str):
                    if capture_path in seen_paths:
                        errors.append(f"{label}: capture path is reused")
                    seen_paths.add(capture_path)
                capture_digest = capture.get("sha256")
                if isinstance(capture_digest, str):
                    if capture_digest in seen_digests:
                        errors.append(
                            f"{label}: screenshot bytes are reused for a distinct capture target"
                        )
                    seen_digests.add(capture_digest)
                errors.extend(validate_run_capture(results_root, capture, targets[capture_id], label))
        if seen_ids != set(targets):
            errors.append(
                f"{path}: captures must exactly cover fixture targets; "
                f"expected {sorted(targets)!r}, got {sorted(seen_ids)!r}"
            )
        runs[key] = result
    if not runs:
        errors.append(f"no {variant} visual result JSON files found under {results_root}")
    return runs, errors


def validate_pairs(
    bundles: dict[str, dict[str, Any]],
    baseline_runs: dict[tuple[str, str], dict[str, Any]],
    workbench_runs: dict[tuple[str, str], dict[str, Any]],
) -> tuple[dict[tuple[str, str], dict[str, dict[str, Any]]], list[str]]:
    errors: list[str] = []
    baseline_keys = set(baseline_runs)
    workbench_keys = set(workbench_runs)
    for case_id, trial_id in sorted(baseline_keys - workbench_keys):
        errors.append(f"missing workbench visual result for {case_id}/{trial_id}")
    for case_id, trial_id in sorted(workbench_keys - baseline_keys):
        errors.append(f"missing baseline visual result for {case_id}/{trial_id}")
    common = baseline_keys & workbench_keys
    for case_id, bundle in sorted(bundles.items()):
        trial_count = sum(1 for key in common if key[0] == case_id)
        minimum = bundle["case"]["minimumTrials"]
        if trial_count < minimum:
            errors.append(
                f"visual case {case_id!r} requires at least {minimum} matched trial(s), "
                f"got {trial_count}"
            )
    pairs: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    seen_pair_ids: set[str] = set()
    seen_sources: set[str] = set()
    seen_traces: set[str] = set()
    for key in sorted(common):
        baseline = baseline_runs[key]
        workbench = workbench_runs[key]
        baseline_pairing = baseline["pairing"]
        workbench_pairing = workbench["pairing"]
        pair_id = baseline_pairing["pairId"]
        if pair_id != workbench_pairing["pairId"]:
            errors.append(f"{key[0]}/{key[1]}: pairId does not match across variants")
        if pair_id in seen_pair_ids:
            errors.append(f"duplicate pairId across visual trials: {pair_id}")
        seen_pair_ids.add(pair_id)
        baseline_digests = baseline_pairing["matchedDigests"]
        workbench_digests = workbench_pairing["matchedDigests"]
        if baseline_digests != workbench_digests:
            changed = [
                field
                for field in MATCHED_DIGESTS
                if baseline_digests.get(field) != workbench_digests.get(field)
            ]
            errors.append(
                f"{key[0]}/{key[1]}: matched pairing digests differ: {changed!r}"
            )
        baseline_receipts = baseline.get("_validatedPairingReceipts", {})
        workbench_receipts = workbench.get("_validatedPairingReceipts", {})
        if baseline_receipts != workbench_receipts:
            changed_receipts = [
                field
                for field in PAIRING_RECEIPTS
                if baseline_receipts.get(field) != workbench_receipts.get(field)
            ]
            errors.append(
                f"{key[0]}/{key[1]}: validated pairing receipts differ: "
                f"{changed_receipts!r}"
            )
        for variant, result in (("baseline", baseline), ("workbench", workbench)):
            source_id = result["evidence"]["sourceId"]
            trace_sha = result["evidence"]["traceSha256"]
            if source_id in seen_sources:
                errors.append(f"reused visual run sourceId: {source_id}")
            seen_sources.add(source_id)
            if trace_sha in seen_traces:
                errors.append(f"reused visual run traceSha256 for {variant}/{key[0]}/{key[1]}")
            seen_traces.add(trace_sha)
        pairs[key] = {"baseline": baseline, "workbench": workbench}
    return pairs, errors


def exclusive_json_write(path: Path, value: dict[str, Any]) -> str:
    payload = json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
    return sha256_bytes(payload)


def pack_one_capture(
    source_root: Path,
    packet_root: Path,
    side: str,
    capture: dict[str, Any],
) -> dict[str, Any]:
    capture_id = capture["captureId"]
    source_path, source_errors = safe_runtime_file(
        source_root,
        capture["path"],
        "screenshots",
        f"blind source {capture_id}",
    )
    if source_path is None or source_errors:
        raise ValueError("; ".join(source_errors))
    relative = f"assets/{side}/{capture_id}.png"
    destination = packet_root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)
    digest = sha256_file(destination)
    if digest != capture["sha256"]:
        raise ValueError(f"blind copy digest mismatch for {capture_id}")
    width, height, chunks = parse_png(destination)
    if png_metadata_leaks_variant(chunks):
        raise ValueError(f"blind copy metadata leaks a variant label for {capture_id}")
    viewport = capture["viewport"]
    if (width, height) != (viewport["width"], viewport["height"]):
        raise ValueError(f"blind copy dimensions changed for {capture_id}")
    return {
        "captureId": capture_id,
        "path": relative,
        "sha256": digest,
        "width": width,
        "height": height,
    }


def build_blind_pack(
    destination: Path,
    seed: str,
    bundles: dict[str, dict[str, Any]],
    pairs: dict[tuple[str, str], dict[str, dict[str, Any]]],
    baseline_root: Path,
    workbench_root: Path,
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[int, list[str]]:
    if destination.exists():
        return 0, [f"blind root already exists; refusing to overwrite: {destination}"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.parent / f".{destination.name}.tmp-{secrets.token_hex(8)}"
    packet_count = 0
    errors: list[str] = []
    try:
        temporary.mkdir()
        for (case_id, trial_id), pair in sorted(pairs.items()):
            bundle = bundles[case_id]
            judge_count = bundle["case"]["minimumJudgesPerTrial"]
            base_assignment = int(
                sha256_bytes(f"{seed}|{case_id}|{trial_id}".encode("utf-8")),
                16,
            ) % 2
            capture_order = [item["captureId"] for item in bundle["fixture"]["captureMatrix"]]
            run_captures = {
                variant: {item["captureId"]: item for item in pair[variant]["captures"]}
                for variant in VARIANTS
            }
            for slot in range(1, judge_count + 1):
                a_variant = VARIANTS[(base_assignment + slot - 1) % 2]
                b_variant = "workbench" if a_variant == "baseline" else "baseline"
                packet_id = "vp-" + sha256_bytes(
                    f"{seed}|{case_id}|{trial_id}|{slot}".encode("utf-8")
                )[:24]
                packet_dir = temporary / "packets" / packet_id
                sides: dict[str, list[dict[str, Any]]] = {}
                for side, variant in (("A", a_variant), ("B", b_variant)):
                    source_root = baseline_root if variant == "baseline" else workbench_root
                    sides[side] = [
                        pack_one_capture(
                            source_root,
                            packet_dir,
                            side,
                            run_captures[variant][capture_id],
                        )
                        for capture_id in capture_order
                    ]
                packet = {
                    "schemaVersion": 1,
                    "packetId": packet_id,
                    "caseId": case_id,
                    "trialId": trial_id,
                    "judgeSlot": slot,
                    "task": {
                        "prompt": bundle["case"]["prompt"],
                        "fixtureSha256": bundle["case"]["fixtureSha256"],
                        "rubricSha256": bundle["case"]["rubricSha256"],
                        "fixture": bundle["fixture"],
                        "rubric": bundle["rubric"],
                    },
                    "sides": sides,
                }
                errors.extend(
                    validate_instance(
                        packet,
                        schemas["eval-blind-packet.schema.json"],
                        registry,
                        f"packet/{packet_id}",
                    )
                )
                if object_leaks_variant(packet):
                    errors.append(f"packet/{packet_id}: public packet leaks a variant label")
                if errors:
                    break
                packet_sha = exclusive_json_write(packet_dir / "packet.json", packet)
                mapping = {
                    "schemaVersion": 1,
                    "packetId": packet_id,
                    "caseId": case_id,
                    "trialId": trial_id,
                    "judgeSlot": slot,
                    "packetSha256": packet_sha,
                    "assignmentNonceSha256": sha256_bytes(
                        f"{seed}|{packet_id}|private".encode("utf-8")
                    ),
                    "assignment": {"A": a_variant, "B": b_variant},
                }
                mapping_errors = validate_instance(
                    mapping,
                    schemas["eval-blind-mapping.schema.json"],
                    registry,
                    f"mapping/{packet_id}",
                )
                if mapping_errors:
                    errors.extend(mapping_errors)
                    break
                exclusive_json_write(
                    temporary / "private-mappings" / f"{packet_id}.json",
                    mapping,
                )
                packet_count += 1
            if errors:
                break
        if errors:
            return packet_count, errors
        temporary.rename(destination)
        return packet_count, []
    except (OSError, ValueError, struct.error) as exc:
        return packet_count, [f"could not build blind pack: {exc}"]
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def load_blind_artifacts(
    blind_root: Path,
    bundles: dict[str, dict[str, Any]],
    pairs: dict[tuple[str, str], dict[str, dict[str, Any]]],
    baseline_root: Path,
    workbench_root: Path,
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    artifacts: dict[str, dict[str, Any]] = {}
    packet_paths = sorted((blind_root / "packets").glob("*/packet.json"))
    for packet_path in packet_paths:
        try:
            packet = load_object(packet_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        packet_id = packet.get("packetId")
        label = str(packet_path)
        errors.extend(
            validate_instance(
                packet,
                schemas["eval-blind-packet.schema.json"],
                registry,
                label,
            )
        )
        if not isinstance(packet_id, str):
            continue
        if packet_path.parent.name != packet_id:
            errors.append(f"{label}: packetId must match packet directory")
        if packet_id in artifacts:
            errors.append(f"duplicate blind packetId: {packet_id}")
            continue
        if object_leaks_variant(packet):
            errors.append(f"{label}: public packet leaks a variant label")
        mapping_path = blind_root / "private-mappings" / f"{packet_id}.json"
        try:
            mapping = load_object(mapping_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_instance(
                mapping,
                schemas["eval-blind-mapping.schema.json"],
                registry,
                str(mapping_path),
            )
        )
        packet_sha = sha256_file(packet_path)
        if mapping.get("packetSha256") != packet_sha:
            errors.append(f"{mapping_path}: packetSha256 does not match packet bytes")
        for field in ("packetId", "caseId", "trialId", "judgeSlot"):
            if mapping.get(field) != packet.get(field):
                errors.append(f"{mapping_path}: {field} does not match its packet")
        case_id = packet.get("caseId")
        trial_id = packet.get("trialId")
        if not isinstance(case_id, str) or not isinstance(trial_id, str):
            continue
        key = (case_id, trial_id)
        if key not in pairs or case_id not in bundles:
            errors.append(f"{label}: packet does not reference a matched visual trial")
            continue
        bundle = bundles[case_id]
        task = packet.get("task")
        if isinstance(task, dict):
            expected_task = {
                "prompt": bundle["case"]["prompt"],
                "fixtureSha256": bundle["case"]["fixtureSha256"],
                "rubricSha256": bundle["case"]["rubricSha256"],
                "fixture": bundle["fixture"],
                "rubric": bundle["rubric"],
            }
            if task != expected_task:
                errors.append(f"{label}: packet task material does not match case bytes")
        assignment = mapping.get("assignment")
        if not isinstance(assignment, dict):
            continue
        packet_dir = packet_path.parent
        target_ids = set(bundle["case"]["expectedCaptureIds"])
        for side in ("A", "B"):
            variant = assignment.get(side)
            if variant not in VARIANTS:
                continue
            run = pairs[key][variant]
            run_captures = {item["captureId"]: item for item in run["captures"]}
            side_captures = packet.get("sides", {}).get(side)
            if not isinstance(side_captures, list):
                continue
            packet_capture_ids = {
                item.get("captureId") for item in side_captures if isinstance(item, dict)
            }
            if packet_capture_ids != target_ids:
                errors.append(f"{label}: side {side} does not cover the case capture matrix")
            for index, capture in enumerate(side_captures):
                if not isinstance(capture, dict):
                    continue
                capture_id = capture.get("captureId")
                if not isinstance(capture_id, str) or capture_id not in run_captures:
                    continue
                source = run_captures[capture_id]
                expected_path = f"assets/{side}/{capture_id}.png"
                if capture.get("path") != expected_path:
                    errors.append(f"{label}: side {side} capture path is not anonymized")
                if capture.get("sha256") != source.get("sha256"):
                    errors.append(f"{label}: side {side} capture digest does not bind to its run")
                viewport = source["viewport"]
                if (capture.get("width"), capture.get("height")) != (
                    viewport["width"],
                    viewport["height"],
                ):
                    errors.append(f"{label}: side {side} capture dimensions do not bind to its run")
                _, png_errors = validate_png_receipt(
                    packet_dir,
                    capture,
                    "assets",
                    f"{label}:sides.{side}[{index}]",
                    viewport["width"],
                    viewport["height"],
                    reject_metadata_leaks=True,
                )
                errors.extend(png_errors)
        artifacts[packet_id] = {
            "packet": packet,
            "mapping": mapping,
            "packetPath": packet_path,
            "packetSha256": packet_sha,
        }
    if not artifacts:
        errors.append(f"no blind packets found under {blind_root / 'packets'}")
    expected_mapping_paths = {
        blind_root / "private-mappings" / f"{packet_id}.json" for packet_id in artifacts
    }
    actual_mapping_paths = set((blind_root / "private-mappings").glob("*.json"))
    for extra in sorted(actual_mapping_paths - expected_mapping_paths):
        errors.append(f"orphan private mapping: {extra}")
    slots_by_trial: dict[tuple[str, str], set[int]] = {}
    for artifact in artifacts.values():
        packet = artifact["packet"]
        key = (packet["caseId"], packet["trialId"])
        slots = slots_by_trial.setdefault(key, set())
        slot = packet["judgeSlot"]
        if slot in slots:
            errors.append(f"duplicate judgeSlot for {key[0]}/{key[1]}: {slot}")
        slots.add(slot)
    for key in pairs:
        required = bundles[key[0]]["case"]["minimumJudgesPerTrial"]
        actual = len(slots_by_trial.get(key, set()))
        if actual < required:
            errors.append(
                f"blind trial {key[0]}/{key[1]} requires at least {required} packet(s), got {actual}"
            )
    return artifacts, errors


def validate_judgment_evidence(
    judgment: dict[str, Any],
    packet: dict[str, Any],
    label: str,
) -> list[str]:
    errors: list[str] = []
    capture_ids = {
        item["captureId"]
        for side in ("A", "B")
        for item in packet["sides"][side]
    }
    for dimension in DIMENSIONS:
        item = judgment["dimensions"].get(dimension)
        if not isinstance(item, dict):
            continue
        verdict = item.get("verdict")
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            continue
        cited_sides: set[str] = set()
        for evidence_item in evidence:
            if not isinstance(evidence_item, dict):
                continue
            capture_id = evidence_item.get("captureId")
            if capture_id not in capture_ids:
                errors.append(
                    f"{label}: dimensions.{dimension} cites unknown captureId {capture_id!r}"
                )
            side = evidence_item.get("side")
            if isinstance(side, str):
                cited_sides.add(side)
        if verdict in {"A", "B"} and verdict not in cited_sides and "both" not in cited_sides:
            errors.append(
                f"{label}: dimensions.{dimension} must cite evidence for preferred side {verdict}"
            )
        if verdict == "tie" and not (
            "both" in cited_sides or {"A", "B"}.issubset(cited_sides)
        ):
            errors.append(
                f"{label}: dimensions.{dimension} tie must cite both sides"
            )
    return errors


def load_judgments(
    judgments_root: Path,
    artifacts: dict[str, dict[str, Any]],
    bundles: dict[str, dict[str, Any]],
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    judgments: dict[str, dict[str, Any]] = {}
    seen_source_ids: set[str] = set()
    judge_ids_by_trial: dict[tuple[str, str], set[str]] = {}
    if not judgments_root.is_dir():
        return {}, [f"judgments directory does not exist: {judgments_root}"]
    for path in sorted(judgments_root.glob("*.json")):
        try:
            judgment = load_object(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_instance(
                judgment,
                schemas["eval-blind-judgment.schema.json"],
                registry,
                str(path),
            )
        )
        packet_id = judgment.get("packetId")
        if not isinstance(packet_id, str) or packet_id not in artifacts:
            errors.append(f"{path}: judgment references an unknown blind packet")
            continue
        if packet_id in judgments:
            errors.append(f"duplicate judgment for packet {packet_id}")
            continue
        artifact = artifacts[packet_id]
        packet = artifact["packet"]
        if judgment.get("packetSha256") != artifact["packetSha256"]:
            errors.append(f"{path}: packetSha256 does not match blind packet bytes")
        case_id = packet["caseId"]
        if judgment.get("rubricSha256") != bundles[case_id]["case"]["rubricSha256"]:
            errors.append(f"{path}: rubricSha256 does not match the visual case")
        if object_leaks_variant(judgment):
            errors.append(f"{path}: judgment leaks a variant label; use only A/B")
        receipt = judgment.get("judgeReceipt")
        if isinstance(receipt, dict):
            judge_id = receipt.get("judgeId")
            source_id = receipt.get("sourceId")
            for field, value in (("judgeId", judge_id), ("sourceId", source_id)):
                if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_IDS:
                    errors.append(f"{path}: {field} cannot be a placeholder")
            if isinstance(source_id, str):
                if source_id in seen_source_ids:
                    errors.append(f"{path}: judge sourceId is reused: {source_id}")
                seen_source_ids.add(source_id)
            key = (case_id, packet["trialId"])
            trial_judges = judge_ids_by_trial.setdefault(key, set())
            if isinstance(judge_id, str):
                if judge_id in trial_judges:
                    errors.append(
                        f"{path}: judgeId is not independent within {case_id}/{packet['trialId']}"
                    )
                trial_judges.add(judge_id)
            trace_path, trace_errors = validate_file_receipt(
                judgments_root,
                receipt.get("tracePath"),
                receipt.get("traceSha256"),
                "judge-traces",
                f"{path}:judgeTrace",
            )
            errors.extend(trace_errors)
            if trace_path is not None and not trace_errors:
                try:
                    if bytes_leak_variant(trace_path.read_bytes()):
                        errors.append(
                            f"{path}: verified judge trace leaks a variant label"
                        )
                except OSError as exc:
                    errors.append(f"{path}: could not scan verified judge trace: {exc}")
        if isinstance(judgment.get("dimensions"), dict):
            errors.extend(validate_judgment_evidence(judgment, packet, str(path)))
        judgments[packet_id] = judgment
    missing = sorted(set(artifacts) - set(judgments))
    extras = sorted(set(judgments) - set(artifacts))
    for packet_id in missing:
        errors.append(f"missing independent judgment for packet {packet_id}")
    for packet_id in extras:
        errors.append(f"judgment references unexpected packet {packet_id}")
    expected_trials = {
        (artifact["packet"]["caseId"], artifact["packet"]["trialId"])
        for artifact in artifacts.values()
    }
    for key in sorted(expected_trials):
        required = bundles[key[0]]["case"]["minimumJudgesPerTrial"]
        actual = len(judge_ids_by_trial.get(key, set()))
        if actual < required:
            errors.append(
                f"visual trial {key[0]}/{key[1]} requires at least {required} "
                f"independent judge receipt(s), got {actual}"
            )
    return judgments, errors


def empty_trial_count() -> dict[str, Any]:
    return {
        "baselineWins": 0,
        "workbenchWins": 0,
        "ties": 0,
        "notJudgeable": 0,
        "disagreement": False,
    }


def empty_suite_count() -> dict[str, int]:
    return {
        "baselineWins": 0,
        "workbenchWins": 0,
        "ties": 0,
        "notJudgeable": 0,
        "disagreementTrials": 0,
    }


def aggregate_scorecard(
    bundles: dict[str, dict[str, Any]],
    pairs: dict[tuple[str, str], dict[str, dict[str, Any]]],
    artifacts: dict[str, dict[str, Any]],
    judgments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    suite_dimensions = {dimension: empty_suite_count() for dimension in DIMENSIONS}
    packets_by_trial: dict[tuple[str, str], list[str]] = {}
    for packet_id, artifact in artifacts.items():
        packet = artifact["packet"]
        key = (packet["caseId"], packet["trialId"])
        packets_by_trial.setdefault(key, []).append(packet_id)
    case_rows: dict[str, list[dict[str, Any]]] = {}
    for key in sorted(pairs):
        trial_dimensions = {dimension: empty_trial_count() for dimension in DIMENSIONS}
        verdict_sets = {dimension: set() for dimension in DIMENSIONS}
        packet_ids = sorted(packets_by_trial.get(key, []))
        for packet_id in packet_ids:
            mapping = artifacts[packet_id]["mapping"]["assignment"]
            judgment = judgments[packet_id]
            for dimension in DIMENSIONS:
                verdict = judgment["dimensions"][dimension]["verdict"]
                if verdict in {"A", "B"}:
                    unblinded = mapping[verdict]
                    count_key = "baselineWins" if unblinded == "baseline" else "workbenchWins"
                    verdict_sets[dimension].add(unblinded)
                elif verdict == "tie":
                    count_key = "ties"
                    verdict_sets[dimension].add("tie")
                else:
                    count_key = "notJudgeable"
                    verdict_sets[dimension].add("not-judgeable")
                trial_dimensions[dimension][count_key] += 1
                suite_dimensions[dimension][count_key] += 1
        for dimension in DIMENSIONS:
            disagreed = len(verdict_sets[dimension]) > 1
            trial_dimensions[dimension]["disagreement"] = disagreed
            if disagreed:
                suite_dimensions[dimension]["disagreementTrials"] += 1
        case_rows.setdefault(key[0], []).append(
            {
                "trialId": key[1],
                "judgeCount": len(packet_ids),
                "dimensions": trial_dimensions,
            }
        )
    judge_source_ids = sorted(
        judgment["judgeReceipt"]["sourceId"] for judgment in judgments.values()
    )
    return {
        "schemaVersion": 1,
        "statement": SCORECARD_STATEMENT,
        "visualQualityScored": True,
        "causalUpliftClaimed": False,
        "caseCount": len(case_rows),
        "trialCount": len(pairs),
        "judgmentCount": len(judgments),
        "dimensions": suite_dimensions,
        "cases": [
            {"caseId": case_id, "trials": trials}
            for case_id, trials in sorted(case_rows.items())
        ],
        "provenance": {
            "fixtureSha256s": sorted(
                {bundle["case"]["fixtureSha256"] for bundle in bundles.values()}
            ),
            "rubricSha256s": sorted(
                {bundle["case"]["rubricSha256"] for bundle in bundles.values()}
            ),
            "packetSha256s": sorted(
                {artifact["packetSha256"] for artifact in artifacts.values()}
            ),
            "judgeSourceIds": judge_source_ids,
        },
    }


def write_scorecard(path: Path, scorecard: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(scorecard))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("fixtures", "blind-pack", "visual-paired"),
        required=True,
    )
    parser.add_argument("--cases", default="evals/design-cases")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--baseline-results")
    parser.add_argument("--workbench-results")
    parser.add_argument("--blind-root")
    parser.add_argument("--judgments")
    parser.add_argument("--scorecard")
    return parser


def parser_contract(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    paired = (args.baseline_results, args.workbench_results, args.blind_root)
    if args.mode == "fixtures":
        if any(value is not None for value in (*paired, args.judgments, args.scorecard)):
            parser.error("fixtures mode accepts only --cases and optional --case-id")
    elif args.mode == "blind-pack":
        if any(value is None for value in paired):
            parser.error(
                "blind-pack mode requires --baseline-results, --workbench-results, and --blind-root"
            )
        if args.judgments is not None or args.scorecard is not None:
            parser.error("blind-pack mode does not accept judgments or scorecard arguments")
    elif args.mode == "visual-paired":
        required = (*paired, args.judgments, args.scorecard)
        if any(value is None for value in required):
            parser.error(
                "visual-paired mode requires baseline/workbench results, blind root, "
                "judgments, and scorecard"
            )


def print_errors(heading: str, errors: list[str]) -> None:
    print(heading, file=sys.stderr)
    for error in sorted(set(errors)):
        print(f"- {error}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    parser_contract(parser, args)
    repo_root = Path(__file__).resolve().parents[1]
    cases_root = resolve_path(repo_root, args.cases)
    try:
        registry, schemas = build_registry(repo_root / "schemas")
        all_bundles, errors = load_cases(repo_root, cases_root, registry, schemas)
    except (KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    bundles, filter_errors = filter_cases(all_bundles, args.case_id)
    errors.extend(filter_errors)
    if errors:
        print_errors(
            "Design fixture validation failed. NO visual quality was scored:",
            errors,
        )
        return 1
    if args.mode == "fixtures":
        print(
            f"Design fixture validation passed: {len(bundles)} case(s). "
            "NO visual quality was scored."
        )
        return 0

    baseline_root = resolve_path(repo_root, args.baseline_results)
    workbench_root = resolve_path(repo_root, args.workbench_results)
    blind_root = resolve_path(repo_root, args.blind_root)
    errors = runtime_location_errors(repo_root, baseline_root, "baseline results")
    errors.extend(runtime_location_errors(repo_root, workbench_root, "workbench results"))
    errors.extend(runtime_location_errors(repo_root, blind_root, "blind packet root"))
    if args.mode == "visual-paired":
        judgments_root = resolve_path(repo_root, args.judgments)
        scorecard_path = resolve_path(repo_root, args.scorecard)
        errors.extend(runtime_location_errors(repo_root, judgments_root, "judgments"))
        errors.extend(runtime_location_errors(repo_root, scorecard_path, "visual scorecard"))
    if errors:
        print_errors(
            "Visual paired storage preflight failed. NO visual quality was scored:",
            errors,
        )
        return 1
    baseline_runs, baseline_errors = load_runs(
        baseline_root,
        "baseline",
        set(all_bundles),
        bundles,
        registry,
        schemas,
    )
    workbench_runs, workbench_errors = load_runs(
        workbench_root,
        "workbench",
        set(all_bundles),
        bundles,
        registry,
        schemas,
    )
    pairs, pair_errors = validate_pairs(bundles, baseline_runs, workbench_runs)
    errors = [*baseline_errors, *workbench_errors, *pair_errors]
    if errors:
        print_errors(
            "Visual paired preflight failed. NO visual quality was scored:",
            errors,
        )
        return 1

    if args.mode == "blind-pack":
        packet_count, pack_errors = build_blind_pack(
            blind_root,
            secrets.token_hex(32),
            bundles,
            pairs,
            baseline_root,
            workbench_root,
            registry,
            schemas,
        )
        if pack_errors:
            print_errors(
                "Blind packet creation failed. NO visual quality was scored:",
                pack_errors,
            )
            return 1
        print(
            f"Blind packet creation passed: {packet_count} anonymized packet(s). "
            "NO visual quality was scored."
        )
        return 0

    artifacts, artifact_errors = load_blind_artifacts(
        blind_root,
        bundles,
        pairs,
        baseline_root,
        workbench_root,
        registry,
        schemas,
    )
    judgments, judgment_errors = load_judgments(
        judgments_root,
        artifacts,
        bundles,
        registry,
        schemas,
    )
    errors = [*artifact_errors, *judgment_errors]
    if errors:
        print_errors(
            "Blind visual scoring failed. NO scorecard was produced:",
            errors,
        )
        return 1
    scorecard = aggregate_scorecard(bundles, pairs, artifacts, judgments)
    scorecard_errors = validate_instance(
        scorecard,
        schemas["eval-visual-scorecard.schema.json"],
        registry,
        "visual-scorecard",
    )
    if scorecard_errors:
        print_errors("Generated visual scorecard is invalid:", scorecard_errors)
        return 2
    try:
        write_scorecard(scorecard_path, scorecard)
    except OSError as exc:
        print(f"Could not write visual scorecard: {exc}", file=sys.stderr)
        return 2
    print(
        f"Blind visual preferences aggregated from {len(judgments)} judgment(s); "
        f"scorecard: {scorecard_path}. No causal uplift was inferred.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
