"""Registry of source adapters.

Adding a new source is a one-line change here. See ``docs/ADAPTER_GUIDE.md``.
"""
from __future__ import annotations

from .base import SourceAdapter
from .rss import RSSAdapter

SOURCES: list[SourceAdapter] = [
    RSSAdapter(
        name="opportunities_corners",
        homepage="https://opportunitiescorners.com/",
        feed_url="https://opportunitiescorners.com/feed/",
    ),
    RSSAdapter(
        name="opportunities_for_youth",
        homepage="https://opportunitiesforyouth.org/",
        feed_url="https://opportunitiesforyouth.org/feed/",
    ),
    RSSAdapter(
        name="opportunity_desk",
        homepage="https://opportunitydesk.org/",
        feed_url="https://opportunitydesk.org/feed/",
    ),
    RSSAdapter(
        name="scholarships_corner",
        homepage="https://scholarshipscorner.website/",
        feed_url="https://scholarshipscorner.website/feed/",
    ),
    RSSAdapter(
        name="opportunities_circle",
        homepage="https://www.opportunitiescircle.com/",
        feed_url="https://www.opportunitiescircle.com/feed/",
    ),
    RSSAdapter(
        name="opportunities_for_africans",
        homepage="https://www.opportunitiesforafricans.com/",
        feed_url="https://www.opportunitiesforafricans.com/feed/",
    ),
    RSSAdapter(
        name="scholars4dev",
        homepage="https://www.scholars4dev.com/",
        feed_url="https://www.scholars4dev.com/feed/",
    ),
]


__all__ = ["SOURCES", "SourceAdapter", "RSSAdapter"]
