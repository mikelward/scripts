# TODO

## Review and merge gates

- [ ] Verify the settings half of the fleet's bar — every repository
      works the same: comprehensive automated review, required merge
      gates, and auto-merge. A ruleset on the default branch requiring
      the gates, the `codex` status, conversation resolution and
      up-to-date branches, with the auto-merge setting enabled.

## Hyprland from source in setup-tide

`setup-tide` builds Hyprland 0.57 from source where apt's is older
(Ubuntu 26.04 ships 0.53). Two follow-ups:

- **Debian 13.** The build needs GCC 16's libstdc++, libxkbcommon 1.11 and
  Lua 5.5; trixie has GCC 14 and older xkbcommon, so setup keeps apt's Hyprland
  there and says why. A newer toolchain from backports, or a container
  build, would cover it.
- **Retire it.** Once Debian and Ubuntu ship Hyprland 0.57 or later, the
  build no longer runs; delete it then, with `~/.local/opt/hyprland` and the links
  in `/usr/local/bin` on machines that built it.

## greetd in setup-tide

- [ ] **Take over Debian's display-manager selection, once tested on a real
      machine.** setup switches to greetd through systemd's
      `display-manager.service` alias alone, and leaves
      `/etc/X11/default-display-manager` as it is. On Debian and Ubuntu that
      file wins: every display manager package's postinst (gdm3, sddm,
      lightdm, and greetd from 0.10.3-6) re-points the alias at whatever the
      file names, on each install and upgrade, so the next upgrade of any of
      them quietly undoes the switch. And greetd from 0.10.3-6 asks which
      display manager to use when it's installed, and writes
      `/usr/sbin/greetd` into the file if it's picked; `--no-greeter` or a
      rollback then brings back GDM or SDDM while their units refuse to
      start, since the file names greetd. The fix: record the file beside
      the replaced unit, point it at greetd, and restore it with the unit.
      Raised in review of mikelward/scripts#288.
- [ ] **Then fall back on that file when systemd can't say.** When greetd is
      the display manager, the run starts by putting its config right, so a
      later step that ends the run can't leave it broken. If systemd can't
      say which display manager this is, that repair is skipped. Stopping the
      run instead would break `setup` in containers and chroots, where
      `systemctl` always fails; the selection file above is the second
      source to read. Also from review of mikelward/scripts#288.
- [ ] **Decide how greetd's profile sourcing is checked.** greetd starts
      every session, the greeter's included, as `/bin/sh -c '. /etc/profile;
      . $HOME/.profile; exec tide-greeter'` (`source_profile`, default
      true). So the greeter's real PATH comes from those files, not the fixed
      PATH setup checks, and a `~/.profile` in the greeter's home could change
      what runs. Two options. Set `source_profile = false`: this is global, so
      users' own sessions would stop getting their profile too, unless tide's
      session sources it. Or check the PATH the sourcing really produces, and
      require the greeter's `~/.profile` to be absent or root's alone. Open
      question from review of mikelward/scripts#288.
- [ ] **Read only the PAM files greetd's stacks reach.** The pass that
      collects includes by full path reads every file in `/etc/pam.d` and the
      vendor directory. So a symlink loop in an unrelated file fails
      `find -L`, and setup refuses greetd though greetd never reads it.
      Unreadable files are already skipped. The fix that ends the class:
      drop the directory-wide pass, and have the stack walker resolve each
      include as it reaches it. Raised in review of mikelward/scripts#288.
- [ ] **Bound greetd's start limits and restart delays, or decide not to.**
      setup requires `Restart=always`, but accepts any start limit, restart
      delay or timeout. A root-owned unit with `StartLimitBurst=1` over a
      year would never restart greetd. Open question: bound these, or leave
      the timing to root. Raised in review of mikelward/scripts#288.
- [ ] **Read root-run programs as root.** setup reads the programs greetd's
      unit and `pam_exec` run as the user running setup. So one only root
      can read, mode 0700 say, fails the check, though systemd and PAM run
      it as root just fine. Read those with sudo instead. Raised in review of
      mikelward/scripts#288.

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
- **setup-tide builds tidewm only with `--tidewm`** (2026-11-05), since
  tide's tidewm session is an option beside Hyprland's, not the default,
  and the build costs a run's time on every machine. It pins a commit, not
  a tag: tidewm has cut no release, and a tag ruleset could make a tag
  permanent. Only Debian testing and Arch, which package the wlroots 0.20
  it builds against; Ubuntu 26.04 (0.19) and Fedora say so and carry on.
  The alternatives are building it by default, or building wlroots too.
  Reversible.
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

- **setup-tide writes tide-tabs's host manifest for Chrome and Brave**
  (2026-11-01), in each one's `NativeMessagingHosts`, when its config
  directory exists or its command is on `PATH`. It allows the Web Store's
  tide for Chrome ID, and an unpacked checkout's at `$TIDECO_DIR` (`~/src/tideco`),
  worked out from the manifest's `key` or else the folder's real path, as
  Chromium does. Sub-choices, each reversible in `install_tabs_host`:
  - setup doesn't clone tide for Chrome; it says where to put it. The alternative
    is cloning it beside tide, one more network fetch per run.
  - No host installed (`--no-install`, or an old tide) writes no manifest
    and warns, rather than a manifest pointing at nothing.
  - Chromium and other Chromium browsers get none; each has its own
    directory to add.

- **mikelward/scripts#288 merges with known gaps in setup-tide's greeter
  checks.** Review kept finding new edge cases in the root-only checks,
  round after round. So the PR stops at the happy path. Each finding left
  over, and any new one before the merge, goes under *greetd in setup-tide*
  above instead of into code. The alternative was to keep fixing each
  finding before merging. It's reversible: each entry is a follow-up to
  pick up.
- **setup-tide masks waybar and swaync per user, instead of disabling
  every enablement.** Distro packages enable their user units, and
  hypridle's, for every session, so they started under Plasma. Setup first
  hunted each enablement (global, per-user, runtime) and undid it, but review
  kept finding more places a link can live. Now setup masks waybar's and
  swaync's units for the user running it, and tide's hypridle drop-in
  skips hypridle outside the tide session (tide PR "Run
  hypridle.service only in the tide session"). The alternative was the
  enablement hunt, which also covered other user accounts on the machine;
  the masks cover only the user who ran setup. It's reversible with
  `systemctl --user unmask waybar.service swaync.service`, or by bringing back
  a `sudo systemctl --global disable`.
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
