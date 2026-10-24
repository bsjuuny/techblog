from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-import-only")

from scripts import generate_daily_post as daily  # noqa: E402


_usage_dir = tempfile.TemporaryDirectory()


def setUpModule() -> None:
    # Token tallies must never land in the real repo's .git (tonight's run would add to them).
    daily._USAGE_DIR = Path(_usage_dir.name)
    # Fake usage accumulates across tests and the env may set a budget; tests that exercise the
    # budget patch it themselves.
    daily.DAILY_TOKEN_BUDGET = 10**12


def tearDownModule() -> None:
    _usage_dir.cleanup()
from scripts.post_meta import normalize_headings  # noqa: E402


class ContentScheduleTests(unittest.TestCase):
    def test_weekend_slots(self) -> None:
        self.assertEqual(daily.pick_content_type(dt.date(2026, 9, 19)), "github_radar")
        self.assertEqual(daily.pick_content_type(dt.date(2026, 9, 20)), "engineering")
        self.assertIn(daily.pick_content_type(dt.date(2026, 9, 21)), {"til", "news"})


class GithubRadarRankingTests(unittest.TestCase):
    reference_date = dt.date(2026, 9, 19)

    def source(
        self,
        name: str,
        *,
        owner: str,
        language: str,
        stars: int,
        age_days: int,
        pushed_days_ago: int = 1,
        **overrides: object,
    ) -> dict[str, object]:
        source: dict[str, object] = {
            "title": f"{owner}/{name}",
            "url": f"https://github.com/{owner}/{name}",
            "description": f"A sufficiently detailed description for {name}",
            "stars": stars,
            "language": language,
            "created_at": (
                self.reference_date - dt.timedelta(days=age_days)
            ).isoformat() + "T00:00:00Z",
            "pushed_at": (
                self.reference_date - dt.timedelta(days=pushed_days_ago)
            ).isoformat() + "T00:00:00Z",
            "forks": 10,
            "fork": False,
            "archived": False,
            "disabled": False,
            "license": "MIT",
            "owner": owner,
        }
        source.update(overrides)
        return source

    def test_ranking_filters_and_keeps_owner_language_diversity(self) -> None:
        sources = [
            self.source("alpha", owner="one", language="Python", stars=900, age_days=3),
            self.source("same-owner", owner="one", language="Rust", stars=850, age_days=3),
            self.source("beta", owner="two", language="Python", stars=700, age_days=4),
            self.source("third-python", owner="three", language="Python", stars=650, age_days=4),
            self.source("gamma", owner="four", language="TypeScript", stars=500, age_days=5),
            self.source("archived", owner="five", language="Go", stars=2_000, age_days=3, archived=True),
            self.source("unlicensed", owner="six", language="Go", stars=1_900, age_days=3, license=""),
        ]

        selected = daily.rank_github_radar_candidates(
            sources,
            reference_date=self.reference_date,
        )

        self.assertEqual(
            [item["title"] for item in selected],
            ["one/alpha", "two/beta", "four/gamma"],
        )
        self.assertTrue(all("stars_per_day" in item for item in selected))

    def test_ranking_returns_empty_when_fewer_than_three_survive(self) -> None:
        sources = [
            self.source("too-new", owner="one", language="Python", stars=900, age_days=1),
            self.source("valid", owner="two", language="Rust", stars=300, age_days=3),
            self.source("stale", owner="three", language="Go", stars=400, age_days=4, pushed_days_ago=20),
        ]

        selected = daily.rank_github_radar_candidates(
            sources,
            reference_date=self.reference_date,
        )

        self.assertEqual(selected, [])


