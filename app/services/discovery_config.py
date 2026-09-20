"""Discovery configuration shared by hunt manager and scheduler."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RemotePreference = Literal["remote", "hybrid", "onsite", "no_preference"]


class JobDiscoveryConfig(BaseModel):
    urls: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_preference: RemotePreference = "no_preference"
    limit_per_source: int = Field(default=25, ge=1, le=250)
    run_search: bool = True
