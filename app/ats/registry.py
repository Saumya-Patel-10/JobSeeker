"""ATS adapter registry + URL routing.

Order matters: the first adapter whose ``detect`` returns True wins.
``GenericAdapter`` is the explicit fallback so unknown URLs still get
processed (just slower, via Playwright + LLM field classification).
"""

from __future__ import annotations

from typing import Any

from app.ats.base import ATSAdapter
from app.ats.generic import GenericAdapter
from app.ats.greenhouse import GreenhouseAdapter
from app.ats.lever import LeverAdapter
from app.ats.linkedin import LinkedInAdapter
from app.utils.errors import AdapterNotFoundError

SPECIFIC_ADAPTERS: list[type[ATSAdapter]] = [
    GreenhouseAdapter,
    LeverAdapter,
    LinkedInAdapter,
]


def detect_adapter_class(url: str, html: str | None = None) -> type[ATSAdapter]:
    """Return the most specific adapter class for ``url``."""
    for adapter_cls in SPECIFIC_ADAPTERS:
        if adapter_cls.detect(url, html):
            return adapter_cls
    return GenericAdapter


def adapter_for(
    url: str,
    *,
    session: Any | None = None,
    llm: Any | None = None,
    prompts: Any | None = None,
    html: str | None = None,
) -> ATSAdapter:
    """Instantiate the right adapter, plumbing the LLM into the generic one."""
    cls = detect_adapter_class(url, html)
    if cls is GenericAdapter:
        return GenericAdapter(session=session, llm=llm, prompts=prompts)
    return cls(session=session)


def adapter_by_name(name: str, *, session: Any | None = None, **kwargs: Any) -> ATSAdapter:
    """Lookup by short name (``greenhouse``, ``lever``, ``linkedin``, ``generic``)."""
    by_name = {cls.name: cls for cls in [*SPECIFIC_ADAPTERS, GenericAdapter]}
    if name not in by_name:
        raise AdapterNotFoundError(f"Unknown adapter: {name}")
    cls = by_name[name]
    if cls is GenericAdapter:
        return GenericAdapter(session=session, **kwargs)
    return cls(session=session)
