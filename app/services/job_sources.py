"""Shared job source URL resolution for CLI and API workflows."""

from __future__ import annotations

import httpx

from app.config.schema import JobSource
from app.utils.logging import get_logger

log = get_logger(__name__)


async def resolve_urls_for_source(source: JobSource, limit: int) -> list[str]:
    if source.type == "url_list":
        raw = source.config.get("urls", [])
        return list(raw) if isinstance(raw, list) else []

    if source.type == "greenhouse_board":
        token = source.config.get("board_token")
        if not token:
            return []
        url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
            data = resp.json()
        except Exception as exc:
            log.warning("job_sources.greenhouse_failed", source=source.name, error=str(exc))
            return []
        keywords = source.config.get("keywords") or []
        keywords = [str(k).lower() for k in keywords] if isinstance(keywords, list) else []
        urls: list[str] = []
        for job_obj in data.get("jobs", []):
            title = (job_obj.get("title") or "").lower()
            if keywords and not any(k in title for k in keywords):
                continue
            absolute = job_obj.get("absolute_url")
            if absolute:
                urls.append(absolute)
            if len(urls) >= limit:
                break
        return urls

    if source.type == "lever_board":
        site = source.config.get("site_id")
        if not site:
            return []
        url = f"https://api.lever.co/v0/postings/{site}?mode=json"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
            postings = resp.json()
        except Exception as exc:
            log.warning("job_sources.lever_failed", source=source.name, error=str(exc))
            return []
        department = source.config.get("department")
        urls: list[str] = []
        for posting in postings:
            if department:
                team = (posting.get("categories") or {}).get("department")
                if team and str(team).lower() != str(department).lower():
                    continue
            absolute = posting.get("hostedUrl")
            if absolute:
                urls.append(absolute)
            if len(urls) >= limit:
                break
        return urls

    return []


async def collect_source_urls(
    sources: list[JobSource],
    *,
    limit: int,
) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for source in sources:
        urls = await resolve_urls_for_source(source, limit)
        output[source.name] = urls
    return output
