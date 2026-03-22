# Bug Fixes to Apply

Apply all of the following bug fixes, commit each one separately, then push and create a PR.

## 1. package:31 — Typo in aptitude search command

**File:** `package`, line 31
**Bug:** `'aptitute'` is misspelled — should be `'aptitude'`
**Fix:**
```diff
-        'search': ['aptitute', 'search'],
+        'search': ['aptitude', 'search'],
```

## 2. editroot:18 — Lost +line argument when editing as root

**File:** `editroot`, line 18
**Bug:** `"$1"` only passes the filename, dropping any preceding `+line` argument. Should be `"$@"` to pass all arguments.
**Fix:**
```diff
-    confirm "Edit as root" && "$SUDO" "$EDITOR" "$1"
+    confirm "Edit as root" && "$SUDO" "$EDITOR" "$@"
```

## 3. fromto:15 — Missing \$help variable in GetOptions

**File:** `fromto`, line 15
**Bug:** `"help|h" =>)` is missing the `\$help` variable reference, so GetOptions fails to parse `--help`.
**Fix:**
```diff
-  "help|h" =>);
+  "help|h" => \$help);
```

## 4. i3statusdwm:14 — Missing backslash continuation in sed pipeline

**File:** `i3statusdwm`, line 14
**Bug:** Line 14 ends without a trailing `\`, so the sed command ends prematurely and the remaining `-e` expressions on lines 15-16 become broken separate commands.
**Fix:**
```diff
-            -e 's/Speaker/🔉/g'
+            -e 's/Speaker/🔉/g' \
```

## 5. pulseprofile.py:34 — bytes % formatting fails in Python 3

**File:** `pulseprofile.py`, line 34
**Bug:** `b'    index: %d' % card_index` — Python 3 does not support the `%` operator on bytes objects.
**Fix:**
```diff
-    want = b'    index: %d' % card_index
+    want = ('    index: %d' % card_index).encode()
```

## 6. diskuse:386 — Hash cleared with {} instead of ()

**File:** `diskuse`, line 386
**Bug:** `%dirsize = {}` assigns an anonymous hash reference to the hash (producing a warning and corrupting it). Should use `()` to properly clear it.
**Fix:**
```diff
-%dirsize = {};
+%dirsize = ();
```

## 7. diskuse:197 — Wrong comparison operator in debug message

**File:** `diskuse`, line 197
**Bug:** The debug message says `"$age seconds < $maxage seconds"` but this is in the else branch where the file is being skipped because age >= maxage.
**Fix:**
```diff
-                    print STDERR "Skipping $path ($age seconds < $maxage seconds)\n" if $debug;
+                    print STDERR "Skipping $path ($age seconds >= $maxage seconds)\n" if $debug;
```

## PR Details

**Title:** Fix bugs across multiple scripts

**Body:**
```
## Summary
- **package**: Fix typo `aptitute` → `aptitude`
- **editroot**: Fix `"$1"` → `"$@"` so the `+line` argument is preserved when editing as root
- **fromto**: Add missing `$help` variable to `GetOptions` so `--help` actually works
- **i3statusdwm**: Add missing backslash continuation in `sed` pipeline
- **pulseprofile.py**: Fix `b'...' % int` which fails in Python 3
- **diskuse**: Fix `%dirsize = {}` (assigns a hash ref) → `%dirsize = ()` (clears the hash)
- **diskuse**: Fix debug message that said `<` when the condition is actually `>=`

## Test plan
- [ ] Verify `package` runs without typo in apt command
- [ ] Verify `editroot +42 file` opens the file at line 42 as root
- [ ] Verify `fromto --help` prints usage
- [ ] Verify `i3statusdwm` sed removes `|` characters and collapses spaces
- [ ] Verify `pulseprofile.py` runs without TypeError on the index line
- [ ] Verify `diskuse` clears its hash without warnings and shows correct debug output
```
