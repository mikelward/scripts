# AGENTS.md

Conventions for AI agents working in this repository.

`CLAUDE.md` is a symlink to this file, so every agent reads the same
conventions. Edit `AGENTS.md`.

## Git

- Use `git worktree` when it's available. Give each branch its own worktree
  instead of switching branches in place, so work in progress on one branch
  isn't disturbed by work on another.
- **One commit per logical change.** Rewrite unmerged commits freely — amend,
  `git commit --fixup` + autosquash, squash, reorder, split — so each commit
  that lands is one coherent change, with fix-ups and review responses folded
  into the commit they belong to. `wip` / `address review` churn doesn't
  survive into `main`.
- `git push --force-with-lease` to your own live feature branch after a rebase
  is routine hygiene — don't ask. Never a bare `--force`.

## Pull requests

- **On every push, update the PR title and body** so they describe the full,
  latest state of the branch — not the scope it had when it was opened.
  Re-read the diff against `origin/main` and patch whatever drifted, then post
  the PR link in the chat reply for that push, not only at the end of the
  conversation.
- End every reply with the open-PR link (or `.../compare/main...<branch>`
  until a PR exists). Never link to a closed or merged PR.
