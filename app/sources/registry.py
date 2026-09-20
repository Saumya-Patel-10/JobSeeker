"""Map JobSource config entries to adapter instances."""

from __future__ import annotations

from app.config.schema import JobSource
from app.sources.base import JobSourceAdapter
from app.sources.glassdoor import GlassdoorSourceAdapter
from app.sources.indeed import IndeedSourceAdapter
from app.sources.l3harris import L3HarrisSourceAdapter
from app.sources.legacy import LegacyHttpSourceAdapter
from app.sources.linkedin import LinkedInSourceAdapter
from app.sources.raytheon import RaytheonCareersSourceAdapter
from app.sources.texas_instruments import TexasInstrumentsSourceAdapter

_LEGACY_TYPES = frozenset({"greenhouse_board", "lever_board", "url_list", "rss", "career_site"})


class SourceRegistry:
    """Registry of job source adapters."""

    @staticmethod
    def get_adapter(source: JobSource) -> JobSourceAdapter:
        return get_adapter_for_source(source)


def get_adapter_for_source(source: JobSource) -> JobSourceAdapter:
    t = source.type
    if t == "linkedin_search":
        return LinkedInSourceAdapter(source)
    if t == "raytheon_careers":
        return RaytheonCareersSourceAdapter(source)
    if t == "indeed_search":
        return IndeedSourceAdapter(source)
    if t == "glassdoor_search":
        return GlassdoorSourceAdapter(source)
    if t == "l3harris_careers":
        return L3HarrisSourceAdapter(source)
    if t == "ti_careers":
        return TexasInstrumentsSourceAdapter(source)
    if t in _LEGACY_TYPES:
        return LegacyHttpSourceAdapter(source)
    return LegacyHttpSourceAdapter(source)
