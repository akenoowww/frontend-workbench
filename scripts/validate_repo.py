#!/usr/bin/env python3
"""Validate Frontend Workbench packaging, skills, schemas, and repository hygiene."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError as exc:  # pragma: no cover - exercised by clean environments
    print(
        "error: install development dependencies with "
        "`python3 -m pip install -r requirements-dev.txt`",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_DIRS = {".git", ".frontend-workbench", ".venv", ".pytest_cache", "__pycache__"}
ROOT_MARKDOWN = {"README.md", "AGENTS.md", "CHANGELOG.md"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
TODO_MARKER = "[" + "TODO:"


def load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing {path.relative_to(path.parents[1]) if len(path.parents) > 1 else path}")
        return None
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON in {path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{path} must contain a JSON object")
        return None
    return value


def iter_repo_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if relative.parts[:2] == ("evals", "results"):
            continue
        yield path, relative


def validate_manifests(root: Path, errors: list[str], release: bool) -> None:
    portable = load_json(root / "plugin.json", errors)
    codex = load_json(root / ".codex-plugin" / "plugin.json", errors)
    marketplace = load_json(root / ".agents" / "plugins" / "marketplace.json", errors)
    if portable is None or codex is None:
        return
    for field in ("name", "version"):
        if portable.get(field) != codex.get(field):
            errors.append(f"plugin manifests disagree on {field}")
    version = codex.get("version")
    if not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None:
        errors.append("plugin version must be strict semver")
    prompts = codex.get("interface", {}).get("defaultPrompt")
    if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
        errors.append("Codex interface.defaultPrompt must contain one to three prompts")
    else:
        for index, prompt in enumerate(prompts):
            if not isinstance(prompt, str) or not prompt.strip():
                errors.append(f"Codex defaultPrompt[{index}] must be non-empty")
            elif len(prompt) > 128:
                errors.append(f"Codex defaultPrompt[{index}] is {len(prompt)} characters; maximum is 128")
    if release and marketplace is not None and isinstance(version, str):
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or len(plugins) != 1 or not isinstance(plugins[0], dict):
            errors.append("release marketplace must contain exactly one plugin entry")
        else:
            source = plugins[0].get("source")
            actual_ref = source.get("ref") if isinstance(source, dict) else None
            expected_ref = f"v{version}"
            if actual_ref != expected_ref:
                errors.append(f"release marketplace ref must be {expected_ref!r}, got {actual_ref!r}")


def validate_skill(skill_root: Path, errors: list[str]) -> None:
    skill_file = skill_root / "SKILL.md"
    if not skill_file.is_file():
        errors.append(f"skill {skill_root.name!r} is missing SKILL.md")
        return
    contents = skill_file.read_text(encoding="utf-8")
    if not contents.startswith("---\n"):
        errors.append(f"{skill_file} must start with YAML frontmatter")
        return
    end = contents.find("\n---", 4)
    if end == -1:
        errors.append(f"{skill_file} frontmatter is not closed")
        return
    try:
        frontmatter = yaml.safe_load(contents[4:end])
    except yaml.YAMLError as exc:
        errors.append(f"{skill_file} frontmatter is invalid YAML: {exc}")
        return
    if not isinstance(frontmatter, dict):
        errors.append(f"{skill_file} frontmatter must be an object")
        return
    if set(frontmatter) != {"name", "description"}:
        errors.append(f"{skill_file} frontmatter must contain only name and description")
    if frontmatter.get("name") != skill_root.name:
        errors.append(f"{skill_file} name must match its folder")
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        errors.append(f"{skill_file} description must contain 1-1024 characters")

    agent_file = skill_root / "agents" / "openai.yaml"
    if not agent_file.is_file():
        errors.append(f"{skill_root.name} is missing agents/openai.yaml")
        return
    try:
        agent = yaml.safe_load(agent_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{agent_file} is invalid YAML: {exc}")
        return
    interface = agent.get("interface") if isinstance(agent, dict) else None
    if not isinstance(interface, dict):
        errors.append(f"{agent_file} needs an interface object")
        return
    short = interface.get("short_description")
    if not isinstance(short, str) or not 25 <= len(short) <= 64:
        errors.append(f"{agent_file} short_description must contain 25-64 characters")
    prompt = interface.get("default_prompt")
    if not isinstance(prompt, str) or f"${skill_root.name}" not in prompt:
        errors.append(f"{agent_file} default_prompt must mention ${skill_root.name}")


def validate_skills(root: Path, errors: list[str]) -> None:
    skills = root / "skills"
    if not skills.is_dir():
        errors.append("missing skills directory")
        return
    for skill_root in sorted(path for path in skills.iterdir() if path.is_dir() and not path.name.startswith(".")):
        validate_skill(skill_root, errors)


def schema_registry(root: Path, errors: list[str]) -> tuple[Registry, dict[str, dict[str, Any]]]:
    registry = Registry()
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "schemas").glob("*.schema.json")):
        schema = load_json(path, errors)
        if schema is None:
            continue
        try:
            Draft202012Validator.check_schema(schema)
            resource = Resource.from_contents(schema)
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str):
                raise ValueError("missing $id")
            registry = registry.with_resource(schema_id, resource)
            schemas[path.name] = schema
        except Exception as exc:  # jsonschema/referencing expose several error classes
            errors.append(f"invalid schema {path}: {exc}")
    return registry, schemas


def validate_instance(
    instance: dict[str, Any],
    schema: dict[str, Any],
    registry: Registry,
    label: str,
    errors: list[str],
) -> None:
    validator = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    for failure in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in failure.absolute_path) or "$"
        errors.append(f"{label}:{location}: {failure.message}")


def validate_schemas_and_evals(root: Path, errors: list[str]) -> None:
    registry, schemas = schema_registry(root, errors)
    contract_schema = schemas.get("deliverable-coverage.schema.json")
    case_schema = schemas.get("eval-case.schema.json")
    if contract_schema is None or case_schema is None:
        errors.append("required contract/eval schemas are missing")
        return
    cases = sorted((root / "evals" / "cases").glob("*.json"))
    if not cases:
        errors.append("evals/cases must contain at least one JSON case")
    for case_path in cases:
        case = load_json(case_path, errors)
        if case is None:
            continue
        validate_instance(case, case_schema, registry, str(case_path.relative_to(root)), errors)
        fixture_value = case.get("contractFixture")
        if not isinstance(fixture_value, str):
            continue
        fixture_path = (root / fixture_value).resolve()
        fixtures_root = (root / "evals" / "fixtures").resolve()
        try:
            fixture_path.relative_to(fixtures_root)
        except ValueError:
            errors.append(f"{case_path}: contractFixture escapes evals/fixtures")
            continue
        fixture = load_json(fixture_path, errors)
        if fixture is not None:
            validate_instance(
                fixture,
                contract_schema,
                registry,
                str(fixture_path.relative_to(root)),
                errors,
            )


def validate_links(root: Path, errors: list[str]) -> None:
    for path, relative in iter_repo_files(root):
        if path.suffix.lower() != ".md":
            continue
        contents = path.read_text(encoding="utf-8")
        for raw_link in LINK_RE.findall(contents):
            link = raw_link.split("#", 1)[0]
            if not link or link.startswith(("http://", "https://", "mailto:", "codex://")):
                continue
            target = (path.parent / link).resolve()
            if not target.exists():
                errors.append(f"broken local link in {relative}: {raw_link}")


def validate_hygiene(root: Path, errors: list[str]) -> None:
    ignore_file = root / ".gitignore"
    if not ignore_file.is_file() or "/.frontend-workbench/" not in ignore_file.read_text(encoding="utf-8").splitlines():
        errors.append("root .gitignore must contain the exact line '/.frontend-workbench/'")
    tracked_result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if tracked_result.returncode == 0:
        for raw_path in tracked_result.stdout.split(b"\0"):
            if not raw_path:
                continue
            tracked = raw_path.decode("utf-8", errors="replace")
            if tracked == ".frontend-workbench" or tracked.startswith(".frontend-workbench/"):
                errors.append(f"runtime state must not be packaged: {tracked}")
            if tracked == "evals/results" or tracked.startswith("evals/results/"):
                errors.append(f"raw eval results must not be packaged: {tracked}")
    for path, relative in iter_repo_files(root):
        if path.is_symlink():
            errors.append(f"symlink is not allowed in the plugin archive: {relative}")
        if path.suffix.lower() in IMAGE_SUFFIXES and "assets" not in relative.parts:
            errors.append(f"image outside an assets directory: {relative}")
        if path.suffix.lower() == ".md":
            allowed = relative.as_posix() in ROOT_MARKDOWN
            allowed = allowed or (
                len(relative.parts) >= 3
                and relative.parts[0] == "skills"
                and (relative.name == "SKILL.md" or "references" in relative.parts)
            )
            if not allowed:
                errors.append(f"unexpected Markdown file: {relative}")
        if path.suffix.lower() in {".md", ".json", ".yaml", ".yml", ".py", ".txt"}:
            try:
                contents = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"expected UTF-8 text file: {relative}")
                continue
            if TODO_MARKER in contents:
                errors.append(f"TODO placeholder remains in {relative}")


def validate_repo(root_value: str | Path, *, release: bool = False) -> list[str]:
    root = Path(root_value).expanduser().resolve()
    errors: list[str] = []
    validate_manifests(root, errors, release)
    validate_skills(root, errors)
    validate_schemas_and_evals(root, errors)
    validate_links(root, errors)
    validate_hygiene(root, errors)
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args(argv)
    errors = validate_repo(args.root, release=args.release)
    if errors:
        print("Repository validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
