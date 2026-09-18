"""Structured outputs for Biodivine Boolean Models searches."""

from typing import Literal

from pydantic import Field

from mcp_biomodelling_servers.structured_outputs import StructuredOutputModel


class BiodivineModelRecord(StructuredOutputModel):
    """One Boolean model found in the Biodivine Boolean Models dataset."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    variables: int = Field(ge=0)
    inputs: int = Field(ge=0)
    regulations: int = Field(ge=0)
    url: str = Field(min_length=1)


class BiodivineModelSearchResult(StructuredOutputModel):
    """Ranked database matches for a Boolean-model research question."""

    server: Literal["MaBoSS"]
    question: str = Field(min_length=1)
    source: str = Field(min_length=1)
    result_count: int = Field(ge=0)
    models: list[BiodivineModelRecord]