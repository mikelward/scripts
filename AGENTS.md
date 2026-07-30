# AGENTS.md

Conventions for AI agents working in this repository.

`CLAUDE.md` is a symlink to this file, so every agent reads the same
conventions. Edit `AGENTS.md`.

This repo is a collection of shell utilities. There is no build step — each
script runs from source. Most are standalone, but not all: `sessionlib` is a
shared library sourced by the session entry points (`autosession`,
`makesession`, `autotmux`, `autoshpool`, and their siblings), and `setup`
dispatches to the per-platform `setup-kde` / `setup-macos` scripts. When you
change a shared contract, follow it through every consumer rather than
stopping at the file you opened.

## Style

- Preserve existing style unless there's a correctness issue. Match the
  script you're editing rather than the repo average.
- Keep comments brief. Explain the non-obvious *why*, not the *what*.
- Use `if test` rather than `if [`.
- When parsing options, support long flags in both `--option argument` and
  `--option=argument` forms.
- Consider portability. These run on Debian, Ubuntu, Fedora, and macOS under
  bash and zsh; note anything that isn't portable across them.

## Testing

- **Any change to executable behavior adds or updates a test.** New
  functionality gets a test that exercises its behavior; a bug fix gets a
  regression test that fails before the fix and passes after. Changes with no
  behavior to exercise — documentation, comments, this file — add no test;
  don't manufacture test churn to satisfy the rule. Run `make test` either
  way.
- Tests live next to the script as `<script>_test` and are listed in the
  `Makefile`. A new test file that isn't added to the `test` target never
  runs — add it there in the same commit.
- Run `make test` after any change, and before committing.
- **Fix any preexisting test failures as the *first* commit of the series.**
  Don't stack new work on a red baseline. If the failure is genuinely
  unrelated and out of scope, say so up front and confirm before skipping it.
- **Don't paper over flaky/racy tests** with `sleep`, retry loops, or bumped
  timeouts. Make the ordering explicit, or fix the underlying race. A test
  that passes "most of the time" is broken.
- **Don't disable a failing check** to make it pass — fix the underlying
  issue.

## Error handling

- **Don't silently swallow errors.** A bare `2>/dev/null`, an unchecked exit
  status, or a `|| true` hides real failures. Report what failed, clean up what
  the failed step created, and decide explicitly what the caller sees. To
  ignore a specific failure, say why in a one-line comment (`# not every host
  has shpool`).

## Privacy

- **Never put user data in any artifact that leaves this machine** — commit
  subjects and bodies, PR titles / descriptions / comments, review replies,
  branch names, code comments, or test fixtures. For this repo that means
  hostnames and internal domain names, absolute paths containing the user's
  real name, work machine names, SSH host aliases and keys, tokens or API
  keys, private remote URLs, and shell history excerpts. Use generic
  placeholders (`/home/user`, `host1`, `git@example.com:org/repo.git`) in
  examples and fixtures. If a bug report contains any of it, paraphrase in
  the commit / PR — don't quote verbatim. When in doubt, ask before pushing.
- **Script output is not one of those artifacts.** It prints on the user's own
  terminal, and naming hosts, paths and remotes is usually the point of the
  message. Redact only secrets: tokens, keys, and passwords embedded in URLs.
  Quoting that output into a commit, PR, or fixture republishes it, and the
  bullet above governs again — paraphrase or use a placeholder there.

## Language and spelling

- Use **US English** everywhere people read English: script output and help
  text, commit subjects and bodies, PR titles and descriptions, comments, and
  identifiers — `color` not `colour`, `behavior` not `behaviour`, `canceled`
  not `cancelled`, `gray` not `grey`. Third-party API spellings stay as those
  APIs spell them.

## Git

- Use `git worktree` when it's available. Give each branch its own worktree
  instead of switching branches in place, so work in progress on one branch
  isn't disturbed by work on another.
