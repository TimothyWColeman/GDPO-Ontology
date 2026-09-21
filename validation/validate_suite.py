#!/usr/bin/env python3
"""Run the public GDPO validation and release-build suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKS = [
    ["validation/validate_version.py"],
    ["validation/validate_imports.py"],
    ["validation/validate_gdpo.py"],
    ["validation/validate_shacl.py"],
    ["validation/validate_queries.py"],
    ["validation/validate_assessment_fixture.py"],
    ["validation/validate_robot.py"],
    ["scripts/build_release.py", "--check"],
]


def release_version() -> str:
    try:
        return (ROOT / "VERSION").read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def main() -> int:
    print(f"GDPO v{release_version()} validation suite", flush=True)
    for command in CHECKS:
        print(f"\n== {' '.join(command)} ==", flush=True)
        result = subprocess.run([sys.executable, *command], cwd=ROOT, check=False)
        if result.returncode:
            print(f"\nSuite stopped after failed gate: {' '.join(command)}", flush=True)
            return result.returncode
    print("\nPASS: all available GDPO validation and release gates succeeded.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
