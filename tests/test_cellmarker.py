from typing import Any

import sqlite3

from NeKo.services import cellmarker


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "data": [
                {"cell_type": "T cell", "gene": "CD3D", "pmid": "1"},
                {"cell_type": "T cell", "gene_symbol": "IL7R"},
                {"cell_type": "T cell", "gene": "CD3D"},
            ]
        }


def test_lookup_markers_normalizes_records_and_genes(
    monkeypatch: Any,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_get(url: str, **kwargs: Any) -> _Response:
        calls.append((url, kwargs))
        return _Response()

    monkeypatch.setattr(cellmarker.requests, "get", fake_get)

    records, genes, source = cellmarker.lookup_markers(["T cell"], "Human")

    assert source == cellmarker.CELLMARKER_API_URL
    assert genes == ["CD3D", "IL7R"]
    assert records[0]["evidence"] == "1"
    assert calls[0][1]["params"] == [
        ("cell_type", "T cell"),
        ("species", "Human"),
    ]


def test_lookup_markers_reads_local_sqlite_without_http(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    database_path = tmp_path / "cellmarker.sqlite"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "CREATE TABLE markers (cell_type TEXT, gene TEXT, species TEXT, tissue TEXT)"
        )
        connection.executemany(
            "INSERT INTO markers VALUES (?, ?, ?, ?)",
            [
                ("T cell", "CD3D", "Human", "Blood"),
                ("T cell", "Trac", "Mouse", "Spleen"),
                ("B cell", "MS4A1", "Human", "Blood"),
            ],
        )

    def fail_get(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("local lookup must not call the CellMarker API")

    monkeypatch.setenv(cellmarker.CELLMARKER_DATA_PATH_ENV, str(database_path))
    monkeypatch.setattr(cellmarker.requests, "get", fail_get)

    records, genes, source = cellmarker.lookup_markers(["T cell"], "Human")

    assert genes == ["CD3D"]
    assert records == [
        {
            "cell_type": "T cell",
            "gene": "CD3D",
            "species": "Human",
            "tissue": "Blood",
            "evidence": None,
        }
    ]
    assert source == database_path.resolve().as_uri()


def test_lookup_markers_reads_local_csv(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "cellmarker.csv"
    data_path.write_text(
        "cell_type,gene,species,tissue\nT cell,CD3E,Human,Blood\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(cellmarker.CELLMARKER_DATA_PATH_ENV, str(data_path))

    records, genes, source = cellmarker.lookup_markers(["t CELL"], "human")

    assert genes == ["CD3E"]
    assert records[0]["tissue"] == "Blood"
    assert source == data_path.resolve().as_uri()


def test_lookup_markers_reads_official_cellmarker_tsv_columns(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "Human_cell_markers.tsv"
    data_path.write_text(
        "speciesType\ttissueType\tcellName\tgeneSymbol\tPMID\n"
        "Human\tBlood\tCD4+ T cell\tIL7R\t12345\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(cellmarker.CELLMARKER_DATA_PATH_ENV, str(data_path))

    records, genes, _ = cellmarker.lookup_markers(["CD4+ T cell"], "Human")

    assert genes == ["IL7R"]
    assert records[0]["evidence"] == "12345"


def test_lookup_markers_expands_official_marker_sets(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "Human_cell_markers.tsv"
    data_path.write_text(
        "speciesType\tcellName\tgeneSymbol\n"
        "Human\tCD4+ T cell\t[CD3D, CD3E], CD4\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(cellmarker.CELLMARKER_DATA_PATH_ENV, str(data_path))

    records, genes, _ = cellmarker.lookup_markers(["CD4+ T cell"], "Human")

    assert genes == ["CD3D", "CD3E", "CD4"]
    assert [record["gene"] for record in records] == ["CD3D", "CD3E", "CD4"]