"""Ranked gene lookup from local ImmGen normalized expression tables."""

from __future__ import annotations

import csv
import os
from pathlib import Path

import requests

IMMGEN_DATA_PATH_ENV = "IMMGEN_DATA_PATH"
IMMGEN_DEFAULT_DATA_URL = (
    "https://sharehost.hms.harvard.edu/immgen/GSE109125/"
    "GSE109125_Normalized_Gene_count_table.csv"
)
DEFAULT_IMMGEN_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "GSE109125_Normalized_Gene_count_table.csv"
)
_CELL_TYPE_COLUMNS = ("cell_type", "cell", "celltype", "population")
_EXPRESSION_COLUMNS = (
    "expression",
    "normalized_expression",
    "expression_value",
    "value",
)
_GENE_COLUMNS = ("gene", "gene_symbol", "symbol", "genesymbol")


def _download_default_expression_table(data_path: Path) -> Path:
    """Download the default table once and publish it only when complete."""
    data_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = data_path.with_name(f".{data_path.name}.part")
    try:
        with requests.get(IMMGEN_DEFAULT_DATA_URL, stream=True, timeout=180) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as data_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        data_file.write(chunk)
        temporary_path.replace(data_path)
    except (OSError, requests.RequestException) as exc:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            "ImmGen GSE109125 could not be downloaded. Set "
            f"{IMMGEN_DATA_PATH_ENV} to a compatible local expression table."
        ) from exc
    return data_path


def _column_name(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    by_normalized_name = {name.casefold(): name for name in fieldnames}
    for candidate in candidates:
        if column := by_normalized_name.get(candidate):
            return column
    return None


def _read_expression_table(data_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not data_path.is_file():
        raise RuntimeError(f"ImmGen data file does not exist: {data_path}")
    if data_path.suffix.lower() not in {".csv", ".tsv"}:
        raise RuntimeError("ImmGen data must be a normalized .csv or .tsv expression table.")

    delimiter = "\t" if data_path.suffix.lower() == ".tsv" else ","
    with data_path.open(newline="", encoding="utf-8") as data_file:
        reader = csv.DictReader(data_file, delimiter=delimiter)
        if reader.fieldnames is None:
            raise RuntimeError("ImmGen expression table must include a header row.")
        return reader.fieldnames, [row for row in reader if row]


def _rank_genes(
    rows: list[dict[str, str]],
    *,
    cell_type: str,
    fieldnames: list[str],
) -> list[tuple[str, float]]:
    gene_column = _column_name(fieldnames, _GENE_COLUMNS)
    if gene_column is None:
        raise RuntimeError(
            "ImmGen expression table must contain a gene, gene_symbol, symbol, or geneSymbol column."
        )

    cell_type_column = _column_name(fieldnames, _CELL_TYPE_COLUMNS)
    expression_column = _column_name(fieldnames, _EXPRESSION_COLUMNS)
    if cell_type_column and expression_column:
        expression_by_gene: dict[str, float] = {}
        for row in rows:
            if (row.get(cell_type_column) or "").strip().casefold() != cell_type.casefold():
                continue
            gene = (row.get(gene_column) or "").strip()
            try:
                expression = float((row.get(expression_column) or "").strip())
            except ValueError:
                continue
            if gene:
                expression_by_gene[gene] = max(expression, expression_by_gene.get(gene, expression))
    else:
        exact_columns = [
            name for name in fieldnames if name.casefold() == cell_type.casefold()
        ]
        expression_columns = exact_columns or [
            name
            for name in fieldnames
            if name.casefold().startswith(f"{cell_type.casefold()}.")
        ]
        if not expression_columns:
            raise ValueError(
                f"ImmGen has no '{cell_type}' cell type. For long tables, use a cell_type and expression column; "
                "for wide tables, use the exact cell type or its replicate-column prefix."
            )
        expression_by_gene = {}
        for row in rows:
            gene = (row.get(gene_column) or "").strip()
            expressions: list[float] = []
            for expression_column in expression_columns:
                try:
                    expressions.append(float((row.get(expression_column) or "").strip()))
                except ValueError:
                    continue
            if gene and expressions:
                expression = sum(expressions) / len(expressions)
                expression_by_gene[gene] = max(expression, expression_by_gene.get(gene, expression))

    if not expression_by_gene:
        raise ValueError(f"ImmGen has no expression values for '{cell_type}'.")
    return sorted(expression_by_gene.items(), key=lambda item: (-item[1], item[0].casefold()))


def lookup_ranked_genes(
    cell_type: str,
    top_n: int = 20,
) -> tuple[list[dict[str, str | float | int]], str]:
    """Return the highest-expressed genes for one ImmGen cell type."""
    local_data = os.environ.get(IMMGEN_DATA_PATH_ENV)
    data_path = (
        Path(local_data).expanduser().resolve()
        if local_data
        else DEFAULT_IMMGEN_DATA_PATH
    )
    if not local_data and not data_path.is_file():
        data_path = _download_default_expression_table(data_path)
    fieldnames, rows = _read_expression_table(data_path)
    ranked_genes = _rank_genes(rows, cell_type=cell_type, fieldnames=fieldnames)
    records = [
        {
            "cell_type": cell_type,
            "gene": gene,
            "rank": rank,
            "expression": expression,
        }
        for rank, (gene, expression) in enumerate(ranked_genes[:top_n], start=1)
    ]
    return records, data_path.as_uri()