class GithubRadarPostTests(unittest.TestCase):
    def test_recent_featured_urls_ignore_source_footer(self) -> None:
        original_posts_dir = daily.POSTS_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            daily.POSTS_DIR = Path(temp_dir)
            today = dt.date.today().isoformat()
            (daily.POSTS_DIR / f"{today}-radar.md").write_text(
                "본문 https://github.com/example/featured\n\n"
                "---\n\n**참고한 원본 소스**\n\n"
                "- [unused](https://github.com/example/unused)\n",
                encoding="utf-8",
            )
            try:
                urls = daily.get_recent_featured_repo_urls()
            finally:
                daily.POSTS_DIR = original_posts_dir

        self.assertIn("https://github.com/example/featured", urls)
        self.assertNotIn("https://github.com/example/unused", urls)

    def test_recent_titles_can_skip_previous_radar_issues(self) -> None:
        original_posts_dir = daily.POSTS_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            daily.POSTS_DIR = Path(temp_dir)
            today = dt.date.today().isoformat()
            (daily.POSTS_DIR / f"{today}-github-radar-1.md").write_text(
                '---\ntitle: "이번 주 GitHub Radar 5선"\n---\n', encoding="utf-8"
            )
            (daily.POSTS_DIR / f"{today}-news-2.md").write_text(
                '---\ntitle: "오늘의 기술 뉴스"\n---\n', encoding="utf-8"
            )
            try:
                all_titles = daily.get_recent_titles()
                non_radar = daily.get_recent_titles(exclude_content_type="github_radar")
            finally:
                daily.POSTS_DIR = original_posts_dir

        self.assertEqual(sorted(all_titles), ["오늘의 기술 뉴스", "이번 주 GitHub Radar 5선"])
        self.assertEqual(non_radar, ["오늘의 기술 뉴스"])

    def test_write_post_uses_radar_category_and_tags(self) -> None:
        original_posts_dir = daily.POSTS_DIR
        original_slugify = daily._slugify
        with tempfile.TemporaryDirectory() as temp_dir:
            daily.POSTS_DIR = Path(temp_dir)
            daily._slugify = lambda title, content_type: "github-radar-test"
            try:
                path = daily.write_post(
                    {
                        "title": "이번 주 GitHub 프로젝트 3선",
                        "body": "본문",
                        "sources": [
                            {
                                "title": "example/project",
                                "url": "https://github.com/example/project",
                            }
                        ],
                        "picked": None,
                    },
                    "github_radar",
                    dt.date(2026, 9, 19),
                )
                text = path.read_text(encoding="utf-8")
            finally:
                daily.POSTS_DIR = original_posts_dir
                daily._slugify = original_slugify

        self.assertIn("  - github-radar", text)
        self.assertIn('category_label: "GitHub Radar · Auto"', text)
        self.assertIn("  - Open Source", text)


