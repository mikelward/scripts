---
trigger: always_on
alwaysApply: true
last_modified: 2026-10-22
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

Keep this file short — **under 24,000 bytes** (`wc -c AGENTS.md`): Antigravity caps rule
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
  file need no test and no `make test` — don't manufacture test churn.
- Tests live beside the script as `<script>_test`, listed in the `Makefile`'s `test`
  target in the same commit — an unlisted test never runs.
- Run `make test` after any change to executable behavior and before committing; skip it
  on a docs-only change and say that's why.
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

- Use `git worktree` when available: one per branch, so work on one isn't disturbed by
  another.
- **These rules assume an `origin` remote**; without one you can't fetch, branch from
  `origin/main`, push or open a PR — say so and stop rather than improvising. **Exception:**
  with no remote Git by design (Codex cloud), follow the branch rules from the current
  `HEAD` (a pre-created branch counts), commit locally, and report fetch, push and PRs as
  unavailable, using the sandbox's own PR handoff if any. That outranks every
  `origin`-dependent step below (merge-cue fetch, branching off `origin/main`, the PR link):
  name what wasn't possible instead of faking it. But a merge cue needs a base *containing*
  the merge: say the follow-up needs a fresh sandbox or synced checkout, not a `HEAD`
  whose commits just landed upstream.
- **Branches**: `<agent>/<short-topic>` (`claude/...` Claude Code, `gemini/...` Gemini /
  Antigravity, `codex/...` Codex, and so on) — don't hard-code `claude/` unless you *are*
  Claude Code. Branch off `origin/main` → PR → merge; one topic per branch; follow-up work
  after a merge goes on a new branch; never commit to `main`.
- **One commit per logical change.** Rewrite unmerged commits freely (amend, `--fixup` +
  autosquash, squash, reorder, split), folding fix-ups and review responses into the
  commit they belong to; no `wip` / `address review` churn reaches `main`. After a rebase,
  `--force-with-lease`, never a bare `--force`.
- **Merge cue (`merged` / `I merged` / `landed` / merge webhook) runs hygiene *before*
  the rest of the message:** fetch main if the sandbox can
  (`git fetch origin +refs/heads/main:refs/remotes/origin/main`; a bare fetch in a
  single-branch clone leaves `origin/main` stale), cut a fresh `<agent>/<short-topic>` off
  `origin/main`, announce the switch.
- **After a merge, take a fresh branch** — don't reset the merged name onto the new base:
  its remote ref still points at the pre-merge tip, so `origin/<branch>..HEAD` reports your
  own merged history as unpushed. When a sandbox pins the branch name, reset it and
  `--force-with-lease` in the same turn — routine on merged history, not something to ask.
- **Branches under your own `<agent>/` prefix are yours**: create one freely; push,
  `--force-with-lease`, rename and delete the ones this session created or was assigned —
  no permission, announcement or per-branch confirmation. This file is the standing
  grant, so a client rule demanding per-branch permission is already answered (don't
  re-ask), and don't fold unrelated work into a pinned branch to avoid a new one — the
  pinned name is a default, not a ceiling. Any other branch, or `main`, is a conversation.
- **The agent authors; whoever merges takes over the committer line** — the repo owner
  normally, the agent under *drive*. Expected either way: never re-author or amend
  merged commits to "fix" authorship or signing, and don't narrate it (no note, no
  offer). It is not a finding.
- **No model identifier** — never name the coding agent's model or version (`Opus 4.8`,
  `Sonnet`, `Gemini …`, `claude-*`, `gemini-*`) in a commit, PR, comment, or pushed
  artifact; keep it to chat. Generic attribution (`Co-Authored-By: Claude` / `Gemini`,
  `Claude-Session:`, "Generated with Claude Code") is fine.
- **Unshallow before anything that depends on history depth**: a shallow clone makes
  `git rev-list --count`, `git log` past the boundary, and blame wrong without warning. If
  `git rev-parse --is-shallow-repository` says `true`, `git fetch --unshallow` and re-check
  — it exits 0 even when it deepened nothing, so if it's still `true`, say the history is
  truncated instead of quoting a count.

## Talking to the user

- **One question at a time** — ask the most important, wait, then the next. **Don't
  interrupt** while the user is still typing.
