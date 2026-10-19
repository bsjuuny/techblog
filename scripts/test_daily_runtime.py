import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-only")
from scripts import daily_runtime as runtime
from scripts import generate_daily_post as daily
from scripts.source_evidence import body_urls, used_sources


class EngineeringRegressionTests(unittest.TestCase):
    def test_engineering_footer_lists_only_body_citations(self):
        urls = [f"https://github.com/bsjuuny/{repo}/commit/{i}" for i, repo in enumerate(
            ["bizradar", "bizradar", "bizradar", "harness-history", "harness-history", "ipo-master"])]
        sources = [{"title": str(i), "url": url} for i, url in enumerate(urls)]
        draft = {"title": "회귀 검증", "body": f"수정 근거 [커밋]({urls[2]})",
                 "sources": sources, "picked": {"repo": "bizradar"}}
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(daily, "POSTS_DIR", Path(temp)):
            text = daily.write_post(draft, "engineering", dt.date(2026, 10, 18)).read_text(encoding="utf-8")
        self.assertEqual(body_urls(text.split("**참고한 원본 소스**")[1]), {urls[2]})

    def test_followup_context_survives_source_filter(self):
        source = {"repo": "local", "title": "old", "body": "old issue", "sha": "old",
                  "files_changed": "", "url": ""}
        followup = {**source, "title": "fixed", "body": "fixed", "sha": "new"}
        with mock.patch.object(daily, "_claude", return_value="과거 기록\nTITLE: 기록") as call:
            draft = daily.generate_draft_engineering([source, followup])
        self.assertIn("fixed", call.call_args.args[0])
        self.assertEqual(draft["review_context"], [source, followup])

    def test_corrected_article_has_exactly_three_cited_sources(self):
        text = (daily.POSTS_DIR / "2026-10-18-engineering-1792254655.md").read_text(encoding="utf-8")
        body, footer = text.split("**참고한 원본 소스**")
        self.assertEqual(body_urls(body), body_urls(footer))
        self.assertEqual(len(body_urls(footer)), 3)
        self.assertNotIn("harness-history", text)
        self.assertNotIn("ipo-master", text)
        self.assertIn("27,764", text)
        self.assertIn("운영 DB에 접속해", text)


class RuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.remote = Path(self.temp.name) / "remote"
        self.local = Path(self.temp.name) / "local"
        self.remote.mkdir()
        runtime.git(self.remote, "init", "-b", "master")
        runtime.git(self.remote, "config", "user.name", "test")
        runtime.git(self.remote, "config", "user.email", "test@example.com")
        (self.remote / "scripts").mkdir()
        (self.remote / "scripts/generator.py").write_text("version = 1\n")
        runtime.git(self.remote, "add", ".")
        runtime.git(self.remote, "commit", "-m", "old")
        runtime.git(Path(self.temp.name), "clone", str(self.remote), str(self.local))
        (self.remote / "scripts/generator.py").write_text("version = 2\n")
        runtime.git(self.remote, "commit", "-am", "new filter")

    def test_stale_checkout_updates_before_fresh_process(self):
        manifest = runtime.synchronize(self.local)
        runtime.verify(self.local, manifest)
        self.assertEqual(manifest["sha"], runtime.git(self.remote, "rev-parse", "HEAD"))
        self.assertIn("version = 2", (self.local / "scripts/generator.py").read_text())

    def test_dirty_checkout_is_preserved_and_blocked(self):
        path = self.local / "scripts/generator.py"
        path.write_text("local work")
        with self.assertRaises(RuntimeError):
            runtime.synchronize(self.local)
        self.assertEqual(path.read_text(), "local work")

    def test_changed_code_after_sync_blocks_publish(self):
        manifest = runtime.synchronize(self.local)
        (self.local / "scripts/generator.py").write_text("unexpected change")
        with self.assertRaises(RuntimeError):
            runtime.verify(self.local, manifest)

    def test_wrong_branch_blocks_sync(self):
        runtime.git(self.local, "checkout", "-b", "feature")
        with self.assertRaises(RuntimeError):
            runtime.synchronize(self.local)

    def test_launcher_tests_before_child_and_check_only_never_generates(self):
        with mock.patch.object(runtime, "synchronize", return_value={"sha": "new"}), \
             mock.patch.object(runtime, "verify"), mock.patch.object(runtime.subprocess, "run") as run, \
             mock.patch.object(runtime, "git", return_value=str(self.local / ".git")):
            runtime.launch(self.local, check_only=True)
        self.assertEqual(run.call_count, 1)
        self.assertIn("unittest", run.call_args.args[0])
        self.assertIsNotNone(run.call_args.kwargs["stdout"])
        self.assertIsNotNone(run.call_args.kwargs["stderr"])

    def test_child_gets_stdio_when_parent_is_pythonw(self):
        with mock.patch.object(runtime.sys, "stdout", None), mock.patch.object(runtime.sys, "stderr", None):
            self.assertEqual(runtime.child_stdio(),
                             {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL})
