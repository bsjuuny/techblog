from __future__ import annotations

import datetime as dt
import os
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-for-import-only")

from scripts import generate_daily_post as daily  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
