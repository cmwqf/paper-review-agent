"""Purpose: Normalize paper metadata such as title, venue, and submission date."""

from __future__ import annotations

from datetime import date


def normalize_metadata(raw: dict) -> dict:
    """Normalize metadata fields used by retrieval time filtering."""
    metadata = dict(raw)
    submission_date = metadata.get("submission_date")
    if isinstance(submission_date, str):
        metadata["submission_date"] = date.fromisoformat(submission_date)
    return metadata

