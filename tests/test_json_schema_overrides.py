from dataclasses import dataclass, field

import pytest

from itemadapter import ItemAdapter


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
