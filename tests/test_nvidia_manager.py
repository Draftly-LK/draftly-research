from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from LLMs.nvidia import (
    NvidiaManager,
    build_model_catalog,
    load_api_keys,
    parse_model_card_page,
    save_model_catalog,
)


def test_numbered_keys_are_ordered_and_override_legacy_forms() -> None:
    environ = {
        "NVIDIA_API_KEY_10": "ten",
        "NVIDIA_API_KEY_2": "two",
        "NVIDIA_API_KEY_1": "one",
        "NVIDIA_API_KEYS": "two, shared",
        "NVIDIA_API_KEY": "legacy",
    }

    assert load_api_keys(environ) == ["one", "two", "ten"]


def test_key_list_falls_back_to_legacy_key() -> None:
    assert load_api_keys({"NVIDIA_API_KEYS": "one, two, one"}) == ["one", "two"]
    assert load_api_keys({"NVIDIA_API_KEY": "legacy"}) == ["legacy"]


def test_manager_round_robins_successful_requests() -> None:
    calls: list[str] = []

    class FakeCompletions:
        def __init__(self, key: str) -> None:
            self.key = key

        def create(self, **kwargs):
            calls.append(self.key)
            return kwargs

    def factory(*, api_key: str, **_kwargs):
        return SimpleNamespace(
            chat=SimpleNamespace(completions=FakeCompletions(api_key)),
            models=SimpleNamespace(),
        )

    manager = NvidiaManager(["first", "second"], client_factory=factory)

    manager.create_chat_completion(model="example/model", messages=[])
    manager.create_chat_completion(model="example/model", messages=[])
    manager.create_chat_completion(model="example/model", messages=[])

    assert calls == ["first", "second", "first"]


def test_manager_requires_at_least_one_key() -> None:
    with pytest.raises(ValueError, match="No NVIDIA API key found"):
        NvidiaManager([])


def test_list_models_is_sorted_and_unique() -> None:
    def factory(**_kwargs):
        models = SimpleNamespace(
            list=lambda: SimpleNamespace(
                data=[
                    SimpleNamespace(id="z/model"),
                    SimpleNamespace(id="a/model"),
                    SimpleNamespace(id="z/model"),
                ]
            )
        )
        return SimpleNamespace(models=models, chat=SimpleNamespace())

    manager = NvidiaManager(["key"], client_factory=factory)

    assert manager.list_models() == ["a/model", "z/model"]


def test_parse_model_card_page_resolves_metadata_and_markdown() -> None:
    state = [
        "$",
        "$component",
        None,
        {
            "initialState": {
                "artifact": {
                    "artifactType": "ENDPOINT",
                    "name": "example-model",
                    "displayName": "Example Model",
                    "publisher": "example",
                    "shortDescription": "Short description.",
                    "description": "$ab",
                    "labels": ["Chat"],
                    "attributes": [{"key": "AVAILABLE", "value": "true"}],
                    "createdDate": "2026-01-01T00:00:00Z",
                    "updatedDate": "2026-01-02T00:00:00Z",
                },
                "openApiSpec": {
                    "info": {
                        "license": {"name": "Example License"},
                        "termsOfService": "https://example.test/terms",
                    }
                },
            }
        },
    ]
    state_chunk = "1:" + json.dumps(state, separators=(",", ":"))
    metadata_chunk = (
        '2:{"specifications":{"contextLength":4096},'
        '"modelCapability":{"functionCalling":true}}'
    )
    markdown = "# Example\n\nFull model description."
    page = "".join(
        f"<script>self.__next_f.push({json.dumps([1, chunk])})</script>"
        for chunk in (
            state_chunk,
            metadata_chunk,
            f"ab:T{len(markdown.encode('utf-8')):x},",
            markdown,
        )
    )

    card = parse_model_card_page(page, url="https://example.test/modelcard")

    assert card["short_description"] == "Short description."
    assert card["description_markdown"] == markdown
    assert card["specifications"] == {"contextLength": 4096}
    assert card["capabilities"] == {"functionCalling": True}
    assert card["attributes"] == {"AVAILABLE": "true"}


def test_parse_model_card_page_supports_older_component_layout() -> None:
    artifact = {
        "artifactType": "ENDPOINT",
        "name": "old-model",
        "displayName": "Old Model",
        "publisher": "example",
        "shortDescription": "Older layout.",
        "description": "$35",
        "labels": "$component:path:labels",
        "attributes": [],
        "bias": "$36",
    }
    component = ["$", "$component", None, {"artifact": artifact}]
    metadata = {
        "labels": ["Chat", "Text-to-Text"],
        "specifications": {"contextLength": 8192},
        "modelCapability": {"reasoning": True},
        "openAPISpec": {"info": {"license": {"name": "Old License"}}},
    }
    description = "# Old Model\n\nComplete description."
    bias = "# Bias\n\nBias details."
    chunks = (
        "1:" + json.dumps(component, separators=(",", ":")),
        "2:" + json.dumps(metadata, separators=(",", ":")),
        "previous-record:{}\n" + f"35:T{len(description.encode('utf-8')):x},",
        description,
        f"36:T{len(bias.encode('utf-8')):x},",
        bias,
    )
    page = "".join(
        f"<script>self.__next_f.push({json.dumps([1, chunk])})</script>"
        for chunk in chunks
    )

    card = parse_model_card_page(page, url="https://example.test/old/modelcard")

    assert card["description_markdown"] == description
    assert card["labels"] == ["Chat", "Text-to-Text"]
    assert card["model_card_subcards"]["bias"] == bias
    assert card["license"] == {"name": "Old License"}


def test_build_and_save_catalog_keeps_unavailable_cards(tmp_path) -> None:
    records = [
        {"id": "a/one", "object": "model"},
        {"id": "b/two", "object": "model"},
    ]

    def fetch_card(model_id: str):
        if model_id == "a/one":
            return {"status": "available", "url": "https://example.test/a/one"}
        raise RuntimeError("missing card")

    catalog = build_model_catalog(records, workers=2, fetch_card=fetch_card)
    output = tmp_path / "models.json"
    save_model_catalog(catalog, output)
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert saved["model_count"] == 2
    assert saved["enriched_count"] == 1
    assert saved["unenriched_count"] == 1
    assert saved["models"][0]["provider"] == "a"
    assert saved["models"][1]["model_card"]["status"] == "unavailable"
