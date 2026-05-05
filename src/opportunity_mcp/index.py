"""SQLite + FTS5 index for opportunity search.

Single-file DB. Zero ops. Triggers keep the FTS index in sync with the
opportunities table on every upsert.
"""
from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from pathlib import Path

from .schema import (
    FundingLevel,
    Opportunity,
    OpportunityType,
    StudyLevel,
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    summary TEXT NOT NULL,
    deadline TEXT,
    funded TEXT NOT NULL,
    eligible_countries TEXT,
    eligible_levels TEXT,
    host_country TEXT,
    apply_url TEXT NOT NULL,
    source_site TEXT NOT NULL,
    source_url TEXT NOT NULL,
    posted_at TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    raw_categories TEXT
);

CREATE INDEX IF NOT EXISTS idx_opportunities_deadline ON opportunities(deadline);
CREATE INDEX IF NOT EXISTS idx_opportunities_posted_at ON opportunities(posted_at);
CREATE INDEX IF NOT EXISTS idx_opportunities_type ON opportunities(type);
CREATE INDEX IF NOT EXISTS idx_opportunities_source ON opportunities(source_site);

CREATE VIRTUAL TABLE IF NOT EXISTS opportunities_fts USING fts5(
    title, summary, raw_categories,
    content='opportunities',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS opportunities_ai
AFTER INSERT ON opportunities BEGIN
    INSERT INTO opportunities_fts(rowid, title, summary, raw_categories)
    VALUES (new.rowid, new.title, new.summary, new.raw_categories);
END;

CREATE TRIGGER IF NOT EXISTS opportunities_ad
AFTER DELETE ON opportunities BEGIN
    INSERT INTO opportunities_fts(opportunities_fts, rowid, title, summary, raw_categories)
    VALUES('delete', old.rowid, old.title, old.summary, old.raw_categories);
END;

CREATE TRIGGER IF NOT EXISTS opportunities_au
AFTER UPDATE ON opportunities BEGIN
    INSERT INTO opportunities_fts(opportunities_fts, rowid, title, summary, raw_categories)
    VALUES('delete', old.rowid, old.title, old.summary, old.raw_categories);
    INSERT INTO opportunities_fts(rowid, title, summary, raw_categories)
    VALUES (new.rowid, new.title, new.summary, new.raw_categories);
END;
"""


def default_db_path() -> Path:
    p = Path.home() / ".cache" / "opportunity-mcp" / "index.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


class Index:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = _connect(self.path)
        self.conn.executescript(_SCHEMA)

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> Index:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def upsert_many(self, opportunities: Iterable[Opportunity]) -> int:
        rows: list[tuple] = []
        for opp in opportunities:
            countries = opp.eligible_countries
            if isinstance(countries, list):
                countries_field: str | None = json.dumps(countries)
            elif countries is None:
                countries_field = None
            else:
                countries_field = countries  # "worldwide"

            rows.append(
                (
                    opp.id,
                    opp.title,
                    _enum_value(opp.type),
                    opp.summary,
                    opp.deadline.isoformat() if opp.deadline else None,
                    _enum_value(opp.funded),
                    countries_field,
                    json.dumps([_enum_value(level) for level in opp.eligible_levels]),
                    opp.host_country,
                    str(opp.apply_url),
                    opp.source_site,
                    str(opp.source_url),
                    opp.posted_at.isoformat(),
                    opp.scraped_at.isoformat(),
                    json.dumps(opp.raw_categories),
                )
            )

        if not rows:
            return 0

        self.conn.executemany(
            """
            INSERT INTO opportunities (
                id, title, type, summary, deadline, funded,
                eligible_countries, eligible_levels, host_country,
                apply_url, source_site, source_url, posted_at, scraped_at, raw_categories
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                type=excluded.type,
                summary=excluded.summary,
                deadline=excluded.deadline,
                funded=excluded.funded,
                eligible_countries=excluded.eligible_countries,
                eligible_levels=excluded.eligible_levels,
                host_country=excluded.host_country,
                apply_url=excluded.apply_url,
                source_url=excluded.source_url,
                posted_at=excluded.posted_at,
                scraped_at=excluded.scraped_at,
                raw_categories=excluded.raw_categories
            """,
            rows,
        )
        return len(rows)

    def search(
        self,
        query: str,
        *,
        opp_type: OpportunityType | None = None,
        funded_only: bool = False,
        deadline_before: date | None = None,
        limit: int = 20,
    ) -> list[Opportunity]:
        fts_query = _to_fts_query(query)
        if fts_query is None:
            # No usable tokens — fall through to a posted_at-ordered listing.
            return self.latest(opp_type=opp_type, limit=limit)

        sql = (
            "SELECT o.* FROM opportunities o "
            "JOIN opportunities_fts f ON f.rowid = o.rowid "
            "WHERE opportunities_fts MATCH ?"
        )
        params: list = [fts_query]

        if opp_type:
            sql += " AND o.type = ?"
            params.append(opp_type.value)
        if funded_only:
            sql += " AND o.funded = ?"
            params.append(FundingLevel.FULLY_FUNDED.value)
        if deadline_before:
            sql += " AND o.deadline IS NOT NULL AND o.deadline <= ?"
            params.append(deadline_before.isoformat())

        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_opportunity(r) for r in rows]

    def get(self, opp_id: str) -> Opportunity | None:
        row = self.conn.execute(
            "SELECT * FROM opportunities WHERE id = ?", (opp_id,)
        ).fetchone()
        return _row_to_opportunity(row) if row else None

    def latest(
        self, *, opp_type: OpportunityType | None = None, limit: int = 20
    ) -> list[Opportunity]:
        sql = "SELECT * FROM opportunities"
        params: list = []
        if opp_type:
            sql += " WHERE type = ?"
            params.append(opp_type.value)
        sql += " ORDER BY posted_at DESC LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_opportunity(r) for r in rows]

    def upcoming_deadlines(
        self,
        *,
        within_days: int = 30,
        opp_type: OpportunityType | None = None,
    ) -> list[Opportunity]:
        today = date.today()
        end = today + timedelta(days=within_days)
        sql = (
            "SELECT * FROM opportunities "
            "WHERE deadline IS NOT NULL AND deadline >= ? AND deadline <= ?"
        )
        params: list = [today.isoformat(), end.isoformat()]
        if opp_type:
            sql += " AND type = ?"
            params.append(opp_type.value)
        sql += " ORDER BY deadline ASC LIMIT 100"
        rows = self.conn.execute(sql, params).fetchall()
        return [_row_to_opportunity(r) for r in rows]

    def source_stats(self) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT source_site,
                   COUNT(*) AS count,
                   MAX(scraped_at) AS last_refreshed
            FROM opportunities
            GROUP BY source_site
            ORDER BY source_site
            """
        ).fetchall()
        return [dict(r) for r in rows]


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _row_to_opportunity(row: sqlite3.Row) -> Opportunity:
    countries_raw = row["eligible_countries"]
    eligible_countries: list[str] | str | None
    if not countries_raw:
        eligible_countries = None
    elif countries_raw == "worldwide":
        eligible_countries = "worldwide"
    else:
        try:
            eligible_countries = json.loads(countries_raw)
        except (json.JSONDecodeError, TypeError):
            eligible_countries = countries_raw

    return Opportunity(
        id=row["id"],
        title=row["title"],
        type=OpportunityType(row["type"]),
        summary=row["summary"],
        deadline=date.fromisoformat(row["deadline"]) if row["deadline"] else None,
        funded=FundingLevel(row["funded"]),
        eligible_countries=eligible_countries,
        eligible_levels=[StudyLevel(level) for level in json.loads(row["eligible_levels"] or "[]")],
        host_country=row["host_country"],
        apply_url=row["apply_url"],
        source_site=row["source_site"],
        source_url=row["source_url"],
        posted_at=datetime.fromisoformat(row["posted_at"]),
        scraped_at=datetime.fromisoformat(row["scraped_at"]),
        raw_categories=json.loads(row["raw_categories"] or "[]"),
    )


def _to_fts_query(q: str) -> str | None:
    """Sanitize a user query for FTS5 — strip operators, prefix-match each token."""
    if not q:
        return None
    tokens = re.findall(r"\w+", q, flags=re.UNICODE)
    tokens = [t for t in tokens if len(t) > 1]
    if not tokens:
        return None
    return " ".join(f'"{t}"*' for t in tokens)
