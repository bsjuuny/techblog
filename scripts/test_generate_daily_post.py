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

    def test_truncated_audit_fails_closed_and_logs_why(self) -> None:
        result, _, log = self.run_fact_check('{"all_claims_supported": true, "claims": [{"cl', "max_tokens")
        self.assertFalse(result["근거검증"])
        self.assertFalse(result["팩트"])
        self.assertIn("max_tokens", log)
        self.assertIn("근거 감사 응답 처리 실패: JSONDecodeError", log)


if __name__ == "__main__":
    unittest.main()
