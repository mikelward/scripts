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
repo). It fetches from conda-forge by default, or GitHub releases:

```sh
homepkg list                          # known tools
homepkg install ripgrep fd bat jq     # from conda-forge into ~/.local
homepkg --backend github install gh   # from GitHub release assets
homepkg --prefix ~/opt install nu     # a different prefix
```

conda packages are sha256-verified against the channel index. `.conda`
payloads need zstd (the python `zstandard` module or the `zstd` CLI); the
GitHub backend needs neither.

## Third-party code

This repository vendors [pidcat](https://github.com/JakeWharton/pidcat)
as `./pidcat`. See [`NOTICE`](./NOTICE) for attribution. The whole
repository (including `pidcat`) is distributed under the Apache License,
Version 2.0; see [`LICENSE`](./LICENSE).
