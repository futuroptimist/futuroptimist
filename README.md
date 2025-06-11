# Futuroptimist

Hi, I'm Futuroptimist. This repository hosts scripts and metadata for my [YouTube channel](https://www.youtube.com/channel/UCA-J-opDpgiRoHYmOAxGQSQ). If you're looking for the full project details, see [INSTRUCTIONS.md](INSTRUCTIONS.md). Guidelines for AI tools live in [AGENTS.md](AGENTS.md).
`metadata.json` files under each video folder now support optional fields like `slug`, `thumbnail`, `transcript_file`, and `summary` for richer automation.

English subtitles are pulled directly from each upload using [scripts/fetch_subtitles.py](scripts/fetch_subtitles.py). Only **manual** captions are downloaded so transcripts stay accurate.
`scripts/update_transcript_links.py` can then populate the optional `transcript_file` field. If a `YOUTUBE_API_KEY` environment variable is set, it fetches missing transcripts via the YouTube Data API.

Test coverage is exercised automatically via GitHub Actions.

## Other Projects
- **[token.place](https://token.place)** – p2p generative AI platform ([repo](https://github.com/futuroptimist/token.place))
- **[DSPACE](https://democratized.space)** – open-source space exploration idle game ([repo](https://github.com/democratizedspace/dspace))
- **sigma** – open-source AI pin device ([repo](https://github.com/futuroptimist/sigma))
- **gabriel** – guardian angel LLM ([repo](https://github.com/futuroptimist/gabriel))
- **f2clipboard** – quickly copy multiple files from nested directories for LLM conversations ([repo](https://github.com/futuroptimist/f2clipboard))

