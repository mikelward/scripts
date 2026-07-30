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
# Only actions kglobalaccel reports it already has are ever set. In Plasma 6
# the daemon runs inside kwin, so a call it mishandles doesn't just fail -- it
# can take the compositor down, and every client with it. Enumerating first
# (read-only) is what keeps a mutating call off an action that doesn't exist.
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

import contextlib
import fcntl
import os
import re
import subprocess
import sys
import tempfile

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
  --who KEYS report which component and action hold KEYS, e.g. --who Meta+T.
             Read-only; use it to find what is grabbing a key
  --quiet    only report failures
  --backend  force a D-Bus backend: gdbus or dbus-python (default: whichever
             works, gdbus first)
  --journal  file naming the shortcut currently being applied, so a call that
             takes kwin down can be identified afterwards. An entry left in it
             is skipped on every later run until --forget retires it. Defaults
             to $XDG_STATE_HOME/kdeshortcut.inflight; a mutating run always has
             one, and refuses to run if it can't be created
  --forget   retire the journal's entries so those shortcuts are attempted
             again. Use it once the cause is fixed
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


def default_journal_path():
    """Where the crash journal lives when --journal isn't given.

    A mutating run always has one: with no path, record() would be a no-op and
    a call that took kwin down would leave nothing to identify it -- the hole
    this whole mechanism exists to close.

    setup-kde passes this same path explicitly. Every entry point shares one
    journal on purpose: a marker names an action that kills the compositor,
    which is true of the action however it came to be applied.
    """
    state = os.environ.get('XDG_STATE_HOME') or os.path.join(
        os.path.expanduser('~'), '.local', 'state')
    return os.path.join(state, 'kdeshortcut.inflight')


class JournalError(Exception):
    """The crash journal couldn't be read or written.

    Fatal to the shortcut it was recording: the journal is what keeps a call
    that killed the compositor from being made again, so a mutating call without
    it is exactly what it exists to prevent.
    """


class DaemonGone(Exception):
    """A call returned an error and left the daemon unreachable.

    Raised so the batch stops there. Carrying on would call into a daemon
    that's already down, and -- worse -- would overwrite the journal entry
    naming the call that took it down, which is the one thing worth keeping.
    """


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


# A QKeySequence is four key slots, and the daemon reports all four: a
# one-key shortcut reads back as the key plus three empty slots. Empty is not
# always zero -- Qt::Key_unknown shows up too -- so a slot counts as real only
# if it's neither.
KEY_UNKNOWN = 0x01FFFFFF


def real_keys(keys):
    """Drop the empty tail slots from a sequence the daemon reported."""
    trimmed = list(keys)
    while trimmed and trimmed[-1] in (0, KEY_UNKNOWN):
        trimmed.pop()
    return trimmed


def holds_wanted(live, wanted):
    """Whether the daemon's reported sequence is the one that was asked for.

    Compared on the real slots only. The tail can hold padding this script
    doesn't get to predict -- an exact list comparison reported every correctly
    applied shortcut as a failure, which made the whole readback worthless.
    """
    return real_keys(live) == real_keys(wanted)


def format_keys(keys):
    """Render keycodes back for reporting. Exact spelling doesn't matter --
    this is only ever shown to a human comparing what was asked vs. what the
    daemon holds, so the raw codes are more honest than a lossy round trip."""
    if not keys:
        return 'none'
    return '+'.join(str(key) for key in keys)


