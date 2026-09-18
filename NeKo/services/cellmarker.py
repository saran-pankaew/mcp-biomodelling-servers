"""CellMarker lookup service."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import sqlite3
from typing import Any

import requests

CELLMARKER_API_URL = (
    "https://bio-bigdata.hrbmu.edu.cn/CellMarker/api/markers"
)
CELLMARKER_DATA_PATH_ENV = "CELLMARKER_DATA_PATH"


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


def _lookup_local_records(
    data_path: Path,
    cell_types: list[str],
    species: str | None,
) -> list[dict[str, Any]]:
    if not data_path.is_file():
        raise RuntimeError(f"CellMarker data file does not exist: {data_path}")

    requested_types = {cell_type.casefold() for cell_type in cell_types}
    requested_species = species.casefold() if species else None
    if data_path.suffix.lower() in {".csv", ".tsv"}:
        delimiter = "\t" if data_path.suffix.lower() == ".tsv" else ","
        with data_path.open(newline="", encoding="utf-8") as data_file:
            records = list(csv.DictReader(data_file, delimiter=delimiter))
    elif data_path.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        placeholders = ", ".join("?" for _ in cell_types)
        query = (
            "SELECT * FROM markers WHERE cell_type COLLATE NOCASE IN "
            f"({placeholders})"
        )
        values: list[str] = list(cell_types)
        if species:
            query += " AND species COLLATE NOCASE = ?"
            values.append(species)
        with sqlite3.connect(f"file:{data_path}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            try:
                records = [dict(row) for row in connection.execute(query, values)]
            except sqlite3.DatabaseError as exc:
                raise RuntimeError(
                    "CellMarker SQLite data must contain a 'markers' table with "
                    "cell_type and species columns."
                ) from exc
    else:
        raise RuntimeError(
            "CellMarker local data must be a .csv, .tsv, .db, .sqlite, or .sqlite3 file."
        )

    return [
        record
        for record in records
        if (
            _first_value(record, ("cell_type", "cell", "celltype", "cellName"))
            or ""
        ).casefold()
        in requested_types
        and (
            requested_species is None
            or (
                _first_value(record, ("species", "organism", "speciesType")) or ""
            ).casefold()
            == requested_species
        )
    ]


def _genes_from_record(record: dict[str, Any]) -> list[str]:
    gene = _first_value(
        record,
        ("gene", "gene_symbol", "marker_gene", "symbol", "geneSymbol"),
    )
    if gene is None:
        return []
    if "geneSymbol" not in record:
        return [gene]
    return [symbol.strip().strip("[]") for symbol in gene.split(",") if symbol.strip().strip("[]")]


def lookup_markers(
    cell_types: list[str],
    species: str | None = None,
) -> tuple[list[dict[str, str | None]], list[str], str]:
    """Look up CellMarker records and return normalized genes for NeKo."""
    local_data = os.environ.get(CELLMARKER_DATA_PATH_ENV)
    if local_data:
        data_path = Path(local_data).expanduser().resolve()
        records = _lookup_local_records(data_path, cell_types, species)
        endpoint = data_path.as_uri()
    else:
        endpoint = os.environ.get("CELLMARKER_API_URL", CELLMARKER_API_URL)
        params: list[tuple[str, str]] = [("cell_type", cell_type) for cell_type in cell_types]
        if species:
            params.append(("species", species))
        try:
            response = requests.get(endpoint, params=params, timeout=20)
            response.raise_for_status()
            records = _records_from_payload(response.json())
        except requests.RequestException as exc:
            response_status = getattr(exc.response, "status_code", None)
            detail = f" (HTTP {response_status})" if response_status else ""
            raise RuntimeError(
                "CellMarker could not be reached"
                f"{detail}. Set {CELLMARKER_DATA_PATH_ENV} to a local CellMarker "
                "CSV, TSV, or SQLite database, or set CELLMARKER_API_URL to a "
                "compatible API endpoint."
            ) from exc
        except ValueError as exc:
            raise RuntimeError("CellMarker returned invalid JSON.") from exc

    normalized: list[dict[str, str | None]] = []
    genes: set[str] = set()
    for record in records:
        matched_type = _first_value(
            record,
            ("cell_type", "cell", "celltype", "cellName"),
        )
        for gene in _genes_from_record(record):
            normalized.append(
                {
                    "cell_type": matched_type,
                    "gene": gene,
                    "species": _first_value(
                        record,
                        ("species", "organism", "speciesType"),
                    ),
                    "tissue": _first_value(record, ("tissue", "organ", "tissueType")),
                    "evidence": _first_value(
                        record,
                        ("evidence", "source", "pmid", "PMID"),
                    ),
                }
            )
            genes.add(gene)
    return normalized, sorted(genes), endpoint