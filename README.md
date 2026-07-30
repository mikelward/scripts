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

## Installing tools without root

On machines where you can't use `apt`/`dnf`, `homepkg` installs prebuilt CLI
tools into a home prefix (default `~/.local`, already on `PATH` via the conf
repo).

`setup --no-root` wires this in automatically: it runs unprivileged (implying
`--no-sudo`, so the `apt`/`dnf` installs and every other privileged step are
skipped) and installs the CLI tools via `homepkg` instead — the core set
(`ripgrep fd bat fzf jq delta gh zoxide`) plus the extras (`helix jj nu`, unless
the minimal profile is in effect). `--no-sudo` on its own is just the mechanism
(skip sudo); it assumes the tools are provided some other way.

`atuin` and `carapace` — the history search and completion engines the conf
repo's shell config wires up — are in no distro repo and have no conda-forge
package, so every `setup` run installs them from their GitHub releases with
`homepkg --backend github`, regardless of profile or privilege.

The heavyweight extras (`helix jj nu`) come the same way on a privileged box
without Homebrew: `setup` fetches the release artifacts rather than building
them from source, so no Rust toolchain is installed. `--brew` (the default
where `brew` is available, and on macOS) uses bottles instead; `--release`
forces the release artifacts. `shpool` publishes no prebuilt artifact and is
no longer installed by `setup` — sessions still prefer it when it's on `PATH`
from somewhere else, and otherwise fall back to `tmux`.

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

The default backend is `mamba`: a rootless [micromamba](https://mamba.readthedocs.io/)
manages one conda environment, so you get a real solver (full dependency
closure), native updates, and clean removal. micromamba is bootstrapped
automatically from conda-forge.

```sh
homepkg install ripgrep fd bat jq     # into a micromamba env, symlinked to ~/.local/bin
homepkg update                        # update everything (micromamba update --all)
homepkg update ripgrep                # or a single tool
homepkg remove jq
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
replays it, so the target builds a correct environment with no network at all;
the few with no feedstock (`atuin`, `carapace`) go in as static release assets.
`install-bundle` replays whichever payloads the bundle carries.

The `github` variant builds a bundle of release assets only. It needs explicit
tool names, since not every registered tool publishes one (`typescript` is
npm-only).

## Third-party code

This repository vendors [pidcat](https://github.com/JakeWharton/pidcat)
as `./pidcat`. See [`NOTICE`](./NOTICE) for attribution. The whole
repository (including `pidcat`) is distributed under the Apache License,
Version 2.0; see [`LICENSE`](./LICENSE).
