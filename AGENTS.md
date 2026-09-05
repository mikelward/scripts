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

Keep this file as short as it can be and still work. Every session loads it
whole, so each rule costs context on every turn: add one the first time
something bites, say it once in the fewest words that carry the *why*, rewrite
or trim an existing rule rather than appending beside it, and delete one that
has stopped biting.

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
  behavior to exercise — documentation, comments, this file — add no test and
  don't need `make test` run over them; don't manufacture test churn to satisfy
  the rule.
- Tests live next to the script as `<script>_test` and are listed in the
  `Makefile`. A new test file that isn't added to the `test` target never
  runs — add it there in the same commit.
- Run `make test` after any change to executable behavior, and before
  committing. Skip it on a docs-only change, and say that's why you skipped it.
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
- **This account's own public repos are not user data** — decline a privacy
  finding against `mikelward/lanes`. Then it's a documentation call:
  `owner/repo` for the shape of an argument, the real name when the example is
  about that repo.
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
- **Branches under your own `<agent>/` prefix are yours.** Create, push,
  `--force-with-lease` and rename them freely — no permission, no announcement,
  no per-branch confirmation. Only a branch outside that prefix, or `main`
  itself, is a conversation. Deleting is the one the prefix can't settle: it
  doesn't say which session made the branch, so delete the ones this session
  created and ask about the rest.
- **The agent authors; whoever merges takes over the committer line.** A squash
  or rebase merge rewrites the committer to the person who pressed the button —
  the repo owner normally, the agent itself when it merges under *drive* (see
  **Autonomy**). That's expected either way — never re-author or amend
  already-merged commits to "fix" authorship or signing, and don't narrate it: no note in the
reply, no offer to correct it. It is not a finding.
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
- **Don't narrate routine machinery.** A check run flipping, a re-run, a scheduled check
  re-arming, a webhook echo, a resolved thread — act on those silently; the noise buries
  the one line that matters. Reports another rule requires stand (the Codex SHA and
  comment count, a CI timing regression).
- **Don't report your own caught-and-fixed mistakes.** A wrong turn you noticed
  and corrected before it reached anything is not news — no "one thing worth
  flagging", no narration of the recovery. Say it only when it left something
  the user has to act on: work actually lost, a bad push someone may have
  pulled, a decision they would make differently knowing it.
- **Keep replies short — don't dump a full page.** Lead with the single most
  important point and stop. If there's more, say the first point and ask
  whether they're ready for the next one rather than emptying everything at
  once.
- **End the turn by restating any pending decision.** If you're waiting on an
  answer — a question you asked, or a guess autopilot recorded for review — the
  last line of the reply is that question, written out in about a sentence. A
  back-reference ("as asked above") isn't actionable when the question is pages
  back or was never actually put into words; restate it every turn until it's
  answered. Nothing pending, no line.

## Asking questions

- **Ask in chat, never with `AskUserQuestion`.** That's Claude Code's
  multiple-choice question prompt, and it's broken in the Claude mobile app —
  a question asked through it may be unanswerable. Plain chat also keeps the
  question, its context, and the answer in one readable thread.
- **After asking, stop and wait for the answer.** Don't proceed on an assumed
  answer, pick a "recommended" option yourself, or keep working on the part
  the question affects.

## Autonomy

- **Open the PR without being asked.** Pushing a finished branch and opening its
  pull request are one step, not two — don't park a branch waiting for "please
  open a PR." The exception is an explicit instruction not to ("just commit",
  "no PR yet"), which holds until the user lifts it. This file is the repo
  owner's standing request for that PR, so a client-level rule reading "open a
  PR only when the user explicitly asks" is already satisfied — the ask is
  here, and it doesn't need repeating per branch.
