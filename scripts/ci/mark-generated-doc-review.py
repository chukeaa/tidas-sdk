#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MARKDOWN_DOCUMENTS = (
    Path("AGENTS.md"),
    Path("README.md"),
    Path("docs/agents/repo-validation.md"),
    Path("docs/agents/repo-architecture.md"),
    Path("docs/release-setup.md"),
    Path("docs/upstream-automation.md"),
)
CONFIG_DOCUMENT = Path(".docpact/config.yaml")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record deterministic governed-doc review metadata for an SDK refresh."
    )
    parser.add_argument("--reviewed-at", required=True, help="Review date in YYYY-MM-DD.")
    parser.add_argument(
        "--reviewed-commit",
        required=True,
        help="Exact tidas-sdk base commit used for the generated refresh.",
    )
    parser.add_argument(
        "--upstream-sha",
        required=True,
        help="Exact tidas-tools commit used to regenerate the SDK.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root. Defaults to the current tidas-sdk checkout.",
    )
    return parser.parse_args()


def replace_frontmatter_field(raw: str, field: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^{re.escape(field)}: .*$")
    replacement = f'{field}: "{value}"'
    if pattern.search(raw):
        return pattern.sub(replacement, raw, count=1)

    commit_line = re.compile(r"(?m)^lastReviewedCommit: .*$")
    match = commit_line.search(raw)
    if match is None:
        raise ValueError(f"missing lastReviewedCommit while adding {field}")
    return raw[: match.end()] + f"\n{replacement}" + raw[match.end() :]


def mark_documents(
    repo_root: Path,
    *,
    reviewed_at: str,
    reviewed_commit: str,
    upstream_sha: str,
) -> None:
    note = (
        "Reviewed generated SDK refresh from tiangong-lca/tidas-tools "
        f"{upstream_sha}; generated package surfaces and current guidance remain aligned."
    )

    for relative_path in MARKDOWN_DOCUMENTS:
        path = repo_root / relative_path
        raw = path.read_text(encoding="utf-8")
        raw = replace_frontmatter_field(raw, "lastReviewedAt", reviewed_at)
        raw = replace_frontmatter_field(raw, "lastReviewedCommit", reviewed_commit)
        raw = replace_frontmatter_field(raw, "lastReviewedNote", note)
        path.write_text(raw, encoding="utf-8")

    config_path = repo_root / CONFIG_DOCUMENT
    config = config_path.read_text(encoding="utf-8")
    config = replace_frontmatter_field(config, "lastReviewedAt", reviewed_at)
    config = replace_frontmatter_field(config, "lastReviewedCommit", reviewed_commit)
    config_path.write_text(config, encoding="utf-8")


def main() -> int:
    args = parse_args()
    mark_documents(
        args.repo_root.resolve(),
        reviewed_at=args.reviewed_at,
        reviewed_commit=args.reviewed_commit,
        upstream_sha=args.upstream_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
