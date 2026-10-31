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
	home_test \
	irc_test \
	notepad_test \
	pa_test \
	package_test \
	homepkg_test \
	gittossh_test \
	gitbackup_test \
	runenv_test \
	setup_test \
	setup-tide_test \
	setup-tide_hyprland_test \
	setup-tide_greeter_test \
	setup-tide_greeter_pam_test \
	setup-tide_greeter_pam_modules_test \
	setup-tide_greetd_unit_test \
	setup-tide_greetd_test \
	setup-tide_pam_test \
	setup-kde_test \
	setup-macos_test \
	kdeshortcut_test \
	dvorak_test \
	confinst_test \
	screenshot_test \
	terminal_on_workstation_test \
	terminal_on_vm_test \
	ci-concurrency_test \
	ci-test-target_test

# setup-tide's tests take most of the run; CI skips them on a pull request
# that can't affect them (ci-test-target).
TIDE_TESTS = $(filter setup-tide_%,$(TESTS))

test: $(TESTS)

test-no-tide: $(filter-out $(TIDE_TESTS),$(TESTS))

$(TESTS):
	./$@

.PHONY: test test-no-tide $(TESTS)
