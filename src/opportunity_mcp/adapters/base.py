"""Base class for source adapters.

Adapters know how to read one site. They produce raw ``Opportunity`` objects.
The query engine knows nothing about sites.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import httpx

from ..schema import Opportunity

log = logging.getLogger(__name__)

USER_AGENT = (
    "OpportunityMCP/0.1 (+https://github.com/opportunity-mcp/opportunity-mcp)"
)


class SourceAdapter(ABC):
    """Subclass and implement ``fetch``. That's it."""

    name: str = ""
    homepage: str = ""
    user_agent: str = USER_AGENT

    @abstractmethod
    def fetch(self) -> Iterator[Opportunity]:
        """Yield Opportunity objects."""

    def respects_robots(self, url: str | None = None) -> bool:
        """Return True iff fetching ``url`` is allowed by the site's robots.txt.

        Uses ``httpx`` to fetch with our identifying User-Agent, then parses
        the body with ``urllib.robotparser``. We can't use ``RobotFileParser.read``
        directly because Python's default ``urllib`` user-agent gets 403'd by
        Cloudflare-protected sites, which the parser then interprets as
        "disallow all" — a false negative.

        If robots.txt is unreachable or returns non-200, we err on the side of
        proceeding: the actual feed/page fetch will surface real blocks.
        """
        target = url or self.homepage
        parsed = urlparse(target)
        if not parsed.scheme or not parsed.netloc:
            return True
        robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

        try:
            response = httpx.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=10,
                follow_redirects=True,
            )
        except httpx.HTTPError as e:
            log.debug("robots.txt fetch failed for %s: %s", robots_url, e)
            return True

        if response.status_code != 200 or not response.text.strip():
            return True

        rp = RobotFileParser()
        rp.parse(response.text.splitlines())
        return rp.can_fetch(self.user_agent, target)
