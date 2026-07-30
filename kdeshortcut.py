#!/usr/bin/env python3
# Apply KDE global shortcuts to the *running* kglobalaccel, so they work
# without logging out.
#
# kwriteconfig6 edits kglobalshortcutsrc behind kglobalaccel's back. The
# daemon holds the whole shortcut registry in memory and treats the file as
# its own serialization, so a file edit changes nothing until the daemon
# reloads it -- which it only does at startup, i.e. at the next login. System
# Settings doesn't have this problem because it doesn't edit the file: it
# calls the daemon, which re-grabs the key and then persists.
#
# This does the same call System Settings does (setForeignShortcutKeys), then
# reads the binding back out of the daemon so a shortcut that didn't take is
# reported now instead of silently deferring to the next login.
#
# Usage:
#     kdeshortcut.py <component> <action> <keys> [label]
#     kdeshortcut.py --batch [<file>]
#     kdeshortcut.py --check <component> <action> <keys> [label]
#
# --batch reads one shortcut per line from <file> (default stdin) as
# tab-separated component, action, keys, and optional label; blank lines and
# #-comments are skipped. --check only reads the daemon back and reports,
# changing nothing.
#
# <keys> is a shortcut in the form KDE writes it -- "Meta+T", "Meta+Shift+F1",
# and note that KDE records shifted characters as the character produced
# ("Meta+!", not "Meta+Shift+1"). "none" (or an empty string) unbinds.
#
# Exit status:
#     0  every shortcut is live in the running session
#     1  at least one shortcut did not take (details on stderr)
#     2  usage error
#     3  the daemon can't be reached at all -- no D-Bus binding available, no
#        session bus, or kglobalaccel not running. The caller should fall back
#        to telling the user to log out; nothing was changed.

import os
import re
import subprocess
import sys

HELP = """Usage: kdeshortcut.py [--check] [--quiet] <component> <action> <keys> [label]
       kdeshortcut.py [--check] [--quiet] --batch [<file>]

Apply KDE global shortcuts to the running kglobalaccel, so they take effect
without logging out.

Arguments:
  component  kglobalaccel component, e.g. kwin, plasmashell, or a launcher's
             .desktop file name
  action     action ID within that component, e.g. "Window Close", _launch
  keys       shortcut as KDE writes it, e.g. Meta+T, Meta+Shift+F1, Meta+!
             ("none" or an empty string unbinds)
  label      optional human-readable name for the action

Options:
  --batch    read tab-separated component/action/keys/label lines from <file>
             (default stdin); blank lines and #-comments are skipped
  --check    report what the daemon currently holds, changing nothing
  --quiet    only report failures
  --backend  force a D-Bus backend: gdbus or dbus-python (default: whichever
             works, gdbus first)
  -h, --help show this help and exit

Exit status:
  0  every shortcut is live in the running session
  1  at least one shortcut did not take
  2  usage error
  3  kglobalaccel could not be reached; nothing was changed
"""

# kglobalaccel's own D-Bus identity. In Plasma 6 the daemon is embedded in
# KWin, but it still owns this service name -- that's how System Settings
# reaches it -- so there's nothing KWin-specific to special-case here.
SERVICE = 'org.kde.kglobalaccel'
OBJECT = '/kglobalaccel'
INTERFACE = 'org.kde.KGlobalAccel'

# Qt6 keyboard modifier bits (Qt::KeyboardModifier).
MODIFIERS = {
    'shift': 0x02000000,
    'ctrl': 0x04000000,
    'control': 0x04000000,
    'alt': 0x08000000,
    'meta': 0x10000000,
    # KDE writes the Super/Windows key as Meta; accept the aliases people
    # type so a hand-edited batch file doesn't fail for a spelling.
    'super': 0x10000000,
    'win': 0x10000000,
}

