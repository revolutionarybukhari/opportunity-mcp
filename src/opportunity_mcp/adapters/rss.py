"""Generic RSS adapter — works for any WordPress-style ``/feed/`` endpoint."""
from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import feedparser
import httpx

from ..extract import classify_type, parse_deadline, parse_funding, parse_summary
from ..schema import Opportunity
from .base import SourceAdapter

log = logging.getLogger(__name__)


class RSSAdapter(SourceAdapter):
    def __init__(self, name: str, homepage: str, feed_url: str) -> None:
        self.name = name
        self.homepage = homepage
        self.feed_url = feed_url

    def fetch(self) -> Iterator[Opportunity]:
        if not self.respects_robots(self.feed_url):
            log.info("Skipping %s: blocked by robots.txt", self.name)
            return
        try:
            response = httpx.get(
                self.feed_url,
                headers={"User-Agent": self.user_agent},
                timeout=20,
                follow_redirects=True,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("Fetch failed for %s: %s", self.name, e)
            return

        feed = feedparser.parse(response.content)
        for entry in feed.entries:
            opp = self._entry_to_opportunity(entry)
            if opp is not None:
                yield opp

    def _entry_to_opportunity(self, entry) -> Opportunity | None:
        url = getattr(entry, "link", None)
        title = (getattr(entry, "title", "") or "").strip()
        if not url or not title:
            return None

        html_body = ""
        content_list = entry.get("content")
        if content_list:
            html_body = content_list[0].get("value", "")
        if not html_body:
            html_body = entry.get("summary", "") or ""

        posted_at = _entry_published(entry)
        tags = [t.term for t in entry.get("tags", []) if hasattr(t, "term") and t.term]

        try:
            return Opportunity(
                id=hashlib.sha1(f"{self.name}:{url}".encode()).hexdigest()[:16],
                title=title,
                type=classify_type(title, tags),
                summary=parse_summary(html_body) or title,
                deadline=parse_deadline(html_body, posted_at=posted_at),
                funded=parse_funding(html_body, title),
                eligible_countries=None,
                eligible_levels=[],
                host_country=None,
                apply_url=url,
                source_site=self.name,
                source_url=url,
                posted_at=posted_at,
                scraped_at=datetime.now(UTC),
                raw_categories=tags,
            )
        except Exception as e:  # validation / URL / parsing
            log.debug("Skipping bad entry from %s: %s", self.name, e)
            return None


def _entry_published(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        struct = entry.get(key)
        if struct:
            return datetime(*struct[:6], tzinfo=UTC)
    return datetime.now(UTC)