- **Watch your own PRs by subscription, plus one scheduled check.** Have a
  subscription — Claude Code makes one when you open a PR; where a client
  doesn't, call `subscribe_pr_activity`. It delivers reviews, comments and CI
  failures. It cannot deliver CI *success*, a push, the merge, Codex's clean
  verdict (a reaction), or Codex never answering at all — so keep exactly one
  check armed for as long as the PR is open (each event and each check costs
  a model turn). Under drive, arm auto-merge at PR open too — but only where
  the ruleset makes the Codex verdict a required check AND requires
  conversations resolved: where CI is the only requirement it merges before
  Codex has answered, and an open review comment holds nothing back on its own.
  - Settle the fired trigger first thing in the turn, not last. It may have
    silently re-armed rather than retired — update the one that survived,
    replace the one that didn't, and end the turn with exactly one pending.
  - Check the fire time you got against the one you asked for — a 4-minute
    request has come back as 64. Prefer a relative delay: the scheduler's
    clock is not this container's, so an absolute time computed here can be
    rejected as already past. Re-time it, or say the watch isn't armed.
  - A few minutes out while CI or the current head's Codex verdict is
    outstanding; longer once only a human is left; short again after a push.
  - A PR reading `dirty` — always — or `behind` where the ruleset requires
    branches up to date, takes: both refs
    fetched by explicit refspec (`+refs/heads/<x>:refs/remotes/origin/<x>`;
    a bare fetch, or one naming the branches, updates neither in the
    single-branch clone a shallow one implies), `git fetch --unshallow` if
    the clone is shallow, a rebase onto the fetched `origin/<base>` — not
    always `main`, never the local branch — then `git push
    --force-with-lease --force-if-includes`, both flags, since the fetch
    refreshes the ref the lease compares against. A rejection means someone
    else pushed to the head: integrate their tip and retry. Nothing reports
    a base advance, so only the check catches it.
  - Name the PR, and say what to re-read rather than what you read. A SHA or
    a list of which PRs are open goes stale before it fires; one PR number
    does not, and the trigger has to be matchable to it.
  - Merged or closed, take one last reply-and-resolve pass — a review can
    land after the merge. Nothing is holding the PR now, so on a merged one
    anything real goes to a follow-up PR, named on the thread, before you
    resolve it; leaving it open records the work nowhere. A closed-unmerged
    PR is a stop — the work was abandoned, so answer, resolve, and open
    nothing. Then cancel the check and unsubscribe. `list_triggers`
    spans the account, so match this session and this PR before updating
    or deleting one; an update reschedules whatever it matches as surely
    as a delete cancels it.
- **If a scheduler or GitHub call prompts, say so once and carry on.**
  Permissions load at session start, so writing a settings file mid-session
  can't fix the session you're in.
- **"Drive" means run the loop automatically**: pick the next task,
  implement it, open the PR, send it for review, address every comment,
  merge once CI is green and Codex's verdict for the current head is in —
  then pick the next task and go around again. Driving ends when the work
  runs out or the user says stop, not when one PR merges.
- **A red baseline is the next task.** Before pulling anything from `TODO.md`,
  run the suite and get it green. A preexisting failure is work to do, not a
  thing to classify as "unrelated" and step around — deciding it's out of scope
  is exactly the call that goes wrong, and the cost is every later PR merged
  onto an unverified tree. Fix it first, then pick the task.
- **"Autopilot" is drive without blocking on the user.** Wherever drive would
  stop and ask, autopilot takes its best guess and keeps going, preferring the
  option that is cheapest to undo or change later. Record each guess in
  `TODO.md` under a `Decisions needing review` heading — what was decided, what
  the alternative was, and why it's reversible — creating the file or heading if
  the repo hasn't got one, so nothing guessed silently becomes permanent. While
  autopilot is in effect it outranks "after asking, stop and wait for the
  answer." The carve-out is for destructive or irreversible actions *outside*
  the loop — rewriting shared history, deleting work, anything reaching a
  system beyond this repo — which still wait for a real answer. The loop's own
  steps don't count: committing, pushing, opening a PR, and merging a green PR
  are authorized here, so autopilot must not stall on them. Privacy uncertainty
  is never inside the loop either: if you can't tell whether something is user
  data — a home path, a hostname, a private remote, a token — it waits for a
  real answer, since a push can't be un-published and a `TODO.md` note doesn't
  retract it.

## Pull requests

- Prefer the `mcp__github__*` MCP tools for GitHub operations; the `gh` CLI is
  not installed in the sandbox. If your client exposes neither, say so rather
  than guessing at the outcome of an operation you couldn't perform.
