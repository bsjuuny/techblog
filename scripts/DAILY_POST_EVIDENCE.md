# Daily post evidence and attribution

Search results are candidates, not citations. TIL researches only its selected
repository; Radar researches its ranked selection; news fetches candidate originals
before selecting stories. Only URLs cited in the body appear in the generated footer,
with duplicates removed. Code examples and HTML comments do not count as citations.
Each covered item must link to its provided source in its own section.

Repository research resolves HEAD to a commit and reads the README at that commit,
including its actual path. The evidence URL stays pinned even if the default branch
changes later. News research retrieves bounded original-page text, excluding scripts,
styles and navigation. It does not crawl links or execute page content. Both generation
and review receive the same fetched evidence and retrieval timestamp; fetch errors are
explicit and never substituted with invented document text.

Review first applies the existing checklist. A passing checklist then triggers a
separate claim audit of title, summary and body, including false claims that a known
specification is unavailable. Every factual claim must be supported; the audit returns
literal source excerpts. Code checks the response schema, source provenance, exact
quote existence and that each claimed passage exists in the draft. Unsupported claims,
invented quotes, missing originals and malformed audit output block publication and
use the existing retry/skip behavior. Unused subjects are removed before review.
Actual local git records remain evidence for engineering posts.

README claims are attributed to the project, not represented as independent tests.
API metadata can support repository statistics, not model sizes or platform support.
Text beyond the 40,000-character research limit is unavailable evidence, not proof that
a feature does not exist. Fetch failures and inaccessible articles can reduce publishing
frequency; this is intentional rather than falling back to unverified specifications.

The model still judges semantic entailment and coverage: an exact quote is a necessary
provenance check, not a mathematical guarantee that the claim follows. This adds one
Claude call after a passing fact checklist, plus original-document requests. An actual
scheduled run with production credentials should be monitored for cost and rejection
rate. Offline regressions mock external calls and never invoke commit/push.

Validation:

```sh
python -m unittest discover -s scripts -p 'test_*.py' -v
python -m compileall -q scripts
git diff --check
```

The 2026-10-17 DigUp correction was checked against README commit
`ec28973268b81f836be72187ff23b3a16ef4fd97` (dated 2026-10-14) and Google's
EmbeddingGemma 2 model card. It removes seven unrelated candidates and corrects
model parameters, language coverage, beta platforms, network behavior and UI architecture.
