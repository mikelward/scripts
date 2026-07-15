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

`setup --no-sudo` wires this in automatically: it skips the `apt`/`dnf`
package installs (and every other privileged step) and installs the CLI tools
via `homepkg` instead — the core set (`ripgrep fd bat fzf jq delta gh`) plus
the extras (`helix jj nu`, unless the minimal profile is in effect).

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
homepkg bundle -o tools.tgz ripgrep fd jq     # solve closure + micromamba
homepkg --backend github bundle -o tools.tgz ripgrep fd jq   # static-asset variant

# air-gapped target (no network)
homepkg install-bundle tools.tgz
```

The default (`mamba`) bundle carries the full dependency closure plus the
micromamba binary, so the target builds a correct environment with no network
and micromamba relocates it into the target's prefix. The `github` variant
carries static release assets — smaller, but only for self-contained tools.

## Third-party code

This repository vendors [pidcat](https://github.com/JakeWharton/pidcat)
as `./pidcat`. See [`NOTICE`](./NOTICE) for attribution. The whole
repository (including `pidcat`) is distributed under the Apache License,
Version 2.0; see [`LICENSE`](./LICENSE).
