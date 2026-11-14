from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


LAUNCHER = Path(__file__).resolve().parents[1] / "scripts" / "run_mwg.py"


@unittest.skipUnless(os.name == "posix", "Uses executable POSIX stubs")
class ModernWebGuidanceLauncherTests(unittest.TestCase):
    def test_installed_and_npx_cli_receive_telemetry_opt_out(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            project = Path(scratch)
            bin_dir = project / "bin"
            bin_dir.mkdir()
            env = {"PATH": str(bin_dir), "DISABLE_TELEMETRY": "0"}

            for mode, executable in (
                ("project", project / "node_modules" / ".bin" / "modern-web-guidance"),
                ("path", bin_dir / "modern-web-guidance"),
                ("npm", bin_dir / "npx"),
            ):
                executable.parent.mkdir(parents=True, exist_ok=True)
                executable.write_text(
                    f"#!{sys.executable}\n"
                    "import json, os, sys\n"
                    "print(json.dumps([os.environ.get('DISABLE_TELEMETRY'), sys.argv[1:]]))\n"
                    "raise SystemExit(7)\n",
                    encoding="utf-8",
                )
                executable.chmod(0o700)
                for command, args in (
                    ("search", ["modal dialog"]),
                    ("retrieve", ["dialog"]),
                    ("list", []),
                    ("legacy-scan", ["./ui folder", "--json"]),
                    ("version", []),
                ):
                    with self.subTest(mode=mode, command=command):
                        options = ["--offline"] if mode == "npm" else []
                        result = subprocess.run(
                            [sys.executable, LAUNCHER, *options, command, *args],
                            cwd=project,
                            env=env,
                            capture_output=True,
                            text=True,
                            timeout=10,
                        )
                        invoked = "--version" if command == "version" else command
                        self.assertEqual(result.returncode, 7, result.stderr)
                        flag, argv = json.loads(result.stdout)
                        self.assertEqual(flag, "1")
                        self.assertEqual(argv[-(len(args) + 1):], [invoked, *args])
                        if mode == "npm":
                            self.assertIn("modern-web-guidance@1.0.0", argv)
                            self.assertIn("--offline", argv)
                executable.unlink()
