"""Refresh the local index by fetching all source adapters.

Run as a CLI: ``opportunity-mcp-refresh`` (after install) or
``python -m opportunity_mcp.refresh``.
"""
from __future__ import annotations

import argparse
import logging
import sys
from typing import TYPE_CHECKING

from .adapters import SOURCES
from .index import Index

if TYPE_CHECKING:
    from .adapters.base import SourceAdapter


log = logging.getLogger("opportunity_mcp.refresh")


def refresh_one(index: Index, adapter: SourceAdapter) -> int:
    log.info("Refreshing %s …", adapter.name)
    try:
        opps = list(adapter.fetch())
    except Exception as e:
        log.warning("  fetch failed: %s", e)
        return 0
    if not opps:
        log.info("  no opportunities returned")
        return 0
    n = index.upsert_many(opps)
    log.info("  upserted %d opportunities", n)
    return n


def refresh_all(index: Index, source_filter: str | None = None) -> dict[str, int]:
    results: dict[str, int] = {}
    for adapter in SOURCES:
        if source_filter and adapter.name != source_filter:
            continue
        results[adapter.name] = refresh_one(index, adapter)
    return results


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Refresh the opportunity index.")
    parser.add_argument("--source", help="Only refresh this source by name.")
    parser.add_argument("--db", help="Path to the SQLite index file.")
    args = parser.parse_args()

    index = Index(args.db)
    try:
        results = refresh_all(index, source_filter=args.source)
    finally:
        index.close()

    total = sum(results.values())
    log.info("Done. Total upserts: %d across %d sources.", total, len(results))
    sys.exit(0 if total > 0 else 1)


if __name__ == "__main__":
    main()
