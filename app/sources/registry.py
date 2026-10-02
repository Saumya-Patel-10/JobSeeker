"""Map JobSource config entries to adapter instances."""

from __future__ import annotations

from app.config.schema import JobSource
from app.sources.ashby import AshbyMultiSourceAdapter, AshbySourceAdapter
from app.sources.base import JobSourceAdapter
from app.sources.glassdoor import GlassdoorSourceAdapter
from app.sources.greenhouse_multi import GreenhouseMultiSourceAdapter, LeverMultiSourceAdapter
from app.sources.indeed import IndeedSourceAdapter
from app.sources.l3harris import L3HarrisSourceAdapter
from app.sources.legacy import LegacyHttpSourceAdapter
from app.sources.linkedin import LinkedInSourceAdapter
from app.sources.raytheon import RaytheonCareersSourceAdapter
from app.sources.smartrecruiters import SmartRecruitersSourceAdapter
from app.sources.texas_instruments import TexasInstrumentsSourceAdapter
from app.sources.workday import WorkdaySourceAdapter

_LEGACY_TYPES = frozenset({"greenhouse_board", "lever_board", "url_list", "rss", "career_site"})


class SourceRegistry:
    """Registry of job source adapters."""

    @staticmethod
    def get_adapter(source: JobSource) -> JobSourceAdapter:
        return get_adapter_for_source(source)


def get_adapter_for_source(source: JobSource) -> JobSourceAdapter:
    t = source.type

    # ── Single-site browser adapters ──────────────────────────────────────────
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

    # ── Multi-company API adapters (Jobright-style) ───────────────────────────
    if t == "greenhouse_multi":
        return GreenhouseMultiSourceAdapter(source)
    if t == "lever_multi":
        return LeverMultiSourceAdapter(source)
    if t == "ashby":
        return AshbySourceAdapter(source)
    if t == "ashby_multi":
        return AshbyMultiSourceAdapter(source)
    if t == "workday":
        return WorkdaySourceAdapter(source)
    if t == "smartrecruiters":
        return SmartRecruitersSourceAdapter(source)

    # ── Legacy HTTP / single-board adapters ───────────────────────────────────
    if t in _LEGACY_TYPES:
        return LegacyHttpSourceAdapter(source)

    return LegacyHttpSourceAdapter(source)
