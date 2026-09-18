"""CellMarker lookup service."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import sqlite3
from typing import Any

import requests

CELLMARKER_DEFAULT_DATA_URL = (
    "https://bio-bigdata.hrbmu.edu.cn/CellMarker/download/human_cell_marker.txt"
)
CELLMARKER_DATA_PATH_ENV = "CELLMARKER_DATA_PATH"
DEFAULT_CELLMARKER_DATA_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "human_cell_marker.txt"
)


def _first_value(record: dict[str, Any], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = record.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _download_default_marker_table(data_path: Path) -> Path:
    """Download the default CellMarker table once and publish it only when complete."""
    data_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = data_path.with_name(f".{data_path.name}.part")
    try:
        with requests.get(
            CELLMARKER_DEFAULT_DATA_URL,
            stream=True,
            timeout=180,
        ) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as data_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        data_file.write(chunk)
        temporary_path.replace(data_path)
    except (OSError, requests.RequestException) as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            "The default CellMarker human marker table could not be downloaded. Set "
            f"{CELLMARKER_DATA_PATH_ENV} to a compatible local marker table."
        ) from exc
    return data_path


def _lookup_local_records(
    data_path: Path,
    cell_types: list[str],
    species: str | None,
) -> list[dict[str, Any]]:
    if not data_path.is_file():
        raise RuntimeError(f"CellMarker data file does not exist: {data_path}")

    requested_types = {cell_type.casefold() for cell_type in cell_types}
    requested_species = species.casefold() if species else None
    if data_path.suffix.lower() in {".csv", ".tsv", ".txt"}:
        delimiter = "\t" if data_path.suffix.lower() in {".tsv", ".txt"} else ","
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
            "CellMarker local data must be a .csv, .tsv, .txt, .db, .sqlite, or .sqlite3 file."
        )

    return [
        record
        for record in records
        if (
            _first_value(record, ("cell_type", "cell", "celltype", "cellName", "cell_name"))
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
        ("gene", "gene_symbol", "marker_gene", "symbol", "geneSymbol", "marker"),
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
    data_path = (
        Path(local_data).expanduser().resolve()
        if local_data
        else DEFAULT_CELLMARKER_DATA_PATH
    )
    if not local_data and not data_path.is_file():
        data_path = _download_default_marker_table(data_path)
    records = _lookup_local_records(data_path, cell_types, species)
    endpoint = data_path.as_uri()

    normalized: list[dict[str, str | None]] = []
    gene_source_counts: dict[str, int] = {}
    for record in records:
        matched_type = _first_value(
            record,
            ("cell_type", "cell", "celltype", "cellName", "cell_name"),
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
            gene_source_counts[gene] = gene_source_counts.get(gene, 0) + 1
    genes = sorted(
        gene_source_counts,
        key=lambda gene: (-gene_source_counts[gene], gene.casefold()),
    )
    return normalized, genes, endpoint