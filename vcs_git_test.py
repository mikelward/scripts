#!/usr/bin/env python3
"""Tests for vcs-git."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vcs-git")


def vcs_git(*args, cwd=None, capture=True):
    """Run vcs-git with the given arguments."""
    cmd = [sys.executable, SCRIPT] + list(args)
    if capture:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return r
    return subprocess.call(cmd, cwd=cwd)


def git(*args, cwd=None):
    """Run raw git and return output."""
    return subprocess.run(["git"] + list(args), cwd=cwd, capture_output=True, text=True)


class GitTestBase(unittest.TestCase):
    """Base class that creates a temporary git repo for each test."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="vcs-git-test-")
        git("init", cwd=self.tmpdir)
        git("config", "user.email", "test@test.com", cwd=self.tmpdir)
        git("config", "user.name", "Test User", cwd=self.tmpdir)
        git("config", "commit.gpgsign", "false", cwd=self.tmpdir)
        # Create initial commit
        self._write_file("README", "hello\n")
        git("add", "README", cwd=self.tmpdir)
        git("commit", "-m", "initial", cwd=self.tmpdir)
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
        r = vcs_git()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Usage:", r.stderr)

    def test_unknown_command(self):
        r = vcs_git("nonexistent_cmd_xyz")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("unknown command", r.stderr)

    def test_command_list_shown(self):
        r = vcs_git()
        self.assertIn("Commands:", r.stderr)


