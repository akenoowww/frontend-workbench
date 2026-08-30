#!/usr/bin/env python3
"""Run a direct, dependency-free browser probe through an installed agent-browser.

The script never installs packages and never uses a search engine. It opens the exact
target URL, exercises a small declarative interaction spec, captures normalized
runtime evidence, and writes a hash-bindable trace under the active session's qa/.
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
from urllib.parse import urlsplit

from runtime_state import sha256_file, validate_screenshot_file


PRODUCER = "frontend-workbench/browser-runtime-probe"
SAFE_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
FORBIDDEN_DISCOVERY_LABELS = {
    "baidu",
    "bing",
    "brave",
    "duckduckgo",
    "ecosia",
    "google",
    "startpage",
    "yahoo",
    "yandex",
}
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
ACTION_KINDS = {
    "click-role",
    "click-text",
    "click-selector",
    "fill-label",
    "press",
}
ASSERTION_KINDS = {
    "visible-text",
    "url",
    "selector-count",
    "text-contains",
    "value-equals",
    "expression",
}


class ProbeError(RuntimeError):
    """A user-correctable browser-probe error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _unknown_keys(value: dict[str, Any], allowed: set[str], label: str, errors: list[str]) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        errors.append(f"{label} has unknown fields: {', '.join(unexpected)}")


