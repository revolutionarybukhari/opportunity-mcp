# Contributing

Thanks for considering a contribution.

## Setup

```bash
git clone https://github.com/opportunity-mcp/opportunity-mcp
cd opportunity-mcp
uv sync                # or: pip install -e ".[dev]"
uv run pytest
uv run ruff check .
```

## What to work on

The fastest way to help is to **add a source**:

1. Pick something from the `add a source` issues, or propose your own.
2. Read [docs/ADAPTER_GUIDE.md](ADAPTER_GUIDE.md).
3. Open a PR — usually 50 lines for an RSS source, ~100 for an HTML source.

Other welcome contributions:

- Tighten the heuristics in `src/opportunity_mcp/extract.py` (deadline / funding / level / country).
- Add country-extraction (Phase 2). `pycountry` plus `spaCy`'s small NER model is the planned approach.
- Improve the FTS5 ranking — e.g. boost recent posts, boost upcoming deadlines.
- Expand tests, especially fixtures with real article HTML.

## Code style

- Python 3.12+. Type-hint everything.
- `ruff check .` and `ruff format .` must be clean.
- Tests must pass: `uv run pytest`.
- New adapters must respect `robots.txt`.

## Pull requests

- Keep them small. One adapter, one fix, one feature per PR.
- Reference the issue if there is one.
- Add or update tests.
- Update `docs/SOURCES.md` if you add a source.

## Code of conduct

Be kind. Assume good intent. The audience for this tool is students worldwide — many of them facing barriers we don't. Bring the energy of building something genuinely useful for them.
