from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_runtime_probe  # noqa: E402


class BrowserRuntimeProbeTests(unittest.TestCase):
    @staticmethod
    def valid_spec() -> dict:
        return {
            "schemaVersion": 1,
            "outputId": "graph-default",
            "url": "http://127.0.0.1:4173/graph",
            "route": "/graph",
            "state": "default",
            "scrollPosition": "top",
            "scroll": {"kind": "top"},
            "viewport": {"label": "desktop", "width": 1440, "height": 900},
            "rootSelector": "#root",
            "ready": {"kind": "selector", "value": ".react-flow"},
            "stateSetup": [],
            "stateAssertion": {
                "id": "graph-ready",
                "kind": "visible-text",
                "value": "Graph ready",
            },
            "interactions": [
                {
                    "id": "select-node",
                    "action": {
                        "kind": "click-selector",
                        "selector": ".react-flow__node",
                    },
                    "assertions": [
                        {
                            "id": "selection-visible",
                            "kind": "selector-count",
                            "selector": ".react-flow__node.selected",
                            "operator": "gte",
                            "count": 1,
                        }
                    ],
                }
            ],
            "implementationSnapshotSha256": "a" * 64,
            "screenshotPath": "qa/graph-default.png",
            "tracePath": "qa/graph-default.runtime-probe.json",
        }

    def test_valid_local_graph_probe_uses_library_behavior(self) -> None:
        self.assertEqual(
            browser_runtime_probe.validate_probe_spec(self.valid_spec()),
            [],
        )

    def test_remote_navigation_is_fail_closed_without_explicit_scope(self) -> None:
        spec = self.valid_spec()
        spec["url"] = "https://www.google.com/search?q=graph"
        errors = browser_runtime_probe.validate_probe_spec(spec)
        self.assertTrue(any("search engine" in error for error in errors))
        self.assertTrue(
            any(
                "search engine" in error
                for error in browser_runtime_probe.validate_probe_spec(
                    spec,
                    allow_remote=True,
                )
            )
        )
        for blocked_url in (
            "https://www.google.co.uk/search?q=graph",
            "https://images.google.com/search?q=graph",
            "https://search.yahoo.com/search?p=graph",
        ):
            candidate = self.valid_spec()
            candidate["url"] = blocked_url
            self.assertTrue(
                any(
                    "search engine" in error
                    for error in browser_runtime_probe.validate_probe_spec(
                        candidate,
                        allow_remote=True,
                    )
                )
            )
        spec["url"] = "https://preview.example.test/graph"
        self.assertTrue(
            any(
                "loopback-local" in error
                for error in browser_runtime_probe.validate_probe_spec(spec)
            )
        )
        self.assertEqual(browser_runtime_probe.validate_probe_spec(spec, allow_remote=True), [])

    def test_document_shell_and_screenshot_only_probe_are_rejected(self) -> None:
        spec = self.valid_spec()
        spec["rootSelector"] = "body"
        spec["interactions"] = []
        errors = browser_runtime_probe.validate_probe_spec(spec)
        self.assertTrue(any("app root" in error for error in errors))
        self.assertTrue(any("target interaction" in error for error in errors))

        for selector in ("html body", ":where(body)", "html, #root"):
            with self.subTest(selector=selector):
                candidate = self.valid_spec()
                candidate["rootSelector"] = selector
                self.assertTrue(
                    any(
                        "app root" in error
                        for error in browser_runtime_probe.validate_probe_spec(candidate)
                    )
                )

    def test_constant_assertion_cannot_prove_interaction(self) -> None:
        spec = self.valid_spec()
        spec["interactions"][0]["action"] = {"kind": "press", "key": "Shift"}
        spec["interactions"][0]["assertions"] = [
            {"id": "constant", "kind": "expression", "expression": "true"}
        ]
        errors = browser_runtime_probe.validate_probe_spec(spec)
        self.assertTrue(any("cannot be constant" in error for error in errors), errors)

    def test_state_assertion_must_be_state_specific(self) -> None:
        generic_assertions = (
            {
                "id": "generic",
                "kind": "selector-count",
                "selector": "body",
                "operator": "gte",
                "count": 1,
            },
            {
                "id": "generic",
                "kind": "selector-count",
                "selector": "#root",
                "operator": "gte",
                "count": 1,
            },
            {
                "id": "generic",
                "kind": "expression",
                "expression": 'document.querySelector("#root") !== null',
            },
            {
                "id": "generic",
                "kind": "expression",
                "expression": "document.title.length > 0",
            },
        )
        for assertion in generic_assertions:
            with self.subTest(assertion=assertion):
                spec = self.valid_spec()
                spec["stateAssertion"] = assertion
                errors = browser_runtime_probe.validate_probe_spec(spec)
                self.assertTrue(any("state-specific" in error for error in errors), errors)

    def test_file_url_is_rejected_even_for_local_probe(self) -> None:
        spec = self.valid_spec()
        spec["url"] = "file:///tmp/fixture.html"
        errors = browser_runtime_probe.validate_probe_spec(spec)
        self.assertTrue(any("http or https" in error for error in errors), errors)

    def test_probe_never_accepts_tiny_visual_evidence(self) -> None:
        spec = self.valid_spec()
        spec["viewport"] = {"label": "desktop", "width": 1, "height": 1}
        errors = browser_runtime_probe.validate_probe_spec(spec)
        self.assertTrue(any("width" in error for error in errors))
        self.assertTrue(any("height" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