def _non_empty(value: Any, label: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return None
    return value.strip()


def _is_constant_expression(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"[\s;()]", "", value).casefold()
    return normalized in {
        "true",
        "false",
        "1",
        "0",
        "!!1",
        "!!0",
        "boolean(1)",
        "boolean(0)",
    }


def _is_generic_state_assertion(
    assertion: dict[str, Any],
    root_selector: str | None,
) -> bool:
    kind = assertion.get("kind")
    if kind == "selector-count":
        selector = str(assertion.get("selector") or "").strip().casefold()
        return selector in {
            "html",
            "body",
            ":root",
            str(root_selector or "").strip().casefold(),
        }
    if kind != "expression":
        return False
    expression = str(assertion.get("expression") or "")
    normalized = re.sub(r"\s+", "", expression).casefold()
    if "document.body" in normalized or "document.documentelement" in normalized:
        return True
    if normalized in {
        "document.title.length>0",
        "document.title!==''",
        "document.title!=''",
    }:
        return True
    if "queryselector" in normalized and any(
        ending in normalized
        for ending in ("!==null", "!=null", ">0", ".length>0")
    ):
        state_signals = (
            ".dataset",
            "aria-",
            ".classlist",
            ".textcontent",
            ".innertext",
            ".value",
            "getattribute",
        )
        if not any(signal in normalized for signal in state_signals):
            return True
    return False


def _safe_qa_relative(value: Any, label: str, errors: list[str]) -> str | None:
    raw = _non_empty(value, label, errors)
    if raw is None:
        return None
    relative = PurePosixPath(raw)
    if relative.is_absolute() or not relative.parts or relative.parts[0] != "qa":
        errors.append(f"{label} must stay under qa/")
        return None
    if any(part in {"", ".", ".."} for part in relative.parts):
        errors.append(f"{label} contains an unsafe path segment")
        return None
    return relative.as_posix()


def validate_probe_spec(spec: dict[str, Any], *, allow_remote: bool = False) -> list[str]:
    errors: list[str] = []
    _unknown_keys(
        spec,
        {
            "schemaVersion",
            "outputId",
            "url",
            "route",
            "state",
            "viewport",
            "scrollPosition",
            "scroll",
            "rootSelector",
            "ready",
            "stateSetup",
            "stateAssertion",
            "interactions",
            "implementationSnapshotSha256",
            "screenshotPath",
            "tracePath",
        },
        "probe spec",
        errors,
    )
    if spec.get("schemaVersion") != 1:
        errors.append("probe spec.schemaVersion must be 1")
    output_id = _non_empty(spec.get("outputId"), "probe spec.outputId", errors)
    if output_id is not None and ID_RE.fullmatch(output_id) is None:
        errors.append("probe spec.outputId is invalid")
    target_url = _non_empty(spec.get("url"), "probe spec.url", errors)
    if target_url is not None:
        parsed = urlsplit(target_url)
        if parsed.scheme not in {"http", "https"}:
            errors.append("probe spec.url must use http or https")
        elif parsed.scheme in {"http", "https"}:
            if not parsed.hostname:
                errors.append("probe spec.url must include a hostname")
            elif any(
                label in FORBIDDEN_DISCOVERY_LABELS
                for label in parsed.hostname.casefold().split(".")
            ):
                errors.append("probe spec.url cannot target a search engine")
            elif not allow_remote and parsed.hostname not in SAFE_LOCAL_HOSTS:
                errors.append(
                    "probe spec.url must be loopback-local unless --allow-remote is explicit"
                )
    _non_empty(spec.get("route"), "probe spec.route", errors)
    _non_empty(spec.get("state"), "probe spec.state", errors)
    _non_empty(spec.get("scrollPosition"), "probe spec.scrollPosition", errors)
    implementation_snapshot = spec.get("implementationSnapshotSha256")
    if (
        not isinstance(implementation_snapshot, str)
        or HASH_RE.fullmatch(implementation_snapshot) is None
    ):
        errors.append("probe spec.implementationSnapshotSha256 is invalid")
    root_selector = _non_empty(spec.get("rootSelector"), "probe spec.rootSelector", errors)
    if root_selector is not None and (
        root_selector.casefold() in {"html", "body", ":root", "*"}
        or re.search(
            r"(^|[\s,>+~:(])(?:html|body)(?=$|[\s,>+~.#\[:)])",
            root_selector,
            flags=re.IGNORECASE,
        )
    ):
        errors.append("probe spec.rootSelector must identify the app root, not the document shell")

    viewport = spec.get("viewport")
    if not isinstance(viewport, dict):
        errors.append("probe spec.viewport must be an object")
    else:
        _unknown_keys(viewport, {"label", "width", "height"}, "probe spec.viewport", errors)
        _non_empty(viewport.get("label"), "probe spec.viewport.label", errors)
        for field, minimum in (("width", 320), ("height", 200)):
            value = viewport.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
                errors.append(f"probe spec.viewport.{field} must be an integer >= {minimum}")

    ready = spec.get("ready")
    if not isinstance(ready, dict):
        errors.append("probe spec.ready must be an object")
    else:
        _unknown_keys(ready, {"kind", "value"}, "probe spec.ready", errors)
        if ready.get("kind") not in {"selector", "text", "expression"}:
            errors.append("probe spec.ready.kind must be selector, text, or expression")
        _non_empty(ready.get("value"), "probe spec.ready.value", errors)

    scroll = spec.get("scroll")
    if not isinstance(scroll, dict):
        errors.append("probe spec.scroll must be an object")
    else:
        _unknown_keys(scroll, {"kind", "selector"}, "probe spec.scroll", errors)
        scroll_kind = scroll.get("kind")
        if scroll_kind not in {"top", "bottom", "full-page", "selector"}:
            errors.append("probe spec.scroll.kind is invalid")
        if scroll_kind == "selector":
            _non_empty(scroll.get("selector"), "probe spec.scroll.selector", errors)
        elif scroll.get("selector") is not None:
            errors.append("probe spec.scroll.selector is valid only for selector scroll")
        declared_scroll_position = spec.get("scrollPosition")
        if declared_scroll_position in {"top", "bottom", "full-page"} and (
            scroll_kind != declared_scroll_position
        ):
            errors.append(
                "probe spec.scroll.kind must match the conventional scrollPosition"
            )

    state_setup = spec.get("stateSetup")
    if not isinstance(state_setup, list):
        errors.append("probe spec.stateSetup must be an array")
        state_setup = []
    for index, action in enumerate(state_setup):
        label = f"probe spec.stateSetup[{index}]"
        if not isinstance(action, dict):
            errors.append(f"{label} must be an action object")
            continue
        _unknown_keys(
            action,
            {"kind", "role", "name", "text", "selector", "label", "value", "key"},
            label,
            errors,
        )
        kind = action.get("kind")
        if kind not in ACTION_KINDS:
            errors.append(f"{label}.kind is invalid")
        required_fields = {
            "click-role": ("role", "name"),
            "click-text": ("text",),
            "click-selector": ("selector",),
            "fill-label": ("label", "value"),
            "press": ("key",),
        }.get(kind, ())
        for field in required_fields:
            _non_empty(action.get(field), f"{label}.{field}", errors)

    state_assertion = spec.get("stateAssertion")
    if not isinstance(state_assertion, dict):
        errors.append("probe spec.stateAssertion must be an assertion object")
    else:
        assertion_kind = state_assertion.get("kind")
        assertion_label = "probe spec.stateAssertion"
        _unknown_keys(
            state_assertion,
            {"id", "kind", "value", "selector", "operator", "count", "expression"},
            assertion_label,
            errors,
        )
        if assertion_kind not in ASSERTION_KINDS:
            errors.append(f"{assertion_label}.kind is invalid")
        state_assertion_id = _non_empty(
            state_assertion.get("id"), f"{assertion_label}.id", errors
        )
        if state_assertion_id is not None and ID_RE.fullmatch(state_assertion_id) is None:
            errors.append(f"{assertion_label}.id is invalid")
        if assertion_kind in {"visible-text", "url"}:
            _non_empty(state_assertion.get("value"), f"{assertion_label}.value", errors)
        elif assertion_kind in {"text-contains", "value-equals"}:
            _non_empty(state_assertion.get("selector"), f"{assertion_label}.selector", errors)
            _non_empty(state_assertion.get("value"), f"{assertion_label}.value", errors)
        elif assertion_kind == "selector-count":
            _non_empty(state_assertion.get("selector"), f"{assertion_label}.selector", errors)
            if state_assertion.get("operator") not in {"eq", "gte", "lte"}:
                errors.append(f"{assertion_label}.operator must be eq, gte, or lte")
            count = state_assertion.get("count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                errors.append(f"{assertion_label}.count must be a non-negative integer")
        elif assertion_kind == "expression":
            _non_empty(state_assertion.get("expression"), f"{assertion_label}.expression", errors)
            if _is_constant_expression(state_assertion.get("expression")):
                errors.append(f"{assertion_label}.expression cannot be constant")
        if _is_generic_state_assertion(state_assertion, root_selector):
            errors.append(
                "probe spec.stateAssertion must identify a state-specific observable, not page/root existence"
            )

    interactions = spec.get("interactions")
    if not isinstance(interactions, list) or not interactions:
        errors.append("probe spec.interactions must contain at least one target interaction")
        interactions = []
    seen_ids: set[str] = set()
    for index, interaction in enumerate(interactions):
        label = f"probe spec.interactions[{index}]"
        if not isinstance(interaction, dict):
            errors.append(f"{label} must be an object")
            continue
        _unknown_keys(interaction, {"id", "action", "assertions"}, label, errors)
        interaction_id = _non_empty(interaction.get("id"), f"{label}.id", errors)
        if interaction_id is not None:
            if ID_RE.fullmatch(interaction_id) is None:
                errors.append(f"{label}.id is invalid")
            elif interaction_id in seen_ids:
                errors.append(f"{label}.id is duplicated")
            seen_ids.add(interaction_id)
        action = interaction.get("action")
        if not isinstance(action, dict):
            errors.append(f"{label}.action must be an object")
        else:
            _unknown_keys(
                action,
                {"kind", "role", "name", "text", "selector", "label", "value", "key"},
                f"{label}.action",
                errors,
            )
            kind = action.get("kind")
            if kind not in ACTION_KINDS:
                errors.append(f"{label}.action.kind is invalid")
            required_fields = {
                "click-role": ("role", "name"),
                "click-text": ("text",),
                "click-selector": ("selector",),
                "fill-label": ("label", "value"),
                "press": ("key",),
            }.get(kind, ())
            for field in required_fields:
                _non_empty(action.get(field), f"{label}.action.{field}", errors)
        assertions = interaction.get("assertions")
        if not isinstance(assertions, list) or not assertions:
            errors.append(f"{label}.assertions must contain at least one observable result")
            assertions = []
        assertion_ids: set[str] = set()
        for assertion_index, assertion in enumerate(assertions):
            assertion_label = f"{label}.assertions[{assertion_index}]"
            if not isinstance(assertion, dict):
                errors.append(f"{assertion_label} must be an object")
                continue
            _unknown_keys(
                assertion,
                {
                    "id",
                    "kind",
                    "value",
                    "selector",
                    "operator",
                    "count",
                    "expression",
                },
                assertion_label,
                errors,
            )
            assertion_id = _non_empty(assertion.get("id"), f"{assertion_label}.id", errors)
            if assertion_id is not None:
                if ID_RE.fullmatch(assertion_id) is None:
                    errors.append(f"{assertion_label}.id is invalid")
                elif assertion_id in assertion_ids:
                    errors.append(f"{assertion_label}.id is duplicated")
                assertion_ids.add(assertion_id)
            assertion_kind = assertion.get("kind")
            if assertion_kind not in ASSERTION_KINDS:
                errors.append(f"{assertion_label}.kind is invalid")
            if assertion_kind in {"visible-text", "url"}:
                _non_empty(assertion.get("value"), f"{assertion_label}.value", errors)
            elif assertion_kind in {"text-contains", "value-equals"}:
                _non_empty(assertion.get("selector"), f"{assertion_label}.selector", errors)
                _non_empty(assertion.get("value"), f"{assertion_label}.value", errors)
            elif assertion_kind == "selector-count":
                _non_empty(assertion.get("selector"), f"{assertion_label}.selector", errors)
                if assertion.get("operator") not in {"eq", "gte", "lte"}:
                    errors.append(f"{assertion_label}.operator must be eq, gte, or lte")
                count = assertion.get("count")
                if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                    errors.append(f"{assertion_label}.count must be a non-negative integer")
            elif assertion_kind == "expression":
                _non_empty(
                    assertion.get("expression"),
                    f"{assertion_label}.expression",
                    errors,
                )
                if _is_constant_expression(assertion.get("expression")):
                    errors.append(f"{assertion_label}.expression cannot be constant")

    screenshot_path = _safe_qa_relative(
        spec.get("screenshotPath"), "probe spec.screenshotPath", errors
    )
    trace_path = _safe_qa_relative(spec.get("tracePath"), "probe spec.tracePath", errors)
    if screenshot_path is not None and Path(screenshot_path).suffix.lower() != ".png":
        errors.append("probe spec.screenshotPath must be a PNG")
    if trace_path is not None and Path(trace_path).suffix.lower() != ".json":
        errors.append("probe spec.tracePath must be JSON")
    if screenshot_path is not None and screenshot_path == trace_path:
        errors.append("probe screenshotPath and tracePath must be distinct")
    return errors


def _load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProbeError(f"Invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProbeError(f"{label} must contain a JSON object")
    return value


def _resolve_session_file(session_dir: Path, relative_value: str, *, require_file: bool) -> Path:
    relative = PurePosixPath(relative_value)
    candidate = session_dir
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ProbeError(f"Refusing symlinked probe path: {relative_value}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(session_dir.resolve())
    except ValueError as exc:
        raise ProbeError(f"Probe path escapes the session: {relative_value}") from exc
    if require_file and (not resolved.is_file() or resolved.is_symlink()):
        raise ProbeError(f"Probe file is missing: {relative_value}")
    return resolved


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _json_command(command: list[str], *, timeout: int = 45) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProbeError(f"Browser command failed: {exc}") from exc
    output = completed.stdout.strip()
    try:
        payload = json.loads(output) if output else {}
    except json.JSONDecodeError as exc:
        detail = completed.stderr.strip() or output or f"exit {completed.returncode}"
        raise ProbeError(f"Browser returned non-JSON output: {detail}") from exc
    if not isinstance(payload, dict):
        raise ProbeError("Browser returned a non-object JSON payload")
    if completed.returncode != 0 and payload.get("success") is not False:
        payload = {"success": False, "data": payload.get("data"), "error": completed.stderr.strip()}
    return payload


def _data(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("data")
    return value if isinstance(value, dict) else {}


def _error_text(payload: dict[str, Any]) -> str:
    error = payload.get("error")
    if isinstance(error, str) and error.strip():
        return error.strip()
    if isinstance(error, dict):
        return json.dumps(error, ensure_ascii=False, sort_keys=True)
    return "agent-browser command failed"


def _browser_version(binary: str) -> str:
    completed = subprocess.run(
        [binary, "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        raise ProbeError("Cannot read the installed agent-browser version")
    return value.removeprefix("agent-browser ").strip()


def _run_action(prefix: list[str], action: dict[str, Any]) -> tuple[dict[str, Any], str]:
    kind = action["kind"]
    if kind == "click-role":
        args = ["find", "role", action["role"], "click", "--name", action["name"]]
        description = f"click role={action['role']} name={action['name']}"
    elif kind == "click-text":
        args = ["find", "text", action["text"], "click", "--exact"]
        description = f"click exact text={action['text']}"
    elif kind == "click-selector":
        args = ["find", "first", action["selector"], "click"]
        description = f"click selector={action['selector']}"
    elif kind == "fill-label":
        args = ["find", "label", action["label"], "fill", action["value"]]
        description = f"fill label={action['label']} value=<redacted>"
    else:
        args = ["press", action["key"]]
        description = f"press key={action['key']}"
    return _json_command(prefix + args), description


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _observe_assertion(
    prefix: list[str], assertion: dict[str, Any]
) -> tuple[bool, Any, str | None]:
    kind = assertion["kind"]
    if kind == "visible-text":
        expression = (
            "(document.body.innerText || '').includes("
            + json.dumps(assertion["value"])
            + ")"
        )
        payload = _json_command(prefix + ["eval", expression])
        return payload.get("success") is True, _data(payload).get("result"), (
            None if payload.get("success") is True else _error_text(payload)
        )
    if kind == "url":
        payload = _json_command(prefix + ["get", "url"])
        return payload.get("success") is True, _data(payload).get("url"), (
            None if payload.get("success") is True else _error_text(payload)
        )
    if kind == "selector-count":
        payload = _json_command(prefix + ["get", "count", assertion["selector"]])
        return payload.get("success") is True, _data(payload).get("count"), (
            None if payload.get("success") is True else _error_text(payload)
        )
    if kind in {"text-contains", "value-equals"}:
        get_kind = "text" if kind == "text-contains" else "value"
        payload = _json_command(prefix + ["get", get_kind, assertion["selector"]])
        data = _data(payload)
        actual = data.get(get_kind)
        if actual is None:
            actual = data.get("value") if get_kind == "value" else data.get("text")
        return payload.get("success") is True, actual, (
            None if payload.get("success") is True else _error_text(payload)
        )
    payload = _json_command(prefix + ["eval", assertion["expression"]])
    return payload.get("success") is True, _data(payload).get("result"), (
        None if payload.get("success") is True else _error_text(payload)
    )


def _assertion_matches(assertion: dict[str, Any], actual: Any) -> bool:
    kind = assertion["kind"]
    if kind == "visible-text":
        return actual is True
    if kind == "url":
        expected = assertion["value"]
        if not isinstance(actual, str):
            return False
        if "*" not in expected:
            return actual == expected
        pattern = "^" + re.escape(expected).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
        return re.fullmatch(pattern, actual) is not None
    if kind == "selector-count":
        expected = assertion["count"]
        return {
            "eq": isinstance(actual, int) and actual == expected,
            "gte": isinstance(actual, int) and actual >= expected,
            "lte": isinstance(actual, int) and actual <= expected,
        }[assertion["operator"]]
    if kind == "text-contains":
        return isinstance(actual, str) and assertion["value"] in actual
    if kind == "value-equals":
        return actual == assertion["value"]
    return bool(actual)


def _run_assertion(
    prefix: list[str],
    assertion: dict[str, Any],
    *,
    before: Any = None,
    require_transition: bool,
) -> dict[str, str]:
    kind = assertion["kind"]
    if kind == "visible-text":
        wait_payload = _json_command(prefix + ["wait", "--text", assertion["value"]])
        if wait_payload.get("success") is not True:
            return {
                "id": assertion["id"],
                "kind": kind,
                "result": "fail",
                "observed": _error_text(wait_payload),
            }
    elif kind == "url":
        wait_payload = _json_command(prefix + ["wait", "--url", assertion["value"]])
        if wait_payload.get("success") is not True:
            return {
                "id": assertion["id"],
                "kind": kind,
                "result": "fail",
                "observed": _error_text(wait_payload),
            }
    success, actual, error = _observe_assertion(prefix, assertion)
    matches = success and _assertion_matches(assertion, actual)
    changed = before != actual
    passed = matches and (changed or not require_transition)
    observed = (
        f"before={before!r}; after={actual!r}; transition={changed}"
        if error is None
        else error
    )
    return {
        "id": assertion["id"],
        "kind": kind,
        "result": "pass" if passed else "fail",
        "observed": observed,
    }


def _page_state_fingerprint(prefix: list[str], root_selector: str) -> str:
    selector = json.dumps(root_selector)
    script = f"""(() => {{
      const root = document.querySelector({selector});
      const active = document.activeElement;
      return {{
        url: window.location.href,
        title: document.title,
        rootText: root ? (root.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 20000) : null,
        rootHtml: root ? root.innerHTML.slice(0, 40000) : null,
        active: active ? {{ tag: active.tagName, id: active.id || null, role: active.getAttribute('role'), value: 'value' in active ? String(active.value).slice(0, 1000) : null }} : null,
        scrollX: window.scrollX,
        scrollY: window.scrollY
      }};
    }})()"""
    payload = _json_command(prefix + ["eval", script])
    if payload.get("success") is not True:
        return _canonical_sha256({"error": _error_text(payload)})
    return _canonical_sha256(_data(payload).get("result"))


def _message_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("text", "message", "description", "error"):
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return json.dumps(item, ensure_ascii=False, sort_keys=True)
    return repr(item)


def _console_errors(payload: dict[str, Any]) -> list[str]:
    messages = _data(payload).get("messages")
    if not isinstance(messages, list):
        return [_error_text(payload)] if payload.get("success") is not True else []
    result: list[str] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        level = item.get("type", item.get("level", item.get("severity")))
        if isinstance(level, str) and level.casefold() == "error":
            result.append(_message_text(item))
    return result


def _page_errors(payload: dict[str, Any]) -> list[str]:
    errors = _data(payload).get("errors")
    if not isinstance(errors, list):
        return [_error_text(payload)] if payload.get("success") is not True else []
    return [_message_text(item) for item in errors]


def _origin(value: str) -> tuple[str, str, int | None] | None:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    port = parsed.port
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return parsed.scheme, parsed.hostname.casefold(), port


def _failed_requests(
    payload: dict[str, Any],
    *,
    allowed_origin: tuple[str, str, int | None],
) -> list[dict[str, Any]]:
    requests = _data(payload).get("requests")
    if not isinstance(requests, list):
        if payload.get("success") is not True:
            return [{"url": "agent-browser://network", "status": None, "method": None, "error": _error_text(payload)}]
        return []
    failed: list[dict[str, Any]] = []
    for item in requests:
        if not isinstance(item, dict):
            continue
        status = item.get("status")
        error = item.get("error", item.get("failure"))
        request_url = str(item.get("url") or "unknown://request")
        request_origin = _origin(request_url)
        cross_origin = request_origin is not None and request_origin != allowed_origin
        is_failed = (
            isinstance(status, int)
            and status >= 400
            or isinstance(error, str)
            and bool(error.strip())
            or item.get("failed") is True
            or cross_origin
        )
        if not is_failed:
            continue
        failed.append(
            {
                "url": request_url,
                "status": status if isinstance(status, int) else None,
                "method": item.get("method") if isinstance(item.get("method"), str) else None,
                "error": (
                    "request origin differs from the exact target origin"
                    if cross_origin
                    else error if isinstance(error, str) and error.strip() else None
                ),
            }
        )
    return failed


def _accessibility(payload: dict[str, Any]) -> dict[str, Any]:
    violations = _data(payload).get("violations")
    if not isinstance(violations, list):
        return {
            "criticalViolations": 1,
            "seriousViolations": 0,
            "otherViolations": [
                {"id": "audit-unavailable", "impact": "critical", "nodeCount": 1}
            ],
        }
    critical = 0
    serious = 0
    other: list[dict[str, Any]] = []
    for item in violations:
        if not isinstance(item, dict):
            continue
        impact = item.get("impact") if isinstance(item.get("impact"), str) else None
        node_count = item.get("nodeCount")
        if not isinstance(node_count, int):
            nodes = item.get("nodes")
            node_count = len(nodes) if isinstance(nodes, list) else 0
        if impact == "critical":
            critical += node_count
        elif impact == "serious":
            serious += node_count
        else:
            other.append(
                {
                    "id": str(item.get("id") or "unknown-rule"),
                    "impact": impact,
                    "nodeCount": node_count,
                }
            )
    return {
        "criticalViolations": critical,
        "seriousViolations": serious,
        "otherViolations": other,
    }


def _page_probe_script(root_selector: str) -> str:
    selector = json.dumps(root_selector)
    return f"""(() => {{
      const root = document.querySelector({selector});
      const box = root ? root.getBoundingClientRect() : {{ width: 0, height: 0 }};
      let effectiveOpacity = 1;
      let hiddenByStyle = false;
      for (let node = root; node && node.nodeType === Node.ELEMENT_NODE; node = node.parentElement) {{
        const style = getComputedStyle(node);
        effectiveOpacity *= Number(style.opacity || 1);
        hiddenByStyle ||= style.display === 'none' || style.visibility === 'hidden' || style.visibility === 'collapse' || style.contentVisibility === 'hidden';
      }}
      const intersectionWidth = root ? Math.max(0, Math.min(box.right, window.innerWidth) - Math.max(box.left, 0)) : 0;
      const intersectionHeight = root ? Math.max(0, Math.min(box.bottom, window.innerHeight) - Math.max(box.top, 0)) : 0;
      const intersectionPixels = intersectionWidth * intersectionHeight;
      const text = root ? (root.innerText || '').replace(/\\s+/g, ' ').trim() : '';
      const landmarks = root ? root.querySelectorAll('main,[role=main],nav,[role=navigation],header,[role=banner],footer,[role=contentinfo],aside,[role=complementary]').length : 0;
      const interactive = root ? root.querySelectorAll('a[href],button,input,select,textarea,[role=button],[role=link],[tabindex]:not([tabindex="-1"])').length : 0;
      return {{
        rootFound: Boolean(root),
        rootIsDocumentShell: Boolean(root && (root === document.body || root === document.documentElement)),
        rootVisible: Boolean(root && !hiddenByStyle && effectiveOpacity > 0.05 && intersectionPixels > 0 && root.getClientRects().length > 0 && root.getAttribute('aria-hidden') !== 'true'),
        rootEffectiveOpacity: Number(effectiveOpacity),
        rootViewportIntersectionPixels: Number(intersectionPixels),
        rootChildElementCount: root ? root.childElementCount : 0,
        visibleTextCharacters: text.length,
        visibleLandmarkCount: landmarks,
        interactiveElementCount: interactive,
        rootWidth: Number(box.width || 0),
        rootHeight: Number(box.height || 0)
      }};
    }})()"""


def _apply_scroll(prefix: list[str], scroll: dict[str, Any]) -> dict[str, Any]:
    kind = scroll["kind"]
    if kind == "selector":
        scroll_payload = _json_command(
            prefix + ["scrollintoview", scroll["selector"]]
        )
        if scroll_payload.get("success") is not True:
            return {
                "kind": kind,
                "x": 0.0,
                "y": 0.0,
                "maxY": 0.0,
                "verified": False,
                "captureFullPage": False,
            }
        selector = json.dumps(scroll["selector"])
        verify_expression = f"""(() => {{
          const target = document.querySelector({selector});
          const rect = target ? target.getBoundingClientRect() : null;
          const maxY = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
          return {{
            x: Number(window.scrollX || 0),
            y: Number(window.scrollY || 0),
            maxY,
            verified: Boolean(rect && rect.bottom > 0 && rect.top < window.innerHeight)
          }};
        }})()"""
    else:
        target = (
            "Math.max(0, document.documentElement.scrollHeight - window.innerHeight)"
            if kind == "bottom"
            else "0"
        )
        verify_expression = f"""(() => {{
          const targetY = {target};
          window.scrollTo(0, targetY);
          const maxY = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
          const y = Number(window.scrollY || 0);
          return {{
            x: Number(window.scrollX || 0),
            y,
            maxY,
            verified: {str(kind == 'full-page').lower()} || ({json.dumps(kind)} === 'top' ? Math.abs(y) <= 1 : Math.abs(y - maxY) <= 2)
          }};
        }})()"""
    payload = _json_command(prefix + ["eval", verify_expression])
    result = _data(payload).get("result")
    if not isinstance(result, dict):
        result = {}
    return {
        "kind": kind,
        "x": float(result.get("x") or 0),
        "y": float(result.get("y") or 0),
        "maxY": float(result.get("maxY") or 0),
        "verified": payload.get("success") is True and result.get("verified") is True,
        "captureFullPage": kind == "full-page",
    }


def run_probe(
    session_dir_value: str | Path,
    spec_value: str | Path,
    *,
    binary: str = "agent-browser",
    allow_remote: bool = False,
) -> dict[str, Any]:
    session_dir = Path(session_dir_value).expanduser().resolve()
    if not session_dir.is_dir() or session_dir.is_symlink():
        raise ProbeError("--session-dir must be a regular Frontend Workbench session directory")
    qa_dir = session_dir / "qa"
    if not qa_dir.is_dir() or qa_dir.is_symlink():
        raise ProbeError("The active session must contain a regular qa/ directory")
    spec_path = Path(spec_value).expanduser().resolve()
    try:
        spec_relative = spec_path.relative_to(session_dir).as_posix()
    except ValueError as exc:
        raise ProbeError("--spec must be stored inside the active session") from exc
    if not spec_relative.startswith("qa/") or not spec_path.is_file() or spec_path.is_symlink():
        raise ProbeError("--spec must be a regular JSON file under the active session qa/")
    spec = _load_json_object(spec_path, "browser probe spec")
    errors = validate_probe_spec(spec, allow_remote=allow_remote)
    if errors:
        raise ProbeError("Invalid browser probe spec: " + "; ".join(errors))

    resolved_binary = shutil.which(binary)
    if resolved_binary is None:
        raise ProbeError(
            "agent-browser is not installed on the host; mark rendered QA BLOCKED or use an already-installed project runner. Do not npm install it inside the product."
        )
    adapter_version = _browser_version(resolved_binary)
    screenshot_relative = spec["screenshotPath"]
    trace_relative = spec["tracePath"]
    screenshot_path = _resolve_session_file(session_dir, screenshot_relative, require_file=False)
    trace_path = _resolve_session_file(session_dir, trace_relative, require_file=False)
    if screenshot_path == trace_path:
        raise ProbeError("Probe screenshot and trace must be distinct files")
    session_name = f"fwb-{spec['outputId']}-{uuid.uuid4().hex[:10]}"
    prefix = [
        resolved_binary,
        "--session",
        session_name,
        "--namespace",
        "frontend-workbench",
        "--json",
    ]
    parsed_url = urlsplit(spec["url"])
    if parsed_url.hostname:
        prefix.extend(["--allowed-domains", parsed_url.hostname])

    launch_errors: list[str] = []
    ready_ok = False
    interaction_results: list[dict[str, Any]] = []
    page_details: dict[str, Any] = {}
    screenshot_sha = ""
    pixel_width = 0
    pixel_height = 0
    console_payload: dict[str, Any] = {"success": False, "error": "not collected"}
    errors_payload: dict[str, Any] = {"success": False, "error": "not collected"}
    network_payload: dict[str, Any] = {"success": False, "error": "not collected"}
    a11y_payload: dict[str, Any] = {"success": False, "error": "not collected"}
    state_verification: dict[str, str] = {
        "id": "state-unverified",
        "kind": "state",
        "result": "fail",
        "observed": "state verification did not run",
    }
    scroll_result: dict[str, Any] = {
        "kind": spec["scroll"]["kind"],
        "x": 0.0,
        "y": 0.0,
        "maxY": 0.0,
        "verified": False,
        "captureFullPage": spec["scroll"]["kind"] == "full-page",
    }
    final_url = ""
    title = ""
    try:
        launch = _json_command(prefix + ["open"])
        if launch.get("success") is not True:
            raise ProbeError(_error_text(launch))
        viewport = spec["viewport"]
        viewport_result = _json_command(
            prefix + ["set", "viewport", str(viewport["width"]), str(viewport["height"])]
        )
        if viewport_result.get("success") is not True:
            raise ProbeError(_error_text(viewport_result))
        for args in (["console", "--clear"], ["errors", "--clear"], ["network", "requests", "--clear"]):
            _json_command(prefix + list(args))
        navigation = _json_command(prefix + ["navigate", spec["url"]])
        if navigation.get("success") is not True:
            launch_errors.append(_error_text(navigation))
        dom_ready = _json_command(prefix + ["wait", "--load", "domcontentloaded"])
        if dom_ready.get("success") is not True:
            launch_errors.append(_error_text(dom_ready))
        ready = spec["ready"]
        ready_args = {
            "selector": ["wait", ready["value"]],
            "text": ["wait", "--text", ready["value"]],
            "expression": ["wait", "--fn", ready["value"]],
        }[ready["kind"]]
        ready_payload = _json_command(prefix + ready_args)
        ready_ok = ready_payload.get("success") is True
        if not ready_ok:
            launch_errors.append(_error_text(ready_payload))
        _json_command(
            prefix
            + [
                "eval",
                "new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(() => resolve(true))))",
            ]
        )

        for action in spec["stateSetup"]:
            setup_payload, setup_description = _run_action(prefix, action)
            if setup_payload.get("success") is not True:
                launch_errors.append(
                    f"state setup {setup_description} failed: {_error_text(setup_payload)}"
                )
        state_verification = _run_assertion(
            prefix,
            spec["stateAssertion"],
            require_transition=False,
        )
        scroll_result = _apply_scroll(prefix, spec["scroll"])

        page_payload = _json_command(prefix + ["eval", _page_probe_script(spec["rootSelector"])])
        page_result = _data(page_payload).get("result")
        if isinstance(page_result, dict):
            page_details = page_result
        else:
            launch_errors.append(_error_text(page_payload))
        url_payload = _json_command(prefix + ["get", "url"])
        title_payload = _json_command(prefix + ["get", "title"])
        final_url = str(_data(url_payload).get("url") or "")
        title = str(_data(title_payload).get("title") or "")
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_args = ["screenshot"]
        if scroll_result["captureFullPage"]:
            screenshot_args.append("--full")
        screenshot_args.append(str(screenshot_path))
        screenshot_payload = _json_command(prefix + screenshot_args)
        if screenshot_payload.get("success") is not True:
            raise ProbeError("Screenshot capture failed: " + _error_text(screenshot_payload))
        screenshot_sha = sha256_file(screenshot_path)
        pixel_width, pixel_height = validate_screenshot_file(screenshot_path)
        a11y_payload = _json_command(prefix + ["a11y"])

        for interaction in spec["interactions"]:
            before_observations = [
                _observe_assertion(prefix, assertion)[1]
                for assertion in interaction["assertions"]
            ]
            before_sha = _page_state_fingerprint(prefix, spec["rootSelector"])
            action_payload, action_description = _run_action(prefix, interaction["action"])
            assertions: list[dict[str, str]] = []
            if action_payload.get("success") is True:
                assertions = [
                    _run_assertion(
                        prefix,
                        assertion,
                        before=before_observations[index],
                        require_transition=True,
                    )
                    for index, assertion in enumerate(interaction["assertions"])
                ]
            else:
                assertions = [
                    {
                        "id": assertion["id"],
                        "kind": assertion["kind"],
                        "result": "fail",
                        "observed": "action failed: " + _error_text(action_payload),
                    }
                    for assertion in interaction["assertions"]
                ]
            after_sha = _page_state_fingerprint(prefix, spec["rootSelector"])
            state_changed = before_sha != after_sha
            interaction_results.append(
                {
                    "id": interaction["id"],
                    "action": action_description,
                    "beforeSha256": before_sha,
                    "afterSha256": after_sha,
                    "stateChanged": state_changed,
                    "assertions": assertions,
                    "result": (
                        "pass"
                        if action_payload.get("success") is True
                        and state_changed
                        and assertions
                        and all(item["result"] == "pass" for item in assertions)
                        else "fail"
                    ),
                }
            )
        console_payload = _json_command(prefix + ["console"])
        errors_payload = _json_command(prefix + ["errors"])
        network_payload = _json_command(prefix + ["network", "requests"])
    finally:
        try:
            _json_command(
                [
                    resolved_binary,
                    "--session",
                    session_name,
                    "--namespace",
                    "frontend-workbench",
                    "--json",
                    "close",
                ],
                timeout=15,
            )
        except ProbeError:
            pass

    runtime_health = {
        "consoleErrors": _console_errors(console_payload),
        "pageErrors": _page_errors(errors_payload),
        "failedRequests": _failed_requests(
            network_payload,
            allowed_origin=_origin(spec["url"]),
        ),
    }
    accessibility = _accessibility(a11y_payload)
    page = {
        "finalUrl": final_url,
        "title": title,
        "rootSelector": spec["rootSelector"],
        "rootFound": page_details.get("rootFound") is True,
        "rootIsDocumentShell": page_details.get("rootIsDocumentShell") is True,
        "rootVisible": page_details.get("rootVisible") is True,
        "rootEffectiveOpacity": float(page_details.get("rootEffectiveOpacity") or 0),
        "rootViewportIntersectionPixels": float(
            page_details.get("rootViewportIntersectionPixels") or 0
        ),
        "rootChildElementCount": int(page_details.get("rootChildElementCount") or 0),
        "visibleTextCharacters": int(page_details.get("visibleTextCharacters") or 0),
        "visibleLandmarkCount": int(page_details.get("visibleLandmarkCount") or 0),
        "interactiveElementCount": int(page_details.get("interactiveElementCount") or 0),
        "rootWidth": float(page_details.get("rootWidth") or 0),
        "rootHeight": float(page_details.get("rootHeight") or 0),
    }
    failure_reasons = list(launch_errors)
    if not ready_ok:
        failure_reasons.append("the declared ready condition did not pass")
    if not page["title"].strip():
        failure_reasons.append("page title is empty")
    if page["finalUrl"] != spec["url"]:
        failure_reasons.append("final URL differs from the exact target URL")
    if not page["rootFound"]:
        failure_reasons.append("declared app root was not found")
    if page["rootIsDocumentShell"]:
        failure_reasons.append("declared app root resolves to the document shell")
    if not page["rootVisible"]:
        failure_reasons.append("declared app root is not visibly intersecting the viewport")
    if page["rootChildElementCount"] < 1:
        failure_reasons.append("declared app root has no rendered child elements")
    if page["visibleTextCharacters"] < 8:
        failure_reasons.append("declared app root lacks meaningful visible text")
    if page["rootWidth"] <= 0 or page["rootHeight"] <= 0:
        failure_reasons.append("declared app root has no visible geometry")
    if page["visibleLandmarkCount"] + page["interactiveElementCount"] < 1:
        failure_reasons.append("render lacks a landmark or interactive element")
    if state_verification["result"] != "pass":
        failure_reasons.append("the declared output state was not verified")
    if not scroll_result["verified"]:
        failure_reasons.append("the declared scroll position was not verified")
    if runtime_health["consoleErrors"]:
        failure_reasons.append("console errors were observed")
    if runtime_health["pageErrors"]:
        failure_reasons.append("uncaught page errors were observed")
    if runtime_health["failedRequests"]:
        failure_reasons.append("failed network requests were observed")
    if accessibility["criticalViolations"] or accessibility["seriousViolations"]:
        failure_reasons.append("critical or serious accessibility violations were observed")
    if not interaction_results or any(item["result"] != "pass" for item in interaction_results):
        failure_reasons.append("the target interaction or its observable assertion failed")
    if pixel_width < 320 or pixel_height < 200:
        failure_reasons.append("screenshot dimensions are below the minimum evidence size")

    verdict = "pass" if not failure_reasons else "fail"
    trace: dict[str, Any] = {
        "schemaVersion": 1,
        "producer": PRODUCER,
        "adapter": "agent-browser",
        "adapterVersion": adapter_version,
        "generatedAt": utc_now(),
        "specPath": spec_relative,
        "specSha256": sha256_file(spec_path),
        "implementationSnapshotSha256": spec["implementationSnapshotSha256"],
        "outputId": spec["outputId"],
        "route": spec["route"],
        "state": spec["state"],
        "viewport": spec["viewport"]["label"],
        "scrollPosition": spec["scrollPosition"],
        "directNavigation": True,
        "page": page,
        "stateVerification": state_verification,
        "scroll": scroll_result,
        "runtimeHealth": runtime_health,
        "accessibility": accessibility,
        "interactions": interaction_results,
        "screenshot": {
            "path": screenshot_relative,
            "sha256": screenshot_sha,
            "pixelWidth": pixel_width,
            "pixelHeight": pixel_height,
        },
        "verdict": verdict,
    }
    if failure_reasons:
        trace["reason"] = "; ".join(dict.fromkeys(failure_reasons))
    _atomic_write_json(trace_path, trace)
    return trace


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--agent-browser-binary", default="agent-browser")
    parser.add_argument("--allow-remote", action="store_true")
    args = parser.parse_args(argv)
    try:
        trace = run_probe(
            args.session_dir,
            args.spec,
            binary=args.agent_browser_binary,
            allow_remote=args.allow_remote,
        )
    except ProbeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(trace, ensure_ascii=False, sort_keys=True))
    return 0 if trace["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
