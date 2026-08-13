.PHONY: test demo-record

test:
	python -m unittest discover -s tests -v

demo-record:
	python scripts/record_demo.py
