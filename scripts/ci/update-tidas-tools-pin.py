#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_HELPER = Path("scripts/ci/lib/tidas-tools-source.sh")
PIN_PATTERN = re.compile(
    r'(?m)^TIDAS_TOOLS_SHA="\$\{TIDAS_TOOLS_SHA:-[0-9a-fA-F]{40}\}"$'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update the default exact tidas-tools source pin."
    )
    parser.add_argument("--upstream-sha", required=True)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the current tidas-sdk checkout.",
    )
    return parser.parse_args()


def update_pin(repo_root: Path, upstream_sha: str) -> None:
    if re.fullmatch(r"[0-9a-fA-F]{40}", upstream_sha) is None:
        raise ValueError("upstream SHA must contain exactly 40 hexadecimal characters")

    path = repo_root / SOURCE_HELPER
    raw = path.read_text(encoding="utf-8")
    replacement = f'TIDAS_TOOLS_SHA="${{TIDAS_TOOLS_SHA:-{upstream_sha.lower()}}}"'
    updated, count = PIN_PATTERN.subn(replacement, raw, count=1)
    if count != 1:
        raise ValueError(f"could not locate the exact source pin in {path}")
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    args = parse_args()
    update_pin(args.repo_root.resolve(), args.upstream_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
