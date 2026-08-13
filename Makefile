.PHONY: test demo-record readme-art

test:
	python -m unittest discover -s tests -v

demo-record:
	python scripts/record_demo.py

readme-art:
	python scripts/render_readme_art.py
	python scripts/record_demo.py
