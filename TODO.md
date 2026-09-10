# TODO

## Prune a previously-installed joshuto on upgrade

Removing joshuto from the install (its `tools` entry, the file-manager step,
and the `homepkg` `TOOLS` registry) stops *new* setups from installing it, but
does nothing for a machine where an earlier `setup` already installed joshuto
through the managed mamba environment: the binary and its `~/.local/bin/joshuto`
symlink linger, and because the registry entry is gone, `homepkg remove joshuto`
now fails in `_require_known`, so there's no supported cleanup command either.

Give upgrades a cleanup path: either prune the setup-managed joshuto (package +
`~/.local/bin` symlink) during `setup`, or keep enough removal metadata that
`homepkg remove joshuto` still works for a deregistered-but-installed tool.
Out of scope for the removal PR itself, which only changes what gets installed
going forward.

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

## setup / homepkg

- [ ] **Purge setup-managed tools that are retired from the registry.**
      Dropping a tool from homepkg's `TOOLS` (e.g. `yazi`, replaced by
      `joshuto` in #235) only stops *installing* it: `install_mamba` /
      `_link_bins` never remove an already-installed package, so it
      lingers orphaned in the managed env, and `homepkg remove <tool>`
      rejects it as unknown once the registry entry is gone. Add a way to
      remove setup-managed tools (distinguishing them from independently
      installed copies) so an upgrade that retires one can clean it up.
      Deferred from #235, where the orphan was accepted.

- [ ] **Install zsh-autosuggestions on the `--no-root` path.** The
      privileged setup installs it from the distro package (apt/dnf/brew,
      alongside zoxide), but under `--no-root` the distro step is skipped
      and, unlike fzf/zoxide, it has no conda-forge package for homepkg to
      fetch. So an unprivileged box gets no inline history ghost text. A
      git clone of zsh-users/zsh-autosuggestions into
      `~/.zsh/zsh-autosuggestions` (pinned to a tag) would cover every path
      uniformly, since the conf shell config already checks that location
      first; deferred from the setup PR that added the packaged steps.
