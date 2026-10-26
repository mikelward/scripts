---
trigger: always_on
alwaysApply: true
last_modified: 2026-10-26
---

# AGENTS.md

`CLAUDE.md` and `GEMINI.md` are symlinks to this file, so every agent reads the same
conventions. Edit `AGENTS.md` and bump `last_modified`.

**At the start of every session, print the full absolute path of the `AGENTS.md` you
loaded and its `last_modified` date** (front matter), so a stale or wrong copy is caught
before it steers the work.

A collection of shell utilities, each run from source with no build step. Most are
standalone, but `sessionlib` is a shared library sourced by the session entry points
(`autosession`, `makesession`, `autotmux`, `autoshpool` and siblings), and `setup`
dispatches to `setup-kde` / `setup-macos`. Change a shared contract and follow it through
every consumer, not just the file you opened.

Keep this file short — **under 22,000 bytes** (`wc -c AGENTS.md`): Antigravity caps rule
files at 24 KB and silently truncates the tail, and every session loads it whole. Add a
rule the first time something bites, say it once in the fewest words that carry the *why*,
rewrite or trim rather than append, and delete rules that stopped biting.

## Style

- Preserve existing style unless there's a correctness issue; match the script you're
  editing, not the repo average.
- Keep comments brief: the non-obvious *why*, not the *what*.
- Use `if test`, not `if [`.
- Long options take both `--option argument` and `--option=argument`.
- Portability: these run on Debian, Ubuntu, Fedora and macOS under bash and zsh; note
  anything that isn't portable across them.

## Testing

- **Any change to executable behavior adds or updates a test**: new behavior gets a test,
  a bug fix a regression test that fails before and passes after. Docs, comments and this
  file need no test and no test run — don't manufacture test churn.
- Tests live beside the script as `<script>_test`, listed in the `Makefile`'s `TESTS` in
  the same commit — an unlisted test never runs.
