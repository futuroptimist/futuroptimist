# Futuroptimist

Hi, I'm Futuroptimist. This repository hosts scripts and metadata for my [YouTube channel](https://www.youtube.com/channel/UCA-J-opDpgiRoHYmOAxGQSQ). If you're looking for the full project details and contribution guidelines, see [INSTRUCTIONS.md](INSTRUCTIONS.md).

## Development

Use the Makefile to set up a virtual environment and run the tests:

```bash
make setup  # install dependencies into .venv
make test   # run unit tests
```

Create new script folders from the YouTube IDs listed in `video_ids.txt`:

```bash
python scripts/scaffold_videos.py
```

This fetches titles and dates and generates `scripts/YYYYMMDD_slug` directories for drafting.

Formatting is enforced with `black` and `ruff` – run `black .` and `ruff check --fix .` before committing.

## Other Projects
- **[token.place](https://token.place)** – p2p generative AI platform ([repo](https://github.com/futuroptimist/token.place))
- **[DSPACE](https://democratized.space)** – open-source space exploration idle game ([repo](https://github.com/democratizedspace/dspace))
- **sigma** – open-source AI pin device ([repo](https://github.com/futuroptimist/sigma))
- **gabriel** – guardian angel LLM ([repo](https://github.com/futuroptimist/gabriel))
- **f2clipboard** – quickly copy multiple files from nested directories for LLM conversations ([repo](https://github.com/futuroptimist/f2clipboard))

For repository structure and AI guidelines see [AGENTS.md](AGENTS.md). Brainstorm files live in the [ideas/](ideas) directory.
