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
  - [Focus follows mouse](#focus-follows-mouse)
  - [Layout model](#layout-model)
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

These are macOS platform limits — no window manager fixes them — with one
exception, focus follows mouse, which is Amethyst's own limitation and is
marked as such below.

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

**This one is Amethyst's, not the platform's.** yabai gets it right by asking
the window server what's under the pointer *first* and only then checking
whether it's a window it manages, so an overlay it doesn't track simply ends
the lookup. Amethyst filters to its tracked windows before the hit test, which
is what makes the overlay invisible. Same platform, opposite order. See
[focus follows mouse](#focus-follows-mouse) in the evaluation below.

There's also no equivalent of KWin's `NextFocusPrefersMouse` or its
focus-stealing prevention levels — that part *is* a platform limit.

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

Three tiling window managers are realistic on macOS. This used to turn on a
single question — whether Spaces survive with SIP enabled — because yabai
couldn't move a window to a Space without disabling it. That changed in yabai
7.1.25 (May 2026), so the comparison now rests on two things instead:
**the layout model** and **focus follows mouse**. Amethyst and yabai each win
one of them.

### Focus follows mouse

Both implement it; only one does it without breaking popovers, and the
difference is two lines of ordering.

yabai asks the window server what is under the pointer, then checks whether
that window is one it manages:

```c
SLSFindWindowAndOwner(g_connection, 0, 1, 0, &point, &window_point, &window_id, &window_cid);
return window_manager_find_window(wm, window_id);
```

A Chrome extension popover isn't a managed window, so the lookup returns
nothing and focus stays put.

Amethyst reverses it — `WindowsInformation.topWindowForScreenAtPoint` narrows
to its tracked windows *before* hit-testing, so an untracked overlay never
enters the comparison and the window underneath it wins. Focusing that window
deactivates the overlay's app, and the overlay dismisses itself. It has been
[ianyh/Amethyst#277][amethyst-277] since 2015, and there is no delay or
exclusion setting to soften it, so `setup-macos` turns the feature off.

### Layout model

The reverse asymmetry, and the bigger one.

Amethyst ships the Krohnkite set and cycles it from a key: `tall` is
master/stack, plus `3column-left`, `column`, `wide` and `fullscreen`. That's
`amethyst.yml`'s current layout list, and it maps one-for-one onto Krohnkite's
Tile / ThreeColumn / Columns / Monocle.

yabai has bsp, stack and float. None of those is master/stack — its `stack`
layout is tabbed stacking, where each window fills the space and you cycle
between them, not a main pane beside a column of others. Nor is one planned:
the algorithm is binary space partitioning throughout, and upstream considers
dwm-style master-stack layouts out of scope ([yabai#908][yabai-908]). The
workarounds are float mode with scripted grid placement — losing BSP and
padding — or signal-driven plugins that re-tile on every window event.

So this isn't a question of extensibility. The ordinary layouts this setup
already uses have no yabai equivalent.

Amethyst will also load user-written layouts as JavaScript from
`~/Library/Application Support/Amethyst/Layouts/`, each defining
`getFrameAssignments(windows, screenFrame, state, extendedFrames)` alongside
`commands` and `initialState`. Not needed for the layouts above — they're
built in — but it's there if the set ever isn't enough.

[yabai-908]: https://github.com/koekeishiya/yabai/issues/908

### Amethyst

Uses native macOS Spaces and tiles within whichever is current. Space
*switching* isn't its job — that's symbolichotkeys, above. It can throw a
window to a Space, which is the part that matters.

**Pros**
- Throwing windows to a Space works with SIP fully enabled.
- **Ships master/stack and column layouts**, cycled from a key — a direct
  match for Krohnkite's Tile / ThreeColumn / Columns / Monocle, and the one
  thing yabai can't reproduce. See [layout model](#layout-model) above.
- User-written layouts in JavaScript if the built-in set ever isn't enough.
- Single app, no daemon, no separate hotkey program, YAML config.
- No SIP or boot-security changes of any kind.

**Cons**
- **Focus follows mouse is unusable** and has to stay off; see
  [above](#focus-follows-mouse).
- Throw-to-space relies on private APIs and has been flaky across macOS
  releases.
- No scripting or query interface, so behavior can't be prototyped without
  rebuilding the app — and it's Swift and Xcode if you do.
- Weaker per-app rules than the alternatives.
- Quieter development than yabai: 0.24.3 in April 2026, in bursts.

### yabai

The most capable of the three. Some features are still behind a scripting
addition that injects into the Dock, needing SIP partially disabled *and* the
boot security policy lowered to Reduced Security — but moving windows between
Spaces is no longer one of them.

**7.1.25 (May 2026) restored throw-to-space with SIP enabled**, via
`SLSBridgedMoveWindowsToManagedSpaceOperation`, validated on macOS 26.4
([yabai#2788][yabai-2788]). That had been the single reason this setup ruled
yabai out, and it no longer holds. It's a private window-server call, so it
carries the same across-releases risk as Amethyst's equivalent — check it
against your own macOS version rather than assuming.

**Pros**
- Throw-to-space works with SIP enabled as of 7.1.25.
- **Focus follows mouse that doesn't dismiss popovers** — see
  [above](#focus-follows-mouse). The one thing Amethyst can't currently do.
- Excellent scripting surface — `yabai -m query`, event signals — so behavior
  can be prototyped in shell before any code is written.
- Fine-grained gaps, padding, and per-app rules.
- Actively developed: roughly monthly releases through 2026.
- Builds from source with Command Line Tools and `make`, no Xcode.

**Cons**
- **No master/stack or column layout, and none planned** — see
  [layout model](#layout-model). This is now the disqualifier.
- Keybindings need skhd, a second daemon with its own config.
- Space create/destroy, window opacity and sticky windows still need the
  scripting addition, so still SIP for those.
- SIP changes are commonly blocked on managed Macs: on Apple Silicon,
  lowering the boot security policy requires a Volume Owner account, and
  every MDM/EDR agent reports SIP state as a compliance attribute.
- Leans harder on private window-server APIs than Amethyst, so it breaks more
  often on macOS major releases.

[yabai-2788]: https://github.com/koekeishiya/yabai/issues/2788

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

Still Amethyst, but the reasoning has changed and it's now a genuine
trade rather than a walkover:

- **AeroSpace is out** on the Cmd+Tab behavior. Breaking the system app
  switcher to gain faster workspace switching is a bad trade when the
  switching already works.
- **yabai is out on layouts.** It has no master/stack and no column layout,
  and upstream doesn't intend to add them. Those are the layouts this setup
  uses daily, so it's a hard regression — the same *kind* of objection that
  used to be aimed at its Spaces handling, just relocated.
- **Amethyst wins on layouts and loses on focus.** It matches Krohnkite's
  layout model one-for-one, which is the thing in daily use; the price is
  focus follows mouse, which has to stay off.

What changed: yabai's throw-to-space limitation was the previous
disqualifier, and 7.1.25 removed it. It's now the better *codebase* — correct
focus handling, a scripting interface, C and `make` rather than Swift and
Xcode, more frequent releases — and it's still the wrong choice here, because
a layout engine is a much larger thing to add to yabai than a corrected hit
test is to add to Amethyst.

That last point is the live one. Amethyst's focus bug is a localized ordering
mistake in a single function, and yabai is a working reference for the fix, so
the gap is closable upstream. If it closes, Amethyst wins outright. If yabai
ever grows a non-BSP layout, this decision is worth reopening — the layout
model is the only thing keeping it out.
