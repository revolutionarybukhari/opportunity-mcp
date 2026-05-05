# Opportunity MCP

> A Model Context Protocol server that lets any AI assistant search youth opportunities — scholarships, fellowships, internships, conferences, and exchange programs — aggregated live from leading opportunity-discovery sites.

<!-- mcp-name: io.github.revolutionarybukhari/opportunity-mcp -->

[![PyPI version](https://img.shields.io/pypi/v/opportunity-mcp.svg)](https://pypi.org/project/opportunity-mcp/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://pypi.org/project/opportunity-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/revolutionarybukhari/opportunity-mcp/test.yml?branch=main&label=tests)](https://github.com/revolutionarybukhari/opportunity-mcp/actions/workflows/test.yml)
[![Refresh cron](https://img.shields.io/github/actions/workflow/status/revolutionarybukhari/opportunity-mcp/refresh.yml?branch=main&label=refresh)](https://github.com/revolutionarybukhari/opportunity-mcp/actions/workflows/refresh.yml)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-published-1f6feb)](https://registry.modelcontextprotocol.io)

> **Status:** alpha (`v0.1.x`). Schema, tool surface, and source list may change as adapters mature. Pin to a minor version in production.

---

## Overview

Students who depend on third-party scholarship-aggregator sites typically open ten or more tabs, sift through dozens of irrelevant posts, and copy deadlines into a personal spreadsheet — only to miss the application window because no aggregator offers reliable deadline tracking. Opportunity MCP collapses that workflow into a single conversational query.

> **You:** Find fully-funded master's scholarships in Europe with deadlines in the next 60 days, eligible for Pakistani citizens.
>
> **Claude:** *(Returns a deduplicated, structured list pulled live from the indexed sources, sorted by deadline, each linking back to the original article.)*

The server runs locally over stdio, ships an SQLite + FTS5 index that refreshes every six hours via CI, and is distributed through PyPI, the official MCP Registry, and Smithery.

---

## Distribution channels

| Channel | Identifier | Status |
|---|---|---|
| PyPI | `opportunity-mcp` | ✅ live |
| MCP Registry | `io.github.revolutionarybukhari/opportunity-mcp` | ✅ published |
| Smithery | `sayedhusnainhader/opportunity-mcp` | ✅ published |
| GitHub | [`revolutionarybukhari/opportunity-mcp`](https://github.com/revolutionarybukhari/opportunity-mcp) | source of truth |
| GitHub Releases | `index-N` snapshots of the SQLite DB, refreshed every 6h | auto-published by CI |

---

## Installation

### Claude Desktop

```bash
pip install opportunity-mcp
opportunity-mcp-refresh           # build the local index (one-off, ~30 seconds)
```

Add the following to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "opportunities": {
      "command": "opportunity-mcp"
    }
  }
}
```

Restart Claude Desktop. The six tools below become available to the model.

### Cursor, Windsurf, Continue, and other MCP clients

Most clients use the same `mcpServers` shape. Point the `command` at `opportunity-mcp` (after `pip install`) or use `uvx` for zero-install:

```json
{
  "mcpServers": {
    "opportunities": {
      "command": "uvx",
      "args": ["opportunity-mcp"]
    }
  }
}
```

### Smithery (one-click install)

`https://smithery.ai/server/sayedhusnainhader/opportunity-mcp` — Smithery handles the install command for you.

### From source

```bash
git clone https://github.com/revolutionarybukhari/opportunity-mcp
cd opportunity-mcp
uv sync                           # or: pip install -e ".[dev]"
uv run opportunity-mcp-refresh
uv run opportunity-mcp            # speaks MCP over stdio
```

---

## Tools

The server exposes six tools. Each accepts JSON arguments and returns Pydantic-typed results.

| Tool | Signature | Description |
|---|---|---|
| `search_opportunities` | `(query, type?, funded_only?, deadline_before?, limit=20)` | Full-text search across all indexed opportunities with optional filters. |
| `get_opportunity` | `(id)` | Retrieve full details for a single opportunity by its ID. |
| `list_latest` | `(type?, limit=20)` | Newest opportunities across all sources, sorted by post date. |
| `list_upcoming_deadlines` | `(within_days=30, type?)` | Opportunities closing within `N` days, sorted by deadline. |
| `list_sources` | `()` | List indexed sources, item counts, and last-refresh timestamps. |
| `refresh_index` | `(source?)` | Re-fetch sources on demand. Optional `source` argument limits the refresh to one site. |

`type` is one of `scholarship`, `fellowship`, `internship`, `conference`, `exchange`, `competition`, `grant`, `award`, or `other`.

---

## Indexed sources

Verified live against each site's RSS feed.

| Source | Mechanism | Status |
|---|---|---|
| [Opportunities Corners](https://opportunitiescorners.com/) | RSS | ✅ live |
| [Opportunities for Youth](https://opportunitiesforyouth.org/) | RSS | ✅ live |
| [Opportunity Desk](https://opportunitydesk.org/) | RSS | ✅ live |
| [Scholarships Corner](https://scholarshipscorner.website/) | RSS | ✅ live |
| [Opportunities Circle](https://www.opportunitiescircle.com/) | RSS | ✅ live |
| [Opportunities for Africans](https://www.opportunitiesforafricans.com/) | RSS | ✅ live |
| [Scholars4Dev](https://www.scholars4dev.com/) | RSS | ✅ adapter live (feed currently empty upstream) |
| [Youth Opportunities](https://www.youthop.com/) | HTML | planned |
| [After School Africa](https://www.afterschoolafrica.com/) | HTML | planned |

Per-source `robots.txt` compliance, ToS notes, and CI quirks are documented in [docs/SOURCES.md](docs/SOURCES.md).

---

## Example prompts

```
Find fully-funded master's scholarships in Europe with deadlines in the next 60 days.

What conferences are happening in Africa in the next three months?

List the ten newest internships indexed today.

Show me everything closing in the next seven days that an undergraduate could apply to.

Get full details for opportunity 7733b95a81e3239d.
```

---

## Architecture

```
AI client  ──MCP──▶  FastMCP server  ──▶  SQLite + FTS5  ◀──  refresh job  ──▶  source adapters  ──▶  opportunity sites
```

Two clean separations of concern:

1. **Adapters** know how to read one site and produce raw `Opportunity` objects (Pydantic-validated).
2. **The query engine** knows nothing about sites — it searches a normalized index.

Adding a new source is typically a fifty-line pull request. See [docs/ADAPTER_GUIDE.md](docs/ADAPTER_GUIDE.md). Full architecture rationale is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Privacy & ethics

- **No user tracking.** All queries are processed locally; nothing leaves the user's machine except the periodic source-site refresh.
- **All indexed data is public.** Summaries are capped at 500 characters and every record links back to the originating article.
- **Polite identification.** The HTTP `User-Agent` includes the project URL so site owners can reach us directly.
- **Conservative refresh cadence.** Sources are polled at most every six hours, via CI — never on user query.
- **Source removals on request** are honored within 24 hours, with no negotiation.
- **`robots.txt` is respected** by every adapter prior to fetching.

---

## Roadmap

- **Phase 2** — country-, level-, and language-aware extraction (currently delegated to the AI client).
- **Phase 3** — first HTML adapter (Youth Opportunities), broader Tier-2/Tier-4 source coverage.
- **Phase 4** — hosted Streamable-HTTP endpoint for clients that prefer remote MCP servers.
- **Phase 5** — optional weekly digest by saved profile.

Open issues with the `add a source` label are good first contributions.

---

## Contributing

Pull requests are welcome. The fastest way to help is to add a source we do not yet index — read [docs/ADAPTER_GUIDE.md](docs/ADAPTER_GUIDE.md) and open a PR. See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for development setup, testing conventions, and the code-of-conduct expectations.

```bash
git clone https://github.com/revolutionarybukhari/opportunity-mcp
cd opportunity-mcp
uv sync
uv run pytest
uv run ruff check .
```

---

## License

[MIT](LICENSE) © Opportunity MCP Contributors.
