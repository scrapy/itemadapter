from __future__ import annotations

import typing
from copy import deepcopy
from dataclasses import field, make_dataclass

import pytest

from itemadapter._imports import pydantic
from itemadapter.adapter import ItemAdapter
from tests import AttrsItem, PydanticModel, ScrapySubclassedItem


def schema_item_with_metadata(adapter, field_type, metadata):
    field_metadata = {"json_schema_extra": metadata}
    if adapter == "dataclass":
        return make_dataclass(
            "SchemaItem", [("value", field_type, field(metadata=field_metadata))]
        )
    if adapter == "typed_dict":
        return typing.TypedDict(
            "SchemaItem", {"value": typing.Annotated[field_type, field_metadata]}
        )
    if adapter == "attrs":
        import attrs

        return attrs.make_class(
            "SchemaItem", {"value": attrs.field(type=field_type, metadata=field_metadata)}
        )
    if adapter == "pydantic":
        return pydantic.create_model(
            "SchemaItem", value=(field_type, pydantic.Field(json_schema_extra=metadata))
        )
    from scrapy import Field, Item

    return type(
        "SchemaItem",
        (Item,),
        {"__annotations__": {"value": field_type}, "value": Field(**field_metadata)},
    )


@pytest.mark.parametrize(
    "adapter",
    [
        "dataclass",
        "typed_dict",
        pytest.param("attrs", marks=pytest.mark.skipif(not AttrsItem, reason="attrs unavailable")),
        pytest.param(
            "pydantic", marks=pytest.mark.skipif(not PydanticModel, reason="pydantic unavailable")
        ),
        pytest.param(
            "scrapy",
            marks=pytest.mark.skipif(not ScrapySubclassedItem, reason="scrapy unavailable"),
        ),
    ],
)
@pytest.mark.parametrize(
    ("first_type", "second_type", "metadata", "path"),
    [
        (list[str], list[int], {"items": {"description": "Shared"}}, ["items"]),
        (
            dict[str, str],
            dict[str, int],
            {"additionalProperties": {"description": "Shared"}},
            ["additionalProperties"],
        ),
        (
            list[dict[str, str]],
            list[dict[str, int]],
            {"items": {"additionalProperties": {"description": "Shared"}}},
            ["items", "additionalProperties"],
        ),
    ],
)
def test_shared_field_schema_metadata(adapter, first_type, second_type, metadata, path):
    metadata = deepcopy(metadata)
    original = deepcopy(metadata)
    first_item = schema_item_with_metadata(adapter, first_type, metadata)
    second_item = schema_item_with_metadata(adapter, second_type, metadata)
    first = ItemAdapter.get_json_schema(first_item)["properties"]["value"]
    second = ItemAdapter.get_json_schema(second_item)["properties"]["value"]
    for key in path:
        first = first[key]
        second = second[key]
    assert first == {"description": "Shared", "type": "string"}
    assert second == {"description": "Shared", "type": "integer"}
    assert metadata == original
