init:
	pip install -r requirements.txt

test:
	test/unit_tests.py

doc:
	sh documentation/compile-doc.sh
.PHONY: init tests doc