- **These rules assume an `origin` remote.** Without one you can't fetch,
  branch from `origin/main`, push, or open a PR — say so and stop rather than
  improvising a local substitute. **Exception:** in a sandbox that
  intentionally provides no remote Git support (Codex cloud, say), follow the
  normal branch rules from the current `HEAD` — a pre-created working branch
  counts — commit locally, and report that fetch, push, and pull requests are
  unavailable, using the sandbox's own PR handoff if it has one. That exception
  outranks every `origin`-dependent step below it — the merge-cue fetch, cutting
  a branch off `origin/main`, the closing PR link — so work from the current
  `HEAD` and name what wasn't possible instead of faking it. One limit: a merge
  cue needs a base that *contains* the merge, and an offline sandbox can't fetch
  one. Say the follow-up needs a fresh sandbox or a synced checkout rather than
  branching off a `HEAD` whose commits just landed upstream.
- **Branch naming.** Feature branches are prefixed with the agent's own short
  name: `<agent>/<short-topic>` (`claude/...` for Claude Code, `codex/...`
  for Codex, and so on). The placeholder `<agent>` stands in for whichever
  prefix you use — don't hard-code `claude/` unless you *are* Claude Code.
- **Workflow.** `<agent>/<short-topic>` branch off `origin/main` → PR → merge.
  One topic per branch. Follow-up work after a merge goes on a new branch.
  Never commit to `main`.
- **One commit per logical change.** Rewrite unmerged commits freely — amend,
  `git commit --fixup` + autosquash, squash, reorder, split — so each commit
  that lands is one coherent change, with fix-ups and review responses folded
  into the commit they belong to. `wip` / `address review` churn doesn't
  survive into `main`.
- `git push --force-with-lease` to your own live feature branch after a rebase
  is routine hygiene — don't ask. Never a bare `--force`.
- **Merge cue (`merged` / `I merged` / `landed` / merge webhook) runs hygiene
  *before* engaging with the rest of the message:** `git fetch origin`, cut a
  fresh `<agent>/<short-topic>` branch off `origin/main`, announce the switch.
- **After a merge, take a fresh `<agent>/<short-topic>`** — don't reset the
  merged name onto the new base. Its remote ref still points at the pre-merge
  tip, so `origin/<branch>..HEAD` keeps spanning the merged commits and
  unpushed-work checks report your own merged history back at you. When a
  sandbox pins the branch name, reset it and `--force-with-lease` in the same
  turn — that's routine on merged history, not something to ask about.
- **The agent authors and the repo owner merges**, so a squash or rebase merge
  rewrites the committer to them. That's expected — never re-author or amend
  already-merged commits to "fix" authorship or signing.
- **Unshallow before answering anything that depends on git history depth.**
  The sandbox clones shallow, so `git rev-list --count`, `git log` past the
  shallow boundary, and blame return wrong answers without warning. If
  `git rev-parse --is-shallow-repository` says `true`, run
  `git fetch --unshallow` first, then re-check — it exits 0 even when it
  deepened nothing, so if `--is-shallow-repository` is still `true`, say the
  history is truncated instead of quoting a count.

## Talking to the user

- **One question at a time.** Never stack multiple questions in a single turn
  — ask the most important one, wait for the answer, then ask the next if you
  still need it. A wall of bundled questions is harder to answer than a short
  back-and-forth.
- **Don't interrupt.** Never fire off a question while the user is still
  typing. Let them finish; a half-typed message isn't an invitation to jump in.
- **Keep replies short — don't dump a full page.** Lead with the single most
  important point and stop. If there's more, say the first point and ask
  whether they're ready for the next one rather than emptying everything at
  once.

## Asking questions

- **Ask in chat, never with `AskUserQuestion`.** That's Claude Code's
  multiple-choice question prompt, and it's broken in the Claude mobile app —
  a question asked through it may be unanswerable. Plain chat also keeps the
  question, its context, and the answer in one readable thread.
