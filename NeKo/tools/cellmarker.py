"""CellMarker MCP tool registration."""

from typing import Annotated

from mcp.types import CallToolResult
from pydantic import Field

from ..app import mcp
from ..contracts import NonEmptyString, NonEmptyStringList, READ_ONLY_OPEN
from ..services.cellmarker import lookup_markers
from ..src.cellmarker_outputs import CellMarkerLookupResult
from mcp_biomodelling_servers.structured_outputs import structured_report


@mcp.tool(
    title="Find CellMarker genes",
    annotations=READ_ONLY_OPEN,
    structured_output=True,
)
def find_cellmarker_genes(
    cell_types: NonEmptyStringList = Field(
        description="CellMarker cell types to search, for example ['T cell', 'macrophage']."
    ),
    species: Annotated[
        NonEmptyString | None,
        Field(description="Optional organism filter, for example 'Human'."),
    ] = None,
) -> Annotated[CallToolResult, CellMarkerLookupResult]:
    """Return deduplicated CellMarker genes suitable as NeKo seed genes."""
    requested = [cell_type.strip() for cell_type in cell_types]
    if len(requested) != len(set(requested)):
        raise ValueError("cell_types must not contain duplicates.")
    records, genes, source = lookup_markers(requested, species)
    payload = CellMarkerLookupResult(
        server="NeKo",
        requested_cell_types=requested,
        species=species,
        source=source,
        record_count=len(records),
        genes=genes,
        records=records,
    )
    text = (
        f"CellMarker returned {len(genes)} unique genes from "
        f"{len(records)} marker records. Use the `genes` field as NeKo input."
    )
    return structured_report(text, payload)