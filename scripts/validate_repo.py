#!/usr/bin/env python3
"""Validate Frontend Workbench packaging, skills, schemas, and repository hygiene."""

from __future__ import annotations

import argparse
import hashlib
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
TEXT_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".toml"}
HOME_PATH_RE = re.compile(
    r"(?:/(?:Users|home)/[^/\s\"']+/)|(?:[A-Za-z]:\\Users\\[^\\\s\"']+\\)"
)
EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)
SECRET_MARKERS = (
    "BEGIN " + "PRIVATE KEY",
    "BEGIN RSA " + "PRIVATE KEY",
    "BEGIN OPENSSH " + "PRIVATE KEY",
    "BEGIN EC " + "PRIVATE KEY",
)
VISUAL_DIMENSIONS = (
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


def _duplicate_values(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_v3_bundle_semantics(
    contract: dict[str, Any],
    structure: dict[str, Any],
    implementation_plan: dict[str, Any] | None = None,
) -> list[str]:
    """Cross-check v3 identities and references that JSON Schema cannot express."""

    if contract.get("schemaVersion") != 3:
        return []
    errors: list[str] = []
    if structure.get("schemaVersion") != 3:
        return ["v3 coverage requires a v3 frontend structure"]

    structure_identity = contract.get("structure", {})
    if structure_identity.get("id") != structure.get("contractId"):
        errors.append("structure.id does not match frontend structure contractId")
    if structure_identity.get("sha256") != _canonical_sha256(structure):
        errors.append("structure.sha256 does not match canonical frontend structure")
    contract_surfaces = {
        item.get("id"): item
        for item in contract.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    structure_surfaces = {
        item.get("id"): item
        for item in structure.get("surfaces", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if set(contract_surfaces) != set(structure_surfaces):
        errors.append("coverage and frontend structure surface IDs must match exactly")

    product_model = contract.get("productModel", {})
    object_items = [
        item for item in product_model.get("objects", []) if isinstance(item, dict)
    ]
    object_ids = [item.get("id") for item in object_items if isinstance(item.get("id"), str)]
    duplicate_object_ids = _duplicate_values(object_ids)
    if duplicate_object_ids:
        errors.append("duplicate product object IDs: " + ", ".join(sorted(duplicate_object_ids)))
    object_map = {item["id"]: item for item in object_items if item.get("id") in object_ids}
    root_object_id = product_model.get("rootObjectId")
    if root_object_id not in object_map:
        errors.append("productModel.rootObjectId references an unknown object")
    elif object_map[root_object_id].get("role") != "root":
        errors.append("productModel.rootObjectId must reference the root-role object")
    elif object_map[root_object_id].get("parentId") is not None:
        errors.append("productModel root object must not have a parent")
    root_role_ids = {
        object_id for object_id, item in object_map.items() if item.get("role") == "root"
    }
    if root_role_ids != {root_object_id}:
        errors.append("productModel must contain exactly one root-role object")
    for object_id, item in object_map.items():
        parent_id = item.get("parentId")
        if parent_id is not None and parent_id not in object_map:
            errors.append(f"product object {object_id} parentId is unknown")
        for evidence_id in item.get("evidenceForObjectIds", []):
            if evidence_id not in object_map:
                errors.append(f"product object {object_id} evidence target {evidence_id} is unknown")
        if item.get("role") == "downstream-evidence" and not item.get("evidenceForObjectIds"):
            errors.append(f"downstream evidence object {object_id} requires an evidence target")

    relation_items = [
        item for item in product_model.get("relations", []) if isinstance(item, dict)
    ]
    relation_ids = [
        item.get("id") for item in relation_items if isinstance(item.get("id"), str)
    ]
    duplicate_relation_ids = _duplicate_values(relation_ids)
    if duplicate_relation_ids:
        errors.append("duplicate product relation IDs: " + ", ".join(sorted(duplicate_relation_ids)))
    for relation in relation_items:
        relation_id = relation.get("id")
        for field in ("fromObjectId", "toObjectId"):
            if relation.get(field) not in object_map:
                errors.append(f"product relation {relation_id} {field} is unknown")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit_object(object_id: str) -> None:
        if object_id in visited:
            return
        if object_id in visiting:
            errors.append(f"product object parent cycle includes {object_id}")
            return
        visiting.add(object_id)
        parent_id = object_map.get(object_id, {}).get("parentId")
        if isinstance(parent_id, str) and parent_id in object_map:
            visit_object(parent_id)
        visiting.remove(object_id)
        visited.add(object_id)

    for object_id in object_map:
        visit_object(object_id)

    output_items = [item for item in contract.get("outputs", []) if isinstance(item, dict)]
    output_ids = {item.get("id") for item in output_items if isinstance(item.get("id"), str)}
    for item in output_items:
        output_id = item.get("id")
        anchor_output_id = item.get("anchorOutputId")
        if anchor_output_id is not None and anchor_output_id not in output_ids:
            errors.append(f"output {output_id} anchorOutputId is unknown")
        if anchor_output_id == output_id:
            errors.append(f"output {output_id} cannot anchor itself")

    object_bindings = {
        item.get("id"): item
        for item in structure.get("objectBindings", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    reference_bindings = {
        item.get("id"): item
        for item in structure.get("referenceBindings", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    shells = {
        item.get("id"): item
        for item in structure.get("shells", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    for binding_id, binding in object_bindings.items():
        surface_id = binding.get("surfaceId")
        if surface_id not in contract_surfaces:
            errors.append(f"object binding {binding_id} references an unknown surface")
        for field in ("primaryObjectId",):
            if binding.get(field) not in object_map:
                errors.append(f"object binding {binding_id} {field} is unknown")
        for field in ("supportingObjectIds", "forbiddenDominantObjectIds"):
            for object_id in binding.get(field, []):
                if object_id not in object_map:
                    errors.append(f"object binding {binding_id} {field} contains unknown {object_id}")
        if binding.get("primaryObjectId") in binding.get("forbiddenDominantObjectIds", []):
            errors.append(f"object binding {binding_id} forbids its own primary object")

    for shell_id, shell in shells.items():
        parent_shell_id = shell.get("parentShellId")
        if parent_shell_id is not None and parent_shell_id not in shells:
            errors.append(f"shell {shell_id} parentShellId is unknown")

    shell_visiting: set[str] = set()
    shell_visited: set[str] = set()

    def visit_shell(shell_id: str) -> None:
        if shell_id in shell_visited:
            return
        if shell_id in shell_visiting:
            errors.append(f"shell parent cycle includes {shell_id}")
            return
        shell_visiting.add(shell_id)
        parent_id = shells.get(shell_id, {}).get("parentShellId")
        if isinstance(parent_id, str) and parent_id in shells:
            visit_shell(parent_id)
        shell_visiting.remove(shell_id)
        shell_visited.add(shell_id)

    for shell_id in shells:
        visit_shell(shell_id)

    for binding_id, binding in reference_bindings.items():
        for surface_id in binding.get("surfaceIds", []):
            if surface_id not in contract_surfaces:
                errors.append(f"reference binding {binding_id} references unknown surface {surface_id}")
        overlap = set(binding.get("aspects", [])) & set(binding.get("mustNotInfluence", []))
        if overlap:
            errors.append(
                f"reference binding {binding_id} both applies to and forbids: "
                + ", ".join(sorted(overlap))
            )

    for surface_id, surface in contract_surfaces.items():
        primary_object_id = surface.get("primaryObjectId")
        if primary_object_id not in object_map:
            errors.append(f"surface {surface_id} primaryObjectId is unknown")
        surface_object_bindings = [
            binding
            for binding in object_bindings.values()
            if binding.get("surfaceId") == surface_id
        ]
        if surface_object_bindings and all(
            binding.get("primaryObjectId") != primary_object_id
            for binding in surface_object_bindings
        ):
            errors.append(f"surface {surface_id} primary object differs from structure binding")
        for shell_id in surface.get("shellIds", []):
            if shell_id not in shells:
                errors.append(f"surface {surface_id} shell {shell_id} is unknown")
        for binding_id in surface.get("referenceBindingIds", []):
            binding = reference_bindings.get(binding_id)
            if binding is None:
                errors.append(f"surface {surface_id} reference binding {binding_id} is unknown")
            elif surface_id not in binding.get("surfaceIds", []):
                errors.append(f"surface {surface_id} is outside reference binding {binding_id} scope")

    scenario_items = [item for item in structure.get("scenarios", []) if isinstance(item, dict)]
    scenario_ids = [item.get("id") for item in scenario_items if isinstance(item.get("id"), str)]
    duplicate_scenario_ids = _duplicate_values(scenario_ids)
    if duplicate_scenario_ids:
        errors.append("duplicate scenario IDs: " + ", ".join(sorted(duplicate_scenario_ids)))
    scenario_map = {item["id"]: item for item in scenario_items if item.get("id") in scenario_ids}
    scenario_object_ids: set[str] = set()
    for scenario_id, scenario in scenario_map.items():
        for object_id in scenario.get("objectIds", []):
            if object_id not in object_map:
                errors.append(f"scenario {scenario_id} references unknown object {object_id}")
            else:
                scenario_object_ids.add(object_id)
        for field in ("entrySurfaceId", "completionSurfaceId"):
            if scenario.get(field) not in contract_surfaces:
                errors.append(f"scenario {scenario_id} {field} is unknown")
        for surface_id in scenario.get("recoverySurfaceIds", []):
            if surface_id not in contract_surfaces:
                errors.append(f"scenario {scenario_id} recovery surface {surface_id} is unknown")

    domain_ids: set[str] = set()
    for surface_id, surface in structure_surfaces.items():
        domain_ids.update(surface.get("domainIds", []))
        for scenario_id in surface.get("scenarioIds", []):
            if scenario_id not in scenario_map:
                errors.append(f"surface {surface_id} references unknown scenario {scenario_id}")
    for scenario_id, scenario in scenario_map.items():
        involved = {
            scenario.get("entrySurfaceId"),
            scenario.get("completionSurfaceId"),
            *scenario.get("recoverySurfaceIds", []),
        }
        for surface_id in involved:
            if surface_id in structure_surfaces and scenario_id not in structure_surfaces[surface_id].get("scenarioIds", []):
                errors.append(f"scenario {scenario_id} is missing from surface {surface_id} scenarioIds")

    required_domains = set(contract.get("productIntent", {}).get("requiredDomains", []))
    missing_domains = required_domains - domain_ids
    if missing_domains:
        errors.append("required domains lack structure surface coverage: " + ", ".join(sorted(missing_domains)))

    bound_object_ids = set(scenario_object_ids)
    for binding in object_bindings.values():
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
        errors.append("product objects lack scenario/surface binding: " + ", ".join(sorted(missing_objects)))

    capability_items = [
        item for item in contract.get("capabilityRequirements", []) if isinstance(item, dict)
    ]
    capability_ids = {
        item.get("id") for item in capability_items if isinstance(item.get("id"), str)
    }
    for capability in capability_items:
        requirement_id = capability.get("id")
        if capability.get("ownerObjectId") not in object_map:
            errors.append(f"capability requirement {requirement_id} ownerObjectId is unknown")
        for surface_id in capability.get("surfaceIds", []):
            if surface_id not in contract_surfaces:
                errors.append(f"capability requirement {requirement_id} surface {surface_id} is unknown")

    target_items = [
        item for item in contract.get("implementationTargets", []) if isinstance(item, dict)
    ]
    target_map = {
        item.get("path"): item
        for item in target_items
        if isinstance(item.get("path"), str)
    }
    for path, target in target_map.items():
        for surface_id in target.get("surfaceIds", []):
            if surface_id not in contract_surfaces:
                errors.append(f"implementation target {path} surface {surface_id} is unknown")

    if implementation_plan is not None:
        if implementation_plan.get("contractId") != contract.get("contractId"):
            errors.append("implementation plan contractId does not match coverage contract")
        if implementation_plan.get("contractSha256") != _canonical_sha256(contract):
            errors.append("implementation plan contractSha256 does not match coverage contract")
        if implementation_plan.get("structureSha256") != structure_identity.get("sha256"):
            errors.append("implementation plan structureSha256 does not match coverage contract")

        decision_items = [
            item
            for item in implementation_plan.get("capabilityDecisions", [])
            if isinstance(item, dict)
        ]
        decision_requirement_ids = [
            item.get("requirementId")
            for item in decision_items
            if isinstance(item.get("requirementId"), str)
        ]
        duplicate_decisions = _duplicate_values(decision_requirement_ids)
        if duplicate_decisions:
            errors.append(
                "duplicate capability decisions: " + ", ".join(sorted(duplicate_decisions))
            )
        decisions = {
            item["requirementId"]: item
            for item in decision_items
            if item.get("requirementId") in decision_requirement_ids
        }
        decided_requirements: set[str] = set()
        for requirement_id, decision in decisions.items():
            if requirement_id not in capability_ids:
                errors.append(f"capability decision {requirement_id} requirementId is unknown")
                continue
            decided_requirements.add(requirement_id)
            candidate_names = [
                candidate.get("name")
                for candidate in decision.get("candidates", [])
                if isinstance(candidate, dict) and isinstance(candidate.get("name"), str)
            ]
            if decision.get("selectedCandidate") not in candidate_names:
                errors.append(f"capability decision {requirement_id} selectedCandidate is unknown")
            requirement = next(
                item for item in capability_items if item.get("id") == requirement_id
            )
            complexity = requirement.get("complexity")
            approach = decision.get("selectedApproach")
            guarded = (
                complexity in {"complex", "foundational"}
                and approach in {"project-owned", "external-dependency"}
            )
            decision_tier = decision.get("decisionTier") or (
                "comparative" if guarded else "direct"
            )
            if complexity == "foundational" and decision_tier != "comparative":
                errors.append(
                    f"capability decision {requirement_id} must be comparative for foundational work"
                )
            if (
                complexity in {"complex", "foundational"}
                and approach == "project-owned"
                and decision_tier != "comparative"
            ):
                errors.append(
                    f"capability decision {requirement_id} must be comparative for project ownership"
                )
            if guarded and decision_tier == "direct":
                errors.append(
                    f"capability decision {requirement_id} direct tier cannot own a complex external or project-owned capability"
                )
            if decision_tier == "known-fit" and approach not in {
                "reuse",
                "extend",
                "compose",
                "platform",
                "framework",
                "external-dependency",
            }:
                errors.append(
                    f"capability decision {requirement_id} known-fit tier requires a non-project-owned capability"
                )
            if guarded:
                if decision_tier == "comparative" and len(set(candidate_names)) < 2:
                    errors.append(f"capability decision {requirement_id} needs two credible candidates")
                if not decision.get("obligations"):
                    errors.append(f"capability decision {requirement_id} needs lifecycle obligations")

        required_capabilities = {
            item.get("id") for item in capability_items if item.get("required") is True
        }
        missing_decisions = required_capabilities - decided_requirements
        if missing_decisions:
            errors.append("required capabilities lack decisions: " + ", ".join(sorted(missing_decisions)))

        bindings = [
            item for item in implementation_plan.get("targetBindings", []) if isinstance(item, dict)
        ]
        binding_paths = {item.get("path") for item in bindings if isinstance(item.get("path"), str)}
        if binding_paths != set(target_map):
            errors.append("implementation plan target paths must match contract targets exactly")
        for binding in bindings:
            path = binding.get("path")
            target = target_map.get(path)
            if target is not None and set(binding.get("surfaceIds", [])) != set(target.get("surfaceIds", [])):
                errors.append(f"target binding {path} surfaceIds differ from contract target")
            for requirement_id in binding.get("capabilityRequirementIds", []):
                if requirement_id not in decisions:
                    errors.append(f"target binding {path} capability requirement {requirement_id} is unknown")

        output_map = {
            item.get("id"): item
            for item in output_items
            if isinstance(item.get("id"), str)
        }
        output_bindings = [
            item for item in implementation_plan.get("outputBindings", []) if isinstance(item, dict)
        ]
        bound_output_ids = {
            item.get("outputId")
            for item in output_bindings
            if isinstance(item.get("outputId"), str)
        }
        required_runtime_output_ids = {
            output_id
            for output_id, output in output_map.items()
            if output.get("runtimeEvidenceRequired") is True
        }
        if bound_output_ids != required_runtime_output_ids:
            errors.append("implementation plan output bindings must match runtime-required outputs")
        for binding in output_bindings:
            output_id = binding.get("outputId")
            if output_id not in output_map:
                errors.append(f"output binding {output_id} references an unknown output")
            for path in binding.get("targetPaths", []):
                if path not in target_map:
                    errors.append(f"output binding {output_id} target path {path} is unknown")
            for requirement_id in binding.get("capabilityRequirementIds", []):
                if requirement_id not in decisions:
                    errors.append(
                        f"output binding {output_id} capability requirement {requirement_id} is unknown"
                    )

    return sorted(set(errors))


def validate_schemas_and_evals(root: Path, errors: list[str]) -> None:
    registry, schemas = schema_registry(root, errors)
    required_schemas = {
        "deliverable-coverage.schema.json",
        "runtime-state.schema.json",
        "eval-case.schema.json",
        "eval-result.schema.json",
        "eval-scorecard.schema.json",
        "eval-visual-case.schema.json",
        "eval-visual-fixture.schema.json",
        "eval-visual-rubric.schema.json",
        "eval-visual-run.schema.json",
        "eval-visual-scorecard.schema.json",
        "eval-blind-packet.schema.json",
        "eval-blind-mapping.schema.json",
        "eval-blind-judgment.schema.json",
        "visual-direction-contract.schema.json",
        "frontend-structure.schema.json",
        "implementation-plan.schema.json",
        "authority-receipt.schema.json",
        "render-brief.schema.json",
        "runtime-probe.schema.json",
    }
    missing_schemas = sorted(required_schemas - set(schemas))
    if missing_schemas:
        errors.append("required schemas are missing: " + ", ".join(missing_schemas))
        return
    contract_schema = schemas.get("deliverable-coverage.schema.json")
    case_schema = schemas.get("eval-case.schema.json")
    assert contract_schema is not None and case_schema is not None
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

    visual_case_schema = schemas["eval-visual-case.schema.json"]
    visual_fixture_schema = schemas["eval-visual-fixture.schema.json"]
    visual_rubric_schema = schemas["eval-visual-rubric.schema.json"]
    visual_cases = sorted((root / "evals" / "design-cases").glob("*.json"))
    if len(visual_cases) < 4:
        errors.append("evals/design-cases must contain at least four JSON cases")
    seen_visual_ids: set[str] = set()
    for case_path in visual_cases:
        case = load_json(case_path, errors)
        if case is None:
            continue
        case_label = str(case_path.relative_to(root))
        validate_instance(case, visual_case_schema, registry, case_label, errors)
        case_id = case.get("id")
        if isinstance(case_id, str):
            if case_id != case_path.stem:
                errors.append(f"{case_label}: case id must match its filename")
            if case_id in seen_visual_ids:
                errors.append(f"duplicate design eval case id: {case_id}")
            seen_visual_ids.add(case_id)
        fixture_value = case.get("fixtureManifest")
        rubric_value = case.get("rubric")
        if not isinstance(fixture_value, str) or not isinstance(rubric_value, str):
            continue
        fixture_path = (root / fixture_value).resolve()
        rubric_path = (root / rubric_value).resolve()
        try:
            fixture_path.relative_to((root / "evals" / "design-fixtures").resolve())
        except ValueError:
            errors.append(f"{case_label}: fixtureManifest escapes evals/design-fixtures")
            continue
        try:
            rubric_path.relative_to((root / "evals" / "rubrics").resolve())
        except ValueError:
            errors.append(f"{case_label}: rubric escapes evals/rubrics")
            continue
        fixture = load_json(fixture_path, errors)
        rubric = load_json(rubric_path, errors)
        if fixture is None or rubric is None:
            continue
        validate_instance(
            fixture,
            visual_fixture_schema,
            registry,
            str(fixture_path.relative_to(root)),
            errors,
        )
        validate_instance(
            rubric,
            visual_rubric_schema,
            registry,
            str(rubric_path.relative_to(root)),
            errors,
        )
        fixture_digest = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
        rubric_digest = hashlib.sha256(rubric_path.read_bytes()).hexdigest()
        if case.get("fixtureSha256") != fixture_digest:
            errors.append(f"{case_label}: fixtureSha256 does not match fixture bytes")
        if case.get("rubricSha256") != rubric_digest:
            errors.append(f"{case_label}: rubricSha256 does not match rubric bytes")
        if isinstance(case_id, str) and fixture.get("fixtureId") != case_id:
            errors.append(f"{case_label}: fixtureId must match the case id")
        capture_items = fixture.get("captureMatrix")
        capture_ids = [
            item.get("captureId")
            for item in capture_items
            if isinstance(item, dict) and isinstance(item.get("captureId"), str)
        ] if isinstance(capture_items, list) else []
        if len(capture_ids) != len(set(capture_ids)):
            errors.append(f"{fixture_value}: capture IDs must be unique")
        if set(capture_ids) != set(case.get("expectedCaptureIds", [])):
            errors.append(
                f"{case_label}: expectedCaptureIds must match the fixture captureMatrix"
            )
        dimensions = rubric.get("dimensions")
        if not isinstance(dimensions, dict) or tuple(dimensions) != VISUAL_DIMENSIONS:
            errors.append(
                f"{rubric_value}: rubric dimensions must be exactly {VISUAL_DIMENSIONS!r}"
            )
        if rubric.get("numericScoresAllowed") is not False:
            errors.append(f"{rubric_value}: numeric visual scores must remain disabled")


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


def validate_privacy(root: Path, errors: list[str]) -> None:
    for path, relative in iter_repo_files(root):
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if HOME_PATH_RE.search(contents):
            errors.append(f"personal home-directory path is forbidden: {relative}")
        if EMAIL_RE.search(contents):
            errors.append(f"personal email-like identifier is forbidden: {relative}")
        if any(marker in contents for marker in SECRET_MARKERS):
            errors.append(f"private-key material is forbidden: {relative}")
        if relative.parts[:2] == ("evals", "design-fixtures") and relative.suffix == ".json":
            try:
                fixture = json.loads(contents)
            except json.JSONDecodeError:
                continue
            source_kind = fixture.get("provenance", {}).get("sourceKind")
            if source_kind != "synthetic-fictional-eval-spec":
                errors.append(
                    f"design fixture must declare synthetic fictional provenance: {relative}"
                )


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
        if path.suffix.lower() in TEXT_SUFFIXES:
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
    validate_privacy(root, errors)
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