class TestBranch(GitTestBase):
    def test_branch_shows_current(self):
        r = vcs_git("branch", cwd=self.tmpdir)
        # default branch name varies, but should print something
        self.assertEqual(r.returncode, 0)
        self.assertTrue(r.stdout.strip())

    def test_branches_lists_all(self):
        git("checkout", "-b", "feature", cwd=self.tmpdir)
        git("checkout", "-", cwd=self.tmpdir)
        r = vcs_git("branches", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("feature", r.stdout)


class TestStatus(GitTestBase):
    def test_status_clean(self):
        r = vcs_git("status", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), "")

    def test_status_shows_untracked(self):
        self._write_file("newfile", "data")
        r = vcs_git("status", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("newfile", r.stdout)

    def test_status_shows_modified(self):
        self._write_file("README", "changed\n")
        r = vcs_git("status", cwd=self.tmpdir)
        self.assertIn("README", r.stdout)


class TestCommit(GitTestBase):
    def test_commit_all(self):
        self._write_file("README", "updated\n")
        r = vcs_git("commit", "-m", "update readme", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = git("log", "--oneline", cwd=self.tmpdir)
        self.assertIn("update readme", log.stdout)

    def test_commit_specific_file(self):
        self._write_file("a.txt", "a\n")
        self._write_file("b.txt", "b\n")
        git("add", "a.txt", "b.txt", cwd=self.tmpdir)
        r = vcs_git("commit", "-m", "just a", "a.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        # b.txt should still be staged
        status = git("status", "--short", cwd=self.tmpdir)
        self.assertIn("b.txt", status.stdout)

    def test_commit_with_flags(self):
        self._write_file("README", "v2\n")
        r = vcs_git("commit", "-m", "flagged commit", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestAmend(GitTestBase):
    def test_amend(self):
        self._write_file("README", "amended\n")
        r = vcs_git("amend", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = git("log", "--oneline", cwd=self.tmpdir)
        # Should still be one commit
        self.assertEqual(len(log.stdout.strip().splitlines()), 1)


class TestAdd(GitTestBase):
    def test_add_intent(self):
        self._write_file("new.txt", "new\n")
        r = vcs_git("add", "new.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        status = git("status", "--short", cwd=self.tmpdir)
        self.assertIn("new.txt", status.stdout)

    def test_addremove(self):
        self._write_file("new.txt", "new\n")
        r = vcs_git("addremove", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestDiff(GitTestBase):
    def test_changes_shows_diff(self):
        self._write_file("README", "modified\n")
        r = vcs_git("changes", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("modified", r.stdout)

    def test_changed_shows_filenames(self):
        self._write_file("README", "modified\n")
        r = vcs_git("changed", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("README", r.stdout)

    def test_diffstat(self):
        self._write_file("README", "modified\n")
        r = vcs_git("diffstat", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("README", r.stdout)


class TestLog(GitTestBase):
    def test_changelog(self):
        r = vcs_git("changelog", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)

    def test_base(self):
        r = vcs_git("base", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)

    def test_graph(self):
        r = vcs_git("graph", "--all", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)


class TestNavigation(GitTestBase):
    def test_prev(self):
        self._write_file("f2.txt", "f2\n")
        git("add", "f2.txt", cwd=self.tmpdir)
        git("commit", "-m", "second", cwd=self.tmpdir)
        r = vcs_git("prev", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        # HEAD should be detached at initial commit
        log = git("log", "-1", "--oneline", cwd=self.tmpdir)
        self.assertIn("initial", log.stdout)

    def test_next(self):
        self._write_file("f2.txt", "f2\n")
        git("add", "f2.txt", cwd=self.tmpdir)
        git("commit", "-m", "second", cwd=self.tmpdir)
        git("checkout", "HEAD~", cwd=self.tmpdir)
        r = vcs_git("next", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = git("log", "-1", "--oneline", cwd=self.tmpdir)
        self.assertIn("second", log.stdout)


class TestCheckout(GitTestBase):
    def test_checkout_branch(self):
        git("checkout", "-b", "feature", cwd=self.tmpdir)
        git("checkout", "-", cwd=self.tmpdir)
        r = vcs_git("checkout", "feature", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=self.tmpdir)
        self.assertEqual(branch.stdout.strip(), "feature")

    def test_goto(self):
        git("checkout", "-b", "feat2", cwd=self.tmpdir)
        git("checkout", "-", cwd=self.tmpdir)
        r = vcs_git("goto", "feat2", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestFileOps(GitTestBase):
    def test_move(self):
        r = vcs_git("move", "README", "README2", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "README2")))

    def test_remove(self):
        r = vcs_git("remove", "README", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertFalse(os.path.exists(os.path.join(self.tmpdir, "README")))

    def test_copy(self):
        r = vcs_git("copy", "README", "README_COPY", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "README_COPY")))

    def test_ignore(self):
        r = vcs_git("ignore", "*.pyc", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        content = self._read_file(".gitignore")
        self.assertIn("*.pyc", content)


class TestUndo(GitTestBase):
    def test_undo(self):
        self._write_file("README", "v2\n")
        git("add", "-A", cwd=self.tmpdir)
        git("commit", "-m", "v2", cwd=self.tmpdir)
        r = vcs_git("undo", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        # Should have uncommitted changes now
        status = git("status", "--short", cwd=self.tmpdir)
        self.assertIn("README", status.stdout)

    def test_uncommit(self):
        self._write_file("README", "v2\n")
        git("add", "-A", cwd=self.tmpdir)
        git("commit", "-m", "v2", cwd=self.tmpdir)
        r = vcs_git("uncommit", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        # Changes should be staged
        status = git("diff", "--cached", "--name-only", cwd=self.tmpdir)
        self.assertIn("README", status.stdout)

    def test_revert_all(self):
        self._write_file("README", "dirty\n")
        r = vcs_git("revert", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self._read_file("README"), "hello\n")

    def test_revert_file(self):
        self._write_file("README", "dirty\n")
        r = vcs_git("revert", "README", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self._read_file("README"), "hello\n")

    def test_restore(self):
        self._write_file("README", "dirty\n")
        r = vcs_git("restore", "README", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(self._read_file("README"), "hello\n")


class TestTrack(GitTestBase):
    def test_track(self):
        self._write_file("new.txt", "new\n")
        r = vcs_git("track", "new.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        status = git("status", "--short", cwd=self.tmpdir)
        self.assertIn("new.txt", status.stdout)

    def test_untrack(self):
        self._write_file("tracked.txt", "data\n")
        git("add", "tracked.txt", cwd=self.tmpdir)
        git("commit", "-m", "add tracked", cwd=self.tmpdir)
        r = vcs_git("untrack", "tracked.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestUnknown(GitTestBase):
    def test_unknown_lists_untracked(self):
        self._write_file("mystery.txt", "who am i\n")
        r = vcs_git("unknown", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("mystery.txt", r.stdout)


class TestRootdir(GitTestBase):
    def test_rootdir(self):
        r = vcs_git("rootdir", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.strip(), self.tmpdir)


class TestFetchtime(GitTestBase):
    def test_fetchtime_no_fetch_head(self):
        r = vcs_git("fetchtime", cwd=self.tmpdir)
        # No FETCH_HEAD yet
        self.assertNotEqual(r.returncode, 0)


class TestShow(GitTestBase):
    def test_show(self):
        r = vcs_git("show", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)


class TestDescribe(GitTestBase):
    def test_describe_with_message(self):
        r = vcs_git("describe", "-m", "new description", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = git("log", "-1", "--format=%s", cwd=self.tmpdir)
        self.assertEqual(log.stdout.strip(), "new description")


class TestReword(GitTestBase):
    def test_reword_with_message(self):
        # reword uses --allow-empty so it should work even with -m
        r = vcs_git("reword", "-m", "reworded", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        log = git("log", "-1", "--format=%s", cwd=self.tmpdir)
        self.assertEqual(log.stdout.strip(), "reworded")


class TestEvolve(GitTestBase):
    def test_evolve_warns(self):
        r = vcs_git("evolve", cwd=self.tmpdir)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no automatic evolve", r.stderr)


class TestMap(GitTestBase):
    def test_map_at_tip(self):
        r = vcs_git("map", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)
        self.assertIn("initial", r.stdout)

    def test_map_detached(self):
        self._write_file("f2.txt", "f2\n")
        git("add", "f2.txt", cwd=self.tmpdir)
        git("commit", "-m", "second", cwd=self.tmpdir)
        git("checkout", "HEAD~", cwd=self.tmpdir)
        r = vcs_git("map", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestCommitForce(GitTestBase):
    def test_commitforce(self):
        self._write_file("README", "forced\n")
        r = vcs_git("commitforce", "-m", "forced commit", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


class TestDrop(GitTestBase):
    def test_drop_no_args(self):
        r = vcs_git("drop", cwd=self.tmpdir)
        self.assertNotEqual(r.returncode, 0)


class TestSplitFlags(GitTestBase):
    def test_commit_with_dash_dash(self):
        self._write_file("a.txt", "a\n")
        git("add", "a.txt", cwd=self.tmpdir)
        r = vcs_git("commit", "-m", "with separator", "--", "a.txt", cwd=self.tmpdir)
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
