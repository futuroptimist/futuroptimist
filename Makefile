# Makefile – developer helpers

VENV := .venv
ifeq ($(OS),Windows_NT)
    PY := $(VENV)/Scripts/python
    REMOVE := rmdir /s /q
    CLEANCACHE := del /s /q **\__pycache__
else
    PY := $(VENV)/bin/python
    REMOVE := rm -rf
    CLEANCACHE := find . -name '__pycache__' -type d -exec rm -rf {} +
endif
PIP := uv pip

.PHONY: help setup test subtitles clean fmt index_footage index_assets describe_images

help:
	@echo "Targets:"
	@echo "  setup       Create venv & install deps"
	@echo "  test        Run pytest inside venv"
	@echo "  subtitles   Download captions for all video IDs"
	@echo "  fmt         Format code with black & ruff"
	@echo "  clean       Remove venv & __pycache__"
	@echo "  index_footage  Index local media under ./footage to footage_index.json"
	@echo "  index_assets   Build rich assets_index.json from per-video manifests"
	@echo "  describe_images  Generate image_descriptions.md from ./footage"

setup:
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

test:
	$(PY) -m pytest -q

subtitles:
	$(PY) src/fetch_subtitles.py

fmt:
	$(PY) -m black .
	$(PY) -m ruff check --fix .

clean:
	@$(REMOVE) $(VENV) 2>/dev/null || true
	@$(CLEANCACHE) 2>/dev/null || true

index_footage:
	$(PY) src/index_local_media.py footage -o footage_index.json

index_assets:
	$(PY) src/index_assets.py -o assets_index.json

describe_images:
	$(PY) src/describe_images.py footage -o image_descriptions.md
