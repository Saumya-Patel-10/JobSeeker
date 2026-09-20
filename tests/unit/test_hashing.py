"""Hashing helpers should be deterministic and URL-normalizing."""

from __future__ import annotations

from app.utils.hashing import content_fingerprint, short_hash, stable_hash, url_hash


def test_stable_hash_is_deterministic() -> None:
    assert stable_hash({"a": 1, "b": 2}) == stable_hash({"b": 2, "a": 1})


def test_stable_hash_differs_for_distinct_input() -> None:
    assert stable_hash({"a": 1}) != stable_hash({"a": 2})


def test_short_hash_length() -> None:
    h = short_hash("anything", length=8)
    assert len(h) == 8


def test_url_hash_normalizes_trailing_slash() -> None:
    a = url_hash("https://boards.greenhouse.io/example/jobs/1/")
    b = url_hash("https://boards.greenhouse.io/example/jobs/1")
    assert a == b


def test_url_hash_strips_fragment() -> None:
    a = url_hash("https://boards.greenhouse.io/example/jobs/1#apply")
    b = url_hash("https://boards.greenhouse.io/example/jobs/1")
    assert a == b


def test_url_hash_preserves_query() -> None:
    a = url_hash("https://example.com/jobs?id=1")
    b = url_hash("https://example.com/jobs?id=2")
    assert a != b


def test_content_fingerprint_case_insensitive() -> None:
    a = content_fingerprint("Backend Engineer", "Acme")
    b = content_fingerprint(" backend engineer ", "acme")
    assert a == b
