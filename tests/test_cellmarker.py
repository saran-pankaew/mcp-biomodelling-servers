import sqlite3
from typing import Any

from NeKo.services import cellmarker
from NeKo.services import immgen


def test_lookup_markers_normalizes_records_and_genes(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "cellmarker.tsv"
    data_path.write_text(
        "cell_type\tgene\tpmid\tspecies\n"
        "T cell\tCD3D\t1\tHuman\nT cell\tIL7R\t\tHuman\nT cell\tCD3D\t\tHuman\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(cellmarker.CELLMARKER_DATA_PATH_ENV, str(data_path))

    records, genes, source = cellmarker.lookup_markers(["T cell"], "Human")

    assert source == data_path.resolve().as_uri()
    assert genes == ["CD3D", "IL7R"]
    assert records[0]["evidence"] == "1"


def test_lookup_markers_ranks_genes_by_marker_source_count(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "cellmarker.tsv"
    data_path.write_text(
        "cell_type\tgene\nT cell\tZAP70\nT cell\tCD3D\nT cell\tZAP70\n"
        "T cell\tCD3D\nT cell\tZAP70\nT cell\tIL7R\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(cellmarker.CELLMARKER_DATA_PATH_ENV, str(data_path))

    _, genes, _ = cellmarker.lookup_markers(["T cell"])

    assert genes == ["ZAP70", "CD3D", "IL7R"]


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


def test_lookup_markers_reads_default_human_cellmarker_table(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "human_cell_marker.txt"
    data_path.write_text(
        "species\tcell_name\tmarker\tpmid\nHuman\tFibroblast\tDCN\t12345\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(cellmarker.CELLMARKER_DATA_PATH_ENV, raising=False)
    monkeypatch.setattr(cellmarker, "DEFAULT_CELLMARKER_DATA_PATH", data_path)

    records, genes, source = cellmarker.lookup_markers(["Fibroblast"], "Human")

    assert genes == ["DCN"]
    assert records[0]["evidence"] == "12345"
    assert source == data_path.as_uri()


def test_lookup_markers_downloads_default_when_cache_is_missing(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "human_cell_marker.txt"
    downloaded = b"species\tcell_name\tmarker\nHuman\tFibroblast\tDCN\n"
    calls: list[tuple[str, dict[str, Any]]] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_content(self, chunk_size: int) -> list[bytes]:
            assert chunk_size == 1024 * 1024
            return [downloaded]

    def fake_get(url: str, **kwargs: Any) -> Response:
        calls.append((url, kwargs))
        return Response()

    monkeypatch.delenv(cellmarker.CELLMARKER_DATA_PATH_ENV, raising=False)
    monkeypatch.setattr(cellmarker, "DEFAULT_CELLMARKER_DATA_PATH", data_path)
    monkeypatch.setattr(cellmarker.requests, "get", fake_get)

    _, genes, source = cellmarker.lookup_markers(["Fibroblast"], "Human")

    assert genes == ["DCN"]
    assert source == data_path.as_uri()
    assert data_path.read_bytes() == downloaded
    assert calls == [
        (
            cellmarker.CELLMARKER_DEFAULT_DATA_URL,
            {"stream": True, "timeout": 180},
        )
    ]


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


def test_lookup_ranked_genes_reads_long_expression_table(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "immgen.tsv"
    data_path.write_text(
        "cell_type\tgene_symbol\tnormalized_expression\n"
        "CD4 T cell\tIl7r\t12.5\n"
        "CD4 T cell\tLef1\t18.0\n"
        "CD4 T cell\tIl7r\t10.0\n"
        "B cell\tCd79a\t22.0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(immgen.IMMGEN_DATA_PATH_ENV, str(data_path))

    records, source = immgen.lookup_ranked_genes("cd4 t CELL", top_n=1)

    assert records == [
        {
            "cell_type": "cd4 t CELL",
            "gene": "Lef1",
            "rank": 1,
            "expression": 18.0,
        }
    ]
    assert source == data_path.resolve().as_uri()


def test_lookup_ranked_genes_reads_wide_expression_table(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "immgen.csv"
    data_path.write_text(
        "gene,CD8 T cell,B cell\nGzmb,25.0,0.5\nCd3d,18.0,1.0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(immgen.IMMGEN_DATA_PATH_ENV, str(data_path))

    records, _ = immgen.lookup_ranked_genes("cd8 t cell")

    assert [record["gene"] for record in records] == ["Gzmb", "Cd3d"]
    assert [record["rank"] for record in records] == [1, 2]


def test_lookup_ranked_genes_averages_wide_replicate_columns(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "immgen.csv"
    data_path.write_text(
        "gene_symbol,T.4.Nve.Sp#1.1,T.4.Nve.Sp#1.2\n"
        "Lef1,15.0,21.0\nIl7r,20.0,10.0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(immgen.IMMGEN_DATA_PATH_ENV, str(data_path))

    records, _ = immgen.lookup_ranked_genes("T.4.Nve")

    assert [record["gene"] for record in records] == ["Lef1", "Il7r"]
    assert records[0]["expression"] == 18.0


def test_lookup_ranked_genes_uses_bundled_default_when_not_overridden(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "immgen.csv"
    data_path.write_text(
        "gene_symbol,T.4.Nve.Sp#1\nLef1,18.0\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(immgen.IMMGEN_DATA_PATH_ENV, raising=False)
    monkeypatch.setattr(immgen, "DEFAULT_IMMGEN_DATA_PATH", data_path)

    records, source = immgen.lookup_ranked_genes("T.4.Nve")

    assert records[0]["gene"] == "Lef1"
    assert source == data_path.as_uri()


def test_lookup_ranked_genes_downloads_default_when_cache_is_missing(
    monkeypatch: Any,
    tmp_path: Any,
) -> None:
    data_path = tmp_path / "immgen.csv"
    downloaded = b"gene_symbol,T.4.Nve.Sp#1\nLef1,18.0\n"
    calls: list[tuple[str, dict[str, Any]]] = []

    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def raise_for_status(self) -> None:
            return None

        def iter_content(self, chunk_size: int) -> list[bytes]:
            assert chunk_size == 1024 * 1024
            return [downloaded]

    def fake_get(url: str, **kwargs: Any) -> Response:
        calls.append((url, kwargs))
        return Response()

    monkeypatch.delenv(immgen.IMMGEN_DATA_PATH_ENV, raising=False)
    monkeypatch.setattr(immgen, "DEFAULT_IMMGEN_DATA_PATH", data_path)
    monkeypatch.setattr(immgen.requests, "get", fake_get)

    records, source = immgen.lookup_ranked_genes("T.4.Nve")

    assert records[0]["gene"] == "Lef1"
    assert source == data_path.as_uri()
    assert data_path.read_bytes() == downloaded
    assert calls == [
        (
            immgen.IMMGEN_DEFAULT_DATA_URL,
            {"stream": True, "timeout": 180},
        )
    ]