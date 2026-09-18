"""MCP tool registration for Biodivine Boolean Models searches."""

from typing import Annotated

from mcp.types import CallToolResult, ToolAnnotations
from pydantic import Field

from mcp_biomodelling_servers.structured_outputs import structured_report

from ..app import mcp
from ..biodivine_outputs import BiodivineModelSearchResult
from ..contracts import NonEmptyString
from ..services.biodivine_models import search_models

_READ_ONLY_OPEN = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)


@mcp.tool(
    title="Search Biodivine Boolean Models",
    annotations=_READ_ONLY_OPEN,
    structured_output=True,
)
def search_biodivine_boolean_models(
    question: NonEmptyString = Field(
        description=(
            "Question or keywords describing the biological process or model, "
            "for example 'T cell receptor signaling'."
        )
    ),
    limit: int = Field(default=10, ge=1, le=25),
) -> Annotated[CallToolResult, BiodivineModelSearchResult]:
    """Find Boolean models in the live Biodivine Boolean Models dataset."""
    normalized_question = question.strip()
    models, source = search_models(normalized_question, limit)
    payload = BiodivineModelSearchResult(
        server="MaBoSS",
        question=normalized_question,
        source=source,
        result_count=len(models),
        models=models,
    )
    text = (
        f"Biodivine Boolean Models returned {len(models)} matches. Each result "
        "links to its database directory, which contains the available model files."
    )
    return structured_report(text, payload)