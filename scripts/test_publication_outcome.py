import datetime as dt
import unittest
from unittest import mock

import os
os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key-import-only')
from scripts import generate_daily_post as daily


class PublicationOutcomeTest(unittest.TestCase):
    def run_mocked(self, draft=None, push_error=None, source_error=None):
        with mock.patch.multiple(
            daily, pick_content_type=mock.DEFAULT, get_recent_titles=mock.DEFAULT,
            fetch_hackernews_top=mock.DEFAULT, _generate_valid_draft=mock.DEFAULT,
            write_post=mock.DEFAULT, commit_and_push=mock.DEFAULT,
            write_watchdog_status_marker=mock.DEFAULT, over_token_budget=mock.DEFAULT,
        ) as m, mock.patch('builtins.print'):
            m['pick_content_type'].return_value = 'news'
            m['fetch_hackernews_top'].side_effect = source_error
            m['_generate_valid_draft'].return_value = draft
            m['commit_and_push'].side_effect = push_error
            m['over_token_budget'].return_value = False
            outcome = daily.run(dt.date(2026, 11, 26))
            return outcome, m

    def test_published_only_after_successful_git_push(self):
        outcome, m = self.run_mocked(draft={'mock': 'article'})
        self.assertEqual(outcome, 'published')
        m['commit_and_push'].assert_called_once()
        self.assertIs(m['write_watchdog_status_marker'].call_args.args[0], True)

    def test_validation_skip_does_not_publish(self):
        outcome, m = self.run_mocked()
        self.assertEqual(outcome, 'skipped')
        m['commit_and_push'].assert_not_called()

    def test_source_unavailable_preserves_normal_skip_policy(self):
        outcome, m = self.run_mocked(source_error=RuntimeError('mock unavailable'))
        self.assertEqual(outcome, 'skipped')
        m['commit_and_push'].assert_not_called()

    def test_git_error_is_not_reported_as_skip_or_published(self):
        outcome, m = self.run_mocked(draft={'mock': 'article'}, push_error=RuntimeError('mock push failed'))
        self.assertEqual(outcome, 'failed')
        self.assertEqual(m['write_watchdog_status_marker'].call_args.kwargs['outcome'], 'failed')
