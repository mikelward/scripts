#!/usr/bin/env python3
"""Tests for vcs-jj."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vcs-jj")


def vcs_jj(*args, cwd=None, capture=True):
    cmd = [sys.executable, SCRIPT] + list(args)
    if capture:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return subprocess.call(cmd, cwd=cwd)


def jj(*args, cwd=None):
    return subprocess.run(["jj"] + list(args), cwd=cwd, capture_output=True, text=True)


class JjTestBase(unittest.TestCase):
    """Base class that creates a temporary jj repo (git-backed) for each test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="vcs-jj-test-")
        jj("git", "init", cwd=self.tmpdir)
        jj("config", "set", "--repo", "user.name", "Test User", cwd=self.tmpdir)
        jj("config", "set", "--repo", "user.email", "test@test.com", cwd=self.tmpdir)
        # Create initial commit
        self._write_file("README", "hello\n")
        jj("commit", "-m", "initial", cwd=self.tmpdir)
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
        r = vcs_jj()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage:", r.stderr)

    def test_unknown_command(self):
        r = vcs_jj("nonexistent_cmd_xyz")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown command", r.stderr)


class TestStatus(JjTestBase):
    def test_status_no_description(self):
        # Working copy has no description, so should show diff summary
        self._write_file("new.txt", "new\n")
        r = vcs_jj("status", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_status_with_description(self):
        # Describe the working copy - status should show nothing
        jj("describe", "-m", "described", cwd=self.tmpdir)
        r = vcs_jj("status", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        # Should produce no file list since it's described
        self.assertEqual(r.stdout.strip(), "")


class TestCommit(JjTestBase):
    def test_commit(self):
        self._write_file("README", "updated\n")
        r = vcs_jj("commit", "-m", "update readme", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_commitforce(self):
        self._write_file("README", "forced\n")
        r = vcs_jj("commitforce", "-m", "forced", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestDescribe(JjTestBase):
    def test_describe(self):
        r = vcs_jj("describe", "-m", "my description", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = jj("log", "--no-graph", "-r", "@", "-T", "description", cwd=self.tmpdir)
        self.assertIn("my description", log.stdout)

    def test_change(self):
        r = vcs_jj("change", "-m", "changed description", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestDiff(JjTestBase):
    def test_changes(self):
        self._write_file("README", "modified\n")
        r = vcs_jj("changes", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("modified", r.stdout)

    def test_changed(self):
        self._write_file("README", "modified\n")
        r = vcs_jj("changed", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("README", r.stdout)

    def test_diffstat(self):
        self._write_file("README", "modified\n")
        r = vcs_jj("diffstat", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("README", r.stdout)

    def test_diffs(self):
        self._write_file("README", "modified\n")
        r = vcs_jj("diffs", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestLog(JjTestBase):
    def test_changelog(self):
        r = vcs_jj("changelog", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)

    def test_graph(self):
        r = vcs_jj("graph", "-r", "all()", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_base(self):
        r = vcs_jj("base", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestFileOps(JjTestBase):
    def test_add(self):
        self._write_file("new.txt", "new\n")
        r = vcs_jj("add", "new.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_addremove(self):
        r = vcs_jj("addremove", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_rename(self):
        r = vcs_jj("rename", "README", "README2", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "README2")))

    def test_rename_wrong_args(self):
        r = vcs_jj("rename", "README", cwd=self.tmpdir)
        self.assertNotEqual(r.returncode, 0)

    def test_copy(self):
        r = vcs_jj("copy", "README", "README_COPY", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "README_COPY")))

    def test_ignore(self):
        r = vcs_jj("ignore", "*.pyc", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        content = self._read_file(".gitignore")
        self.assertIn("*.pyc", content)


class TestNavigation(JjTestBase):
    def test_prev(self):
        self._write_file("README", "v2\n")
        jj("commit", "-m", "second", cwd=self.tmpdir)
        r = vcs_jj("prev", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_next(self):
        self._write_file("README", "v2\n")
        jj("commit", "-m", "second", cwd=self.tmpdir)
        vcs_jj("prev", cwd=self.tmpdir)
        r = vcs_jj("next", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestDrop(JjTestBase):
    def test_drop(self):
        r = vcs_jj("drop", "@", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestRestore(JjTestBase):
    def test_restore(self):
        self._write_file("README", "modified\n")
        r = vcs_jj("restore", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self._read_file("README"), "hello\n")


class TestShow(JjTestBase):
    def test_show(self):
        self._write_file("README", "shown\n")
        jj("describe", "-m", "show me", cwd=self.tmpdir)
        r = vcs_jj("show", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("show me", r.stdout)


class TestRootdir(JjTestBase):
    def test_rootdir(self):
        r = vcs_jj("rootdir", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), self.tmpdir)


class TestEvolve(JjTestBase):
    def test_evolve_message(self):
        r = vcs_jj("evolve", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("automatically rebases", r.stderr)


class TestHistedit(JjTestBase):
    def test_histedit_warns(self):
        r = vcs_jj("histedit", cwd=self.tmpdir)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no interactive histedit", r.stderr)


class TestBranch(JjTestBase):
    def test_branch_returns_ok(self):
        r = vcs_jj("branch", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)

    def test_branches(self):
        r = vcs_jj("branches", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestSquash(JjTestBase):
    def test_squash(self):
        self._write_file("README", "squashed\n")
        r = vcs_jj("squash", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestSplit(JjTestBase):
    def test_split_noninteractive(self):
        # split requires interactive input, just verify it doesn't crash on invocation
        # (it will fail but shouldn't error in our wrapper)
        r = vcs_jj("split", "--help", cwd=self.tmpdir)
        # --help should succeed
        self.assertEqual(r.returncode, 0)


class TestReword(JjTestBase):
    def test_reword_with_message(self):
        r = vcs_jj("reword", "new description", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = jj("log", "--no-graph", "-r", "@", "-T", "description", cwd=self.tmpdir)
        self.assertIn("new description", log.stdout)


class TestUndo(JjTestBase):
    def test_undo(self):
        jj("describe", "-m", "will undo", cwd=self.tmpdir)
        r = vcs_jj("undo", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestBookmarks(JjTestBase):
    def test_branches_empty(self):
        r = vcs_jj("branches", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestPresubmit(JjTestBase):
    def test_presubmit_git_backend(self):
        r = vcs_jj("presubmit", cwd=self.tmpdir)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no presubmit", r.stderr)


if __name__ == "__main__":
    unittest.main()
