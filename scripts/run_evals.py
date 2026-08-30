#!/usr/bin/env python3
"""Validate eval fixtures or score paired measured behavioral results."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as exc:  # pragma: no cover
    print(
        "error: install development dependencies with "
        "`python3 -m pip install -r requirements-dev.txt`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


VARIANTS = ("baseline", "workbench")
USAGE_FIELDS = (
    "inputTokens",
    "cachedInputTokens",
    "outputTokens",
    "reasoningTokens",
    "modelCalls",
    "toolCalls",
    "durationMs",
)
PLACEHOLDER_SOURCE_IDS = {"fixture", "none", "synthetic", "test", "unknown"}


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value


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
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    errors: list[str] = []
    for failure in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in failure.absolute_path) or "$"
        errors.append(f"{label}:{location}: {failure.message}")
    return errors


def load_cases(
    repo_root: Path,
    cases_root: Path,
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    cases: dict[str, dict[str, Any]] = {}
    for path in sorted(cases_root.glob("*.json")):
        try:
            case = load_object(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_instance(case, schemas["eval-case.schema.json"], registry, str(path)))
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id != path.stem:
                errors.append(f"{path}: case id must match its filename")
            if case_id in cases:
                errors.append(f"duplicate eval case ID: {case_id}")
            cases[case_id] = case
        fixture_value = case.get("contractFixture")
        if not isinstance(fixture_value, str):
            continue
        fixture_path = (repo_root / fixture_value).resolve()
        fixtures_root = (repo_root / "evals" / "fixtures").resolve()
        try:
            fixture_path.relative_to(fixtures_root)
            fixture = load_object(fixture_path)
        except (ValueError, OSError) as exc:
            errors.append(f"{path}: invalid fixture: {exc}")
            continue
        errors.extend(
            validate_instance(
                fixture,
                schemas["deliverable-coverage.schema.json"],
                registry,
                str(fixture_path),
            )
        )
        fixture_outputs = {
            item.get("id") for item in fixture.get("outputs", []) if isinstance(item, dict)
        }
        expected_outputs = set(case.get("expected", {}).get("plannedOutputIds", []))
        if fixture_outputs != expected_outputs:
            errors.append(
                f"{path}: expected plannedOutputIds must exactly match its contract fixture"
            )
    if not cases:
        errors.append(f"no eval cases found under {cases_root}")
    return cases, errors


def score_result(case: dict[str, Any], result: dict[str, Any]) -> list[str]:
    expected = case["expected"]
    failures: list[str] = []
    for field in ("plannedOutputIds", "completedOutputIds", "missingOutputIds"):
        if set(result[field]) != set(expected[field]):
            failures.append(f"{field} expected {expected[field]!r}, got {result[field]!r}")
    if result["finalStatus"] != expected["finalStatus"]:
        failures.append(
            f"finalStatus expected {expected['finalStatus']!r}, got {result['finalStatus']!r}"
        )
    invoked = set(result["invokedSkills"])
    missing_skills = set(expected["requiredSkills"]) - invoked
    forbidden_skills = set(expected["forbiddenSkills"]) & invoked
    if missing_skills:
        failures.append(f"missing required skills: {sorted(missing_skills)!r}")
    if forbidden_skills:
        failures.append(f"invoked forbidden skills: {sorted(forbidden_skills)!r}")
    transformations = set(result["transformations"])
    missing_transformations = set(expected["requiredTransformations"]) - transformations
    forbidden_transformations = set(expected["forbiddenTransformations"]) & transformations
    if missing_transformations:
        failures.append(f"missing required transformations: {sorted(missing_transformations)!r}")
    if forbidden_transformations:
        failures.append(f"used forbidden transformations: {sorted(forbidden_transformations)!r}")
    if result["hostFilesOutsideRuntime"]:
        failures.append(
            "created host files outside .frontend-workbench: "
            + ", ".join(result["hostFilesOutsideRuntime"])
        )
    return failures


def prompt_sha256(case: dict[str, Any]) -> str:
    return hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest()


def validate_result_semantics(
    result: dict[str, Any],
    label: str,
    case: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    usage = result.get("usage")
    if isinstance(usage, dict):
        input_tokens = usage.get("inputTokens")
        cached_tokens = usage.get("cachedInputTokens")
        output_tokens = usage.get("outputTokens")
        reasoning_tokens = usage.get("reasoningTokens")
        if isinstance(input_tokens, int) and isinstance(cached_tokens, int):
            if cached_tokens > input_tokens:
                errors.append(f"{label}: cachedInputTokens cannot exceed inputTokens")
        if isinstance(output_tokens, int) and isinstance(reasoning_tokens, int):
            if reasoning_tokens > output_tokens:
                errors.append(f"{label}: reasoningTokens cannot exceed outputTokens")
        model_calls = usage.get("modelCalls")
        duration_ms = usage.get("durationMs")
        if isinstance(model_calls, int) and model_calls < 1:
            errors.append(f"{label}: modelCalls must be at least 1")
        if isinstance(duration_ms, int) and duration_ms < 1:
            errors.append(f"{label}: durationMs must be at least 1")
    defects = result.get("defects")
    if isinstance(defects, dict):
        seen: set[str] = set()
        for category in ("outcome", "fidelity"):
            category_defects = defects.get(category)
            if not isinstance(category_defects, list):
                continue
            for defect in category_defects:
                if not isinstance(defect, dict) or not isinstance(defect.get("id"), str):
                    continue
                defect_id = defect["id"]
                if defect_id in seen:
                    errors.append(f"{label}: duplicate defect id {defect_id!r}")
                seen.add(defect_id)
    evidence = result.get("evidence")
    if isinstance(evidence, dict):
        capture_status = evidence.get("captureStatus")
        outcome_defects = defects.get("outcome") if isinstance(defects, dict) else None
        if capture_status == "complete" and isinstance(usage, dict):
            for field in ("inputTokens", "outputTokens"):
                value = usage.get(field)
                if isinstance(value, int) and value < 1:
                    errors.append(
                        f"{label}: {field} must be positive for a complete capture"
                    )
        if capture_status == "failed":
            if not isinstance(outcome_defects, list) or not outcome_defects:
                errors.append(
                    f"{label}: failed capture requires an explicit outcome defect"
                )
            if result.get("finalStatus") == "complete":
                errors.append(f"{label}: failed capture cannot have finalStatus 'complete'")
        source_id = evidence.get("sourceId")
        if isinstance(source_id, str):
            normalized_source_id = source_id.strip().lower()
            if normalized_source_id in PLACEHOLDER_SOURCE_IDS:
                errors.append(f"{label}: sourceId cannot be a placeholder")
            if isinstance(result.get("caseId"), str) and source_id == result["caseId"]:
                errors.append(f"{label}: sourceId must identify a trace, not the eval case")
        trace_digest = evidence.get("traceSha256")
        prompt_digest = evidence.get("promptSha256")
        if isinstance(trace_digest, str):
            if len(set(trace_digest.lower())) < 2:
                errors.append(f"{label}: traceSha256 cannot be a placeholder digest")
            if isinstance(prompt_digest, str) and trace_digest == prompt_digest:
                errors.append(f"{label}: traceSha256 cannot reuse promptSha256")
        if case is not None and isinstance(prompt_digest, str):
            expected_prompt_digest = prompt_sha256(case)
            if prompt_digest != expected_prompt_digest:
                errors.append(
                    f"{label}: promptSha256 does not match eval case {case['id']!r}"
                )
    return errors


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_trace_evidence(
    result: dict[str, Any],
    results_root: Path,
    label: str,
) -> list[str]:
    evidence = result.get("evidence")
    if not isinstance(evidence, dict):
        return [f"{label}: trace evidence receipt is required"]
    trace_value = evidence.get("tracePath")
    if not isinstance(trace_value, str):
        return [f"{label}: tracePath receipt is required"]
    relative = PurePosixPath(trace_value)
    if (
        relative.is_absolute()
        or not relative.parts
        or relative.parts[0] != "traces"
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.as_posix() != trace_value
    ):
        return [
            f"{label}: tracePath must be a canonical relative path under traces/"
        ]

    root = results_root.resolve()
    candidate = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return [f"{label}: tracePath must not traverse a symlink: {trace_value}"]
    if not candidate.exists():
        return [f"{label}: trace file does not exist: {trace_value}"]
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        return [f"{label}: tracePath escapes its result root: {trace_value}: {exc}"]
    if not resolved.is_file():
        return [f"{label}: tracePath is not a regular file: {trace_value}"]
    try:
        if resolved.stat().st_size == 0:
            return [f"{label}: trace file must not be empty: {trace_value}"]
        actual_digest = sha256_file(resolved)
    except OSError as exc:
        return [f"{label}: could not read trace file {trace_value}: {exc}"]
    expected_digest = evidence.get("traceSha256")
    if not isinstance(expected_digest, str) or actual_digest != expected_digest:
        return [
            f"{label}: traceSha256 does not match trace file bytes: {trace_value}"
        ]
    return []


def result_location_errors(repo_root: Path, results_root: Path, variant: str) -> list[str]:
    try:
        results_root.relative_to(repo_root)
    except ValueError:
        return []
    runtime_root = (repo_root / "evals" / "results").resolve()
    try:
        results_root.relative_to(runtime_root)
    except ValueError:
        return [
            f"{variant} raw results inside the repository must be under ignored "
            f"{runtime_root}"
        ]
    ignore_file = repo_root / ".gitignore"
    try:
        ignored = "/evals/results/" in ignore_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        ignored = False
    if not ignored:
        return ["root .gitignore must contain the exact line '/evals/results/'"]
    return []


def load_results(
    results_root: Path,
    variant: str,
    cases: dict[str, dict[str, Any]],
    registry: Registry,
    schemas: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    results: dict[str, dict[str, Any]] = {}
    if not results_root.is_dir():
        return {}, [f"{variant} results directory does not exist: {results_root}"]
    paths = sorted(results_root.glob("*.json"))
    if not paths:
        errors.append(f"no {variant} result JSON files found under {results_root}")
    for path in paths:
        try:
            result = load_object(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        errors.extend(
            validate_instance(
                result,
                schemas["eval-result.schema.json"],
                registry,
                str(path),
            )
        )
        case_id = result.get("caseId")
        case = cases.get(case_id) if isinstance(case_id, str) else None
        errors.extend(validate_result_semantics(result, str(path), case))
        errors.extend(validate_trace_evidence(result, results_root, str(path)))
        if result.get("variant") != variant:
            errors.append(
                f"{path}: expected variant {variant!r}, got {result.get('variant')!r}"
            )
        if isinstance(case_id, str):
            if case_id in results:
                errors.append(f"duplicate {variant} eval result for case {case_id}")
            results[case_id] = result
    return results, errors


def validate_evidence_receipts(
    baseline_results: dict[str, dict[str, Any]],
    workbench_results: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    seen_sources: dict[tuple[str, str], str] = {}
    seen_traces: dict[str, str] = {}
    seen_trace_paths: dict[str, str] = {}
    for variant, results in (
        ("baseline", baseline_results),
        ("workbench", workbench_results),
    ):
        for case_id, result in sorted(results.items()):
            evidence = result.get("evidence")
            if not isinstance(evidence, dict):
                continue
            label = f"{variant}/{case_id}"
            source_kind = evidence.get("sourceKind")
            source_id = evidence.get("sourceId")
            if isinstance(source_kind, str) and isinstance(source_id, str):
                source_key = (source_kind, source_id)
                previous = seen_sources.get(source_key)
                if previous is not None:
                    errors.append(
                        f"duplicate evidence source receipt for {previous} and {label}"
                    )
                seen_sources[source_key] = label
            trace_digest = evidence.get("traceSha256")
            if isinstance(trace_digest, str):
                previous = seen_traces.get(trace_digest)
                if previous is not None:
                    errors.append(
                        f"duplicate traceSha256 receipt for {previous} and {label}"
                    )
                seen_traces[trace_digest] = label
            trace_path = evidence.get("tracePath")
            if isinstance(trace_path, str):
                previous = seen_trace_paths.get(trace_path)
                if previous is not None:
                    errors.append(
                        f"duplicate tracePath receipt for {previous} and {label}"
                    )
                seen_trace_paths[trace_path] = label
    return errors


def validate_result_coverage(
    cases: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
    variant: str,
) -> list[str]:
    errors = [
        f"missing {variant} eval result for case {case_id}"
        for case_id in sorted(set(cases) - set(results))
    ]
    errors.extend(
        f"{variant} result references unknown case {case_id}"
        for case_id in sorted(set(results) - set(cases))
    )
    return errors


def usage_with_total(result: dict[str, Any]) -> dict[str, int]:
    usage = result["usage"]
    measured = {field: usage[field] for field in USAGE_FIELDS}
    measured["totalTokens"] = usage["inputTokens"] + usage["outputTokens"]
    return measured


def measure_case(case: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    assertion_failures = score_result(case, result)
    defect_counts = {
        "outcome": len(result["defects"]["outcome"]),
        "fidelity": len(result["defects"]["fidelity"]),
    }
    return {
        "behavioralPassed": not assertion_failures and not any(defect_counts.values()),
        "assertionFailures": len(assertion_failures),
        "defects": defect_counts,
        "usage": usage_with_total(result),
        "evidence": dict(result["evidence"]),
    }


def summarize(measurements: list[dict[str, Any]]) -> dict[str, Any]:
    usage_fields = (*USAGE_FIELDS, "totalTokens")
    passes = sum(1 for item in measurements if item["behavioralPassed"])
    return {
        "behavioralPasses": passes,
        "behavioralPassRate": round(passes / len(measurements), 6),
        "assertionFailures": sum(item["assertionFailures"] for item in measurements),
        "defects": {
            category: sum(item["defects"][category] for item in measurements)
            for category in ("outcome", "fidelity")
        },
        "usage": {
            field: sum(item["usage"][field] for item in measurements)
            for field in usage_fields
        },
    }


def percent_change(baseline: int | float, workbench: int | float) -> float | None:
    if baseline == 0:
        return None
    return round(((workbench - baseline) / baseline) * 100, 6)


def build_scorecard(
    cases: dict[str, dict[str, Any]],
    baseline_results: dict[str, dict[str, Any]],
    workbench_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_rows: list[dict[str, Any]] = []
    baseline_measurements: list[dict[str, Any]] = []
    workbench_measurements: list[dict[str, Any]] = []
    for case_id, case in sorted(cases.items()):
        baseline = measure_case(case, baseline_results[case_id])
        workbench = measure_case(case, workbench_results[case_id])
        baseline_measurements.append(baseline)
        workbench_measurements.append(workbench)
        case_rows.append(
            {"caseId": case_id, "baseline": baseline, "workbench": workbench}
        )
    baseline_summary = summarize(baseline_measurements)
    workbench_summary = summarize(workbench_measurements)
    baseline_usage = baseline_summary["usage"]
    workbench_usage = workbench_summary["usage"]
    return {
        "schemaVersion": 1,
        "caseCount": len(cases),
        "variants": {
            "baseline": baseline_summary,
            "workbench": workbench_summary,
        },
        "change": {
            "behavioralPasses": (
                workbench_summary["behavioralPasses"]
                - baseline_summary["behavioralPasses"]
            ),
            "behavioralPassRatePoints": round(
                (
                    workbench_summary["behavioralPassRate"]
                    - baseline_summary["behavioralPassRate"]
                )
                * 100,
                6,
            ),
            "assertionFailures": (
                workbench_summary["assertionFailures"]
                - baseline_summary["assertionFailures"]
            ),
            "assertionFailuresPercent": percent_change(
                baseline_summary["assertionFailures"],
                workbench_summary["assertionFailures"],
            ),
            "outcomeDefects": (
                workbench_summary["defects"]["outcome"]
                - baseline_summary["defects"]["outcome"]
            ),
            "outcomeDefectsPercent": percent_change(
                baseline_summary["defects"]["outcome"],
                workbench_summary["defects"]["outcome"],
            ),
            "fidelityDefects": (
                workbench_summary["defects"]["fidelity"]
                - baseline_summary["defects"]["fidelity"]
            ),
            "fidelityDefectsPercent": percent_change(
                baseline_summary["defects"]["fidelity"],
                workbench_summary["defects"]["fidelity"],
            ),
            **{
                f"{field}Percent": percent_change(
                    baseline_usage[field], workbench_usage[field]
                )
                for field in (
                    "inputTokens",
                    "cachedInputTokens",
                    "outputTokens",
                    "reasoningTokens",
                    "totalTokens",
                    "modelCalls",
                    "toolCalls",
                    "durationMs",
                )
            },
        },
        "cases": case_rows,
    }


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (repo_root / path).resolve()


def write_scorecard(scorecard: dict[str, Any], destination: str, repo_root: Path) -> str:
    payload = json.dumps(scorecard, sort_keys=True, separators=(",", ":")) + "\n"
    if destination == "-":
        sys.stdout.write(payload)
        return "stdout"
    path = resolve_repo_path(repo_root, destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return str(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("fixtures", "paired"),
        required=True,
        help="fixtures validates static cases only; paired scores measured baseline/workbench results",
    )
    parser.add_argument("--cases", default="evals/cases")
    parser.add_argument("--baseline-results")
    parser.add_argument("--workbench-results")
    parser.add_argument("--scorecard")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paired_values = (args.baseline_results, args.workbench_results, args.scorecard)
    if args.mode == "fixtures" and any(value is not None for value in paired_values):
        parser.error("fixture mode does not accept result or scorecard arguments")
    if args.mode == "paired" and any(value is None for value in paired_values):
        parser.error(
            "paired mode requires --baseline-results, --workbench-results, and --scorecard"
        )

    repo_root = Path(__file__).resolve().parents[1]
    cases_root = resolve_repo_path(repo_root, args.cases)
    try:
        registry, schemas = build_registry(repo_root / "schemas")
        cases, errors = load_cases(repo_root, cases_root, registry, schemas)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if errors:
        label = "Fixture validation" if args.mode == "fixtures" else "Paired scoring preflight"
        print(f"{label} failed; behavioral results were not scored:", file=sys.stderr)
        for error in sorted(set(errors)):
            print(f"- {error}", file=sys.stderr)
        return 1

    if args.mode == "fixtures":
        print(
            f"Fixture validation passed: {len(cases)} case(s). "
            "NO behavioral results were scored."
        )
        return 0

    baseline_root = resolve_repo_path(repo_root, args.baseline_results)
    workbench_root = resolve_repo_path(repo_root, args.workbench_results)
    errors = result_location_errors(repo_root, baseline_root, "baseline")
    errors.extend(result_location_errors(repo_root, workbench_root, "workbench"))
    baseline_results, baseline_errors = load_results(
        baseline_root, "baseline", cases, registry, schemas
    )
    workbench_results, workbench_errors = load_results(
        workbench_root, "workbench", cases, registry, schemas
    )
    errors.extend(baseline_errors)
    errors.extend(workbench_errors)
    errors.extend(validate_result_coverage(cases, baseline_results, "baseline"))
    errors.extend(validate_result_coverage(cases, workbench_results, "workbench"))
    errors.extend(validate_evidence_receipts(baseline_results, workbench_results))
    if errors:
        print(
            "Paired behavioral scoring failed; no scorecard was produced:",
            file=sys.stderr,
        )
        for error in sorted(set(errors)):
            print(f"- {error}", file=sys.stderr)
        return 1

    scorecard = build_scorecard(cases, baseline_results, workbench_results)
    scorecard_errors = validate_instance(
        scorecard,
        schemas["eval-scorecard.schema.json"],
        registry,
        "scorecard",
    )
    if scorecard_errors:
        print("Generated scorecard is invalid:", file=sys.stderr)
        for error in scorecard_errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    try:
        destination = write_scorecard(scorecard, args.scorecard, repo_root)
    except OSError as exc:
        print(f"Could not write scorecard: {exc}", file=sys.stderr)
        return 2

    baseline_passes = scorecard["variants"]["baseline"]["behavioralPasses"]
    workbench_passes = scorecard["variants"]["workbench"]["behavioralPasses"]
    passed = workbench_passes == len(cases)
    status = "passed" if passed else "failed"
    print(
        f"Paired behavioral eval {status}: baseline {baseline_passes}/{len(cases)}, "
        f"workbench {workbench_passes}/{len(cases)}; scorecard: {destination}",
        file=sys.stderr,
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