class RunRetryAndFallbackTests(unittest.TestCase):
    """요일 슬롯의 재시도·대체 경로와 watchdog 상태 마커. 외부 호출(API·Claude·git)은 전부 막는다."""

    saturday = dt.date(2026, 10, 10)
    sunday = dt.date(2026, 10, 11)
    url = "https://github.com/example/project"
    PASS_FACT = {"팩트": True, "최신성": True, "공식출처": True, "중복충돌": True}
    FAIL_FACT = {**PASS_FACT, "중복충돌": False, "_reason": "최근 글과 주제가 사실상 동일"}
    PASS_QUALITY = {
        "검색의도": True, "반복제거": True, "제목/CTR": 90, "네이버SEO": 90,
        "모바일UX": 90, "차별성": 90, "생성형검색": 90,
    }

    def draft(self, body: str | None = None) -> dict:
        return {
            "title": "제목", "summary": "", "body": body or f"본문 {self.url}",
            "sources": [{"title": "example/project", "url": self.url}], "picked": None,
        }

    def run_day(self, target_date, *, facts, radar_bodies=None, radar_sources=None,
                radar_error=None, commits=None):
        sources = [{"title": "example/project", "url": self.url}]
        calls = {"radar": 0, "excluded": []}
        fact_iter = iter(facts)
        bodies = iter(radar_bodies or [])

        def recent_titles(*_args, **kwargs):
            calls["excluded"].append(kwargs.get("exclude_content_type"))
            return []

        def radar_candidates(_date):
            if radar_error:
                raise radar_error
            return sources if radar_sources is None else radar_sources

        def radar_draft(_sources):
            calls["radar"] += 1
            return self.draft(next(bodies, None))

        out = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.multiple(
            daily,
            _STATUS_DIR=Path(temp_dir),
            get_recent_titles=recent_titles,
            fetch_github_radar_candidates=radar_candidates,
            generate_draft_github_radar=radar_draft,
            fetch_project_commits=lambda: commits or [],
            generate_draft_engineering=lambda _s, pick_rank=0: self.draft(),
            fetch_github_trending=lambda: sources,
            fetch_hackernews_top=lambda: sources,
            generate_draft_til=lambda _s, pick_rank=0: self.draft(),
            generate_draft_news=lambda _s: self.draft(),
            fact_check_agent=lambda _d, _t: next(fact_iter),
            quality_check_agent=lambda _d, _c: self.PASS_QUALITY,
            write_post=lambda _d, c, _t: Path(temp_dir) / f"{c}.md",
            commit_and_push=lambda _p: None,
        ), contextlib.redirect_stdout(out):
            daily.run(target_date)
            [marker_path] = Path(temp_dir).glob("techblog-*.json")
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        return marker, calls, out.getvalue()

    def test_radar_retries_until_a_draft_passes(self) -> None:
        marker, calls, log = self.run_day(
            self.saturday,
            radar_bodies=["본문 度 " + self.url, "본문 https://example.com/invented", None],
            facts=[self.PASS_FACT],
        )
        self.assertEqual(calls["radar"], 3)
        self.assertIn("github_radar", calls["excluded"])
        self.assertIn("한자 오염 감지", log)
        self.assertIn("링크 검증 실패", log)
        self.assertEqual(marker["published"], True)
        self.assertEqual(marker["contentType"], "github_radar")
        self.assertNotIn("fallbackFrom", marker)

    def test_radar_validation_failure_falls_back_and_is_recorded(self) -> None:
        marker, calls, log = self.run_day(self.saturday, facts=[self.FAIL_FACT] * 3 + [self.PASS_FACT])
        self.assertEqual(calls["radar"], 3)
        self.assertIn("GitHub Radar 3번 시도 모두 검증 실패, 평소 유형으로 대체", log)
        self.assertEqual(marker["published"], True)
        self.assertEqual(marker["contentType"], daily._fallback_content_type(self.saturday))
        self.assertEqual(marker["fallbackFrom"], "github_radar(3번 시도 모두 검증 실패)")

    def test_radar_fallback_reason_distinguishes_shortage_and_fetch_error(self) -> None:
        marker, calls, _ = self.run_day(self.saturday, radar_sources=[], facts=[self.PASS_FACT])
        self.assertEqual(calls["radar"], 0)
        self.assertEqual(marker["fallbackFrom"], "github_radar(후보 3개 미만)")

        marker, _, _ = self.run_day(
            self.saturday, radar_error=RuntimeError("rate limit"), facts=[self.PASS_FACT]
        )
        self.assertEqual(marker["fallbackFrom"], "github_radar(소재 수집 실패: rate limit)")

    def test_engineering_without_commits_falls_back(self) -> None:
        marker, _, _ = self.run_day(self.sunday, commits=[], facts=[self.PASS_FACT])
        self.assertEqual(marker["fallbackFrom"], "engineering(이번 주 커밋 소재 없음)")
        self.assertEqual(marker["contentType"], daily._fallback_content_type(self.sunday))

    def test_skip_after_every_attempt_fails_keeps_type_in_marker(self) -> None:
        marker, _, log = self.run_day(self.saturday, facts=[self.FAIL_FACT] * 6)
        self.assertIn("오늘은 발행을 건너뜀", log)
        self.assertEqual(marker["published"], False)
        self.assertEqual(marker["reason"], "3번 시도 모두 검증 실패")
        self.assertEqual(marker["fallbackFrom"], "github_radar(3번 시도 모두 검증 실패)")


