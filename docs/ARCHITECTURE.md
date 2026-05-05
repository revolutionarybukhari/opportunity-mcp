# Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   AI client (Claude, ChatGPT, …)             │
└──────────────────────────────┬───────────────────────────────┘
                               │  MCP (JSON-RPC over stdio / Streamable HTTP)
┌──────────────────────────────▼───────────────────────────────┐
│                  Opportunity MCP server                      │
│  ┌────────────────┐  ┌─────────────────┐  ┌───────────────┐  │
│  │  Tool layer    │──▶│  Query engine  │◀─│  Normalizer   │  │
│  │  (FastMCP)     │  │  (SQLite FTS5)  │  │  (Pydantic)   │  │
│  └────────────────┘  └─────────────────┘  └───────┬───────┘  │
│                                                   │          │
│                       ┌───────────────────────────┴───────┐  │
│                       │       Source adapters             │  │
│                       │  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐  │  │
│                       │  │ RSS │ │ RSS │ │HTML │ │ ... │  │  │
│                       │  └──┬──┘ └──┬──┘ └──┬──┘ └─────┘  │  │
│                       └─────┼───────┼───────┼─────────────┘  │
└─────────────────────────────┼───────┼───────┼────────────────┘
                              ▼       ▼       ▼
                       Live opportunity sites (refreshed every 6h)
```

## Two separations of concern

1. **Adapters know how to read one site.** They produce raw `Opportunity` objects.
2. **The query engine knows nothing about sites.** It searches the normalized index.

Adding source #20 should not require touching anything else.

## Data flow

### Refresh path (every 6h via CI cron, or on-demand via the tool)

```
for adapter in SOURCES:
  for opp in adapter.fetch():           # RSS / HTML → Opportunity objects
    upsert into SQLite (by id)          # triggers update FTS5 automatically
```

### Query path (every tool call from the AI client)

```
query → FTS5 sanitize → MATCH → JOIN opportunities → filter → return Pydantic models
```

## Files

| File | Role |
|---|---|
| `src/opportunity_mcp/server.py` | FastMCP entrypoint, defines the six tools. |
| `src/opportunity_mcp/schema.py` | Pydantic models. |
| `src/opportunity_mcp/extract.py` | Heuristic extractors for type / funding / deadline / summary. |
| `src/opportunity_mcp/index.py` | SQLite + FTS5 wrapper. |
| `src/opportunity_mcp/refresh.py` | CLI + library function for refreshing the index. |
| `src/opportunity_mcp/adapters/base.py` | `SourceAdapter` ABC + `respects_robots`. |
| `src/opportunity_mcp/adapters/rss.py` | Generic RSS adapter (works for any WordPress-style feed). |
| `src/opportunity_mcp/adapters/__init__.py` | The `SOURCES` registry. |

## Why SQLite + FTS5

- Zero ops, ships with Python.
- Full-text search built in with Porter stemming.
- File-based DB makes distribution trivial — we publish the latest DB as a GitHub release artifact and clients fetch it on first run, so source sites are not hammered.
- 100k+ rows is well within FTS5's comfort zone.

## Why the adapter pattern

Most opportunity sites are WordPress under the hood, so a single `RSSAdapter` covers seven of them. Sites without RSS get a per-site HTML adapter. The shape of `Opportunity` is fixed — adapters deal with the messy world; the index sees a clean schema.
