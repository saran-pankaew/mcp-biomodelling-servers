"""Biodivine Boolean Models dataset lookup service."""

from __future__ import annotations

import csv
import io
import os
import re

import requests

BIODIVINE_MODELS_SUMMARY_URL = (
    "https://raw.githubusercontent.com/sybila/biodivine-boolean-models/"
    "main/models/summary.csv"
)
BIODIVINE_MODELS_REPOSITORY_URL = (
    "https://github.com/sybila/biodivine-boolean-models"
)


def _tokens(question: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", question.lower())


def _model_url(model_id: str, name: str, variables: int, inputs: int) -> str:
    directory = (
        f"[id-{model_id}]__[var-{variables}]__[in-{inputs}]__[{name}]"
    )
    return f"{BIODIVINE_MODELS_REPOSITORY_URL}/tree/main/models/{directory}"


def search_models(question: str, limit: int = 10) -> tuple[list[dict[str, int | str]], str]:
    """Search the live Biodivine Boolean Models summary index by model name."""
    endpoint = os.environ.get(
        "BIODIVINE_MODELS_SUMMARY_URL", BIODIVINE_MODELS_SUMMARY_URL
    )
    try:
        response = requests.get(endpoint, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            "The Biodivine Boolean Models database could not be reached. Check "
            "network access or set BIODIVINE_MODELS_SUMMARY_URL to a compatible "
            "summary.csv endpoint."
        ) from exc

    tokens = _tokens(question)
    if not tokens:
        return [], endpoint

    results: list[tuple[int, dict[str, int | str]]] = []
    try:
        rows = csv.DictReader(io.StringIO(response.text), skipinitialspace=True)
        for row in rows:
            model_id = (row.get("ID") or "").strip()
            name = (row.get("name") or "").strip()
            if not model_id or not name:
                continue
            normalized_name = name.lower().replace("-", " ")
            matched_tokens = sum(token in normalized_name for token in tokens)
            if not matched_tokens:
                continue
            score = matched_tokens * 10 + int(" ".join(tokens) in normalized_name)
            variables = int((row.get("variables") or "").strip())
            inputs = int((row.get("inputs") or "").strip())
            results.append(
                (
                    score,
                    {
                        "id": model_id,
                        "name": name,
                        "variables": variables,
                        "inputs": inputs,
                        "regulations": int((row.get("regulations") or "").strip()),
                        "url": _model_url(model_id, name, variables, inputs),
                    },
                )
            )
    except (TypeError, ValueError, csv.Error) as exc:
        raise RuntimeError("The Biodivine Boolean Models summary CSV is invalid.") from exc

    results.sort(key=lambda result: (-result[0], result[1]["name"]))
    return [record for _, record in results[:limit]], endpoint