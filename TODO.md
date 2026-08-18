# TODO

## Review and merge gates

- [ ] Require the existing `test` check in the ruleset —
      `.github/workflows/test.yml` already runs `make test` on every pull
      request and push to main, so the gate exists and only the
      requirement is missing.
- [ ] Verify the settings half of the fleet's bar — every repository
      works the same: comprehensive automated review, required merge
      gates, and auto-merge. A ruleset on the default branch requiring
      the gates, the `codex` status, conversation resolution and
      up-to-date branches, with the auto-merge setting enabled.
