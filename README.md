# scripts

## Setup

Bootstrap a new machine by running the setup script directly from GitHub:

```sh
curl -fsSL https://mikelward.com/setup | sh
```

or

```sh
wget -qO- https://mikelward.com/setup | sh
```

The short URLs redirect to the raw script on GitHub. You can also use the full URLs:

```sh
curl -fsSL https://github.com/mikelward/scripts/raw/main/setup | sh
wget -qO- https://github.com/mikelward/scripts/raw/main/setup | sh
```

Re-run `setup` whenever you like: it installs what's missing and leaves what's
installed at its version, upgrading only once a week. That pass upgrades
`setup`'s apt or dnf packages, everything Homebrew has, the `homepkg` tools,
the release binaries and `uv`, and `~/.local/state/setup/last-upgrade` records
the last one that didn't fail; a failed one is tried again on the next run.
`setup --upgrade` upgrades now. A managed machine that has each new version of
a binary approved before it runs sees new versions at most weekly. The repos
`setup` clones (`scripts`, `conf` and the rest) are config, so they're pulled
on every run.

`setup` asks for what it needs at the start, so the rest of the run can go
unattended. On Linux it asks for your sudo password and keeps it fresh until
it's done. When the repos come over SSH, it signs in to their host, so a
security key asks for its touch then, and every pull shares that connection.
A sign-in that hasn't finished in a minute, as with a hung security key, is
given up on with a warning.

## Installing tools without root

On machines where you can't use `apt`/`dnf`, `homepkg` installs prebuilt CLI
tools into a home prefix (default `~/.local`, already on `PATH` via the conf
repo).

`setup --no-root` wires this in automatically: it runs unprivileged (implying
`--no-sudo`, so the `apt`/`dnf` installs and every other privileged step are
skipped) and installs the CLI tools via `homepkg` instead — the core set
(`ripgrep fd bat fzf jq delta gh zoxide lf`) plus the extras (`helix jj nu`, unless
the minimal profile is in effect). `--no-sudo` on its own is just the mechanism
(skip sudo); it assumes the tools are provided some other way.

`atuin` and `carapace` — the history search and completion engines the conf
repo's shell config wires up — are in no distro repo and have no conda-forge
package, so `setup` installs them from their GitHub releases with
`homepkg --backend github`, regardless of profile or privilege, and upgrades
them on its weekly upgrade run.

The heavyweight extras (`helix jj nu`) come the same way on a privileged box
without Homebrew: `setup` fetches the release artifacts rather than building
them from source, so no Rust toolchain is installed. `--brew` (the default
where `brew` is available, and on macOS) uses bottles instead; `--release`
forces the release artifacts. `jj` is left out of that install whenever the
box already has one `setup` didn't install — a distro package, a Homebrew
formula — so the packaged copy stays the one that runs instead of being
shadowed by a second install in `~/.local/bin`. A `jj` already under
`~/.local` is `setup`'s own and is refreshed on the weekly upgrade run. `shpool` publishes no
prebuilt artifact and is no longer installed by `setup` — sessions still
prefer it when it's on `PATH` from somewhere else, and otherwise fall back to
`tmux`.

On a host with no internet, stage a bundle instead. The one-shot bundle below
covers them along with everything else, which is all a `--no-root` machine
needs. On a privileged machine the distro packages come from apt/dnf and that
bundle isn't installed, so stage these two on their own — beside the scripts
repo, in `$HOME`, or wherever `$HOMEPKG_SHELL_BUNDLE` points:

```sh
homepkg --backend github bundle -o homepkg-shell-tools.tgz atuin carapace
```

`setup` prefers a bundle over the download, so an offline run never waits for
a fetch that can't succeed.

