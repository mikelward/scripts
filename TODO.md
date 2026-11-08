# TODO

## Review and merge gates

- [ ] Verify the settings half of the fleet's bar — every repository
      works the same: comprehensive automated review, required merge
      gates, and auto-merge. A ruleset on the default branch requiring
      the gates, the `codex` status, conversation resolution and
      up-to-date branches, with the auto-merge setting enabled.

## Crostini

The rest of the Crostini mode in mikelward/tideco's SPEC.md A.5, after
`setup` learned to detect it and skip the desktop:

- Set `BROWSER` to `garcon-url-handler`, if the container doesn't already
  *(unverified)*. `chrome` hands plain URLs to it already.
- Warn on Baguette (the newer VM container) that kitty renders on the CPU.
  Telling it apart from Crostini is unverified, so it waits for a device.
- Check the detection markers (`/dev/.cros_milestone`,
  `/opt/google/cros-containers`) on a Chromebook, Baguette included.

## Font smoothing on macOS

- [ ] **Live with light smoothing a while, then settle it.** `setup-macos`
      writes `AppleFontSmoothing` 1. Normal weights look right; bold may be
      too blurry. If it is, either go to `0` and give kitty a little weight
      back (`text_composition_strategy` in conf's `kitty.conf`), or keep
      `1` and give kitty a lighter bold (`bold_font`). macOS has nothing
      between 0 and 1.

## Decisions needing review

- **setup asks for sudo and SSH at the start** (2026-11-06), so a run can
  go unattended. sudo only on Linux: macOS needs it for a step or two at
  most, and asking there would add a prompt. A failed or hung sign-in warns
  and carries on rather than stopping, so offline runs and new machines
  still work; the sign-in gets 60s, the agent check 5s. The SSH connection
  is shared through `GIT_SSH_COMMAND`, unless you set your own. Reversible.

- **KDE's Win+V pastes with Ctrl+V into every window** (2026-11-04),
  terminals included. KWin has no D-Bus call for the focused window's
  class, so `clipboard-menu` can't pick Ctrl+Shift+V for a terminal, as
  tide's picker does. conf's kitty pastes on Ctrl+V; Konsole doesn't. The
  alternative is asking KWin through a loaded script, or `kdotool`.
  Reversible: one `tide-kwin-paste --shift` in `clipboard-menu`.
- **clipboard-menu reads Klipper, not cliphist** (2026-11-04), so it lists
  what Plasma already keeps and needs no service. Images are left out:
  Klipper's D-Bus gives only their size. Reversible: the history comes
  from one `busctl` call.

- **On macOS, tide for macOS's app keys open apps through `open`.** `chrome` runs
  `open -na "Google Chrome" --args …` (the beta if stable isn't in
  `/Applications` or `~/Applications`), so `browser1`–`3`, the Google web
  apps and `youtube-music` keep their Linux flags: the same
  `--user-data-dir`s and `--app=` windows, not Chrome's installed web apps
  (an installed app's id differs per machine). `home` opens Finder, `irc`
  the HexChat app, and `notepad` TextEdit, since SciTE has no Mac build.
  `terminal` and `terminal_on_workstation` need no change once kitty is on
  `PATH`: `runenv` now puts Homebrew's prefix (`/opt/homebrew`) ahead of
  launchd's bare `PATH` on macOS, behind `~/.env`'s own entries. The alternative for the web apps is
  opening each installed app by its bundle id. It's reversible: one branch
  per script on `uname -s`.
- **setup-macos still names conf's old "Alt+Tab switches applications"
  rule without `--wm tide`, when the conf checkout predates it.** That
  rule still works as it always did there, so the run names it as it is,
  as it does a stale arrow rule, and says an update replaces it. Under
  `--wm tide` it isn't named: it would make Alt+Tab Cmd+Tab, which is
  tide for macOS's key now. The alternative was to warn and name nothing in both
  modes. It's reversible: one `elif` arm in `configure_karabiner`.
