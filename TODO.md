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

## Decisions needing review

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
