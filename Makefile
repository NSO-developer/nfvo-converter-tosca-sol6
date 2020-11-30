init:
	pip install -r requirements.txt

test:
	test/unit_tests.py

.PHONY: init tests