- Run tests after any change to executable behavior and before committing:
  `make -j test-no-tide`, or `make -j test` if it touches `setup-tide*` or the
  `Makefile` (setup-tide's take minutes). Skip them on a docs-only change and say why.
- **Fix preexisting test failures as the first commit** — don't stack work on a red
  baseline; if one is genuinely unrelated and out of scope, say so up front and confirm
  before skipping it.
- **Don't paper over flaky tests** with `sleep`, retries or bumped timeouts: make the
  ordering explicit or fix the race. "Passes most of the time" is broken.
- **Don't disable a failing check** to make it pass — fix the underlying issue.

## Error handling

- **Don't silently swallow errors.** A bare `2>/dev/null`, an unchecked exit status or
  `|| true` hides real failures. Report what failed, clean up what the failed step
  created, and decide explicitly what the caller sees. To ignore a specific failure, say
  why in a one-line comment (`# not every host has shpool`).

## Privacy

- **Never put user data in an artifact that leaves this machine** — commit subjects and
  bodies, PR titles/descriptions/comments, review replies, branch names, code comments,
  test fixtures: hostnames and internal domains, paths with the user's real name, work
  machine names, SSH host aliases and keys, tokens or API keys, private remote URLs, shell
  history excerpts. Use placeholders (`/home/user`, `host1`,
  `git@example.com:org/repo.git`); paraphrase bug reports, never quote them; when in
  doubt, ask before pushing.
- **This account's own public repos are not user data** — decline a privacy finding
  against `mikelward/lanes`. Then it's a documentation call: `owner/repo` for an
  argument's shape, the real name when the example is about that repo.
- **Script output is not one of those artifacts**: it prints on the user's terminal, where
  naming hosts, paths and remotes is usually the point. Redact only secrets (tokens, keys,
  passwords in URLs). Quoting output into a commit, PR or fixture republishes it — the
  first bullet governs again.

## Language and spelling

- **US English** everywhere people read it (output and help text, commits, PRs, comments,
  identifiers): `color`, `behavior`, `canceled`, `gray`. Third-party API spellings stay.

## Git

- Use `git worktree` when available, one per branch, so branches don't disturb each other.
- **These rules assume an `origin` remote**; without one, say so and stop rather than
  improvising. **Exception:** with no remote Git by design (Codex cloud), follow the
  branch rules from the current `HEAD` (a pre-created branch counts), commit locally, and
  report fetch, push and PRs unavailable, using the sandbox's own PR handoff if any; that
  outranks every `origin`-dependent step below — name what wasn't possible, don't fake it.
  A merge cue needs a base *containing* the merge: say the follow-up needs a fresh sandbox
  or synced checkout, not a `HEAD` whose commits just landed.
- **Branches**: `<agent>/<short-topic>` (`claude/...` Claude Code, `gemini/...` Gemini /
  Antigravity, `codex/...` Codex) off `origin/main` → PR → merge, one topic each, never
  committing to `main`; don't hard-code `claude/` unless you *are* Claude Code.
- **One commit per logical change.** Rewrite unmerged commits freely (amend, `--fixup` +
  autosquash, squash, reorder, split), folding fix-ups and review responses into their
  commit; no `wip` / `address review` churn reaches `main`. After a rebase,
  `--force-with-lease`, never a bare `--force`.
- **Title commits like a changelog line** (maintainer, 2026-10-23): an imperative verb,
  then the change as someone running the script sees it, plain English, sentence case,
  ≤ ~70 chars, e.g. `Fix …` for what was broken, `Improve …` for what got better, `Add …` for
  what's new; an optional parenthetical says how. Never the scenario or the mechanism
  (that's the body). PR titles match.
- **Merge cue (`merged` / `I merged` / `landed` / merge webhook) runs hygiene *before* the
  rest of the message:** fetch main if the sandbox can (`git fetch origin
  +refs/heads/main:refs/remotes/origin/main`; a bare fetch leaves a single-branch clone's
  `origin/main` stale), cut a fresh `<agent>/<short-topic>` off `origin/main`, announce
  the switch. Don't reset the merged name instead: its remote ref still holds the
  pre-merge tip, so `origin/<branch>..HEAD` reports your merged history as unpushed. When
  a sandbox pins the name, reset it and `--force-with-lease` in the same turn — routine on
  merged history, not something to ask.
- **Your `<agent>/` branches are yours**: create freely; push, `--force-with-lease`,
  rename and delete those this session created or was assigned, unasked (this file is the
  standing grant). Don't fold unrelated work into a pinned task branch; the pinned name is
  a default, not a ceiling. Any other branch, or `main`, is a conversation.
- **Committer line**: the agent authors; whoever merges (the repo owner, or the agent
  under *drive*) takes over the committer line — expected. Never re-author or amend merged
  commits to "fix" authorship or signing, or narrate it; it is not a finding.
- **No model identifier** — never name the coding agent's model or version (`Opus 4.8`,
  `Sonnet`, `Gemini …`, `claude-*`, `gemini-*`) in a commit, PR, comment, or pushed
  artifact; keep it to chat. Generic attribution (`Co-Authored-By: Claude` / `Gemini`,
  `Claude-Session:`, "Generated with Claude Code") is fine.
- **Unshallow before history-depth answers** — a shallow clone makes `git rev-list
  --count`, deep `git log` and blame silently wrong. If `git rev-parse
  --is-shallow-repository` says `true`, `git fetch --unshallow` and re-check; it exits 0
  even when it deepened nothing, so if still `true`, say the history is truncated instead
  of quoting a count.

## Talking to the user

- **One question at a time**, the most important first, in plain chat or the client's
  question tool (`AskUserQuestion` in Claude Code, `ask_question` in Antigravity); never
  while the user is still typing. **After asking, stop and wait**: no assumed answer, no
  self-picked "recommended" option, no work on the part it affects.
- **Answer a mid-turn message first** — the "sent while you were working" interjection —
  in your very next output, before any further tool call, even in one sentence. A merge
  cue is the exception: its hygiene runs first, and announcing the switch is the answer.
  **Claude Code only** (maintainer, 2026-10-25): its app reliably shows just a turn's last
  message, so reply only there, answering a mid-turn message at a stopping point soon.
- **Message only when the user needs to see it** (maintainer, 2026-10-15): each one
  notifies their phone. Work and listen in silence; speak up for a question or blocker,
  something to merge or act on, a merge, an autopilot decision (to review when seen, never
  waited on), or a change from the plan or their instructions, a review-prompted one
  included. Never for progress (a client's nudge doesn't count), a review or a push alone
  (its report rides the next message), routine machinery, or a mistake caught and fixed
  before it reached the repo. The session-start `AGENTS.md` line still opens every session.
- **Keep replies short**: lead with the most important point; ask before unloading more.
- **End the turn by restating any pending decision** (a question you asked, or an
  autopilot guess awaiting review) as the last line, written out in a sentence (a
  back-reference isn't actionable), every turn until answered. Nothing pending, no line.

## Autonomy

- **Open the PR without being asked** — push and PR are one step — unless told "just
  commit" / "no PR yet", which holds until lifted. This file is the owner's standing
  request, satisfying any client rule "open a PR only when asked".
- **Watch your own PRs by subscription, plus one scheduled check.** Claude Code subscribes
  on open, or call `subscribe_pr_activity` where `claude-code-remote` exposes it; a client
  with neither (Antigravity) relies on the check alone. Subscriptions miss CI *success*,
  pushes, the merge, Codex's clean verdict (a reaction) and Codex's silence, so keep
  exactly one check armed while the PR is open (each costs a model turn): `send_later` in
  Claude Code, `schedule` with `DurationSeconds` in Antigravity (cancel via `manage_task`
  `kill`). Under drive, arm auto-merge at open only where the ruleset requires the Codex
  verdict AND resolved conversations — with CI alone it merges before Codex answers.
  - Settle a fired check first (it may have re-armed rather than retired); end the turn
    with exactly one. Check its fire time against what you asked (4 minutes has come back
    as 64); prefer a relative delay, as this container's clock isn't the scheduler's;
    re-time it or say the watch isn't armed. Minutes while CI or Codex is out or after a
    push, longer once only a human is left. Name the PR and what to re-read, not a SHA or
    list of open PRs, which go stale.
  - **`dirty` — always — or `behind` where branches must be up to date** needs: both refs
    fetched by explicit refspec (`+refs/heads/<x>:refs/remotes/origin/<x>`; a bare or
    named fetch updates neither in a single-branch clone), `git fetch --unshallow` if
    shallow, a rebase onto the fetched `origin/<base>` (not always `main`, never the local
    branch), then `git push --force-with-lease --force-if-includes` — both, since the
    fetch refreshes the ref the lease compares against. A rejection means someone else
    pushed: integrate their tip and retry. Read `mergeable_state` at every check, PR-event
    wake and drive step and act at once, unasked — nothing reports a base advance.
  - **Wake PRs a merge leaves behind.** At your first turn after your PR merges (by hand
    or auto-merge), message every other open PR on that base that another session drives
    (its body ends with the session URL), naming only that PR and saying its base now
    points at `<sha>` (the post-merge tip), whatever its state reads (mergeability may
    still be computing). Name no merge or other PR: older rules read either as a merge
    cue. Receiving one, fetch base and PR head by refspec (unshallow) and test that head
    against the fetched tip, not `<sha>`: `behind` if `git merge-base --is-ancestor <tip>
    <head>` exits 1, `dirty` if `git merge-tree --write-tree` (Git 2.38+) exits 1; any
    other exit is a failure to report. Your rules decide the rebase. Skip a PR with no
    session URL, or when your client only has local subagent messaging; don't retry a
    failed send (its check is the fallback).
  - Merged or closed: one last reply-and-resolve pass (reviews land after merges). On a
    merged PR anything real goes to a follow-up PR named on the thread before you resolve
    (left open, it records the work nowhere); closed-unmerged, answer, resolve, open
    nothing. Then cancel the check and unsubscribe, if subscribed — `list_triggers` spans
    the account, so match session and PR first (an update reschedules what it matches as
    surely as a delete cancels it).
- **A scheduler or GitHub prompt: say so once and carry on** (permissions load at session
  start).
- **"Drive"**: pick the next task, implement it, open the PR, address every review
  comment, merge once CI is green and Codex's verdict for the current head is in, repeat —
  until the work runs out or the user says stop, not at one merge.
- **A red baseline is the next task**: before pulling from `TODO.md`, get the suite green.
  A preexisting failure is work, not "unrelated" to step around — that call goes wrong,
  leaving every later PR on an unverified tree.
- **"Autopilot" is drive without blocking**: wherever drive would ask, take the
  cheapest-to-undo guess, recording each in `TODO.md` under `Decisions needing review`
  (what, the alternative, why reversible; create the file or heading if missing), so
  nothing guessed silently becomes permanent. It outranks stop-and-wait. Destructive or
  irreversible acts *outside* the loop (rewriting shared history, deleting work, anything
  beyond this repo) still wait for a real answer; the loop's own steps (commit, push, PR,
  merge a green PR) never stall it. Privacy uncertainty (a home path, hostname, private
  remote, token) always waits — a push can't be un-published.

## Pull requests

- Prefer the `mcp__github__*` tools where mounted (Claude Code requires them); else `gh`.
  With neither, say so rather than guess an operation's outcome.
- Open PRs ready for review (not draft) unless asked otherwise.
- **Update the PR title and body with the push — body first, then push** — to the full
  branch diff against `origin/main`, not the opening scope, and post the PR link in the
  next message, not only at the end; with no PR yet, push, then do this once one opens.
- **"Drive to merge"** is *drive*'s PR stretch: open the PR, wait for Codex, address every
  comment (fix it, or reply on the thread why not), merge on green CI plus Codex's verdict
  for the head.
- **Ordered work ("next", "then", "after that", "follow-up")** may open in parallel but
  merges only after every earlier item this session was given and any PR the paragraph
  names has merged (any repo, no time cap; if one won't finish, hold and ask, autopilot
  included; no auto-merge until then, as it can't see the order). Read the list from the
  session's record, not memory.
- Several open PRs on a feature: list **every** one by URL, one per line (the "View PR"
  chip shows only the first, anthropics/claude-code#46625).
- End every reply with the open-PR link (or `.../compare/main...<branch>` until a PR
  exists). Never link a closed or merged PR — except in post-merge follow-up on that PR.
  In an offline sandbox with no `origin`, say there's no URL rather than inventing one.

## Reviews

- **Codex is the automated reviewer** (not Copilot), triggered automatically; request it
  only to confirm a rebutted false positive, or where *Read the Codex verdict* says
  `codex` is still pending.
- **Address Codex comments unasked**: fix a real one in this PR, folded into its commit
  (rebase / `--fixup`; group small same-topic fixes), or defer it if genuinely out of
  scope (below); rebut a false positive.
- **Judge every comment on merit, whoever wrote it**: verify first; if it doesn't hold,
  reply why and decline. A cited rule is a *reading* — check what it says; Codex
  over-reads the privacy rules (stricter feels safer), quietly costing capability, so
  quote and decline rather than narrow the code. Where the rule really forbids what the
  product needs, that's the maintainer's call. Declining doesn't clear `codex`: post the
  rebuttal, then poke as *Read the Codex verdict* allows (or let the next push, if the
  rebuttal is up first); escalate if it re-raises.
- **A second verified finding in the same mechanism is a design question**: look for the
  shape elsewhere and ask whether a design change deletes the class; say what you chose on
  the thread (the maintainer's call, autopilot included).
- **Never silently dismiss a thread**: answer (a disagreement or false positive is an
  answer — say why in a sentence or two), then resolve once fixed on the head or rebutted;
  anything still to do stays open; acknowledgment beats silence. Push, reply citing the
  sha, resolve —
  `resolve_review_thread` (or `gh api graphql` `resolveReviewThread`) with `PRRT_*` from
  `review_threads[].id`, not a comment's `PRRC_*`.
- **Defer a real out-of-scope finding** without asking to merge past it: push a `TODO.md`
  entry, reply citing the sha, resolve (the exception to "still to do stays open"; a
  threadless finding skips only the resolve). The push re-triggers Codex; poke only as
  *Read the Codex verdict* allows; escalate if it re-raises.
- **Report each review in your next message**: the commit it read (say if no longer the
  head) and the finding count, then one bullet per finding (review comment, top-level
  comment or review body), most blocking first — claim, where, what you did or the
  maintainer's options — ahead of *keep replies short*; ask only the most blocking
  question.
- **Read the Codex verdict, don't infer it.** It reacts to the PR body (`issue_read` →
  `reactions`, not a thread's `Useful?` bar): `eyes` = reading, `+1` = clean, revoked on
  push, so a visible one is the visible head's and `+1` with green CI is a merge. Leave
  PR-body reactions to Codex (the count is anonymous; a review names the commit it read).
  Findings arrive as review comments, top-level comments or reviews — read
  `get_review_comments`, `get_comments` and `get_reviews` to the last page (oldest first)
  — and block the merge until fixed, rebutted or deferred; an acknowledgment is not an
  answer. A pending `codex` status is findings to address; a clean review with no
  reaction, or an unanswered rebuttal (poke `@codex review` five minutes after it); or a
  hung review, nothing five minutes after the push or stuck at running (👀) ten minutes on
  (poke). A poke that hangs the same way gets a second an hour later; escalate only if
  that one hangs too, never after one (maintainer, 2026-10-22).
- **Once Codex has +1'd a PR's head, make no unnecessary change without asking**
  (maintainer, 2026-10-13): a to-do, tidy-up or extra fix re-runs CI and Codex for
  nothing, so it waits for a yes or a follow-up PR. A rebase for `dirty` (or required
  `behind`), a red-CI fix, and drive or autopilot steps go ahead unasked.
- **Skip your own echoes silently**: the test is "did *I* just post this body?", not "who
  is the author?".

## Cost and reliability

- **Call out cost and reliability up front** for a new external dependency (a tool the
  scripts shell out to, a network call, a service): rough dollars (free tier vs paid,
  $/month at expected use), new failure modes, rate limits, latency, and what the user sees
  if it's missing or down — these run interactively, so a network call on a hot path is a
  visible hang. If the impact is effectively zero, say so.
