# Opportunity MCP

> Search 10+ youth-opportunity sites — scholarships, fellowships, internships, conferences, exchange programs — from any AI assistant via MCP.

[![PyPI](https://img.shields.io/pypi/v/opportunity-mcp.svg)](https://pypi.org/project/opportunity-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![tests](https://img.shields.io/github/actions/workflow/status/opportunity-mcp/opportunity-mcp/test.yml?branch=main&label=tests)](https://github.com/opportunity-mcp/opportunity-mcp/actions)

> **Status:** alpha. The schema and source list will change as adapters mature.

---

## Why

A bright student in Lahore, Lagos, Cairo, or Manila wants to find a fully-funded master's scholarship. Today they:

1. Open 10+ tabs (Scholarships Corner, Youth Opportunities, Opportunity Desk, …).
2. Manually filter through dozens of irrelevant posts.
3. Copy-paste deadlines into a spreadsheet.
4. Miss the deadline anyway because no source tracks them.

Opportunity MCP turns that into:

> **You:** Find me fully-funded master's scholarships in Europe with deadlines in the next 60 days.
>
> **Claude:** *(returns a clean, deduplicated, structured list pulled live from every source)*

---

## Install (Claude Desktop)

```bash
pip install opportunity-mcp
opportunity-mcp-refresh           # build the local index (one-off, ~30s)
```

Then add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "opportunities": {
      "command": "opportunity-mcp"
    }
  }
}
```

Restart Claude Desktop. Try: *"Use the opportunities tool to find fully-funded fellowships closing in the next 30 days."*

### Cursor / Windsurf / Continue

Most MCP clients accept the same shape under `mcpServers`. Point them at the `opportunity-mcp` command.

### Run from source

```bash
git clone https://github.com/opportunity-mcp/opportunity-mcp
cd opportunity-mcp
uv sync                           # or: pip install -e ".[dev]"
uv run opportunity-mcp-refresh
uv run opportunity-mcp            # speaks MCP over stdio
```

---

## Tools exposed

| Tool | What it does |
|---|---|
| `search_opportunities(query, type?, funded_only?, deadline_before?, limit?)` | Full-text search with filters. |
| `get_opportunity(id)` | Look up a single opportunity by id. |
| `list_latest(type?, limit?)` | Newest opportunities across all sources. |
| `list_upcoming_deadlines(within_days?, type?)` | Sorted by closing date. |
| `list_sources()` | What's indexed and when it was last refreshed. |
| `refresh_index(source?)` | Re-fetch sources on demand. Optional: limit to one source. |

---

## Sources

| Source | Type | Status |
|---|---|---|
| Opportunities Corners | RSS | ✅ |
| Opportunities for Youth | RSS | ✅ |
| Opportunity Desk | RSS | ✅ |
| Scholarships Corner | RSS | ✅ |
| Opportunities Circle | RSS | ✅ |
| Opportunities for Africans | RSS | ✅ |
| Scholars4Dev | RSS | ✅ |
| Youth Opportunities (`youthop.com`) | HTML | planned |
| After School Africa | HTML | planned |

See [docs/SOURCES.md](docs/SOURCES.md) for `robots.txt` / ToS notes per source.

---

## Example prompts

> Find me fully-funded master's scholarships in Europe with deadlines in the next 60 days.
>
> What internships are open right now for students in Africa?
>
> List the top 10 newest opportunities indexed.
>
> Anything closing in the next 7 days that I might be eligible for as a Pakistani undergrad?
>
> Get details on opportunity `a1b2c3d4e5f60718`.

---

## Privacy & ethics

- **No user tracking.** Queries never leave your machine.
- **All indexed data is public.** Articles always link back to the original source.
- **Polite identification.** The User-Agent contains a contact URL so site owners can reach us.
- **Conservative refresh cadence.** Every 6h via CI, never on user query.
- **Source removals.** If a site asks to be delisted, we honor it within 24h. No negotiation.

---

## Architecture

```
AI client ──MCP──▶ FastMCP server ──▶ SQLite + FTS5 ◀── refresh job ──▶ source adapters ──▶ scholarship sites
```

- **Adapters** know how to read one site. They produce raw `Opportunity` objects.
- **The query engine** knows nothing about sites. It searches the normalized index.

Adding a new source is a 50-line PR. See [docs/ADAPTER_GUIDE.md](docs/ADAPTER_GUIDE.md).

---

## Contributing

PRs welcome. The fastest way to help:

1. Find a source we don't index yet.
2. Read its `robots.txt` and ToS.
3. Send a 50-line PR adding an adapter (RSS) or a 100-line PR (HTML).

See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

---

## License

MIT. See [LICENSE](LICENSE).
