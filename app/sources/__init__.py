"""Job source adapters for discovery polling."""

from app.sources.base import DiscoveryContext, JobSourceAdapter, SourceHealth
from app.sources.registry import get_adapter_for_source

__all__ = [
    "DiscoveryContext",
    "JobSourceAdapter",
    "SourceHealth",
    "get_adapter_for_source",
]