# Qt6 Qt::Key values for keys with no printable character. Printable ASCII
# needs no table -- those Qt::Key values are the character's own code point,
# which keycode() relies on.
NAMED_KEYS = {
    'escape': 0x01000000,
    'esc': 0x01000000,
    'tab': 0x01000001,
    'backtab': 0x01000002,
    'backspace': 0x01000003,
    'return': 0x01000004,
    'enter': 0x01000005,
    'insert': 0x01000006,
    'ins': 0x01000006,
    'delete': 0x01000007,
    'del': 0x01000007,
    'pause': 0x01000008,
    'print': 0x01000009,
    'sysreq': 0x0100000A,
    'clear': 0x0100000B,
    'home': 0x01000010,
    'end': 0x01000011,
    'left': 0x01000012,
    'up': 0x01000013,
    'right': 0x01000014,
    'down': 0x01000015,
    'pageup': 0x01000016,
    'prior': 0x01000016,
    'pagedown': 0x01000017,
    'next': 0x01000017,
    'space': 0x20,
    'menu': 0x01000055,
    'help': 0x01000058,
}

# Qt::Key_F1; F2..F35 follow consecutively.
KEY_F1 = 0x01000030
MAX_FUNCTION_KEY = 35


class ShortcutError(Exception):
    """A shortcut string that can't be turned into Qt keycodes."""


def keycode(token):
    """Map one key name ("T", "Return", "F3", "\\") to its Qt::Key value."""
    key = token.strip()
    if not key:
        raise ShortcutError('empty key name')

    # Shortcuts come through in the form kglobalshortcutsrc holds them, where
    # a comma or a backslash in the key is backslash-escaped: KConfig reads
    # the value with readEntry(QStringList), so an unescaped comma would split
    # the entry into a fourth field and be discarded. The escape belongs to
    # that file format, not to the key, so drop it before looking the key up.
    if len(key) == 2 and key.startswith('\\'):
        key = key[1:]

    lowered = key.lower()
    if lowered in NAMED_KEYS:
        return NAMED_KEYS[lowered]

    match = re.fullmatch(r'f([0-9]+)', lowered)
    if match:
        number = int(match.group(1))
        if not 1 <= number <= MAX_FUNCTION_KEY:
            raise ShortcutError('no such function key: %s' % key)
        return KEY_F1 + number - 1

    if len(key) == 1:
        # Qt::Key values for printable ASCII are the code point of the
        # *uppercase* character: Qt::Key_A is 0x41, and there is no Key_a.
        # Non-ASCII (a dead key, a national layout character) has no stable
        # Qt::Key we can compute, so refuse rather than send a wrong code.
        char = key.upper()
        if ord(char) > 0x7E:
            raise ShortcutError('non-ASCII key not supported: %s' % key)
        return ord(char)

    raise ShortcutError('unrecognized key name: %s' % key)


def parse_shortcut(text):
    """Parse "Meta+Shift+F1" into a list of Qt keycodes (one per sequence).

    Returns [] for an unbind, which is what the daemon wants for "no keys".
    """
    shortcut = (text or '').strip()
    if not shortcut or shortcut.lower() == 'none':
        return []

    # '+' separates modifiers from the key, but is also a key name itself
    # ("Meta++"), so a trailing '+' is the key rather than an empty token.
    if shortcut.endswith('+'):
        modifier_text, key = shortcut[:-1], '+'
    else:
        modifier_text, _, key = shortcut.rpartition('+')

    modifiers = 0
    for part in modifier_text.split('+'):
        if not part.strip():
            continue
        name = part.strip().lower()
        if name not in MODIFIERS:
            raise ShortcutError('unrecognized modifier: %s' % part)
        modifiers |= MODIFIERS[name]

    return [modifiers | keycode(key)]


def format_keys(keys):
    """Render keycodes back for reporting. Exact spelling doesn't matter --
    this is only ever shown to a human comparing what was asked vs. what the
    daemon holds, so the raw codes are more honest than a lossy round trip."""
    if not keys:
        return 'none'
    return '+'.join(str(key) for key in keys)