What the installers say — apt's, dnf's and pacman's lines a package,
Homebrew's downloads and caveats, micromamba's progress, the root build, and
on a Linux desktop tide's `make`, Krohnkite's install and `systemctl`'s
notices — goes to
`~/.local/state/setup/setup.log`, which `setup` starts afresh each run and
`setup-macos`, `setup-kde` and `setup-tide` add to (each starts the log itself
when it's run on its own). Each package manager's run shows a header and what
changed:

```
Installing apt packages
Installed: zoxide zsh-autosuggestions (and 3 dependencies)
Upgraded: git
Failed: frob
```

`setup-tide`'s steps say `Installing tide's apt packages`, `Installing
Quickshell`, and so on. A failed step also shows the last lines it printed.
`--verbose` (`-v`) shows what the installers print instead of logging it;
`setup` passes it on to the others, and `setup-tide`'s source builds are
shown and still kept in their own logs. It also shows what was already so,
which a plain run leaves out: `Skipping jj: already installed at /usr/bin/jj`.
debconf's questions about the packages apt installs, such as which keyboard
layout or display manager to use, are asked on the terminal, as plain text,
before the packages are installed. A question already answered isn't asked
again. Everything else apt would ask takes its default, since the question
would land in the log, and so does every question when there's no terminal or
no apt-utils, or when sudo won't let setup set `DEBIAN_FRONTEND`. A config
file changed on the machine keeps that version, apt's own default answer,
and a warning names the package's new version beside it, to merge by hand:
`FILE.dpkg-dist`, or dnf's `FILE.rpmnew` and pacman's `FILE.pacnew`.

A checkout `setup` can't pull (this repo, conf, tide, tilemo) is used as it
is, with a warning that says why: it can't reach origin, local changes are in
the way, it has diverged, or its branch has no upstream. One that pulls but
is on a branch other than its default gets a warning too, since that's how
an old branch gets installed unnoticed. Nothing switches the branch or drops
a change.

**A machine that won't run binaries from `~/.local/bin`** — a managed Mac whose
policy kills any binary it hasn't approved (exit 137), or a `noexec` home —
gets none of this. Before installing anything there, `setup` copies a system
binary (`true`) into `~/.local/bin` and runs the copy. If that fails, it
installs nothing there (the `homepkg` tools, `uv`) and removes the `atuin` and
`carapace` an earlier run left there that won't run, so the shell stops
starting them. Nothing looks for a particular company or product; install the
tools some other way (Homebrew, if the policy allows it) instead.

**A Mac whose Santa is in Lockdown mode**, where each new version of a
binary needs an administrator's approval, gets no command-line tools: `setup`
says so once and skips Homebrew's formulae and the tools it downloads (helix,
jj, nushell, atuin, carapace, lf, node, uv and fnm). Homebrew and its apps
(kitty, iTerm2, android-platform-tools) still install, the weekly upgrade
upgrades only the apps, and `setup-macos` installs Hammerspoon,
Karabiner-Elements and the rest as usual.

The default backend is `mamba`: a rootless [micromamba](https://mamba.readthedocs.io/)
manages one conda environment, so you get a real solver (full dependency
closure), native updates, and clean removal. micromamba is bootstrapped
automatically from conda-forge.

```sh
homepkg install ripgrep fd bat jq     # into a micromamba env, symlinked to ~/.local/bin
homepkg update                        # update everything (micromamba update --all)
homepkg update ripgrep                # or a single tool
homepkg remove jq
homepkg prune                         # remove the tools homepkg has retired (joshuto, yazi)
homepkg bootstrap                     # just fetch micromamba
homepkg list                          # known tools
```

For one-shot installs or building push-bundles there are two stateless
backends that unpack a single artifact (no solver, no dependency resolution):

```sh
homepkg --backend conda  install ripgrep   # unpack a conda-forge package (sha256-verified)
homepkg --backend github install gh        # unpack a GitHub release asset
```

conda artifacts are sha256-verified against the channel index. `.conda`
payloads (and the channel index) need zstd (the python `zstandard` module or
a `zstd`/`unzstd` CLI; the code falls back to the uncompressed index). The
GitHub backend needs neither.

### Push bundles (air-gapped installs)

Build a self-contained bundle on an online host, copy it to a machine with no
internet, and install offline:

```sh
# online builder
homepkg bundle -o tools.tgz                   # every registered tool
homepkg bundle -o tools.tgz ripgrep fd jq     # ...or just the named ones
homepkg --backend github bundle -o tools.tgz ripgrep fd jq   # static-asset variant

# air-gapped target (no network)
homepkg install-bundle tools.tgz
```

`bundle` with no tool names is the one-shot: it covers the whole registry,
taking each tool from wherever it comes from. Tools with a conda-forge package
go in as a solved dependency closure alongside the micromamba binary that
unpacks it, so `install-bundle` lays the packages flat into the prefix
(`bin`/`lib`/`share`) with no network and no environment at all; the few with
no feedstock (`atuin`, `carapace`) go in as static release assets.
`install-bundle` unpacks whichever payloads the bundle carries. These are plain
files in the prefix — `homepkg update` / `remove` manage only the online mamba
env, not bundle-unpacked tools; to refresh those, install a newer bundle over
them.

The `github` variant builds a bundle of release assets only. It needs explicit
tool names, since not every registered tool publishes one (`typescript` is
npm-only).

## Third-party code

This repository vendors [pidcat](https://github.com/JakeWharton/pidcat)
as `./pidcat`. See [`NOTICE`](./NOTICE) for attribution. The whole
repository (including `pidcat`) is distributed under the Apache License,
Version 2.0; see [`LICENSE`](./LICENSE).
