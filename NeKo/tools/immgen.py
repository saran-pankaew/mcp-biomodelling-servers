"""ImmGen MCP tool registration."""

from typing import Annotated

from mcp.types import CallToolResult
from pydantic import Field

from ..app import mcp
from ..contracts import NonEmptyString, READ_ONLY_OPEN
from ..services.immgen import lookup_ranked_genes
from ..src.cellmarker_outputs import ImmGenLookupResult
from mcp_biomodelling_servers.structured_outputs import structured_report


@mcp.tool(
    title="Find ranked ImmGen genes",
    annotations=READ_ONLY_OPEN,
    structured_output=True,
)
def find_immgen_genes(
    cell_type: Annotated[
        NonEmptyString,
        Field(description="ImmGen mouse cell type to rank, for example 'CD4 T cell'."),
    ],
    top_n: int = Field(
        20,
        ge=1,
        le=100,
        description="Number of highest-expressed genes to return.",
    ),
) -> Annotated[CallToolResult, ImmGenLookupResult]:
    """Return the highest-expressed genes for one ImmGen mouse cell type."""
    requested_cell_type = cell_type.strip()
    records, source = lookup_ranked_genes(requested_cell_type, top_n)
    genes = [record["gene"] for record in records]
    payload = ImmGenLookupResult(
        server="NeKo",
        cell_type=requested_cell_type,
        species="Mouse",
        top_n=top_n,
        source=source,
        genes=genes,
        records=records,
    )
    text = (
        f"ImmGen returned the top {len(genes)} genes ranked by normalized expression "
        f"for {requested_cell_type}. Use the `genes` field as NeKo input."
    )
    return structured_report(text, payload)