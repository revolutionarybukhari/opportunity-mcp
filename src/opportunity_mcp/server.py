"""FastMCP server exposing six opportunity-search tools over stdio.

Run via the ``opportunity-mcp`` console script or
``python -m opportunity_mcp.server``.
"""
import logging
from datetime import date

from mcp.server.fastmcp import FastMCP

from .adapters import SOURCES
from .index import Index
from .refresh import refresh_all
from .schema import Opportunity, OpportunityType

log = logging.getLogger("opportunity_mcp")
mcp = FastMCP("opportunity-mcp")
_index: Index | None = None


def _get_index() -> Index:
    global _index
    if _index is None:
        _index = Index()
    return _index


@mcp.tool()
def search_opportunities(
    query: str,
    type: OpportunityType | None = None,
    funded_only: bool = False,
    deadline_before: date | None = None,
    limit: int = 20,
) -> list[Opportunity]:
    """Full-text search across all indexed opportunities.

    Args:
        query: Natural-language search query (e.g. "fully funded master's
            scholarship Germany").
        type: Optional filter by opportunity type
            (scholarship, fellowship, internship, conference, …).
        funded_only: If True, only return fully-funded opportunities.
        deadline_before: Only return opportunities with deadlines on or
            before this date (ISO YYYY-MM-DD).
        limit: Maximum number of results. Default 20.
    """
    return _get_index().search(
        query,
        opp_type=type,
        funded_only=funded_only,
        deadline_before=deadline_before,
        limit=limit,
    )


@mcp.tool()
def get_opportunity(id: str) -> Opportunity | None:
    """Get full details for a single opportunity by ID."""
    return _get_index().get(id)


@mcp.tool()
def list_latest(
    type: OpportunityType | None = None,
    limit: int = 20,
) -> list[Opportunity]:
    """List the newest opportunities across all sources, most recent first."""
    return _get_index().latest(opp_type=type, limit=limit)


@mcp.tool()
def list_upcoming_deadlines(
    within_days: int = 30,
    type: OpportunityType | None = None,
) -> list[Opportunity]:
    """List opportunities with deadlines in the next N days, soonest first.

    Args:
        within_days: Look ahead this many days from today. Default 30.
        type: Optional filter by opportunity type.
    """
    return _get_index().upcoming_deadlines(within_days=within_days, opp_type=type)


@mcp.tool()
def list_sources() -> list[dict]:
    """List indexed sources, the count each contributed, and last-refresh time."""
    stats = {row["source_site"]: row for row in _get_index().source_stats()}
    out = []
    for adapter in SOURCES:
        s = stats.get(adapter.name, {})
        out.append(
            {
                "name": adapter.name,
                "homepage": adapter.homepage,
                "count": s.get("count", 0),
                "last_refreshed": s.get("last_refreshed"),
            }
        )
    return out


@mcp.tool()
def refresh_index(source: str | None = None) -> dict:
    """Refresh the local index by re-fetching sources.

    Args:
        source: If provided, only refresh this source by name. Otherwise refresh all.
    """
    results = refresh_all(_get_index(), source_filter=source)
    return {"upserts_per_source": results, "total": sum(results.values())}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    _get_index()
    mcp.run()


if __name__ == "__main__":
    main()