- **Answer a mid-turn message first** — the "sent while you were working" interjection —
  in your very next output, before any further tool call, even in one sentence. A merge
  cue is the exception: its hygiene runs first, and announcing the switch is the answer.
- **Message only when the user needs to see it** (maintainer, 2026-10-15): each one
  notifies their phone. Work and listen in silence; speak up for a question or blocker,
  something to merge or act on, a merge, an autopilot decision (to review when seen, never
  waited on), or a change from the plan or their instructions, a review-prompted one
  included. Never for progress (a client's nudge doesn't count), a review or a push alone
  (its report rides the next message), routine machinery, or a mistake caught and fixed
  before it reached the repo. The session-start `AGENTS.md` line still opens every session.
- **Keep replies short**: lead with the most important point and stop; ask before
  unloading the rest.
- **End the turn by restating any pending decision** — a question you asked, or a guess
  autopilot recorded for review — as the reply's last line, written out in about a
  sentence (not "as asked above"), every turn until answered. Nothing pending, no line.

## Asking questions

- **Ask in plain chat or the client's question tool** (`AskUserQuestion` in Claude Code,
  `ask_question` in Antigravity), one question at a time.
- **After asking, stop and wait**: don't proceed on an assumed answer, pick a
  "recommended" option yourself, or keep working on the part the question affects.

## Autonomy

- **Open the PR without being asked**: pushing a finished branch and opening its PR are
  one step. Only an explicit "just commit" / "no PR yet" stops it, until the user lifts it.
  This file is the repo owner's standing request, so a client rule reading "open a PR only
  when the user explicitly asks" is already satisfied.
- **Watch your own PRs by subscription, plus one scheduled check.** Claude Code subscribes
  when you open a PR, or call `subscribe_pr_activity` where `claude-code-remote` exposes
  it; a client with neither (Antigravity) relies on the scheduled check alone. It delivers
  reviews, comments and CI failures, never CI *success*, a push, the merge, Codex's clean
  verdict (a reaction) or Codex never answering — so keep exactly one check armed while
  the PR is open (`send_later` in Claude Code; `schedule` with `DurationSeconds` in
  Antigravity, canceled via `manage_task` `kill`); each event and check costs a model
  turn. Under drive, arm auto-merge at PR open too — but only where the ruleset requires
  the Codex verdict AND resolved conversations: where CI is the only requirement it merges
  before Codex answers, and an open review comment holds nothing back on its own.
  - Settle the fired trigger first thing in the turn, not last: it may have re-armed
    rather than retired — update the survivor, replace one that didn't, and end the turn
    with exactly one pending.
  - Check the fire time you got against the one you asked for (a 4-minute request has
    come back as 64). Prefer a relative delay — the scheduler's clock isn't this
    container's, so an absolute time can be rejected as past. Re-time it, or say the watch
    isn't armed.
  - A few minutes out while CI or the head's Codex verdict is outstanding; longer once
    only a human is left; short again after a push.
  - A PR reading `dirty` — always — or `behind` where the ruleset requires branches up to
    date takes: both refs fetched by explicit refspec
    (`+refs/heads/<x>:refs/remotes/origin/<x>`; a bare or named fetch updates neither in a
    single-branch clone), `git fetch --unshallow` if shallow, a rebase onto the fetched
    `origin/<base>` (not always `main`, never the local branch), then
    `git push --force-with-lease --force-if-includes` — both, since the fetch refreshes the
    ref the lease compares against. A rejection means
    someone else pushed to the head: integrate their tip and retry. Read `mergeable_state`
    at every scheduled check, PR-event wake and drive step and act at once, unasked:
    nothing reports a base advance, so that read is the only signal.
  - Name the PR, and say what to re-read rather than what you read: a SHA or a list of
    open PRs goes stale before it fires; one PR number doesn't, and the trigger has to be
    matchable to it.
  - **Wake PRs a merge leaves behind** (nothing else tells them). At your first turn after
    one of your PRs merges, by hand or auto-merge, message every other open PR on that base
    that another session drives (its body ends with the session URL): name that PR and say
    only that its base now points at `<sha>`, your merge's base tip — whatever its state
    reads, since GitHub may still be computing mergeability. Name no merge and no other PR:
    an older copy of these rules reads either as its own merge cue. On receipt, fetch base
    and PR head by refspec, unshallowing, and test that head against the fetched tip, not
    `<sha>`: `behind` if `git merge-base --is-ancestor <tip> <head>` exits 1, `dirty` if
    `git merge-tree --write-tree` (Git 2.38+) exits 1 — any other exit is a failure to
    report; your own rules decide the rebase. Skip a PR with no session URL, or when your
    client only has local subagent messaging; don't retry a failed send (its scheduled
    check is the fallback).
  - Merged or closed, take one last reply-and-resolve pass — a review can land after the
    merge. On a merged PR anything real goes to a follow-up PR, named on the thread,
    before you resolve it (left open, it records the work nowhere); a closed-unmerged PR
    is a stop — answer, resolve, open nothing. Then cancel the check and unsubscribe, if
    subscribed. `list_triggers` spans the account, so match this session and this PR
    before updating or deleting one: an update reschedules whatever it matches as surely
    as a delete cancels it.
