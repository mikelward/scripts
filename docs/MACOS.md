---
title: macOS desktop setup
---

# macOS desktop setup

How the KDE/Krohnkite setup in `setup-kde` is reproduced on macOS by
`setup-macos`, what carries over, what doesn't, and why Amethyst was chosen
over the alternatives.

The window manager config itself lives in the `conf` repo as `amethyst.yml`,
which `confinst` symlinks to `~/.amethyst.yml`. This file covers the setup
around it.

For why Amethyst rather than yabai or AeroSpace, skip to the
[window manager evaluation](#window-manager-evaluation) at the end.

## Contents

- [Running it](#running-it)
  - [Full bootstrap](#full-bootstrap)
  - [Desktop configuration on its own](#desktop-configuration-on-its-own)
  - [What `setup-macos` requires](#what-setup-macos-requires)
  - [Install backends for Amethyst](#install-backends-for-amethyst)
- [Do these by hand first](#do-these-by-hand-first)
  - [And afterwards](#and-afterwards)
- [Key mapping](#key-mapping)
  - [Modifier rotation](#modifier-rotation)
  - [The one binding the rotation inverts](#the-one-binding-the-rotation-inverts)
- [How desktop switching works](#how-desktop-switching-works)
  - [Reliability](#reliability)
- [What doesn't carry over](#what-doesnt-carry-over)
- [Troubleshooting](#troubleshooting)
- [Window manager evaluation](#window-manager-evaluation)
  - [Amethyst](#amethyst)
  - [yabai](#yabai)
  - [AeroSpace](#aerospace)
  - [Recommendation: Amethyst](#recommendation-amethyst)

## Running it

There are two entry points. `setup` is the full machine bootstrap and calls
`setup-macos` at the end; `setup-macos` is the desktop configuration on its
own and is safe to run directly.

### Full bootstrap

```sh
setup
```

On macOS this installs Homebrew if it's missing, then, by category:

| Category | Examples |
| --- | --- |
| Core CLI packages | git, python3, ripgrep, vim, zsh, shellcheck, unzip, p7zip |
| Directory jumping | zoxide |
| Node toolchain | node, typescript (skip with `--no-npm`) |
| Android CLI tools | android-platform-tools (adb, fastboot) |
| Graphical apps | kitty, iTerm2, Amethyst, Rectangle (skip with `--no-gui`) |
| Heavyweight extras | helix, jj, nushell (`--minimal` skips, `--brew` / `--release` picks the source) |
| Dotfiles | clones the `conf` repo and symlinks it via `confinst` |

Then it hands off to `setup-macos` for the desktop configuration described in
this file.

`setup` flags that matter here:

| Flag | Effect |
| --- | --- |
| `--no-gui` | Skip graphical packages *and* the whole desktop configuration |
| `--no-install` | Configure only; install nothing. Forwarded to `setup-macos` |
| `--ignore-errors` | Keep going past failures. Forwarded to `setup-macos` |
| `--minimal` / `--full` | Skip or force the heavyweight extras |
| `--brew` / `--release` | Take the extras from Homebrew bottles, or from GitHub releases into `~/.local` via `homepkg` |
| `--no-root` | Unprivileged install; CLI tools come from conda-forge via `homepkg` instead |
| `--no-npm` | Skip node and tsc |

`--no-sudo` and `--no-root` change little on macOS. Homebrew never wants sudo
and installing Amethyst needs write access to an Applications directory rather
than privilege. The one exception is Karabiner: its cask is backed by a `.pkg`,
so Homebrew hands it to the system installer, which asks for an administrator
password.

The default is to try anyway. If you have admin rights you'll get the usual
password prompt; if you don't, the install fails, the run warns and carries on,
and everything except the Alt+Tab rule still applies. Pass `--no-sudo` only if
you want to skip the attempt outright — `setup` promises that flag never
prompts or stalls, so it has to skip rather than try.

### Desktop configuration on its own

```sh
setup-macos
```

The run opens with a preflight message listing what has to be done by hand,
then waits for Enter. Do those steps first — two of them can't be done from a
script at all, and skipping them looks like a broken keybinding rather than a
missed step.

| Flag | Effect |
| --- | --- |
| `--no-install` | Configure whatever Amethyst is already there; don't install |
| `--ignore-errors` | Keep going past failures instead of aborting on the first |
| `--yes` | Skip the preflight pause |
| `--no-sudo` | Skip anything needing administrator rights — only Karabiner's installer does |
| `--help` | Usage |

`setup` forwards `--no-install`, `--no-sudo` and `--ignore-errors` when it
dispatches here. The preflight pause is skipped automatically when stdin isn't
a terminal, so an unattended bootstrap doesn't block on an Enter that can
never arrive.

### What `setup-macos` requires

It's standalone: it doesn't need `setup` to have run, doesn't need root, and
degrades with a warning rather than failing when an optional piece is absent.

**Hard requirements**, checked up front so running it on the wrong OS says so
instead of failing several steps in:

- `defaults` and `hidutil` — i.e. macOS.

**Optional, each with a stated fallback:**

| Missing | Consequence |
| --- | --- |
| `brew` and no staged bundle | Amethyst isn't installed; the tiling settings have no effect until it is |
| `activateSettings` | Shortcuts are written but need a logout to take effect |
| `launchctl` | The modifier remap applies at next login rather than now |
| `pbs` | Launch shortcuts need a logout to register |
| `killall` / `pgrep` | Finder and the Dock need a manual restart or a logout |
| Launcher helpers | Those launch shortcuts are skipped; the rest are configured |
| `~/.amethyst.yml` | Warns; Amethyst runs with its own defaults instead of this setup's layouts and keybindings |

The launcher helpers (`browser1`, `browser2`, `terminal`,
`terminal_on_workstation`, `music`) are found on `PATH` or beside the script,
so running out of a fresh clone works before anything is on `PATH`.

`~/.amethyst.yml` is symlinked out of the `conf` repo by `confinst`. Without
the `conf` repo cloned, everything else still applies — only the window
manager's own layouts and keybindings are missing.

### Install backends for Amethyst

`setup-macos` tries these in order:

1. **Homebrew** — `brew install --cask amethyst`. The normal path.
2. **Staged bundle** — offline. Run `brew fetch --cask amethyst` on a
   connected machine and drop the zip at `$AMETHYST_BUNDLE`, `./amethyst.zip`,
   or `~/amethyst.zip`. It's unpacked to `/Applications`, falling back to
   `~/Applications` when that isn't writable, with the quarantine attribute
   cleared.

There's no third backend. If Amethyst is already installed in either location,
both are skipped.

## Do these by hand first

**Create nine Spaces** in Mission Control (Ctrl-Up, then `+` at the top
right). There is no API that creates a Space — not for this script, not for
any window manager. macOS accepts a "switch to desktop 7" binding whether or
not desktop 7 exists, and the key simply does nothing when it doesn't. The
script counts the Spaces afterwards and names which of `Option+1..9` are dead,
but it can't fix it for you.

With "Displays have separate Spaces" enabled, each display needs its own nine
— the numbering is per display, so five Spaces on each of two displays leaves
`Option+6..9` dead on both. The count is reported per display for that reason.

**Quit System Settings.** It holds the keyboard shortcut registry in memory
while open and can flush its cached copy back over the script's writes when it
closes, silently reverting them. The script warns if it sees it running.

### And afterwards

**Grant Amethyst Accessibility access**, under System Settings > Privacy &
Security > Accessibility. Amethyst moves and resizes windows through the
Accessibility API and is completely inert without it — it will run, show its
menu bar icon, and tile nothing.

This one can only be done *after* the run, not before it: on a first run
Amethyst isn't installed yet, so there's nothing to grant the permission to.
The run repeats the instruction when it gets there.

## Key mapping

Both columns are the **physical keys you press** on a PC keyboard — not the
modifier macOS receives. That distinction matters here, because the rotation
below means the two are never the same thing: pressing `Win` sends Option,
pressing `Ctrl` sends Command.

Reading it this way is also the point of the whole arrangement. The columns
match on all but two rows, which is the muscle memory being preserved.

| Action | Linux (KDE) | macOS | Provided by |
| --- | --- | --- | --- |
| Switch to desktop 1–9 | `Win+1`…`9` | `Win+1`…`9` | symbolichotkeys (IDs 118–126) |
| Move window to desktop 1–9 | `Win+Shift+1`…`9` | **`Win+Alt+1`…`9`** | Amethyst `throw-space-N` |
| Grow main pane | `Win+\` | `Win+\` | Amethyst `expand-main` |
| Shrink main pane | `Win+/` | `Win+/` | Amethyst `shrink-main` |
| Monocle / fullscreen layout | ``Win+` `` | ``Win+` `` | Amethyst `select-fullscreen-layout` |
| Previous layout | `Win+,` | `Win+,` | Amethyst `cycle-layout-backward` |
| Next layout | `Win+.` | `Win+.` | Amethyst `cycle-layout` |
| Set master window | `Win+Return` | `Win+Return` | Amethyst `swap-main` |
| Launcher / Spotlight | — | `Win+Space` | symbolichotkeys (ID 64) |
| Browser 1 | `Win+G` | `Win+G` | Automator Quick Action |
| Browser 2 | `Win+H` | `Win+H` | Automator Quick Action |
| Terminal | `Win+T` | `Win+T` | Automator Quick Action |
| Terminal on workstation | `Win+W` | `Win+W` | Automator Quick Action |
| Music | `Win+Y` | `Win+Y` | Automator Quick Action |
| Close window | `Win+Backspace` | **`Ctrl+W`** | macOS default, not configured |
| Switch applications | `Alt+Tab` | `Alt+Tab` † | Karabiner rule |
| Next tab in app | `Ctrl+Tab` | `Ctrl+Tab` † | Karabiner rule |

† Without Karabiner those last two swap round — `Ctrl+Tab` switches
applications and `Alt+Tab` goes to the next tab. Its driver extension is the
one part of this setup a managed Mac can refuse; see
[the one binding the rotation inverts](#the-one-binding-the-rotation-inverts).

Only two rows differ from the Linux keys:

**Move-to-desktop is `Win+Alt+N`, not `Win+Shift+N`.** With `Win` sending
Option, macOS treats `Option+Shift+1` as its dead-key layer and emits `⁄`
rather than registering a modifier combination. Krohnkite's `Meta+Shift+N` has
no clean equivalent, so `amethyst.yml` uses `mod2` (Option+Control) — which is
`Win+Alt` under the fingers.

**Close window is `Ctrl+W`.** `Cmd+W` is the macOS convention and it isn't
rebound; after the rotation it lands under the physical Ctrl key, which is
where a Linux hand already reaches for close.

### Modifier rotation

`hidutil` applies a three-key rotation, not a swap:

| Physical key | Sends | Used for |
| --- | --- | --- |
| Ctrl (pinky) | Command | copy, paste, tabs, close |
| Win / Super | Option | launcher, desktop switching, window management |
| Alt (by space) | Control | free for per-app shortcuts |

This assumes a PC keyboard. `hidutil` applies it to every attached keyboard,
including a laptop's built-in one whose keys are already in the Mac order this
rotation is undoing.

### The one binding the rotation inverts

The rotation works because macOS uses Command wherever Linux uses Control, so
`Ctrl+C`, `Ctrl+V`, `Ctrl+T` and `Ctrl+W` all stay under the same physical key.

Tab is the exception. macOS switches applications with `Cmd+Tab`, which Linux
does with `Alt+Tab` — the one common binding where macOS uses Command for
something Linux does with Alt. Left alone, the rotation swaps the two round:

| | Linux (PC keyboard) | After the rotation alone |
| --- | --- | --- |
| physical `Ctrl+Tab` | next tab in app | **switch applications** |
| physical `Alt+Tab` | switch windows | **next tab in app** |

`setup-macos` installs Karabiner-Elements and the conf repo ships a complex
modification that swaps them back:

| Physical keys | Rotation alone | With the Karabiner rule |
| --- | --- | --- |
| `Alt+Tab` | next tab in app | **switch applications** |
| `Ctrl+Tab` | switch applications | **next tab in app** |

Both directions are mapped, and that matters. Remapping only `Alt+Tab` would
put application switching on the physical Alt key without taking it off the
physical Ctrl key, leaving next-tab with no physical keys at all. Shift
variants are mapped alongside each, so `Shift+Alt+Tab` cycles the switcher
backwards and `Shift+Ctrl+Tab` goes to the previous tab.

**This is the one part of the setup that a managed Mac can refuse.** Karabiner
installs a driver extension, and an MDM profile can block system extensions
outright — which is why the key mapping table qualifies both Tab rows. It's
free and open source, so there's no cost beyond disk, but it is a heavier
commitment than an ordinary app: a driver extension loading at boot plus a
background service, and a macOS upgrade can require re-approving the
extension. If it's blocked, fails, or is uninstalled, the keyboard keeps
working — the `hidutil` rotation is independent of it — and the only effect is
that the two Tab bindings revert to the "rotation alone" column above.

The rule maps left Alt+Tab to **`left_control`**+Tab, which reads wrong until
you follow the layering: Karabiner grabs the keyboard and sees the *physical*
key, and its output then passes through the `hidutil` rotation. So it has to
name the key the rotation turns into Command — left Control. Naming
`left_command` would come out as Option.

Karabiner needs three things done by hand, none of them scriptable: its driver
extension approved, Input Monitoring granted, and the rule enabled under
Complex Modifications > Add rule. Until then Alt+Tab keeps switching tabs. The
full reasoning, and what to flip if the layering differs on your macOS
version, is in the conf repo's `config/karabiner/README.md`.

The reciprocal mapping works the same way in reverse: physical Ctrl emits
`left_option`, which the rotation turns back into Control. Karabiner doesn't
feed its own output through its manipulators, so the two directions don't
chase each other.

Only left Alt is mapped; right Alt stays a plain modifier.

## How desktop switching works

macOS has no public API to switch Spaces — nothing can say "go to desktop 3".
The only scriptable route is to hijack the system's own shortcut registry.

`com.apple.symbolichotkeys` is the preference domain behind System Settings >
Keyboard > Keyboard Shortcuts. Its `AppleSymbolicHotKeys` dictionary is keyed
by integer IDs, one per built-in action:

| ID | Action |
| --- | --- |
| 64 | Spotlight |
| 65 | Finder search window (disabled here, to free Option+Space) |
| 118–126 | Switch to Desktop 1–9 |

Each entry carries `enabled` plus `parameters = [ASCII code, virtual keycode,
modifier bitmask]`. The bitmask values are Shift 131072, Control 262144,
Option 524288, Command 1048576 — so the `524288` throughout `setup-macos` is
"Option, nothing else". The number-row virtual keycodes aren't sequential
(`1=18 2=19 3=20 4=21 5=23 6=22 7=26 8=28 9=25`), which is why the script
carries an explicit table.

The Dock reads this domain, so it's restarted after the writes.

### Reliability

Once live, these bindings are solid. They aren't a third-party grab layered on
top of macOS — they're the same registry the stock `Ctrl+1..9` uses, enforced
by WindowServer, so they beat every application and need no daemon running.

Getting them live is the fragile part:

- **cfprefsd caching.** `defaults write` doesn't reach the running
  WindowServer by itself. `activateSettings -u` is the nudge, but it's an
  unsupported private-framework binary that Apple is free to move. The script
  falls back to advising a logout, which always works.
- **System Settings write-back.** See above — quit it before running.
- **Spaces that don't exist.** The write succeeds and the key does nothing.
  This is the most common apparent failure.
- **Per-display numbering.** With "Displays have separate Spaces" enabled,
  desktop numbers are per-display, so `Option+5` can land somewhere
  unexpected on a multi-monitor setup.

The script pins the Spaces order (`mru-spaces false`) because "Automatically
rearrange Spaces based on most recent use" is on by default and reorders the
desktops behind the numbered bindings.

To check the current state:

```sh
defaults read com.apple.symbolichotkeys AppleSymbolicHotKeys   # bindings
defaults read com.apple.spaces                                 # Spaces
```

## What doesn't carry over

These are macOS platform limits. No window manager fixes them.

**Window decorations.** There is no equivalent of KWin's "No titlebar and
frame" rule. Every tile keeps its titlebar and rounded corners. Only per-app
opt-outs exist — kitty, Alacritty and iTerm2 can hide their own.

**Exact sizing.** Krohnkite sets geometry inside KWin. Amethyst goes through
the Accessibility API, so applications can refuse or round a requested size:
terminals that snap to a character grid, Electron and Java apps, and anything
with a minimum size will leave gaps or overlap.

**Relayout performance.** Accessibility calls are synchronous round-trips per
window, so retiling is visibly slower than Krohnkite's, and one unresponsive
application stalls the whole relayout.

**Space-switch animation** can't be disabled. Turning on Reduce Motion makes
it a crossfade rather than a slide, which is faster and less distracting.

**Focus follows mouse.** The script explicitly turns Amethyst's off, so this
is the one KDE behavior that's deliberately *not* reproduced.

Amethyst hit-tests only the windows it tracks and then focuses the topmost
match. An overlay it doesn't track — a Chrome extension popover, a panel that
floats by the `float-small-windows` rule — is invisible to that test, so the
window *underneath* the overlay wins and gets focused, which deactivates the
overlay's app and makes the overlay dismiss itself. Popovers close the instant
the pointer reaches them. It's [ianyh/Amethyst#277][amethyst-277], open since
2015.

KWin doesn't have this problem: `FocusFollowsMouse` exempts popups, which is
exactly why `setup-kde` picks it over `FocusUnderMouse`. Amethyst has no such
exemption, no dwell delay, and no per-app exclusions, so there's no setting
that softens it — the only fix is to leave it off.

There's also no equivalent of KWin's `NextFocusPrefersMouse` or its
focus-stealing prevention levels.

[amethyst-277]: https://github.com/ianyh/Amethyst/issues/277

**Dim inactive windows.** No macOS equivalent of KWin's `diminactive` effect.
Two ways to get the cue back, neither installed or configured by the script:

- **JankyBorders** — `brew install borders`. Free and open source. Draws a
  colored border around the focused window instead of dimming the others.
  Works with SIP fully enabled because it injects into nothing. This is the
  practical choice.
- **HazeOver** — paid (around $10 one-time, also on Setapp). Actually dims
  the inactive windows, which is closer to the KDE behavior.

Both run as a small always-on process. Neither touches shell startup, so
there's no latency cost on a new prompt.


## Troubleshooting

**`Option+5..9` does nothing.** Fewer than nine Spaces exist on that display.
Create the rest in Mission Control; re-running `setup-macos` reports the count
per display.

**Shortcuts reverted after the run.** System Settings was open and wrote its
cached copy back. Quit it and re-run.

**Amethyst doesn't tile anything.** Accessibility access wasn't granted, or
was reset by an update. Re-grant it under System Settings > Privacy &
Security > Accessibility.

**Keyboard layout or modifiers unchanged.** Those are read by the login
session — log out and back in.

**Popovers and menus dismiss themselves as the pointer reaches them.**
Amethyst's focus-follows-mouse is on. `setup-macos` turns it off, but the
Preferences checkbox (Tweaks > Focus follows mouse) sets it back, and Amethyst
flushes its preferences on quit — so turn it off in the UI, or quit Amethyst
*before* writing the setting:

```sh
killall Amethyst
defaults write com.amethyst.Amethyst focus-follows-mouse -bool false
open -a Amethyst
```

See [focus follows mouse](#what-doesnt-carry-over) above for why it can't be
made to work.

**Numbered desktops switch to the wrong one.** The Spaces order drifted.
`setup-macos` pins it, but verify "Automatically rearrange Spaces based on
most recent use" is still off in Mission Control settings.

## Window manager evaluation

Three tiling window managers are realistic on macOS. The decisive question is
how each one handles Spaces, because that determines whether a nine-desktop
workflow survives at all.

### Amethyst

Uses native macOS Spaces and tiles within whichever is current. Space
*switching* isn't its job — that's symbolichotkeys, above. It can throw a
window to a Space, which is the part that matters.

**Pros**
- Throwing windows to a Space works with SIP fully enabled.
- Layout model is a cycled list of named layouts — a direct match for
  Krohnkite's Tile / ThreeColumn / Columns / Monocle.
- Single app, no daemon, no separate hotkey program, YAML config.
- No SIP or boot-security changes of any kind.

**Cons**
- Throw-to-space relies on private APIs and has been flaky across macOS
  releases.
- Fixed feature set — no scripting or query interface.
- Weaker per-app rules than the alternatives.

### yabai

The most capable of the three, but its best features are behind a scripting
addition that injects into the Dock, which needs SIP partially disabled *and*
the boot security policy lowered to Reduced Security.

**Pros**
- With the scripting addition: real Space create/destroy/focus, window
  opacity and shadows, sticky windows.
- Excellent scripting surface — `yabai -m query`, event signals.
- Fine-grained gaps, padding, and per-app rules.

**Cons**
- **With SIP enabled, it cannot move a window to another Space or focus one.**
  That removes the whole move-to-desktop workflow with no keyboard
  workaround.
- SIP changes are commonly blocked on managed Macs: on Apple Silicon,
  lowering the boot security policy requires a Volume Owner account, and
  every MDM/EDR agent reports SIP state as a compliance attribute.
- The scripting addition breaks on macOS major releases until updated, and
  SIP must be re-disabled after some updates.
- BSP tiling is a different mental model from Krohnkite's layout cycle.

### AeroSpace

Rejects native Spaces entirely, emulating workspaces by moving windows to
far off-screen coordinates.

**Pros**
- Instant, animation-free workspace switching.
- Workspace count is config, not something created by hand in Mission
  Control.
- No SIP changes, no symbolichotkeys, no Dock restarts.
- i3-style tiling with a coherent config language.

**Cons**
- macOS still believes every window is on one Space, so **Cmd+Tab lists
  windows from workspaces you aren't looking at** and Mission Control shows
  all of them at once.
- Native-fullscreen apps behave oddly.
- Tools that query window position — screen recording, some accessibility
  software — can get confused.

### Recommendation: Amethyst

For a nine-desktop workflow on a Mac where SIP can't be touched:

- **yabai is out.** Without the scripting addition it can't move a window to a
  Space at all, which is a hard regression against the Krohnkite setup, not a
  trade-off.
- **AeroSpace is out** on the Cmd+Tab behavior. Breaking the system app
  switcher to gain faster workspace switching is a bad trade when the
  switching already works.
- **Amethyst keeps the workflow intact** and matches Krohnkite's layout model
  one-for-one. It's also what `amethyst.yml` and `setup-macos` already target.

If SIP restrictions ever lift, yabai plus skhd becomes the closest overall
match to Krohnkite — but that's a boot-security change, not a preference.