# setForeignShortcut/shortcut rather than the current setForeignShortcutKeys/
# shortcutKeys pair: the newer methods take a(ai), an array of QKeySequence
# structs, and sending that from a generic D-Bus tool crashed kwin_wayland
# outright ("dbus: type invalid 0 not a basic type" -- the daemon's
# demarshaller reading past the end of the container). The older methods take a
# flat ai, which is the same QList<int> the daemon converts to and from
# internally (see intListFromShortcut/shortcutFromIntList in kglobalaccel), so
# there is no struct to get wrong. They're deprecated but still exported, and a
# deprecated call that can't take the compositor down beats a current one that
# can.
class DbusPythonBackend:
    """dbus-python: no subprocess, and it marshals ai natively."""

    name = 'dbus-python'

    def __init__(self):
        import dbus

        self._dbus = dbus
        bus = dbus.SessionBus()
        proxy = bus.get_object(SERVICE, OBJECT)
        self._iface = dbus.Interface(proxy, INTERFACE)
        self._peer = dbus.Interface(proxy, 'org.freedesktop.DBus.Peer')

    def set_keys(self, action_id, keys):
        self._iface.setForeignShortcut(
            self._dbus.Array(action_id, signature='s'),
            self._dbus.Array([self._dbus.Int32(key) for key in keys], signature='i'))

    def get_keys(self, action_id):
        result = self._iface.shortcut(self._dbus.Array(action_id, signature='s'))
        return [int(key) for key in result]

    def list_actions(self, component):
        result = self._iface.allActionsForComponent(
            self._dbus.Array(component_id(component), signature='s'))
        return {str(entry[1]) for entry in result if len(entry) > 1}

    def alive(self):
        try:
            self._peer.Ping()
        except Exception:  # noqa: BLE001 - any failure means "can't tell, assume gone"
            return False
        return True

    def holders(self, key):
        result = self._iface.getGlobalShortcutsByKey(self._dbus.Int32(key))
        return [(str(info[0]), str(info[2])) for info in result if len(info) > 2]


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
        # An empty list is ambiguous in GVariant text, so annotate the type.
        flat = '[%s]' % ', '.join(str(key) for key in keys) if keys else '@ai []'
        self._call('%s.setForeignShortcut' % INTERFACE,
                   [self._action_id(action_id), flat])

    def get_keys(self, action_id):
        output = self._call('%s.shortcut' % INTERFACE,
                            [self._action_id(action_id)])
        return [int(match) for match in re.findall(r'-?\d+', output)]

    def list_actions(self, component):
        output = self._call('%s.allActionsForComponent' % INTERFACE,
                            [self._action_id(component_id(component))])
        return {group[1] for group in parse_gvariant_string_lists(output)
                if len(group) > 1}

    def alive(self):
        try:
            self._call('org.freedesktop.DBus.Peer.Ping', [])
        except RuntimeError:
            return False
        return True

    def holders(self, key):
        # The deprecated flat-int form again: its argument is a plain i, where
        # globalShortcutsByKey takes a QKeySequence struct.
        output = self._call('%s.getGlobalShortcutsByKey' % INTERFACE, [str(key)])
        return parse_shortcut_infos(output)


def gvariant_string(text):
    """Quote a string for GVariant text format."""
    return "'%s'" % text.replace('\\', '\\\\').replace("'", "\\'")


def parse_gvariant_string_lists(text):
    """Pull the inner string lists out of gdbus's aas output.

    Matching the innermost brackets keeps each action's fields together, which
    membership testing over every quoted token in the reply would not: an
    action name can appear as some other action's friendly name.
    """
    groups = []
    for match in re.finditer(r'\[([^][]*)\]', text):
        items = re.findall(r"'((?:[^'\\]|\\.)*)'", match.group(1))
        if items:
            groups.append([item.replace("\\'", "'").replace('\\\\', '\\')
                           for item in items])
    return groups


def parse_shortcut_infos(text):
    """Pull (component, action) out of a KGlobalShortcutInfo reply.

    Each entry is (ssssssaiai): unique and friendly names for the component,
    the action and the context, then the keys. Only the first and third
    matter here, so this reads the six leading strings of each struct and
    ignores the int arrays -- enough for a diagnostic, and it can't be confused
    by a name that happens to look like a keycode.
    """
    field = r"'((?:[^'\\]|\\.)*)'"
    pattern = r'\(\s*' + r'\s*,\s*'.join([field] * 6)
    return [(match.group(1), match.group(3))
            for match in re.finditer(pattern, text)]


