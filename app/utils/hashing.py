"""Stable hashing helpers used for deduplication and content fingerprinting."""

from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import urlparse, urlunparse


def stable_hash(value: Any) -> str:
    """SHA-256 hex digest of any JSON-serializable value (keys sorted)."""
    encoded = json.dumps(value, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def short_hash(value: Any, length: int = 12) -> str:
    """Truncated :func:`stable_hash` for friendlier IDs."""
    return stable_hash(value)[:length]


def url_hash(url: str) -> str:
    """Hash a URL after a light normalization pass.

    Normalization: strip fragment, lowercase scheme/host, drop trailing slash
    from path. Query strings are preserved because many ATS URLs encode the
    job id there.
    """
    parsed = urlparse(url.strip())
    normalized = urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            parsed.params,
            parsed.query,
            "",
        )
    )
    return stable_hash(normalized)


def content_fingerprint(*parts: str) -> str:
    """Fingerprint multiple text parts after normalization (lower + strip)."""
    normalized = [p.strip().lower() for p in parts if p]
    return stable_hash(normalized)
