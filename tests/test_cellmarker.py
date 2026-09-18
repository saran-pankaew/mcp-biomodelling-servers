from typing import Any

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