- **After asking, stop and wait for the answer.** Don't proceed on an assumed
  answer, pick a "recommended" option yourself, or keep working on the part
  the question affects.

## Pull requests

- Prefer the `mcp__github__*` MCP tools for GitHub operations; the `gh` CLI is
  not installed in the sandbox. If your client exposes neither, say so rather
  than guessing at the outcome of an operation you couldn't perform.
- Open PRs ready for review (not draft) unless asked otherwise.
- **On every push, update the PR title and body** so they describe the full,
  latest state of the branch — not the scope it had when it was opened.
  Re-read the diff against `origin/main` and patch whatever drifted, then post
  the PR link in the chat reply for that push, not only at the end of the
  conversation.
- **"Drive to merge"** is shorthand for the whole loop: open the PR, wait for
  the automatic Codex review, address every review comment — fix it if you
  agree, reply on the thread saying why if you don't — and merge once CI is
  green and Codex has left its thumbs up.
- When a feature has multiple open PRs, list **every** open PR by URL, one per
  line — the "View PR" chip sticks to the first link and hides the rest
  (anthropics/claude-code#46625).
- End every reply with the open-PR link (or `.../compare/main...<branch>`
  until a PR exists). Never link to a closed or merged PR — except when the
  reply *is* post-merge follow-up on that PR, where linking it is correct. In an
  offline sandbox with no `origin` there's no URL to end with — say that, rather
  than inventing a link that resolves to nothing.

## Reviews

- **Codex is the automated reviewer on this repo** — not Copilot. Its reviews
  are triggered automatically; you don't request them.
- **Address Codex comments automatically — don't wait to be asked.** Read
  each one, decide whether it's a real issue or a false positive, and if it's
  real, fix it in the same PR. Fold the fix into the commit it belongs to
  (rebase / `--fixup`) rather than tacking on an "address review" commit.
  Group several small fixes into one commit when they share a topic.
- **Judge every review comment on merit, whoever wrote it.** Verify the claim
  before acting; if it doesn't hold up, reply saying why and decline.
- **Never leave a review comment thread silently dismissed.** Either reply on
  the thread *or* resolve it. When you think a comment is a false positive,
  say *why* on the thread (one or two sentences). Acknowledgement noise is
  fine and preferred over silence.
- **`resolve_review_thread` works — pass the `PRRT_*` thread node ID** from
  `pull_request_read` / `get_review_comments` (`review_threads[].id`) as
  `threadId`. A comment's `PRRC_*` node ID fails; they're different objects.
  Order of operations: push the fix commit first, then reply citing the new
  sha, then resolve.
- **Report when Codex finishes reviewing a fresh push** — a one-liner naming
  the SHA and comment count, e.g. `Codex reviewed 87d9f02 — 0 comments`. Tie
  it to the *latest* pushed SHA so a stale review of a superseded commit isn't
  conflated with the current state.
- **Skip echo events silently.** Replies posted via the GitHub MCP come back
  moments later as webhook events authored by the same identity; if the body
  matches a comment you just posted, it's your own echo — continue without
  comment. The test is "did *I* just post this body?", not "who is the
  author?".
- **Keep watching merged PRs for late review comments.** Reviewers and bots
  routinely comment after merge. Stay subscribed and handle each new comment
  per the reply-or-resolve rule; stop once every post-merge comment is handled
  or after ~24h of silence.

## Cost and reliability

- **Call out cost and reliability up front** when recommending a new external
  dependency (a tool the scripts would shell out to, a network call, a
  third-party service). Include a rough dollar figure — free-tier vs. paid
  thresholds and $/month at expected use — and note reliability implications:
  new failure modes, rate limits, added latency, and what the user sees if the
  dependency is missing or down. These scripts run interactively in a shell
  session, so a network call on a hot path is a visible hang. If the impact is
  effectively zero, say so rather than omitting the note.
