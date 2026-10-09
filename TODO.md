# TODO

## Review and merge gates

- [ ] **Add `zizmor` to the ruleset's required set** once it has reported
      on a pull request: the new zizmor workflow runs unfiltered on every
      PR precisely so it can be required (a paths-filtered workflow
      creates no check run at all on a non-matching PR, which a ruleset
      waits on forever) — the posture piloted in mikelward/lanes and
      mikelward/ci-commit-artifact. `repo setup mikelward/scripts` with
      no arguments applies the standard `lanes codex zizmor` set.

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

## Hyprland from source in setup-tide

`setup-tide` builds Hyprland 0.56 from source where apt's is older
(Ubuntu 26.04 ships 0.53). Two follow-ups:

- **Debian 13.** The build needs GCC 16's libstdc++, libxkbcommon 1.11 and
  Lua 5.5; trixie has GCC 14 and older xkbcommon, so setup keeps apt's Hyprland
  there and says why. A newer toolchain from backports, or a container
  build, would cover it.
- **Retire it.** Once Debian and Ubuntu ship Hyprland 0.56 or later, the
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
      run instead would break `setup --tide` in containers and chroots, where
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
- [ ] **Disable greetd when enabling it fails partway.** If
      `display-manager.service` is a plain unit file rather than a link,
      `systemctl enable --force greetd.service` can add greetd's
      `graphical.target.wants` link and then fail on the alias. setup then
      stops switching, but leaves that link, so greetd and the old display
      manager could both start at the next boot. The fix: disable greetd on
      every failed enable, and warn if that fails, as the check after a
      successful enable already does. Raised in review of
      mikelward/scripts#288.
- [ ] **Read a script's `#!` line only as far as the kernel does.** setup
      reads the whole first line, but Linux reads only the first 256 bytes
      (`BINPRM_BUF_SIZE`) and may cut the argument short. So with a very
      long `#!/usr/bin/env <name>` line, setup can check a helper that
      exists while the kernel hands `env` a cut-off name that doesn't.
      greetd or the greeter would then fail at boot. The fix: parse only the
      first 256 bytes, with a test for a long `#!` line. Raised in review of
      mikelward/scripts#288.

## Decisions needing review

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
