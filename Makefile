# Makefile – developer helpers

VENV := .venv
PY := $(VENV)/Scripts/python
PIP := $(PY) -m pip

.PHONY: help setup test subtitles clean

help:
	@echo "Targets:"
	@echo "  setup       Create venv & install deps"
	@echo "  test        Run pytest inside venv"
	@echo "  subtitles   Download captions for all video IDs"
	@echo "  clean       Remove venv & __pycache__"

setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

test:
	$(PY) -m pytest -q

subtitles:
	$(PY) scripts/fetch_subtitles.py

clean:
	rmdir /s /q $(VENV) 2>nul || true
	del /s /q **\__pycache__ 2>nul || true 