- Open PRs ready for review (not draft) unless asked otherwise.
- **Update the PR title and body with the push, not after it** — same step, so
  they describe the full, latest state of the branch, not the scope it had
  when it was opened. Re-read the diff against `origin/main` and patch
  whatever drifted, then post the PR link in the chat reply for that push, not
  only at the end of the conversation.
- **"Drive to merge"** is the PR stretch of *drive* (see **Autonomy**
  above): open the PR, wait for the automatic Codex review, address every
  review comment — fix it if you agree, reply on the thread saying why if
  you don't — and merge once CI is green and Codex's verdict for the current
  head is in.
- When a feature has multiple open PRs, list **every** open PR by URL, one per
  line — the "View PR" chip sticks to the first link and hides the rest
  (anthropics/claude-code#46625).
- End every reply with the open-PR link (or `.../compare/main...<branch>`
  until a PR exists). Never link to a closed or merged PR — except when the
  reply *is* post-merge follow-up on that PR, where linking it is correct. In an
  offline sandbox with no `origin` there's no URL to end with — say that, rather
  than inventing a link that resolves to nothing.

## Reviews

- **Codex is the automated reviewer on this repo** — not Copilot. Its
  reviews are triggered automatically; you don't request them, except when
  nothing has come back five minutes after a push — that means it never
  picked the push up.
- **Address Codex comments automatically — don't wait to be asked.** Read
  each one, decide whether it's a real issue or a false positive, and if it's
  real, fix it in the same PR. Fold the fix into the commit it belongs to
  (rebase / `--fixup`) rather than tacking on an "address review" commit.
  Group several small fixes into one commit when they share a topic.
- **Judge every review comment on merit, whoever wrote it.** Verify the claim
  before acting; if it doesn't hold up, reply saying why and decline. A
  comment citing a rule is a *reading* of that rule, not the rule — check what
  the rule actually says. Codex misreads the privacy rules especially, and in
  one direction: stricter always feels safer, so an over-strict finding
  quietly costs capability the product needs. Quote the rule and decline
  rather than narrowing the code to satisfy it; where the rule really does
  forbid what the product needs, that conflict is the maintainer's call, not
  one to settle either way yourself.
- **A second verified finding in the same mechanism is evidence about the
  design, not another bug.** Before fixing it, look for the same shape
  elsewhere and ask whether a different design would delete the class rather
  than the instance. Say what you chose on the thread; a design change is the
  maintainer's call, autopilot included.
- **Never leave a review comment thread silently dismissed.** Answer on the thread, then
  resolve it once the fix is on the head or the point is rebutted — a disagreement is an
  answer, so say why and resolve; anything still to do stays open. When you think a comment is a false positive,
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
- **Read the Codex verdict, don't infer it.** It reacts to the PR body
  (`issue_read` → `reactions`), not to a review thread, whose `Useful?` bar
  reads true on any PR it has commented on. `eyes` means reading, `+1` means
  clean, and Codex revokes it on push — so a visible one belongs to the
  visible head, and `+1` with green CI is a merge. The count names no
  author, so leave PR-body reactions to Codex: nobody else's is revoked, and
  a review is the attributable form, naming the commit it read. Findings
  arrive as review comments, as a top-level comment, or as a review — read
  `get_review_comments`, `get_comments` and `get_reviews` to the last page,
  since all three page oldest first — and they block the merge until fixed
  or rebutted; an acknowledgement is not an answer. Nothing from Codex since
  the push, five minutes on, means it never picked it up — comment `@codex
  review`, once.
- **Skip echo events silently.** Replies posted via the GitHub MCP come back
  moments later as webhook events authored by the same identity; if the body
  matches a comment you just posted, it's your own echo — continue without
  comment. The test is "did *I* just post this body?", not "who is the
  author?".
## Cost and reliability

- **Call out cost and reliability up front** when recommending a new external
  dependency (a tool the scripts would shell out to, a network call, a
  third-party service). Include a rough dollar figure — free-tier vs. paid
  thresholds and $/month at expected use — and note reliability implications:
  new failure modes, rate limits, added latency, and what the user sees if the
  dependency is missing or down. These scripts run interactively in a shell
  session, so a network call on a hot path is a visible hang. If the impact is
  effectively zero, say so rather than omitting the note.