def component_id(component):
    """kglobalaccel only reads field 0 of an actionId when looking up a
    component, but send all four so a stricter build can't index past the end."""
    return [component, '', component, '']


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


class Journal:
    """Records the shortcut about to be applied, on disk, before the call.

    kglobalaccel is part of kwin in Plasma 6, so a call that kills the daemon
    takes the compositor down and every client with it -- including whatever
    terminal this was reporting to. A file is what survives to name the
    shortcut that was in flight.

    Every entry found at startup is therefore a shortcut some previous run did
    not come back from. Those are skipped and named, so one crash doesn't
    become a crash every run.

    They also accumulate: a marker outlives the run that reads it, and only
    --forget removes one. Clearing it once it had been read would mean the run
    after that retried the crashing call -- a crash every other run rather than
    every run. The in-flight entry is written alongside them, so a run that
    skips a known-bad shortcut still journals the ones it does attempt.

    A journal that can't be read or written fails closed. It isn't a diagnostic
    aid: it's what stops a call that killed the compositor from being made
    again, so mutating without it is the thing it exists to prevent. An
    unreadable file may be preserving exactly the marker that matters, and an
    unwritable one can't record the call about to be made.
    """

    def __init__(self, path):
        self.path = path
        self.poisoned = set()
        self.sealed = False
        # Set when the existing journal couldn't be read. Not raised here, so
        # --forget can still retire an unreadable file; main() fails closed on
        # it before anything mutating.
        self.unreadable = None
        self._load()

    def _load(self):
        """Read the markers. Called again inside transaction(), under the lock,
        so a concurrent run's markers are seen rather than a stale snapshot."""
        self.poisoned = set()
        self.unreadable = None
        if not self.path:
            return
        try:
            with open(self.path) as stream:
                lines = stream.read().splitlines()
        except FileNotFoundError:
            # No journal yet: no previous run left anything in flight.
            return
        except OSError as error:
            self.unreadable = str(error)
            return
        for line in lines:
            fields = line.rstrip('\n').split('\t')
            if len(fields) >= 2 and fields[0] and fields[1]:
                self.poisoned.add((fields[0], fields[1]))

    @contextlib.contextmanager
    def _locked(self):
        """Hold the exclusive lock, nothing else.

        Separate from transaction() because --forget has to take the same lock
        while still working on a journal it can't read, which transaction()
        refuses.
        """
        if not self.path:
            yield
            return
        try:
            handle = open(self.path + '.lock', 'w')
        except OSError as error:
            raise JournalError('cannot open the journal lock for %s: %s'
                               % (self.path, error))
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield
        finally:
            # Closing releases the lock, including on the raising paths.
            handle.close()

    @contextlib.contextmanager
    def transaction(self):
        """Hold an exclusive lock across one record/call/clear cycle.

        Replacing each write atomically isn't enough when two runs overlap: both
        would snapshot the same markers, and the second record() would replace
        the first's in-flight entry. If the first call then killed kwin, the
        surviving journal would name the wrong action -- and the real one would
        be retried. The lock makes the whole cycle exclusive, and the markers are
        re-read inside it so this run sees what the other one wrote.

        The wait is unbounded on purpose: a holder that dies -- which is what a
        compositor crash does to it -- releases the lock through the kernel, so
        there's nothing to time out for.
        """
        with self._locked():
            self._load()
            if self.unreadable:
                raise JournalError('cannot read %s: %s'
                                   % (self.path, self.unreadable))
            yield

    def seal(self):
        """Keep the file as it stands: it names the call that killed the daemon,
        so no later record() or clear() may rewrite it."""
        self.sealed = True

    def _write(self, entries):
        """Replace the file with these entries, or remove it when there are
        none. Raises JournalError so the caller can decide -- which for record()
        means not making the call it was about to journal.

        Written to a temporary file and renamed over the original, never
        truncated in place: a write that fails partway -- out of space, a bad
        fsync, or the compositor taking this process down mid-update -- would
        otherwise erase the existing markers or leave a half-written line that
        the next run parses as absent, and retry a shortcut already known to
        kill kwin.
        """
        if not entries:
            try:
                os.remove(self.path)
            except FileNotFoundError:
                pass
            except OSError as error:
                raise JournalError('cannot remove %s: %s' % (self.path, error))
            return

        directory = os.path.dirname(self.path) or '.'
        try:
            handle, temporary = tempfile.mkstemp(
                dir=directory, prefix=os.path.basename(self.path) + '.')
        except OSError as error:
            raise JournalError('cannot write %s: %s' % (self.path, error))
        try:
            with os.fdopen(handle, 'w') as stream:
                for component, action in entries:
                    stream.write('%s\t%s\n' % (component, action))
                stream.flush()
                os.fsync(stream.fileno())
            # The rename is what makes the new contents visible, so until it
            # succeeds the previous markers are still the journal.
            os.replace(temporary, self.path)
        except OSError as error:
            try:
                os.remove(temporary)
            except OSError:
                # Reported below either way; a leftover temp file is the lesser
                # problem and naming both errors would obscure the real one.
                pass
            raise JournalError('cannot write %s: %s' % (self.path, error))

    def record(self, component, action):
        """Name the call about to be made, keeping every existing marker.

        Propagates JournalError: without the marker written, a call that takes
        kwin down leaves nothing to identify it and the next run retries it, so
        the call must not be made.
        """
        if not self.path or self.sealed:
            return
        self._write(sorted(self.poisoned) + [(component, action)])

    def clear(self):
        """Called once a mutating call has returned: nothing is in flight. The
        markers stay -- only --forget retires those.

        Failure is reported but not raised: the call already returned, so
        there's nothing left to prevent. The cost is a stale marker that skips a
        good shortcut next run, which --forget retires.
        """
        if not self.path or self.sealed:
            return
        try:
            self._write(sorted(self.poisoned))
        except JournalError as error:
            sys.stderr.write('kdeshortcut.py: %s\n' % error)

    def forget(self):
        """Retire the markers this journal was holding, so those shortcuts are
        attempted again. Returns (retired, kept).

        Under the same lock as a transaction: otherwise this could delete an
        entry another process had just journaled and not yet returned from, and
        if that call took kwin down there'd be nothing left to name it.

        Only the markers read at startup are retired. Waiting for the lock can
        take as long as someone else's D-Bus call, and if that call is the one
        that kills kwin, its marker appears while this waits -- writing an empty
        file on acquiring the lock would delete the very evidence the crash just
        produced. Retiring is a decision about the markers the user was told
        about, so anything newer is kept.
        """
        with self._locked():
            retiring = set(self.poisoned)
            self._load()
            if self.unreadable:
                # Nothing can be compared, so there's no way to tell a fresh
                # marker from an old one. Removing it is the documented way out
                # of an unreadable journal, and main() says the set is unknown.
                self.poisoned = set()
                self.sealed = False
                self.unreadable = None
                self._write([])
                return sorted(retiring), []
            kept = self.poisoned - retiring
            self.sealed = False
            self._write(sorted(kept))
            self.poisoned = set(kept)
            return sorted(retiring), sorted(kept)


