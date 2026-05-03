test:
	./autoshpool_test
	python3 -m pytest vcs_git_test.py vcs_hg_test.py vcs_jj_test.py -v
