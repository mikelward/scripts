# One phony target per test, so `make -j test` runs them concurrently and
# `make setup_test` runs just one. Serial `make test` still runs them in this
# order, and a test not listed here never runs.
TESTS = \
	autoshpool_test \
	autotmux_test \
	autosession_test \
	sessionlib_test \
	changeshpool_test \
	changetmux_test \
	changesession_test \
	detachsession_test \
	makesession_test \
	mdf_test \
	chrome_test \
	pa_test \
	package_test \
	homepkg_test \
	gittossh_test \
	gitbackup_test \
	runenv_test \
	setup_test \
	setup-tide_test \
	setup-tide_pam_test \
	setup-kde_test \
	setup-macos_test \
	kdeshortcut_test \
	dvorak_test \
	confinst_test \
	screenshot_test \
	ci-concurrency_test

test: $(TESTS)

$(TESTS):
	./$@

.PHONY: test $(TESTS)