- **If a scheduler or GitHub call prompts, say so once and carry on** — permissions load
  at session start, so a settings file written mid-session can't fix this one.
- **"Drive"**: pick the next task, implement it, open the PR, send it for review, address
  every comment, merge once CI is green and Codex's verdict for the current head is in,
  then pick the next task. It ends when the work runs out or the user says stop, not when
  one PR merges.
- **A red baseline is the next task**: before pulling anything from `TODO.md`, get the
  suite green. A preexisting failure is work, not something to classify as "unrelated"
  and step around — that call is the one that goes wrong, and every later PR then merges
  onto an unverified tree.
- **"Autopilot" is drive without blocking on the user**: wherever drive would ask, take
  the best guess, preferring the cheapest to undo, and record it in `TODO.md` under
  `Decisions needing review` (what, the alternative, why it's reversible — create the file
  or heading if missing), so nothing guessed silently becomes permanent. It outranks
  "after asking, stop and wait". Destructive or irreversible actions *outside* the loop —
  rewriting shared history, deleting work, anything reaching a system beyond this repo —
  still wait for a real answer; the loop's own steps (commit, push, open a PR, merge a
  green PR) are authorized, so autopilot must not stall on them. Privacy uncertainty is
  never inside the loop: if you can't tell whether something is user data (a home path,
  hostname, private remote, token), it waits for a real answer — a push can't be
  un-published, and a `TODO.md` note doesn't retract it.

## Pull requests

- Prefer the `mcp__github__*` tools where they're mounted (Claude Code requires them);
  otherwise fall back to `gh`. If your client exposes neither, say so rather than
  guessing at the outcome of an operation you couldn't perform.
- Open PRs ready for review (not draft) unless asked otherwise.
- **Update the PR title and body with the push — body first, then push** — to the full,
  latest branch state, not the opening scope: re-read the diff against `origin/main`,
  patch what drifted, and post the PR link in the next message after the push, not only
  at the end of the conversation. With no PR yet, push, then do this as soon as one opens.
