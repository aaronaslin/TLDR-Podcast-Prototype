PYTHON ?= ./venv/bin/python

.PHONY: run test lint fmt

run:
	$(PYTHON) main.py

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	@echo "No linter configured. Add ruff/flake8 if desired."

fmt:
	@echo "No formatter configured. Add black if desired."