def apply_shortcut(backend, entry, check_only, registered, journal):
    """Set one shortcut and confirm the daemon holds it. Returns (ok, note)."""
    component, action, keys_text, label = entry
    wanted = parse_shortcut(keys_text)

    # actionId is kglobalaccel's 4-field identity: unique and friendly names
    # for both the component and the action. Only the two unique names are
    # matched against the registry -- the friendly names are display text the
    # daemon uses when it has to create an entry -- so the component's unique
    # name stands in for its friendly name, which this script has no way to
    # know, and the label describes the action.
    action_id = [component, action, component, label or action]

    # A marker blocks mutating, not reading. --check makes no call that could
    # repeat the crash, and after one this is exactly the shortcut you want to
    # ask the daemon about -- same reasoning as letting --check past an
    # unreadable journal.
    poisoned = (component, action) in journal.poisoned
    if poisoned and not check_only:
        return False, ('skipped: a previous run did not return from applying '
                       'this one, which is what would take kwin down with it '
                       '(--forget to retry it)')

    # Never mutate an action the daemon doesn't already have. setShortcutKeys
    # is only defined for a registered action, and since the daemon lives
    # inside kwin, a call it mishandles costs the whole session -- so an
    # unregistered action is reported, not attempted.
    if action not in registered:
        if not wanted:
            # Nothing is bound, which is all an unbind was asking for.
            return True, 'not registered, nothing to unbind'
        return False, ('daemon has no such action, so it was not called; the '
                       'shortcut applies at next login')

    if not check_only:
        # One transaction: nothing else may rewrite the journal between naming
        # this call and the call returning.
        with journal.transaction():
            # Re-checked under the lock, against markers just re-read: a
            # concurrent run may have journaled this very action as crashing
            # since this one started.
            if (component, action) in journal.poisoned:
                return False, ('skipped: a concurrent run did not return from '
                               'applying this one (--forget to retry it)')
            journal.record(component, action)
            try:
                backend.set_keys(action_id, wanted)
            except Exception as error:
                # Control came back, so this call didn't take the process down.
                # Keep the entry only when the daemon itself is gone -- that's
                # the case it exists to catch. An ordinary transient error must
                # not poison the shortcut, or one failed call would refuse to
                # apply it ever again.
                if backend.alive():
                    journal.clear()
                    raise
                journal.seal()
                raise DaemonGone('%s (the daemon stopped answering)' % error)
            journal.clear()

    live = backend.get_keys(action_id)
    # Under --check a marker is still worth saying: the daemon may well hold the
    # shortcut, and the reason an apply would skip it isn't otherwise visible.
    marked = ' (journaled as crashing; --forget to retry it)' if poisoned else ''
    if holds_wanted(live, wanted):
        return True, format_keys(real_keys(live)) + marked
    return False, ('daemon holds %s, wanted %s%s'
                   % (format_keys(live), format_keys(wanted), marked))


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
    journal_path = None
    who = None
    forget = False
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
        elif argument == '--who' or argument.startswith('--who='):
            if argument == '--who':
                index += 1
                if index >= len(argv):
                    return usage('--who needs a shortcut')
                who = argv[index]
            else:
                who = argument.split('=', 1)[1]
        elif argument == '--forget':
            forget = True
        elif argument == '--journal' or argument.startswith('--journal='):
            if argument == '--journal':
                index += 1
                if index >= len(argv):
                    return usage('--journal needs an argument')
                journal_path = argv[index]
            else:
                journal_path = argument.split('=', 1)[1]
        elif argument in ('-h', '--help'):
            sys.stdout.write(HELP)
            return 0
        elif argument.startswith('-') and argument != '-':
            return usage('unknown option: %s' % argument)
        else:
            args.append(argument)
        index += 1

    if who is not None:
        try:
            keys = parse_shortcut(who)
        except ShortcutError as error:
            sys.stderr.write('kdeshortcut.py: %s\n' % error)
            return 2
        if not keys:
            return usage('--who needs a shortcut, not an unbind')
        try:
            backend = open_backend(wanted_backend)
        except RuntimeError as error:
            sys.stderr.write('kdeshortcut.py: cannot reach kglobalaccel (%s)\n'
                             % error)
            return 3
        holders = backend.holders(keys[0])
        if not holders:
            sys.stdout.write('nothing holds %s\n' % who)
        for component, action in holders:
            sys.stdout.write('%s holds %s/%s\n' % (who, component, action))
        return 0

    # Retiring markers is a file operation, so it needs no daemon and happens
    # before anything else -- including on a bare --forget with no shortcut to
    # apply, which is how a user clears one after fixing the cause.
    # A mutating run always gets a journal: without one, record() is a no-op and
    # a call that takes kwin down leaves nothing to identify it. --check needs
    # none, since it makes no such call.
    if journal_path is None and (forget or not check_only):
        journal_path = default_journal_path()
        directory = os.path.dirname(journal_path)
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as error:
            sys.stderr.write('kdeshortcut.py: cannot create %s for the crash '
                             'journal (%s)\n' % (directory, error))
            sys.stderr.write('kdeshortcut.py: refusing to apply shortcuts '
                             'without one -- pass --journal to put it '
                             'elsewhere\n')
            return 1

    if forget:
        retired = Journal(journal_path)
        if retired.unreadable:
            # Worth saying: the names being retired can't be listed, so this is
            # retiring an unknown set rather than the ones printed below.
            sys.stderr.write('kdeshortcut.py: cannot read %s (%s); retiring it '
                             'anyway\n' % (journal_path, retired.unreadable))
        try:
            gone, kept = retired.forget()
        except JournalError as error:
            sys.stderr.write('kdeshortcut.py: %s\n' % error)
            return 1
        for component, action in gone:
            sys.stdout.write('forgetting %s/%s; it will be retried\n'
                             % (component, action))
        # Anything journaled while this waited for the lock is somebody else's
        # fresh crash, not part of what was being retired.
        for component, action in kept:
            sys.stdout.write('keeping %s/%s; it was journaled while this ran\n'
                             % (component, action))
        if not args and not batch:
            return 0

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

    journal = Journal(journal_path)

    # An unreadable journal may be preserving the marker for a call that took
    # kwin down, so nothing mutating may run until it can be read or --forget
    # retires it. --check is read-only, so it's allowed through.
    if journal.unreadable and not check_only:
        sys.stderr.write('kdeshortcut.py: cannot read the crash journal %s '
                         '(%s)\n' % (journal_path, journal.unreadable))
        sys.stderr.write('kdeshortcut.py: refusing to apply shortcuts without '
                         'it -- it may name a call that took kwin down. Fix its '
                         'permissions, or --forget to retire it.\n')
        return 1

    for component, action in sorted(journal.poisoned):
        sys.stderr.write('kdeshortcut.py: skipping %s/%s this run: a previous '
                         'run did not return from it (--forget to retry it)\n'
                         % (component, action))

    # Ask the daemon which actions it actually has, once per component, before
    # changing anything. Enumeration is read-only, and it's what keeps a
    # mutating call off an action the daemon never registered.
    registered = {}

    def actions_in(component):
        if component not in registered:
            registered[component] = backend.list_actions(component)
        return registered[component]

    failures = 0
    remaining = list(entries)
    for position, entry in enumerate(entries):
        component, action, keys_text = entry[0], entry[1], entry[2]
        try:
            ok, note = apply_shortcut(backend, entry, check_only,
                                      actions_in(component), journal)
        except DaemonGone as error:
            # Don't touch the daemon again: it's down, and the journal now names
            # the call that took it there.
            failures += 1
            sys.stderr.write('FAIL  %s/%s (%s): %s\n'
                             % (component, action, keys_text, error))
            skipped = remaining[position + 1:]
            if skipped:
                failures += len(skipped)
                sys.stderr.write('kdeshortcut.py: stopping; %d shortcut(s) not '
                                 'attempted\n' % len(skipped))
            break
        except JournalError as error:
            # The marker couldn't be written, so this call wasn't made -- and it
            # won't be for the rest either, since a full or unwritable state
            # directory doesn't fix itself between entries. Stop once rather
            # than repeat the same failure for every shortcut.
            failures += 1
            sys.stderr.write('FAIL  %s/%s (%s): %s\n'
                             % (component, action, keys_text, error))
            sys.stderr.write('kdeshortcut.py: not applying anything without a '
                             'crash journal -- a call that takes kwin down could '
                             'not be identified afterwards\n')
            skipped = remaining[position + 1:]
            if skipped:
                failures += len(skipped)
                sys.stderr.write('kdeshortcut.py: stopping; %d shortcut(s) not '
                                 'attempted\n' % len(skipped))
            break
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
