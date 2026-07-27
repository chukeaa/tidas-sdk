#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
TYPESCRIPT_PACKAGE = Path("sdks/typescript/package.json")
PYTHON_PACKAGE = Path("sdks/python/pyproject.toml")
ZERO_SHA = "0" * 40
PYTHON_VERSION_PATTERN = re.compile(r'(?m)^version = "(?P<version>\d+\.\d+\.\d+)"$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect package version changes between two git refs."
    )
    parser.add_argument("--base-ref", required=True, help="Base git ref to compare from.")
    parser.add_argument(
        "--head-ref",
        default="HEAD",
        help="Head git ref to compare to. Defaults to HEAD.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root for git commands.",
    )
    parser.add_argument(
        "--github-output",
        default=os.environ.get("GITHUB_OUTPUT", ""),
        help="Optional GitHub Actions output file.",
    )
    return parser.parse_args()


def load_ref_file(repo_root: Path, ref: str, relative_path: Path) -> str | None:
    if not ref or ref == ZERO_SHA:
        return None

    command = ["git", "-C", str(repo_root), "show", f"{ref}:{relative_path.as_posix()}"]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def parse_typescript_version(raw: str) -> str:
    return json.loads(raw)["version"]


def parse_python_version(raw: str) -> str:
    match = PYTHON_VERSION_PATTERN.search(raw)
    if match is None:
        raise ValueError("could not locate Python package version")
    return match.group("version")


def tag_exists(repo_root: Path, tag_name: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "rev-parse",
            "--verify",
            "--quiet",
            f"refs/tags/{tag_name}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def build_outputs(
    repo_root: Path,
    base_ref: str,
    head_ref: str,
) -> dict[str, str]:
    definitions: list[tuple[str, Path, Callable[[str], str], str]] = [
        ("typescript", TYPESCRIPT_PACKAGE, parse_typescript_version, "typescript-v"),
        ("python", PYTHON_PACKAGE, parse_python_version, "python-v"),
    ]

    outputs: dict[str, str] = {}
    any_changed = False

    for name, relative_path, parser, tag_prefix in definitions:
        base_raw = load_ref_file(repo_root, base_ref, relative_path)
        head_raw = load_ref_file(repo_root, head_ref, relative_path)

        base_version = parser(base_raw) if base_raw is not None else ""
        head_version = parser(head_raw) if head_raw is not None else ""
        tag_name = f"{tag_prefix}{head_version}" if head_version else ""
        version_changed = bool(
            base_version and head_version and base_version != head_version
        )
        pending_untagged_version = bool(
            head_version and not tag_exists(repo_root, tag_name)
        )
        changed = version_changed or pending_untagged_version

        outputs[f"{name}_previous_version"] = base_version
        outputs[f"{name}_version"] = head_version
        outputs[f"{name}_changed"] = "true" if changed else "false"
        outputs[f"{name}_tag"] = tag_name if changed else ""
        any_changed = any_changed or changed

    outputs["any_changed"] = "true" if any_changed else "false"
    return outputs


def write_outputs(outputs: dict[str, str], github_output: str) -> None:
    lines = [f"{key}={value}" for key, value in outputs.items()]
    if github_output:
        with Path(github_output).open("a", encoding="utf-8") as fh:
            for line in lines:
                fh.write(f"{line}\n")
    else:
        for line in lines:
            print(line)


def main() -> int:
    args = parse_args()
    outputs = build_outputs(
        repo_root=args.repo_root.resolve(),
        base_ref=args.base_ref,
        head_ref=args.head_ref,
    )
    write_outputs(outputs, args.github_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
