from dataclasses import dataclass, field
from typing import Annotated, TypedDict

import pytest

from itemadapter import ItemAdapter
from itemadapter._imports import attrs, pydantic, scrapy
from tests import requires_attrs, requires_pydantic, requires_scrapy


@pytest.mark.parametrize("allow_additional", [False, True])
def test_boolean_additional_properties(allow_additional):
    extra = {
        "properties": {"small": {"type": "integer"}, "large": {"type": "integer"}},
        "additionalProperties": allow_additional,
    }

    @dataclass
    class Product:
        quantities: dict[str, int] = field(metadata={"json_schema_extra": extra})

    schema = ItemAdapter.get_json_schema(Product)
    assert schema["properties"]["quantities"] == {"type": "object", **extra}


@pytest.mark.parametrize("allow_items", [False, True])
def test_boolean_items(allow_items):
    @dataclass
    class Product:
        tags: list[str] = field(metadata={"json_schema_extra": {"items": allow_items}})

    schema = ItemAdapter.get_json_schema(Product)
    assert schema["properties"]["tags"] == {"type": "array", "items": allow_items}


def test_nested_boolean_schema():
    @dataclass
    class Product:
        quantities: list[dict[str, int]] = field(
            metadata={"json_schema_extra": {"items": {"additionalProperties": False}}}
        )

    schema = ItemAdapter.get_json_schema(Product)
    assert schema["properties"]["quantities"] == {
        "type": "array",
        "items": {"type": "object", "additionalProperties": False},
    }


def make_dataclass(value_type, extra):
    @dataclass
    class Item:
        value: value_type = field(metadata={"json_schema_extra": extra})

    return Item


def make_attrs(value_type, extra):
    @attrs.define
    class Item:
        value: value_type = attrs.field(metadata={"json_schema_extra": extra})

    return Item


def make_typed_dict(value_type, extra):
    class Item(TypedDict):
        value: Annotated[value_type, {"json_schema_extra": extra}]

    return Item


def make_pydantic(value_type, extra):
    class Item(pydantic.BaseModel):
        value: value_type = pydantic.Field(json_schema_extra=extra)

    return Item


def make_scrapy(value_type, extra):
    class Item(scrapy.Item):
        value: value_type = scrapy.Field(json_schema_extra=extra)

    return Item


@pytest.mark.parametrize(
    "make_item",
    [
        make_dataclass,
        pytest.param(make_attrs, marks=requires_attrs),
        make_typed_dict,
        pytest.param(make_pydantic, marks=requires_pydantic),
        pytest.param(make_scrapy, marks=requires_scrapy),
    ],
)
def test_shared_field_json_schema_extra(make_item):
    extra = {"items": {"description": "Tag."}}

    str_schema = ItemAdapter.get_json_schema(make_item(list[str], extra))
    int_schema = ItemAdapter.get_json_schema(make_item(list[int], extra))
    assert extra == {"items": {"description": "Tag."}}
    assert str_schema["properties"]["value"] == {
        "type": "array",
        "items": {"description": "Tag.", "type": "string"},
    }
    assert int_schema["properties"]["value"] == {
        "type": "array",
        "items": {"description": "Tag.", "type": "integer"},
    }


def test_class_json_schema_extra_unchanged():
    extra = {"properties": {"name": {}}}

    @dataclass
    class Product:
        __json_schema_extra__ = extra
        name = "Product"
        """Product name."""

    schema = ItemAdapter.get_json_schema(Product)
    assert schema["properties"] == {"name": {"description": "Product name."}}
    assert extra == {"properties": {"name": {}}}
