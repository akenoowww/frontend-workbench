#!/usr/bin/env python3
"""Validate eval fixtures and score structured behavioral results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
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
        fixture_outputs = {item.get("id") for item in fixture.get("outputs", []) if isinstance(item, dict)}
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="evals/cases")
    parser.add_argument("--results", help="Optional directory of structured model result JSON files")
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    cases_root = (repo_root / args.cases).resolve() if not Path(args.cases).is_absolute() else Path(args.cases).resolve()
    try:
        registry, schemas = build_registry(repo_root / "schemas")
        cases, errors = load_cases(repo_root, cases_root, registry, schemas)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.results:
        results_root = Path(args.results).expanduser().resolve()
        results_by_case: dict[str, dict[str, Any]] = {}
        for path in sorted(results_root.glob("*.json")):
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
            if isinstance(case_id, str):
                if case_id in results_by_case:
                    errors.append(f"duplicate eval result for case {case_id}")
                results_by_case[case_id] = result
        for case_id, case in cases.items():
            result = results_by_case.get(case_id)
            if result is None:
                errors.append(f"missing eval result for case {case_id}")
                continue
            for failure in score_result(case, result):
                errors.append(f"{case_id}: {failure}")
        unknown_results = set(results_by_case) - set(cases)
        for case_id in sorted(unknown_results):
            errors.append(f"result references unknown case {case_id}")

    if errors:
        print("Eval validation failed:")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    mode = "fixtures and results" if args.results else "fixtures"
    print(f"Eval {mode} passed: {len(cases)} case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
