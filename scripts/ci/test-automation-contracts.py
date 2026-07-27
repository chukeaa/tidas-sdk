#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent


def load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_ROOT / filename)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


detect_release_changes = load_script(
    "detect_release_changes", "detect-release-changes.py"
)
mark_generated_doc_review = load_script(
    "mark_generated_doc_review", "mark-generated-doc-review.py"
)
update_tidas_tools_pin = load_script(
    "update_tidas_tools_pin", "update-tidas-tools-pin.py"
)


class ReleaseDetectionTests(unittest.TestCase):
    def test_untagged_current_version_is_release_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "sdks/typescript").mkdir(parents=True)
            (repo / "sdks/python").mkdir(parents=True)
            (repo / "sdks/typescript/package.json").write_text(
                json.dumps({"version": "0.1.46"}), encoding="utf-8"
            )
            (repo / "sdks/python/pyproject.toml").write_text(
                'version = "0.2.14"\n', encoding="utf-8"
            )
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo), "config", "user.name", "Automation Test"],
                check=True,
            )
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-qm", "fixture"], check=True
            )
            head = subprocess.check_output(
                ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
            ).strip()
            subprocess.run(
                ["git", "-C", str(repo), "tag", "python-v0.2.14"], check=True
            )

            outputs = detect_release_changes.build_outputs(repo, head, head)
            self.assertEqual("true", outputs["typescript_changed"])
            self.assertEqual("typescript-v0.1.46", outputs["typescript_tag"])
            self.assertEqual("false", outputs["python_changed"])

            subprocess.run(
                ["git", "-C", str(repo), "tag", "typescript-v0.1.46"], check=True
            )
            outputs = detect_release_changes.build_outputs(repo, head, head)
            self.assertEqual("false", outputs["typescript_changed"])
            self.assertEqual("false", outputs["any_changed"])


class GeneratedDocReviewTests(unittest.TestCase):
    def test_review_metadata_is_deterministic_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            for relative_path in mark_generated_doc_review.MARKDOWN_DOCUMENTS:
                path = repo / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    "---\n"
                    "lastReviewedAt: 2026-01-01\n"
                    "lastReviewedCommit: old\n"
                    "---\n",
                    encoding="utf-8",
                )
            config_path = repo / mark_generated_doc_review.CONFIG_DOCUMENT
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                'lastReviewedAt: "2026-01-01"\nlastReviewedCommit: "old"\n',
                encoding="utf-8",
            )

            kwargs = {
                "reviewed_at": "2026-07-27",
                "reviewed_commit": "a" * 40,
                "upstream_sha": "b" * 40,
            }
            mark_generated_doc_review.mark_documents(repo, **kwargs)
            first = {
                path: (repo / path).read_text(encoding="utf-8")
                for path in (
                    *mark_generated_doc_review.MARKDOWN_DOCUMENTS,
                    mark_generated_doc_review.CONFIG_DOCUMENT,
                )
            }
            mark_generated_doc_review.mark_documents(repo, **kwargs)
            second = {
                path: (repo / path).read_text(encoding="utf-8")
                for path in first
            }

            self.assertEqual(first, second)
            for relative_path, raw in second.items():
                self.assertIn("2026-07-27", raw, relative_path.as_posix())
                self.assertIn("a" * 40, raw, relative_path.as_posix())
            for relative_path in mark_generated_doc_review.MARKDOWN_DOCUMENTS:
                self.assertIn("b" * 40, second[relative_path])


class UpstreamPinTests(unittest.TestCase):
    def test_pin_update_is_exact_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            pin_path = repo / update_tidas_tools_pin.SOURCE_HELPER
            pin_path.parent.mkdir(parents=True)
            pin_path.write_text(
                'TIDAS_TOOLS_SHA="${TIDAS_TOOLS_SHA:-' + "a" * 40 + '}"\n',
                encoding="utf-8",
            )

            update_tidas_tools_pin.update_pin(repo, "B" * 40)
            first = pin_path.read_text(encoding="utf-8")
            update_tidas_tools_pin.update_pin(repo, "B" * 40)
            second = pin_path.read_text(encoding="utf-8")

            self.assertEqual(first, second)
            self.assertIn("b" * 40, second)


if __name__ == "__main__":
    unittest.main()
