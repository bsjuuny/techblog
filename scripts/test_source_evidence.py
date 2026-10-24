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


_usage_dir = tempfile.TemporaryDirectory()


def setUpModule() -> None:
    # Token tallies must never land in the real repo's .git (tonight's run would add to them).
    daily._USAGE_DIR = Path(_usage_dir.name)
    # Fake usage accumulates across tests and the env may set a budget; tests that exercise the
    # budget patch it themselves.
    daily.DAILY_TOKEN_BUDGET = 10**12


def tearDownModule() -> None:
    _usage_dir.cleanup()


class SourceEvidenceTests(unittest.TestCase):
    repo = "https://github.com/example/project"
    readme = repo + "/blob/" + "a" * 40 + "/README.md"
    text = "The model has 740M parameters. It supports more than 100 languages. Windows and Linux are beta."

    def setUp(self):
        # The launcher runs these tests before every daily run, so their log lines would
        # land in the scheduler log next to the real run.
        for module in (evidence, daily):
            patcher = mock.patch.object(module, "print", create=True)
            patcher.start()
            self.addCleanup(patcher.stop)

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
            text = daily.write_post(draft, "news", dt.date(2026, 10, 17)).read_text(encoding="utf-8")
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

    def failed_news(self):
        return {"title": "Oregon waterfall for sale", "url": "https://apnews.com/article/x", "score": 120,
                "description": "Lawmakers want the state to buy the waterfall.",
                "evidence": [], "evidence_error": "403 Client Error: Forbidden"}

    def test_article_text_is_not_replaced_by_its_metadata(self):
        url = "https://example.com/posts/docker"
        article = "Unlike VMs, containers are just processes with special restrictions on them."
        source = {"title": "Docker is weird", "url": url, "score": 300,
                  "evidence": [{"url": url, "kind": "original_article", "text": article}]}
        draft = {"title": "오늘의 소식", "summary": "",
                 "body": "컨테이너는 제약이 걸린 프로세스이고 300점을 받았습니다. " + url,
                 "sources": evidence.evidence_sources([source]), "picked": None}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "컨테이너는 제약이 걸린 프로세스", "supported": True, "url": url, "quote": article},
            {"claim": "300점", "supported": True, "url": url, "quote": "score: 300"}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))

    def test_repository_metadata_can_be_cited_via_readme_url(self):
        source = {**self.source(), "created_at": "2026-10-12T08:41:19Z", "forks": 1207}
        draft = {"title": "저장소", "summary": "", "body": "2026-10-12에 공개됐고 별 200개입니다. " + self.readme,
                 "sources": evidence.evidence_sources([source]), "picked": None}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "2026-10-12에 공개됐고 별 200개", "supported": True, "url": self.readme,
             "quote": '"stars": 200, "created_at": "2026-10-12T08:41:19Z"'}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))
        audit["claims"][0]["quote"] = '"stars": 4438'
        self.assertFalse(evidence.validate_claim_audit(audit, draft))

    def test_unsupported_claim_logs_auditor_reason(self):
        audit = {"all_claims_supported": False, "claims": [
            {"claim": "모델 크기는 740M입니다.", "supported": False, "url": self.readme,
             "quote": "The model has 740M parameters.", "reason": "원문은 탈옥 불필요를 말하지 않음"}]}
        evidence.print.reset_mock()
        self.assertFalse(evidence.validate_claim_audit(audit, self.draft()))
        logged = "\n".join(str(c.args[0]) for c in evidence.print.call_args_list)
        self.assertIn("이유: 원문은 탈옥 불필요를 말하지 않음", logged)

    def test_til_prompt_names_readme_url_and_draft_without_it_skips_reviewers(self):
        with mock.patch.object(daily, "enrich_sources", return_value=[self.source()]), \
             mock.patch.object(daily, "_claude", return_value="본문 " + self.readme + "\nTITLE: 제목") as claude:
            daily.generate_draft_til([self.source()])
        self.assertIn(f"README URL({self.readme})을 반드시 인용", claude.call_args.args[0])

        draft = {"title": "제목", "summary": "", "body": "README에 따르면 740M입니다. " + self.repo,
                 "sources": evidence.evidence_sources([self.source()]), "picked": self.source()}
        reviewer = mock.Mock(side_effect=AssertionError("reviewer must not be called"))
        with mock.patch.multiple(daily, generate_draft_til=lambda _s, pick_rank=0: draft,
                                 fact_check_agent=reviewer, MAX_ATTEMPTS=1):
            self.assertIsNone(daily._generate_valid_draft("til", [self.source()], []))
        logged = "\n".join(str(c.args[0]) for c in daily.print.call_args_list)
        self.assertIn("README URL 인용 누락", logged)

    def test_claim_copied_without_backticks_still_matches_draft(self):
        draft = {**self.draft(), "body": "`region_consistent`는 지역 단위 판정입니다. " + self.readme}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "region_consistent는 지역 단위 판정입니다", "supported": True,
             "url": self.readme, "quote": "The model has 740M parameters."}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))
        audit["claims"][0]["claim"] = "region_consistent는 건물 단위 검증입니다"
        self.assertFalse(evidence.validate_claim_audit(audit, draft))

    def test_local_commit_document_includes_changed_files(self):
        sha = "30cd385f514e9bf4a517880df777331d2d160a3a"
        commit = {"title": "feat: updater", "body": "Add signed update storage.", "sha": sha, "url": "",
                  "files_changed": " src/update/capacitorStorage.ts |  55 ++++++\n src/update/storage.ts | 40 ++++"}
        draft = {"title": "개발기", "summary": "", "body": "저장소 계층을 두 파일로 나눴다.",
                 "sources": [commit], "picked": commit}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "저장소 계층을 두 파일로 나눴다", "supported": True, "url": "local:" + sha,
             "quote": "src/update/capacitorStorage.ts | 55 ++++++ src/update/storage.ts"}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))

    def test_readme_markdown_is_compared_as_rendered_text(self):
        doc = '**Since v2.0 there is an Android version** (community port); see [HarmonyOS](#harmonyos).'
        self.assertTrue(evidence.quote_in_document(
            "Since v2.0 there is an Android version (community port); see HarmonyOS.", doc))
        self.assertTrue(evidence.quote_in_document("**Since v2.0 there is an Android version**", doc))
        self.assertFalse(evidence.quote_in_document("Since v2.0 there is an iOS version", doc))

    def test_readme_text_can_be_cited_via_repository_url(self):
        draft = {**self.draft(), "body": "모델 크기는 740M입니다. " + self.repo}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "모델 크기는 740M입니다.", "supported": True, "url": self.repo,
             "quote": "The model has 740M parameters."}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))
        audit["claims"][0]["quote"] = "The model has 7B parameters."
        self.assertFalse(evidence.validate_claim_audit(audit, draft))

    def test_metadata_fields_elided_out_of_json_order(self):
        doc = json.dumps({"title": "a/b", "stars": 31500, "language": "Java",
                          "created_at": "2026-10-17T08:12:35Z", "license": "NOASSERTION"})
        quote = 'language": "Java", ... created_at": "2026-10-17T08:12:35Z" ... stars": 31500 ... license": "NOASSERTION"'
        self.assertTrue(evidence.quote_in_document(quote, doc))
        self.assertFalse(evidence.quote_in_document(quote.replace("31500", "3150"), doc))

    def test_separately_quoted_metadata_fields_match_whole_fields_only(self):
        doc = json.dumps({"title": "a/b", "language": "C", "stars": 4438, "forks": 1226,
                          "description": "CSS tool"})
        self.assertTrue(evidence.quote_in_document("language: C, forks: 1226", doc))
        self.assertTrue(evidence.quote_in_document('"language": "C", "forks": 1226', doc))
        self.assertFalse(evidence.quote_in_document("language: CSS, forks: 1226", doc))
        self.assertFalse(evidence.quote_in_document("language: C, forks: 122", doc))
        self.assertFalse(evidence.quote_in_document("language: C, license: MIT", doc))

    def test_rejected_claims_are_collected_for_revision(self):
        problems = []
        audit = {"all_claims_supported": False, "claims": [
            {"claim": "모델 크기는 740M입니다.", "supported": False, "reason": "원문과 다름"}]}
        self.assertFalse(evidence.validate_claim_audit(audit, self.draft(), problems))
        self.assertEqual(problems, [{"claim": "모델 크기는 740M입니다.", "reason": "원문과 다름"}])
        problems = []
        audit = self.audit()
        audit["claims"][0]["quote"] = "The model has 7B parameters."
        self.assertFalse(evidence.validate_claim_audit(audit, self.draft(), problems))
        self.assertEqual(problems, [{"claim": "모델 크기는 740M입니다.", "reason": "원문에 없는 발췌"}])

    def test_quote_failure_logs_cited_url_and_quote(self):
        audit = self.audit()
        audit["claims"][0]["quote"] = "The model has 7B parameters."
        evidence.print.reset_mock()
        self.assertFalse(evidence.validate_claim_audit(audit, self.draft()))
        logged = "\n".join(str(c.args[0]) for c in evidence.print.call_args_list)
        self.assertIn("원문에 없는 발췌", logged)
        self.assertIn("인용 URL: " + self.readme, logged)
        self.assertIn("7B parameters", logged)

    def test_unfetched_source_may_be_linked_by_headline(self):
        source = self.failed_news()
        draft = {"title": "오늘의 소식", "summary": "",
                 "body": "Oregon waterfall for sale 기사는 원문을 확인하지 못해 제목만 소개합니다. " + source["url"],
                 "sources": [source], "picked": None}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "Oregon waterfall for sale", "supported": True,
             "url": source["url"], "quote": "Oregon waterfall for sale"}]}
        self.assertTrue(evidence.validate_claim_audit(audit, draft))

    def test_unfetched_source_content_cannot_be_claimed(self):
        source = self.failed_news()
        draft = {"title": "오늘의 소식", "summary": "",
                 "body": "의원들이 주 정부의 폭포 매입을 원합니다. " + source["url"],
                 "sources": [source], "picked": None}
        audit = {"all_claims_supported": True, "claims": [
            {"claim": "의원들이 주 정부의 폭포 매입을 원합니다.", "supported": True,
             "url": source["url"], "quote": "Lawmakers want the state to buy the waterfall."}]}
        self.assertFalse(evidence.validate_claim_audit(audit, draft))

    def test_news_prompt_marks_unfetched_source_link_only(self):
        enriched = [{**self.failed_news(), "hn_discussion": "https://news.ycombinator.com/item?id=1"}]
        with mock.patch.object(daily, "enrich_sources", return_value=enriched), \
             mock.patch.object(daily, "_claude", return_value="본문\nTITLE: 제목") as claude:
            draft = daily.generate_draft_news([self.failed_news()])
        prompt = claude.call_args.args[0]
        self.assertIn("원문 없음", prompt)
        self.assertNotIn("Lawmakers want", prompt)
        self.assertEqual(draft["sources"][0]["evidence"], [])
        self.assertNotIn("description", draft["sources"][0])

    def test_elided_and_typographic_quotes_match_in_order(self):
        doc = "We strongly recommend that you roll all variables.\nDon’t use async/.await in\nChrome\n. " \
              "The sdist leaves out the cook folder entirely."
        self.assertTrue(evidence.quote_in_document("Don't use async/.await in Chrome.", doc))
        self.assertTrue(evidence.quote_in_document("leaves out the `cook` folder", doc))
        self.assertTrue(evidence.quote_in_document(
            "We strongly recommend that you roll ... leaves out the cook folder", doc))
        self.assertTrue(evidence.quote_in_document(
            "We strongly recommend that you roll … leaves out the cook folder", doc))

    def test_elided_quote_accepts_any_order_but_rejects_short_or_invented_parts(self):
        doc = "We strongly recommend that you roll all variables. The sdist leaves out the cook folder."
        # README bullets were quoted out of order (2026-10-25 Radar); each part is still literal.
        self.assertTrue(evidence.quote_in_document(
            "leaves out the cook folder ... We strongly recommend that", doc))
        self.assertFalse(evidence.quote_in_document("We ... folder", doc))
        self.assertFalse(evidence.quote_in_document(
            "We strongly recommend that you roll ... deletes every secret it finds", doc))
        self.assertFalse(evidence.quote_in_document("...", doc))

    def test_audit_json_wrapped_in_prose_or_fence_is_parsed(self):
        wrapped = "다음은 감사 결과입니다.\n```json\n" + json.dumps(self.audit()) + "\n```"
        self.assertEqual(daily._parse_json_object(wrapped), self.audit())
        with self.assertRaises(ValueError):
            daily._parse_json_object("감사 결과 없음")

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
        text = path.read_text(encoding="utf-8")
        body, footer = text.split("**참고한 원본 소스**")
        self.assertEqual(evidence.body_urls(footer), evidence.body_urls(body))
        self.assertEqual(len(evidence.body_urls(footer)), 2)
        self.assertIn("740M", body)
        self.assertIn("100개 이상", body)
        self.assertIn("베타", body)
        self.assertNotIn("openai/math", text)


if __name__ == "__main__":
    unittest.main()