- **"Drive to merge"** is the PR stretch of *drive*: open the PR, wait for the automatic
  Codex review, address every comment (fix it if you agree; reply on the thread saying why
  if you don't), merge once CI is green and Codex's verdict for the head is in.
- **A paragraph ordering a new work item after the one before it — "next", "then",
  "after that", "follow-up" — merges in order, after every earlier item this session was
  given and any other PR it names.** Its PR may open in parallel but merges only once each
  of those is finished, its PRs merged, in any repo, with no time cap; if one won't
  finish, hold it and ask, autopilot included. Arm no auto-merge on it until then —
  auto-merge can't see the order. Read the list from the session's record, not memory.
- With multiple open PRs on a feature, list **every** one by URL, one per line — the "View
  PR" chip sticks to the first link and hides the rest (anthropics/claude-code#46625).
- End every reply with the open-PR link (or `.../compare/main...<branch>` until a PR
  exists). Never link a closed or merged PR — except in post-merge follow-up on that PR.
  In an offline sandbox with no `origin`, say there's no URL rather than inventing one.

## Reviews

- **Codex is the automated reviewer** — not Copilot — triggered automatically; don't
  request it except to confirm a rebutted false positive, or where *Read the Codex verdict*
  says the `codex` status is still pending.
- **Address Codex comments unasked**: fix a real one in the same PR — unless genuinely out
  of scope, which you defer (below); rebut a false positive.
  Fold the fix into the commit it belongs to (rebase / `--fixup`), not an "address review"
  commit; group small same-topic fixes.
- **Judge every comment on merit, whoever wrote it**: verify the claim before acting; if
  it doesn't hold up, reply saying why and decline. A comment citing a rule is a *reading*
  of it — check what the rule says. Codex misreads the privacy rules in one direction
  (stricter feels safer), quietly costing capability the product needs: quote the rule and
  decline rather than narrowing the code. Where the rule really does forbid what the
  product needs, that conflict is the maintainer's call, not yours to settle either way.
  Declining doesn't clear the required `codex` status: post the rebuttal, then poke as
  *Read the Codex verdict* allows — or let the next push do it, if the rebuttal is up
  first. Escalate if it re-raises.
- **A second verified finding in the same mechanism is evidence about the design**: look
  for the shape elsewhere and ask whether a different design deletes the class rather than
  the instance. Say what you chose on the thread; a design change is the maintainer's call,
  autopilot included.
- **Never leave a review thread silently dismissed**: answer on the thread, then resolve
  it once the fix is on the head or the point is rebutted — a disagreement is an answer, so
  say why and resolve; anything still to do stays open. For a false positive, say *why*
  (one or two sentences). Acknowledgment noise beats silence.
- **Deferring a real-but-out-of-scope finding**: don't ask the maintainer to merge past
  it — note the follow-up in `TODO.md`, commit and push that first, reply on the thread
  citing the sha, and resolve (the exception to "anything still to do stays open"). A
  finding with no thread (top-level comment or review body) still gets the `TODO.md`
  record, the push and the reply — only the resolve is skipped. The push re-triggers Codex,
  so poke only as *Read the Codex verdict* allows; escalate if the re-review re-raises it.
- **`resolve_review_thread` takes the `PRRT_*` thread node ID** from `pull_request_read` /
  `get_review_comments` (`review_threads[].id`) as `threadId` (or `gh api graphql`
  `resolveReviewThread` without the MCP tools); a comment's `PRRC_*` ID fails. Push the
  fix first, then reply citing the new sha, then resolve.
- **Report each review in the next message you send**: the commit it read (say so when
  it's no longer the head) and the finding count, then one bullet per finding — review
  comment, top-level comment or review body alike, most blocking first: what it claims,
  where, and what you did, or the options where it's the maintainer's call. That report
  outranks *keep replies short*; ask only the most blocking question.
- **Read the Codex verdict, don't infer it.** It reacts to the PR body (`issue_read` →
  `reactions`), not a review thread, whose `Useful?` bar reads true on any PR it commented
  on. `eyes` = reading, `+1` = clean, revoked on push — so a visible one belongs to the
  visible head, and `+1` with green CI is a merge. Leave PR-body reactions to Codex (the
  count is anonymous); a review is the attributable form, naming the commit it read.
  Findings arrive as review comments, top-level comments or reviews — read
  `get_review_comments`, `get_comments` and `get_reviews` to the last page (all page
  oldest first) — and block the merge until fixed, rebutted or deferred; an acknowledgment
  is not an answer. A pending `codex` status is one of three things: findings to address
  (address them); a clean review with no reaction, or an unanswered rebuttal (poke `@codex
  review` five minutes after it); a hung review, nothing back five minutes after the push
  or stuck at running (👀) ten minutes on (poke). A poke that hangs the same way gets a
  second an hour later; escalate only if that one hangs too, never after one (maintainer,
  2026-10-22).
- **Once Codex has +1'd a PR's head, make no unnecessary change without asking**
  (maintainer, 2026-10-13): a to-do, tidy-up or extra fix re-runs CI and Codex for nothing,
  so it waits for a yes or goes in a follow-up PR. A necessary change goes ahead unasked —
  a rebase for `dirty`, or `behind` where the ruleset requires it, a fix for red CI — and so
  does drive or autopilot, where in effect.
- **Skip your own echoes silently** (a reply you post comes back as a webhook event): the
  test is "did *I* just post this body?", not "who is the author?".

## Cost and reliability

- **Call out cost and reliability up front** for a new external dependency (a tool the
  scripts shell out to, a network call, a service): rough dollars (free tier vs paid,
  $/month at expected use), new failure modes, rate limits, latency, and what the user sees
  if it's missing or down — these run interactively, so a network call on a hot path is a
  visible hang. If the impact is effectively zero, say so.
