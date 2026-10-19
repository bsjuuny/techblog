# 2026-10-18 engineering attribution incident

## Verified repository evidence

- PR #1 merged at 2026-10-17 10:43:23 KST as `80db475fd7b780e6f74fdb906c1ec91976c69bd1`.
- The article commit `cfba1a674c54b49e0df67aa8f8be2249b589a9ff` was created at
  2026-10-18 01:30:57 KST, directly on that merge. It nevertheless lists six candidates
  while its body cites only `3185fdeb`.
- `write_post` on master already filters every content type using `used_sources`.
- The old entry point imports the generator, generates and writes the article, and only
  then calls `git pull --ff-only` inside `commit_and_push`. Updating disk at this point
  cannot replace the Python functions already loaded in memory. This provides a
  reproducible stale-code path consistent with the observed parent commit and footer.
- Engineering generation supplied only the chosen commit to the author. Its candidate
  list already contained `c6731826`, the follow-up timestamp migration, but that evidence
  was not part of the generation prompt.
- The repository has no checked-in Actions generation workflow. The inspected Actions
  runs are Pages build/deployment. Source code refers to Windows `C:/github` and
  `C:/github/scheduler/status`; these are runtime clues, not a live host inspection.

## Limits of attribution

The scheduler repository/API was not accessible (404). No Windows checkout, PM2
configuration, October 18 process log or status marker was available. Thus the exact
executed SHA and scheduler command are **not established**. Stale in-memory code is a
supported explanation and a fixed design defect, not a falsely claimed host-level proof.
Pages deployment success does not establish which generator code produced a post.

## Correction and prevention

The article now cites the initial fix, subsequent migration and pinned pipeline document.
It attributes the documented 27,764-row correction to repository records and does not
claim a direct production database check. No database mutation is performed.

The existing direct Python entry point now synchronizes the origin default branch before
third-party/generator imports, requires a clean checkout, fast-forwards only, runs the
offline regression suite, and starts a fresh interpreter. It refuses non-default branches,
local-only commits, concurrent runs and code changes during generation. Publication
fetches again and stops if origin moved instead of pulling beneath a loaded generator.
The post comment and watchdog marker retain the executed SHA and Python-file SHA-256s.
Engineering generation includes same-repository follow-ups and fetches current touched
Markdown documents at a pinned remote HEAD; reviewers retain this context even when
the footer omits uncited candidates. Context and excerpts are bounded; model semantic
review remains fallible.

## Production rollout / acceptance (not yet executed on Windows)

1. In the actual scheduler checkout, inspect local changes and the configured command.
   Confirm it runs `C:/github/techblog/scripts/generate_daily_post.py` and uses master.
2. With a clean checkout, run `git pull --ff-only` once to install the bootstrap. Old
   code cannot bootstrap an update it has not received; do not rely on one more old run.
3. Using the scheduler's Python/environment, run
   `python scripts/generate_daily_post.py --check-runtime`.
   This synchronizes and runs tests without Claude generation or publication.
4. Compare the printed runtime SHA with origin/master and retain that output. If a
   stale lock exists, first confirm its owner process is dead; do not delete active locks.
5. On the next authorized scheduled run, compare the watchdog `runtime` object with
   the generated post's `generator-runtime` comment. Verify the Pages build for the
   resulting publication commit. A no-post quality rejection is not a deployment proof.

Do not mark host deployment complete until steps 1–5 have corresponding host evidence.
