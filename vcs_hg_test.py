#!/usr/bin/env python3
"""Tests for vcs-hg."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vcs-hg")


def vcs_hg(*args, cwd=None, capture=True):
    cmd = [sys.executable, SCRIPT] + list(args)
    if capture:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return subprocess.call(cmd, cwd=cwd)


def hg(*args, cwd=None):
    return subprocess.run(["hg"] + list(args), cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, "HGPLAIN": "1"})


class HgTestBase(unittest.TestCase):
    """Base class that creates a temporary hg repo for each test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="vcs-hg-test-")
        hg("init", cwd=self.tmpdir)
        # Configure user
        hgrc = os.path.join(self.tmpdir, ".hg", "hgrc")
        with open(hgrc, "w") as f:
            f.write("[ui]\nusername = Test User <test@test.com>\n")
        # Create initial commit
        self._write_file("README", "hello\n")
        hg("add", "README", cwd=self.tmpdir)
        hg("commit", "-m", "initial", cwd=self.tmpdir)
        self.orig_dir = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.orig_dir)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_file(self, name, content=""):
        path = os.path.join(self.tmpdir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def _read_file(self, name):
        with open(os.path.join(self.tmpdir, name)) as f:
            return f.read()


class TestNoArgs(unittest.TestCase):
    def test_no_command_prints_usage(self):
        r = vcs_hg()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage:", r.stderr)

    def test_unknown_command(self):
        r = vcs_hg("nonexistent_cmd_xyz")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown command", r.stderr)


class TestBranch(HgTestBase):
    def test_branch(self):
        r = vcs_hg("branch", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "default")


class TestStatus(HgTestBase):
    def test_status_clean(self):
        r = vcs_hg("status", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_status_shows_modified(self):
        self._write_file("README", "changed\n")
        r = vcs_hg("status", cwd=self.tmpdir)
        self.assertIn("README", r.stdout)

    def test_status_shows_untracked(self):
        self._write_file("newfile", "data")
        r = vcs_hg("status", cwd=self.tmpdir)
        self.assertIn("newfile", r.stdout)


class TestCommit(HgTestBase):
    def test_commit(self):
        self._write_file("README", "updated\n")
        r = vcs_hg("commit", "-m", "update readme", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = hg("log", "--template", "{desc}\\n", cwd=self.tmpdir)
        self.assertIn("update readme", log.stdout)


class TestAdd(HgTestBase):
    def test_add(self):
        self._write_file("new.txt", "new\n")
        r = vcs_hg("add", "new.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_addremove(self):
        self._write_file("new.txt", "new\n")
        r = vcs_hg("addremove", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestDiff(HgTestBase):
    def test_changes(self):
        self._write_file("README", "modified\n")
        r = vcs_hg("changes", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("modified", r.stdout)

    def test_diffstat(self):
        self._write_file("README", "modified\n")
        r = vcs_hg("diffstat", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("README", r.stdout)


class TestLog(HgTestBase):
    def test_changelog(self):
        r = vcs_hg("changelog", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        # Output depends on template, but should have something
        self.assertTrue(r.stdout.strip())


class TestFileOps(HgTestBase):
    def test_move(self):
        r = vcs_hg("move", "README", "README2", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "README2")))

    def test_remove(self):
        r = vcs_hg("remove", "README", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_copy(self):
        r = vcs_hg("copy", "README", "README_COPY", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "README_COPY")))


class TestRevert(HgTestBase):
    def test_revert(self):
        self._write_file("README", "dirty\n")
        r = vcs_hg("revert", "README", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self._read_file("README"), "hello\n")

    def test_restore(self):
        self._write_file("README", "dirty\n")
        r = vcs_hg("restore", "README", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self._read_file("README"), "hello\n")


class TestRootdir(HgTestBase):
    def test_rootdir(self):
        r = vcs_hg("rootdir", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), self.tmpdir)


class TestIgnore(HgTestBase):
    def test_ignore(self):
        r = vcs_hg("ignore", "*.pyc", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        content = self._read_file(".hgignore")
        self.assertIn("*.pyc", content)


class TestTrack(HgTestBase):
    def test_track(self):
        self._write_file("new.txt", "new\n")
        r = vcs_hg("track", "new.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_untrack(self):
        self._write_file("tracked.txt", "data\n")
        hg("add", "tracked.txt", cwd=self.tmpdir)
        hg("commit", "-m", "add tracked", cwd=self.tmpdir)
        r = vcs_hg("untrack", "tracked.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestUnknown(HgTestBase):
    def test_unknown(self):
        self._write_file("mystery.txt", "who am i\n")
        r = vcs_hg("unknown", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("mystery.txt", r.stdout)


class TestShow(HgTestBase):
    def test_show(self):
        r = vcs_hg("show", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)


class TestReview(HgTestBase):
    def test_review_not_supported(self):
        r = vcs_hg("review", cwd=self.tmpdir)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not supported", r.stderr)


class TestFetchtime(HgTestBase):
    def test_fetchtime(self):
        r = vcs_hg("fetchtime", cwd=self.tmpdir)
        # changelog should exist after a commit
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.strip().isdigit())


class TestNav(HgTestBase):
    def test_prev(self):
        self._write_file("f2.txt", "f2\n")
        hg("add", "f2.txt", cwd=self.tmpdir)
        hg("commit", "-m", "second", cwd=self.tmpdir)
        r = vcs_hg("prev", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = hg("log", "-r", ".", "--template", "{desc}", cwd=self.tmpdir)
        self.assertEqual(log.stdout, "initial")


class TestChanged(HgTestBase):
    def test_changed_no_args(self):
        self._write_file("README", "modified\n")
        r = vcs_hg("changed", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("README", r.stdout)


class TestGoto(HgTestBase):
    def test_goto(self):
        self._write_file("f2.txt", "f2\n")
        hg("add", "f2.txt", cwd=self.tmpdir)
        hg("commit", "-m", "second", cwd=self.tmpdir)
        r = vcs_hg("goto", "0", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
