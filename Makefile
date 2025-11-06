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

# NOTE: Keep recipe indentation as tabs; GNU Make treats spaces as errors.
.PHONY: help setup test subtitles clean fmt index_footage index_assets describe_images \
        convert_assets verify_assets convert_missing convert_all report_funnel newsletter \
        process update_metadata scripts_from_subtitles assets_manifest render upload_video \
        format lint typecheck serve serve-http

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
	@echo "  convert_assets  Convert incompatible originals/ into converted/ using ffmpeg"
	@echo "  verify_assets  Verify converted/ matches originals/ dimensions/aspect"
	@echo "  convert_missing Convert only missing items from verify_report.json"
	@echo "  scripts_from_subtitles Generate script.md files from subtitles"
        @echo "  convert_all    Convert images+videos for all footage (or SLUG=...)"
        @echo "  report_funnel  Write selections.json for a slug (use SLUG=...)"
        @echo "  assets_manifest Generate assets.json from footage (SLUG=... OVERWRITE=1)"
        @echo "  newsletter    Generate newsletter markdown (SINCE=YYYY-MM-DD STATUS=live OUTPUT=path)"
	@echo "  update_metadata  Refresh metadata via YouTube API (SLUG=...)"
	@echo "  process       One-command: convert+verify+report (requires SLUG=...)"

setup:
	python -m venv $(VENV)
	$(PIP) install -r requirements.txt

test:
        $(PY) -m pytest -q

format:
        $(PY) -m black tools/youtube_mcp tests
        $(PY) -m ruff check --fix tools/youtube_mcp tests

lint:
        $(PY) -m ruff check tools/youtube_mcp tests

typecheck:
        $(PY) -m mypy tools/youtube_mcp

serve:
        $(PY) tools/youtube_mcp/mcp_server.py

serve-http:
        $(PY) -m tools.youtube_mcp --host $(if $(HOST),$(HOST),127.0.0.1) --port $(if $(PORT),$(PORT),8765)

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

convert_assets:
	$(PY) src/convert_assets.py footage

verify_assets:
	$(PY) src/verify_converted_assets.py footage

convert_missing:
	$(PY) src/convert_missing.py --report verify_report.json

scripts_from_subtitles:
	$(PY) src/generate_scripts_from_subtitles.py

# Convert images and videos in one command. Optionally limit to a slug:
#   make convert_all SLUG=20251001_indoor-aquariums-tour
CONVERT_SLUG:=$(if $(SLUG),--slug $(SLUG),)
convert_all:
	$(PY) src/convert_assets.py footage --include-video $(CONVERT_SLUG) --force

update_metadata:
	$(PY) src/update_video_metadata.py $(if $(SLUG),--slug $(SLUG),)

report_funnel:
	@if [ -z "$(SLUG)" ]; then echo "Usage: make report_funnel SLUG=YYYYMMDD_slug [SELECTS=path]"; exit 1; fi
	$(PY) src/report_funnel.py --slug $(SLUG) $(if $(SELECTS),--selects-file $(SELECTS),)

assets_manifest:
        $(PY) src/generate_assets_manifest.py \
                $(if $(SLUG),--slug $(SLUG),) \
                $(if $(FOOTAGE),--footage-root $(FOOTAGE),) \
                $(if $(OVERWRITE),--overwrite,) \
                $(if $(DRY_RUN),--dry-run,)

newsletter:
        $(PY) src/newsletter_builder.py \
                $(if $(OUTPUT),--output $(OUTPUT),) \
                $(if $(SINCE),--since $(SINCE),) \
		$(if $(STATUS),--status $(STATUS),) \
		$(if $(LIMIT),--limit $(LIMIT),) \
		$(if $(DATE),--date $(DATE),)

# One-command processing for a slug
process:
	@if [ -z "$(SLUG)" ]; then echo "Usage: make process SLUG=YYYYMMDD_slug [SELECTS=path]"; exit 1; fi
	$(PY) src/convert_assets.py footage --include-video --slug $(SLUG) --force
	$(PY) src/verify_converted_assets.py footage --slug $(SLUG) --report verify_report.json || true
	$(PY) src/convert_missing.py --report verify_report.json || true
	$(PY) src/report_funnel.py --slug $(SLUG) $(if $(SELECTS),--selects-file $(SELECTS),)

render:
        @if [ -z "$(VIDEO)" ]; then echo "Usage: make render VIDEO=YYYYMMDD_slug [CAPTIONS=path]"; exit 1; fi
        $(PY) src/render_video.py \
                --slug $(VIDEO) \
                $(if $(FOOTAGE),--footage-root $(FOOTAGE),) \
                $(if $(OUTPUT),--output-dir $(OUTPUT),) \
                $(if $(CAPTIONS),--captions $(CAPTIONS),)

upload_video:
        @if [ -z "$(SLUG)" ]; then echo "Usage: make upload_video SLUG=YYYYMMDD_slug [VIDEO=path] [CLIENT=client.json] [TOKEN=token.json]"; exit 1; fi
        $(PY) src/upload_to_youtube.py \
                --slug $(SLUG) \
                $(if $(VIDEO),--video $(VIDEO),) \
                $(if $(CLIENT),--client-secrets $(CLIENT),) \
                $(if $(TOKEN),--credentials $(TOKEN),)