class PostMetaTest(unittest.TestCase):
    """excerpt / 본문 H1 정규화 — 생성형 엔진이 인용할 근거가 되는 메타데이터."""

    def _write(self, draft: dict, content_type: str = "news") -> str:
        original_posts_dir = daily.POSTS_DIR
        original_slugify = daily._slugify
        with tempfile.TemporaryDirectory() as temp_dir:
            daily.POSTS_DIR = Path(temp_dir)
            daily._slugify = lambda title, content_type: "meta-test"
            try:
                path = daily.write_post(draft, content_type, dt.date(2026, 10, 6))
                return path.read_text(encoding="utf-8")
            finally:
                daily.POSTS_DIR = original_posts_dir
                daily._slugify = original_slugify

    def test_split_meta_separates_summary_and_demotes_body_h1(self) -> None:
        title, summary, body = daily._split_meta(
            "# 오늘의 브리핑\n\n첫 문단입니다.\n\nTITLE: 오늘의 개발 뉴스 3가지\nSUMMARY: 세 가지 소식을 각각 왜 봐둘 만한지로 정리했습니다."
        )
        self.assertEqual(title, "오늘의 개발 뉴스 3가지")
        self.assertEqual(summary, "세 가지 소식을 각각 왜 봐둘 만한지로 정리했습니다.")
        self.assertNotIn("TITLE:", body)
        self.assertNotIn("SUMMARY:", body)
        # 레이아웃이 이미 제목을 H1으로 출력하므로 본문 H1은 남으면 안 된다.
        self.assertNotIn("\n# ", "\n" + body)
        self.assertIn("## 오늘의 브리핑", body)

    def test_write_post_uses_model_summary_as_excerpt(self) -> None:
        text = self._write(
            {
                "title": "오늘의 개발 뉴스 3가지",
                "summary": "세 가지 소식을 각각 왜 봐둘 만한지로 정리했습니다.",
                "body": "첫 문단입니다.",
                "sources": [],
                "picked": None,
            }
        )
        self.assertIn('excerpt: "세 가지 소식을 각각 왜 봐둘 만한지로 정리했습니다."', text)

    def test_write_post_falls_back_to_first_paragraph(self) -> None:
        # 모델이 SUMMARY를 빠뜨리거나 제목을 그대로 되풀이하면 본문에서 뽑는다.
        for summary in ("", "오늘의 개발 뉴스 3가지"):
            text = self._write(
                {
                    "title": "오늘의 개발 뉴스 3가지",
                    "summary": summary,
                    "body": "## 소제목\n\n오늘은 보안 사고와 인프라 도구 소식이 섞여 있습니다.",
                    "sources": [],
                    "picked": None,
                }
            )
            self.assertIn('excerpt: "오늘은 보안 사고와 인프라 도구 소식이 섞여 있습니다."', text)

    def test_code_fence_comments_are_not_treated_as_headings(self) -> None:
        body = "본문입니다.\n\n```bash\n# 설치 스크립트\nbrew install foo\n```\n"
        self.assertIn("# 설치 스크립트", normalize_headings(body, "제목"))


class MixedWordTests(unittest.TestCase):
    def test_korean_prefix_with_acronym_is_not_broken(self) -> None:
        body = "비ASCII 문자와 맥OS, 웹API 지원. GPT가 iPhone에서 동작한다."
        self.assertEqual(daily.find_broken_mixed_words(body), [])

    def test_language_switch_inside_word_is_still_caught(self) -> None:
        self.assertEqual(daily.find_broken_mixed_words("암azon 서비스"), ["암azon"])


class TilPromptTests(unittest.TestCase):
    def test_prompt_does_not_suggest_an_age_and_forbids_elapsed_periods(self) -> None:
        source = {"title": "example/project", "url": "https://github.com/example/project",
                  "description": "A sufficiently descriptive project", "created_at": "2026-10-12T00:00:00Z"}
        with mock.patch.object(daily, "enrich_sources", return_value=[source]), \
             mock.patch.object(daily, "_claude", return_value="본문\nTITLE: 제목") as claude:
            daily.generate_draft_til([source])
        prompt = claude.call_args.args[0]
        self.assertNotIn("14일", prompt)
        self.assertIn("경과 기간은 쓰지 말고", prompt)