class DbusPythonBackend:
    """dbus-python: preferred, since it marshals a(ai) natively."""

    name = 'dbus-python'

    def __init__(self):
        import dbus

        self._dbus = dbus
        bus = dbus.SessionBus()
        proxy = bus.get_object(SERVICE, OBJECT)
        self._iface = dbus.Interface(proxy, INTERFACE)

    def _sequences(self, keys):
        dbus = self._dbus
        # a(ai): array of QKeySequence, each a struct wrapping an int array.
        return dbus.Array(
            [dbus.Struct((dbus.Array([dbus.Int32(key) for key in keys], signature='i'),))],
            signature='(ai)',
        ) if keys else dbus.Array([], signature='(ai)')

    def set_keys(self, action_id, keys):
        self._iface.setForeignShortcutKeys(
            self._dbus.Array(action_id, signature='s'), self._sequences(keys))

    def get_keys(self, action_id):
        result = self._iface.shortcutKeys(self._dbus.Array(action_id, signature='s'))
        return [int(key) for sequence in result for key in sequence]


class GdbusBackend:
    """gdbus: GVariant's text format can express a(ai), which qdbus6 and
    dbus-send cannot -- neither can build a struct argument at all."""

    name = 'gdbus'

    def __init__(self):
        if not which('gdbus'):
            raise RuntimeError('gdbus not found')
        # Fail here rather than on the first shortcut, so the caller gets
        # "can't reach the daemon" instead of a list of failed shortcuts.
        self._call('org.freedesktop.DBus.Peer.Ping', [])

    def _call(self, method, args):
        command = ['gdbus', 'call', '--session', '--dest', SERVICE,
                   '--object-path', OBJECT, '--method', method] + args
        result = subprocess.run(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout).strip()
                               or 'gdbus call failed: %s' % method)
        return result.stdout

    def _action_id(self, action_id):
        return '[%s]' % ', '.join(gvariant_string(field) for field in action_id)

    def set_keys(self, action_id, keys):
        if keys:
            # A one-element GVariant tuple needs the trailing comma.
            sequences = '[([%s],)]' % ', '.join(str(key) for key in keys)
        else:
            # An empty list is ambiguous in GVariant text; annotate the type.
            sequences = '@a(ai) []'
        self._call('%s.setForeignShortcutKeys' % INTERFACE,
                   [self._action_id(action_id), sequences])

    def get_keys(self, action_id):
        output = self._call('%s.shortcutKeys' % INTERFACE,
                            [self._action_id(action_id)])
        return [int(match) for match in re.findall(r'-?\d+', output)]


def gvariant_string(text):
    """Quote a string for GVariant text format."""
    return "'%s'" % text.replace('\\', '\\\\').replace("'", "\\'")


def which(program):
    for directory in os.environ.get('PATH', '').split(os.pathsep):
        candidate = os.path.join(directory, program)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


BACKENDS = (GdbusBackend, DbusPythonBackend)


def open_backend(wanted=None):
    """Return a working D-Bus backend, or raise RuntimeError describing why
    none is usable. Reasons are collected so the message names every thing
    that was tried -- "no D-Bus binding" is not actionable on its own.

    gdbus is tried first because it needs no Python D-Bus binding installed,
    and because it's the path the tests cover; dbus-python is the fallback for
    a box with the binding but without glib's CLI tools.
    """
    reasons = []
    for factory in BACKENDS:
        if wanted and factory.name != wanted:
            continue
        try:
            return factory()
        except ImportError:
            reasons.append('%s: not installed' % factory.name)
        except Exception as error:  # noqa: BLE001 - reported, never swallowed
            reasons.append('%s: %s' % (factory.name, error))
    if not reasons:
        raise RuntimeError('unknown backend: %s' % wanted)
    raise RuntimeError('; '.join(reasons))


