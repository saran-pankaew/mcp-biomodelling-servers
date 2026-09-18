"""Structured outputs for CellMarker lookups."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from mcp_biomodelling_servers.structured_outputs import StructuredOutputModel


class CellMarkerRecord(StructuredOutputModel):
    """One normalized CellMarker marker record."""

    cell_type: str | None = None
    gene: str = Field(min_length=1)
    species: str | None = None
    tissue: str | None = None
    evidence: str | None = None


class CellMarkerLookupResult(StructuredOutputModel):
    """CellMarker records and deduplicated genes ready for NeKo."""

    server: Literal["NeKo"]
    requested_cell_types: list[str] = Field(min_length=1)
    species: str | None = None
    source: str = Field(min_length=1)
    record_count: int = Field(ge=0)
    genes: list[str]
    records: list[CellMarkerRecord]