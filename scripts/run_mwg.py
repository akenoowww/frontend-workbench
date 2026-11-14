#!/usr/bin/env python3
"""Run Modern Web Guidance with telemetry disabled."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess


CLI = "modern-web-guidance"
PACKAGE = f"{CLI}@1.0.0"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline", action="store_true",
        help="Only use an installed CLI or the npm cache.",
    )
    parser.add_argument("command", choices=("search", "retrieve", "list", "legacy-scan", "version"))
    parser.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    command = "--version" if options.command == "version" else options.command

    local_bin = Path.cwd() / "node_modules" / ".bin"
    executable = shutil.which(CLI, path=str(local_bin)) or shutil.which(CLI)
    if executable:
        launch = [executable]
    else:
        npx = shutil.which("npx")
        if not npx:
            parser.exit(127, f"{CLI} and npx are unavailable. Read the official guides directly.\n")
        launch = [
            npx, "--yes", "--ignore-scripts", "--no-audit", "--logs-max=0",
            "--offline" if options.offline else "--prefer-offline",
            "--", PACKAGE,
        ]

    try:
        completed = subprocess.run(
            [*launch, command, *options.args],
            env=dict(os.environ, DISABLE_TELEMETRY="1"),
            check=False,
        )
    except OSError as error:
        parser.exit(126, f"Unable to run {CLI}: {error.strerror}\n")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