class CostControlTests(unittest.TestCase):
    """원문 중복 제거·길이 상한·토큰 기록·하루 상한. 외부 호출은 전부 가짜로 대신한다."""

    readme_text = "README-BODY " * 50
    repo = "https://github.com/example/project"
    readme_url = repo + "/blob/" + "a" * 40 + "/README.md"

    def setUp(self) -> None:
        self.usage_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.usage_dir.cleanup)
        patcher = mock.patch.object(daily, "_USAGE_DIR", Path(self.usage_dir.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def picked(self) -> dict:
        return {"title": "example/project", "url": self.repo, "stars": 10, "created_at": "2026-10-12",
                "description": "A sufficiently descriptive project",
                "evidence": [{"url": self.readme_url, "kind": "official_readme", "text": self.readme_text}]}

    def test_til_prompt_carries_readme_once_and_uses_readme_cap(self) -> None:
        with mock.patch.object(daily, "enrich_sources", return_value=[self.picked()]) as enrich, \
             mock.patch.object(daily, "_claude", return_value="본문\nTITLE: 제목") as claude:
            draft = daily.generate_draft_til([self.picked()])
        self.assertEqual(enrich.call_args.kwargs["max_chars"], daily.README_MAX_CHARS)
        self.assertEqual(claude.call_args.args[0].count(self.readme_text), 1)
        self.assertEqual(json.dumps(draft["sources"], ensure_ascii=False).count(self.readme_text), 1)
        self.assertIn(self.readme_url, {s["url"] for s in draft["sources"]})

    def test_enrich_respects_max_chars(self) -> None:
        from scripts import source_evidence
        with mock.patch.object(source_evidence, "_article", return_value="x" * 50_000), \
             mock.patch.object(source_evidence, "print", create=True):
            [source] = source_evidence.enrich_sources([{"title": "t", "url": "https://example.com/a"}],
                                                      max_chars=daily.NEWS_ARTICLE_MAX_CHARS)
        self.assertEqual(len(source["evidence"][0]["text"]), daily.NEWS_ARTICLE_MAX_CHARS)

    def test_news_fetches_only_top_scored_originals(self) -> None:
        items = [{"title": f"story {i}", "url": f"https://example.com/{i}", "score": i, "description": ""}
                 for i in range(8)]

        def fake_enrich(sources, max_chars):
            return [{**s, "evidence": [{"url": s["url"], "kind": "original_article", "text": "body"}]}
                    for s in sources]

        with mock.patch.object(daily, "enrich_sources", side_effect=fake_enrich) as enrich, \
             mock.patch.object(daily, "_claude", return_value="본문\nTITLE: 제목"):
            draft = daily.generate_draft_news(items)
        [call] = enrich.call_args_list
        self.assertEqual([s["score"] for s in call.args[0]], [7, 6, 5, 4, 3])
        self.assertEqual(call.kwargs["max_chars"], daily.NEWS_ARTICLE_MAX_CHARS)
        link_only = [s for s in draft["sources"] if s.get("evidence_error")]
        self.assertEqual({s["score"] for s in link_only}, {0, 1, 2})
        self.assertTrue(all(s["evidence"] == [] and "description" not in s for s in link_only))

    def test_reviewers_get_sources_once_without_indent(self) -> None:
        draft = {"title": "제목", "summary": "", "body": "본문", "sources": [self.picked()],
                 "picked": self.picked(), "review_context": [self.picked()]}
        prompts = []

        def fake_claude(prompt, **_kw):
            prompts.append(prompt)
            return "팩트: PASS\n최신성: PASS\n공식출처: PASS\n중복충돌: PASS\n사유: 없음" if len(prompts) == 1 \
                else '{"all_claims_supported": false}'

        with mock.patch.object(daily, "_claude", side_effect=fake_claude):
            daily.fact_check_agent(draft, [])
        checklist, audit = prompts
        self.assertEqual(checklist.count(self.readme_text), 1)
        self.assertNotIn('\n  "', checklist)  # no indent=2 JSON
        self.assertEqual(audit.count(self.readme_text), 1)

    def fake_response(self, inp: int, out: int) -> SimpleNamespace:
        return SimpleNamespace(content=[SimpleNamespace(type="text", text="ok")], stop_reason="end_turn",
                               usage=SimpleNamespace(input_tokens=inp, output_tokens=out))

    def test_usage_is_logged_and_accumulated_per_day(self) -> None:
        out = io.StringIO()
        responses = iter([self.fake_response(1000, 200), self.fake_response(3000, 400)])
        with mock.patch.object(daily._client.messages, "create", lambda **_kw: next(responses)), \
                contextlib.redirect_stdout(out):
            daily._claude("a")
            daily._claude("b")
        self.assertEqual(daily.today_usage(), {"input": 4000, "output": 600, "calls": 2})
        self.assertIn("토큰: 입력 3,000 / 출력 400 (오늘 누적 4,600", out.getvalue())

    def test_budget_stops_remaining_attempts_and_marker_records_tokens(self) -> None:
        daily._usage_path().write_text(json.dumps({"input": 140_000, "output": 20_000, "calls": 9}),
                                       encoding="utf-8")
        out = io.StringIO()
        # 상한은 환경변수로 바뀔 수 있다 — 고정하지 않으면 DAILY_TOKEN_BUDGET 을 준 실행에서 이 테스트가
        # 실패해 런처가 생성을 시작하지 못한다(2026-10-25 수동 실행).
        with tempfile.TemporaryDirectory() as status_dir, mock.patch.multiple(
            daily, _STATUS_DIR=Path(status_dir), get_recent_titles=lambda *a, **k: [], DAILY_TOKEN_BUDGET=150_000,
            fetch_github_trending=lambda: [self.picked()], fetch_hackernews_top=lambda: [self.picked()],
            generate_draft_til=mock.Mock(side_effect=AssertionError("must not generate")),
            generate_draft_news=mock.Mock(side_effect=AssertionError("must not generate")),
        ), contextlib.redirect_stdout(out):
            daily.run(dt.date(2026, 10, 21))
            [marker_path] = Path(status_dir).glob("techblog-*.json")
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        self.assertEqual(marker["reason"], "토큰 상한 도달")
        self.assertEqual(marker["tokens"]["input"], 140_000)
        self.assertIn("남은 시도 중단", out.getvalue())


class PromptRuleTests(unittest.TestCase):
    """Radar 원문 상한·저장소 정보 출처 표기·engineering 지어내기 금지가 프롬프트에 들어가는지."""

    def capture(self, fn, *args, enrich_result=None):
        with mock.patch.object(daily, "enrich_sources", return_value=enrich_result or []) as enrich, \
             mock.patch.object(daily, "_claude", return_value="본문\nTITLE: 제목") as claude:
            fn(*args)
        return enrich, claude.call_args.args[0]

    def radar_source(self) -> dict:
        return {"title": "a/b", "url": "https://github.com/a/b", "description": "desc", "language": "Java",
                "stars": 10, "created_at": "2026-10-01", "pushed_at": "2026-10-20", "stars_per_day": 1,
                "license": "MIT", "evidence": []}

    def test_radar_uses_short_readme_cap_and_metadata_rule(self) -> None:
        enrich, prompt = self.capture(daily.generate_draft_github_radar, [self.radar_source()],
                                      enrich_result=[self.radar_source()])
        self.assertEqual(enrich.call_args.kwargs["max_chars"], daily.RADAR_README_MAX_CHARS)
        self.assertLess(daily.RADAR_README_MAX_CHARS, daily.README_MAX_CHARS)
        self.assertIn("GitHub 저장소 정보 기준", prompt)

    def test_til_has_metadata_rule(self) -> None:
        source = {**self.radar_source(), "description": "A sufficiently descriptive project"}
        _, prompt = self.capture(daily.generate_draft_til, [source], enrich_result=[source])
        self.assertIn("'README에 따르면'으로 쓰지 마세요", prompt)

    def test_engineering_forbids_filling_gaps(self) -> None:
        commit = {"repo": "today-signal", "title": "fix", "body": "b" * 100, "files_changed": "a.py", "url": ""}
        with mock.patch.object(daily, "_claude", return_value="본문\nTITLE: 제목") as claude:
            daily.generate_draft_engineering([commit])
        prompt = claude.call_args.args[0]
        self.assertIn("코드 식별자(상태 이름·함수명)", prompt)
        self.assertIn("커밋에는 나와 있지 않다", prompt)


class ReviseStepTests(unittest.TestCase):
    """검수 실패 시 지적된 문장만 고쳐 쓰고 다시 검수하는 단계. 외부 호출은 가짜로 대신한다."""

    url = "https://example.com/a"
    PASS = {"팩트": True, "최신성": True, "공식출처": True, "중복충돌": True}
    QUALITY = {"검색의도": True, "반복제거": True, "제목/CTR": 90, "네이버SEO": 90,
               "모바일UX": 90, "차별성": 90, "생성형검색": 90}

    def setUp(self) -> None:
        self.usage_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.usage_dir.cleanup)
        for patcher in (mock.patch.object(daily, "_USAGE_DIR", Path(self.usage_dir.name)),
                        mock.patch.object(daily, "print", create=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def draft(self, body: str) -> dict:
        return {"title": "제목", "summary": "요약", "body": body + " " + self.url,
                "sources": [{"title": "a", "url": self.url}], "picked": None}

    def run_attempts(self, facts, revised_body="고친 본문"):
        revise = mock.Mock(return_value=self.draft(revised_body))
        with mock.patch.multiple(daily, generate_draft_news=lambda _s: self.draft("원래 본문"),
                                 fact_check_agent=mock.Mock(side_effect=facts), revise_draft=revise,
                                 quality_check_agent=lambda _d, _c: self.QUALITY, MAX_ATTEMPTS=1):
            result = daily._generate_valid_draft("news", [], [])
        return result, revise

    def test_unsupported_claims_are_revised_then_rechecked(self) -> None:
        problems = [{"claim": "원래 본문", "reason": "원문에 없음"}]
        failed = {**self.PASS, "팩트": False, "_reason": "원문 근거 감사 실패", "_problems": problems}
        result, revise = self.run_attempts([failed, self.PASS])
        self.assertEqual(revise.call_args.args[1], problems)
        self.assertIn("고친 본문", result["body"])

    def test_revised_draft_that_still_fails_is_not_published(self) -> None:
        failed = {**self.PASS, "팩트": False, "_reason": "지어낸 수치", "_problems": []}
        result, revise = self.run_attempts([failed, failed])
        self.assertIsNone(result)
        self.assertEqual(revise.call_args.args[1], [{"claim": "", "reason": "지어낸 수치"}])

    def test_topic_duplication_is_not_revised(self) -> None:
        duplicate = {**self.PASS, "중복충돌": False, "_reason": "최근 글과 주제 동일"}
        result, revise = self.run_attempts([duplicate])
        self.assertIsNone(result)
        revise.assert_not_called()

    def test_revise_prompt_lists_problems_and_forbids_new_facts(self) -> None:
        draft = self.draft("원래 본문")
        with mock.patch.object(daily, "_claude", return_value="고친 본문 " + self.url) as claude:
            revised = daily.revise_draft(draft, [{"claim": "원래 본문", "reason": "원문에 없음"}])
        prompt = claude.call_args.args[0]
        self.assertIn("지적: 원문에 없음", prompt)
        self.assertIn("새로운 사실·수치·이름·링크를 추가하지 마세요", prompt)
        self.assertEqual(revised["title"], "제목")  # TITLE 줄이 없으면 원래 제목 유지
        self.assertIn("고친 본문", revised["body"])


class FactCheckAuditTests(unittest.TestCase):
    """근거 감사 호출의 토큰 한도와 잘린 응답 처리. Claude 호출은 가짜 응답으로 대신한다."""

    CHECKLIST = "팩트: PASS\n최신성: PASS\n공식출처: PASS\n중복충돌: PASS\n사유: 없음"
    draft = {"title": "제목", "summary": "", "body": "본문", "sources": []}

    def run_fact_check(self, audit_text: str, audit_stop: str):
        calls = []

        def create(**kw):
            calls.append(kw)
            text, stop = (self.CHECKLIST, "end_turn") if len(calls) == 1 else (audit_text, audit_stop)
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text=text)],
                stop_reason=stop, usage=SimpleNamespace(output_tokens=kw["max_tokens"]),
            )

        out = io.StringIO()
        with mock.patch.object(daily._client.messages, "create", create), \
                contextlib.redirect_stdout(out):
            result = daily.fact_check_agent(self.draft, [])
        return result, calls, out.getvalue()

    def test_audit_has_room_for_measured_response_length(self) -> None:
        # 실측 감사 응답은 6.3~7.1k 출력 토큰이었다(2026-10-22). 4096이면 매번 잘린다.
        _, calls, _ = self.run_fact_check('{"all_claims_supported": false}', "end_turn")
        self.assertGreaterEqual(calls[1]["max_tokens"], 12000)

    def test_audit_scope_matches_checklist_background_rule(self) -> None:
        # 체크리스트가 허용하는 일반 배경 지식을 감사만 실패로 보면 til/news가 통과할 수 없다.
        _, calls, _ = self.run_fact_check('{"all_claims_supported": false}', "end_turn")
        audit_prompt = calls[1]["messages"][0]["content"]
        self.assertIn("판정에서 제외", audit_prompt)
        self.assertNotIn("근거 없는 배경 사실", audit_prompt)

    def test_truncated_audit_fails_closed_and_logs_why(self) -> None:
        result, _, log = self.run_fact_check('{"all_claims_supported": true, "claims": [{"cl', "max_tokens")
        self.assertFalse(result["근거검증"])
        self.assertFalse(result["팩트"])
        self.assertIn("max_tokens", log)
        self.assertIn("근거 감사 응답 처리 실패", log)


if __name__ == "__main__":
    unittest.main()
