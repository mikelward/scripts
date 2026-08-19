# TODO

## Review and merge gates

- [ ] Require the `lanes` check in the ruleset, not `test` — `test` now
      skips on a docs-only diff (see `.github/lanes.conf`), and a skipped
      required check counts as satisfied, so requiring `test` directly
      would let a docs-only PR through with no check actually enforcing
      the allowed prefixes or independently re-deriving the skip. `lanes`
      is the one that always runs and always reports.
- [ ] Verify the settings half of the fleet's bar — every repository
      works the same: comprehensive automated review, required merge
      gates, and auto-merge. A ruleset on the default branch requiring
      the gates, the `codex` status, conversation resolution and
      up-to-date branches, with the auto-merge setting enabled.
