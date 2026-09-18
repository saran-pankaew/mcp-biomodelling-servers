"""CellMarker lookup service."""

from __future__ import annotations

import os
from typing import Any

import requests

CELLMARKER_API_URL = (
    "https://bio-bigdata.hrbmu.edu.cn/CellMarker/api/markers"
)


def _first_value(record: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = record.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _records_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        raise ValueError("CellMarker returned a JSON value with no records.")
    for key in ("data", "results", "records", "rows"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return [payload]


def lookup_markers(
    cell_types: list[str],
    species: str | None = None,
) -> tuple[list[dict[str, str | None]], list[str], str]:
    """Look up CellMarker records and return normalized genes for NeKo."""
    endpoint = os.environ.get("CELLMARKER_API_URL", CELLMARKER_API_URL)
    params: list[tuple[str, str]] = [("cell_type", cell_type) for cell_type in cell_types]
    if species:
        params.append(("species", species))
    try:
        response = requests.get(endpoint, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(
            "CellMarker could not be reached. Check network access or set "
            "CELLMARKER_API_URL to a compatible CellMarker API endpoint."
        ) from exc
    except ValueError as exc:
        raise RuntimeError("CellMarker returned invalid JSON.") from exc

    normalized: list[dict[str, str | None]] = []
    genes: set[str] = set()
    for record in _records_from_payload(payload):
        gene = _first_value(record, ("gene", "gene_symbol", "marker_gene", "symbol"))
        if gene is None:
            continue
        matched_type = _first_value(record, ("cell_type", "cell", "celltype"))
        normalized.append(
            {
                "cell_type": matched_type,
                "gene": gene,
                "species": _first_value(record, ("species", "organism")),
                "tissue": _first_value(record, ("tissue", "organ")),
                "evidence": _first_value(record, ("evidence", "source", "pmid")),
            }
        )
        genes.add(gene)
    return normalized, sorted(genes), endpoint