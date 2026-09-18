from typing import Any

from MaBoSS.services import biodivine_models


class _Response:
    text = """ID, name, variables, inputs, regulations
012, T-CELL-RECEPTOR-SIGNALING, 94, 7, 158
050, CD4-T-CELL-SIGNALING, 154, 34, 351
"""

    def raise_for_status(self) -> None:
        return None


def test_search_models_returns_ranked_records_with_database_urls(
    monkeypatch: Any,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_get(url: str, **kwargs: Any) -> _Response:
        calls.append((url, kwargs))
        return _Response()

    monkeypatch.setattr(biodivine_models.requests, "get", fake_get)

    models, source = biodivine_models.search_models("T cell receptor signaling")

    assert source == biodivine_models.BIODIVINE_MODELS_SUMMARY_URL
    assert [model["id"] for model in models] == ["012", "050"]
    assert models[0]["url"].endswith(
        "[id-012]__[var-94]__[in-7]__[T-CELL-RECEPTOR-SIGNALING]"
    )
    assert calls == [(biodivine_models.BIODIVINE_MODELS_SUMMARY_URL, {"timeout": 20})]