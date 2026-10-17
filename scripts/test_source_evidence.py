from __future__ import annotations

import base64
import datetime as dt
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-import-only")
from scripts import generate_daily_post as daily
from scripts import source_evidence as evidence


class SourceEvidenceTests(unittest.TestCase):
    repo = "https://github.com/example/project"
    readme = repo + "/blob/" + "a" * 40 + "/README.md"
    text = "The model has 740M parameters. It supports more than 100 languages. Windows and Linux are beta."

    def source(self):
        return {"title": "example/project", "url": self.repo,
                "description": "A sufficiently descriptive local file search application",
                "language": "Swift", "stars": 200,
                "evidence": [{"url": self.readme, "kind": "official_readme", "text": self.text}]}

    def draft(self):
        return {"title": "모델 사양", "summary": "740M 모델을 살펴봅니다.",
                "body": "모델 크기는 740M입니다. " + self.readme,
                "sources": evidence.evidence_sources([self.source()]), "picked": None}

    def audit(self):
        return {"all_claims_supported": True, "claims": [
            {"claim": "모델 크기는 740M입니다.", "supported": True,
             "url": self.readme, "quote": "The model has 740M parameters."}]}

    def test_footer_only_lists_body_sources_and_deduplicates(self):
        sources = [self.source(), {"title": "unused dog brace", "url": "https://example.com/dog"}, self.source()]
        draft = {**self.draft(), "body": "원본 " + self.repo + "/#intro", "sources": sources}
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(daily, "POSTS_DIR", Path(temp)):
            text = daily.write_post(draft, "news", dt.date(2026, 10, 17)).read_text()
        footer = text.split("**참고한 원본 소스**")[1]
        self.assertEqual(footer.count(self.repo), 1)
        self.assertNotIn("dog", footer)

    def test_url_boundaries_queries_and_examples(self):
        body = (self.repo + "-other\n```\n" + self.repo + "\n```\n<!-- " + self.repo + " -->")
        self.assertEqual(evidence.used_sources(body, [self.source()]), [])
        self.assertEqual(evidence.used_sources(self.repo + "?v=2", [self.source()]), [])

    def test_readme_fetch_is_pinned_and_preserves_specs(self):
        commit, readme = mock.Mock(), mock.Mock()
        commit.json.return_value = {"sha": "a" * 40}
        readme.json.return_value = {"encoding": "base64", "path": "README.md", "size": len(self.text),
                                    "content": base64.b64encode(self.text.encode()).decode()}
        with mock.patch.object(evidence.requests, "get", side_effect=[commit, readme]) as get:
            [source] = evidence.enrich_sources([self.source()])
        self.assertEqual(get.call_args.kwargs["params"], {"ref": "a" * 40})
        self.assertEqual(source["evidence"][0]["url"], self.readme)
        self.assertIn("740M", source["evidence"][0]["text"])
        self.assertIn("100 languages", source["evidence"][0]["text"])
        self.assertIn("beta", source["evidence"][0]["text"])

    def test_fetch_failure_does_not_invent_evidence(self):
        with mock.patch.object(evidence.requests, "get", side_effect=evidence.requests.Timeout("timeout")):
            [source] = evidence.enrich_sources([self.source()])
        self.assertEqual(source["evidence"], [])
        self.assertIn("evidence_error", source)
        draft = {**self.draft(), "sources": [source], "body": self.repo}
        self.assertFalse(evidence.validate_claim_audit(self.audit(), draft))

    def test_til_researches_only_picked_subject_and_shares_original(self):
        unused = {**self.source(), "title": "unused/other", "url": "https://github.com/unused/other",
                  "description": "Shorter description still long enough"}
        with mock.patch.object(daily, "enrich_sources", return_value=[self.source()]) as enrich, \
             mock.patch.object(daily, "_claude", return_value="본문 " + self.readme + "\nTITLE: 제목") as claude:
            draft = daily.generate_draft_til([self.source(), unused])
        self.assertEqual(len(enrich.call_args.args[0]), 1)
        self.assertIn(self.text, claude.call_args.args[0])
        self.assertNotIn("unused/other", claude.call_args.args[0])
        self.assertIn(self.readme, {s["url"] for s in draft["sources"]})

    def test_valid_literal_grounding_passes(self):
        self.assertTrue(evidence.validate_claim_audit(self.audit(), self.draft()))

    def test_unsupported_claim_is_rejected(self):
        audit = self.audit()
        audit["all_claims_supported"] = False
        self.assertFalse(evidence.validate_claim_audit(audit, self.draft()))
        audit = self.audit()
        audit["claims"][0]["supported"] = False
        self.assertFalse(evidence.validate_claim_audit(audit, self.draft()))

    def test_fabricated_quote_url_or_claim_is_rejected(self):
        for key, value in [("quote", "The model has 7B parameters."),
                           ("url", "https://example.com/not-fetched"),
                           ("claim", "초안에 없는 주장")]:
            audit = self.audit()
            audit["claims"][0][key] = value
            self.assertFalse(evidence.validate_claim_audit(audit, self.draft()), key)

    def test_malformed_or_empty_audit_fails_closed(self):
        for audit in [None, [], {}, {"all_claims_supported": "true", "claims": []},
                      {"all_claims_supported": True, "claims": []}]:
            self.assertFalse(evidence.validate_claim_audit(audit, self.draft()))

    def test_fact_checker_requires_grounding_after_checklist_pass(self):
        checklist = "팩트: PASS\n최신성: PASS\n공식출처: PASS\n중복충돌: PASS\n사유: 없음"
        for audit, expected in [(self.audit(), True), ({"all_claims_supported": False}, False)]:
            with mock.patch.object(daily, "_claude", side_effect=[checklist, json.dumps(audit)]) as claude:
                result = daily.fact_check_agent(self.draft(), [])
            self.assertEqual(result["팩트"], expected)
            self.assertIn(self.text, claude.call_args.args[0])
            self.assertIn("740M 모델을", claude.call_args.args[0])

    def test_wrong_unknown_specs_fail_audit(self):
        draft = self.draft()
        draft["body"] = "파라미터 수와 지원 언어는 확인되지 않습니다. " + self.readme
        checklist = "팩트: PASS\n최신성: PASS\n공식출처: PASS\n중복충돌: PASS"
        with mock.patch.object(daily, "_claude", side_effect=[checklist, json.dumps({
            "all_claims_supported": False, "claims": [{"claim": draft["body"], "supported": False}]})]) as claude:
            result = daily.fact_check_agent(draft, [])
        self.assertFalse(result["팩트"])
        self.assertIn("부정 주장", claude.call_args.args[0])

    def test_invalid_audit_json_blocks_publication(self):
        checklist = "팩트: PASS\n최신성: PASS\n공식출처: PASS\n중복충돌: PASS"
        with mock.patch.object(daily, "_claude", side_effect=[checklist, "not JSON"]):
            self.assertFalse(daily.fact_check_agent(self.draft(), [])["팩트"])

    def test_original_article_text_not_just_metadata_is_retained(self):
        with mock.patch.object(evidence, "_article", return_value="Original verified technical details."):
            [source] = evidence.enrich_sources([{"title": "news", "url": "https://example.com/news"}])
        self.assertEqual(source["evidence"][0]["kind"], "original_article")
        self.assertIn("technical details", source["evidence"][0]["text"])

    def test_private_source_addresses_are_blocked(self):
        for url in ["file:///etc/passwd", "https://user:secret@example.com", "http://127.0.0.1/test"]:
            with mock.patch.object(evidence.socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 80))]):
                with self.assertRaises(ValueError):
                    evidence._public_url(url)

    def test_html_scripts_and_navigation_are_not_evidence(self):
        parser = evidence._ArticleText()
        parser.feed("<nav>menu</nav><script>invented</script><article><p>Actual facts</p></article>")
        self.assertEqual(parser.parts, ["Actual facts"])

    def test_unsupported_claim_cannot_reach_quality_gate(self):
        checklist = "팩트: PASS\n최신성: PASS\n공식출처: PASS\n중복충돌: PASS"
        with mock.patch.object(daily, "generate_draft_til", side_effect=lambda *_a, **_k: self.draft()), \
             mock.patch.object(daily, "_claude", side_effect=[checklist, '{"all_claims_supported": false}'] * 3), \
             mock.patch.object(daily, "quality_check_agent") as quality:
            draft = daily._generate_valid_draft("til", [self.source()], [])
        self.assertIsNone(draft)
        quality.assert_not_called()
        self.assertEqual(daily.MAX_ATTEMPTS, 3)

    def test_unused_subject_does_not_reach_fact_checker(self):
        draft = self.draft()
        draft["sources"].append({"title": "dog", "url": "https://example.com/dog"})
        with mock.patch.object(daily, "generate_draft_news", return_value=draft), \
             mock.patch.object(daily, "fact_check_agent", return_value={
                 "팩트": False, "최신성": True, "공식출처": True, "중복충돌": True}) as fact:
            daily._generate_valid_draft("news", draft["sources"], [])
        self.assertNotIn("dog", {s["title"] for s in fact.call_args.args[0]["sources"]})

    def test_local_commit_remains_a_valid_evidence_source(self):
        source = {"title": "repo: fixed parsing", "body": "Fixed parser failure", "sha": "abc123", "url": ""}
        draft = {"title": "파서 수정", "summary": "", "body": "파서를 수정했다.", "sources": [source]}
        audit = {"all_claims_supported": True, "claims": [{"claim": "파서를 수정했다.", "supported": True,
                 "url": "local:abc123", "quote": "Fixed parser failure"}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))

    def test_corrected_post_has_only_two_used_primary_sources(self):
        path = daily.POSTS_DIR / "2026-10-17-til-1792168366.md"
        text = path.read_text()
        body, footer = text.split("**참고한 원본 소스**")
        self.assertEqual(evidence.body_urls(footer), evidence.body_urls(body))
        self.assertEqual(len(evidence.body_urls(footer)), 2)
        self.assertIn("740M", body)
        self.assertIn("100개 이상", body)
        self.assertIn("베타", body)
        self.assertNotIn("openai/math", text)


if __name__ == "__main__":
    unittest.main()