def apply_shortcut(backend, component, action, keys_text, label, check_only):
    """Set one shortcut and confirm the daemon holds it. Returns (ok, note)."""
    wanted = parse_shortcut(keys_text)

    # actionId is kglobalaccel's 4-field identity: unique and friendly names
    # for both the component and the action. Only the two unique names are
    # matched against the registry -- the friendly names are display text the
    # daemon uses when it has to create an entry -- so the component's unique
    # name stands in for its friendly name, which this script has no way to
    # know, and the label describes the action.
    action_id = [component, action, component, label or action]

    if not check_only:
        backend.set_keys(action_id, wanted)

    live = backend.get_keys(action_id)
    if live == wanted:
        return True, format_keys(wanted)

    if not live:
        # setForeignShortcutKeys only mutates actions already registered in
        # the session. An action the daemon has never heard of stays absent,
        # which is the common case for a component that hasn't started yet.
        return False, ('daemon holds no binding -- action not registered in '
                       'this session, so it applies at next login')
    return False, ('daemon holds %s, wanted %s' % (format_keys(live), format_keys(wanted)))


def read_batch(stream):
    """Parse tab-separated component/action/keys/label lines."""
    entries = []
    for number, line in enumerate(stream, start=1):
        text = line.strip()
        if not text or text.startswith('#'):
            continue
        fields = line.rstrip('\n').split('\t')
        if len(fields) < 3:
            raise ShortcutError(
                'line %d: need tab-separated component, action, keys' % number)
        component, action, keys = fields[0], fields[1], fields[2]
        label = fields[3] if len(fields) > 3 else ''
        entries.append((component.strip(), action.strip(), keys.strip(), label.strip()))
    return entries


def usage(message=None):
    if message:
        sys.stderr.write('kdeshortcut.py: %s\n' % message)
    sys.stderr.write(
        'Usage: kdeshortcut.py [--check] <component> <action> <keys> [label]\n'
        '       kdeshortcut.py [--check] --batch [<file>]\n')
    return 2


def main(argv):
    check_only = False
    batch = False
    quiet = False
    wanted_backend = None
    args = []

    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == '--check':
            check_only = True
        elif argument == '--batch':
            batch = True
        elif argument == '--quiet':
            quiet = True
        elif argument == '--backend' or argument.startswith('--backend='):
            if argument == '--backend':
                index += 1
                if index >= len(argv):
                    return usage('--backend needs an argument')
                wanted_backend = argv[index]
            else:
                wanted_backend = argument.split('=', 1)[1]
        elif argument in ('-h', '--help'):
            sys.stdout.write(HELP)
            return 0
        elif argument.startswith('-') and argument != '-':
            return usage('unknown option: %s' % argument)
        else:
            args.append(argument)
        index += 1

    try:
        if batch:
            if len(args) > 1:
                return usage('--batch takes at most one file')
            if args and args[0] != '-':
                with open(args[0]) as stream:
                    entries = read_batch(stream)
            else:
                entries = read_batch(sys.stdin)
        else:
            if not 3 <= len(args) <= 4:
                return usage('expected <component> <action> <keys> [label]')
            entries = [(args[0], args[1], args[2], args[3] if len(args) > 3 else '')]
    except (ShortcutError, OSError) as error:
        sys.stderr.write('kdeshortcut.py: %s\n' % error)
        return 2

    if not entries:
        return 0

    try:
        backend = open_backend(wanted_backend)
    except RuntimeError as error:
        sys.stderr.write('kdeshortcut.py: cannot reach kglobalaccel (%s)\n' % error)
        return 3

    failures = 0
    for component, action, keys_text, label in entries:
        try:
            ok, note = apply_shortcut(backend, component, action, keys_text,
                                      label, check_only)
        except ShortcutError as error:
            ok, note = False, str(error)
        except Exception as error:  # noqa: BLE001 - one bad shortcut isn't fatal
            ok, note = False, str(error)

        if ok:
            if not quiet:
                sys.stdout.write('live  %s/%s -> %s\n' % (component, action, note))
        else:
            failures += 1
            sys.stderr.write('FAIL  %s/%s (%s): %s\n'
                             % (component, action, keys_text, note))

    if failures:
        sys.stderr.write('kdeshortcut.py: %d of %d shortcut(s) not live in this '
                         'session\n' % (failures, len(entries)))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
