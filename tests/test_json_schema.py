from __future__ import annotations

import json
import sys
import typing
import unittest
from collections.abc import Mapping, Sequence  # noqa: TC003
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union

import pytest

from itemadapter._imports import pydantic
from itemadapter.adapter import AttrsAdapter, ItemAdapter, PydanticAdapter, ScrapyItemAdapter
from tests import (
    AttrsItem,
    AttrsItemJsonSchemaNested,
    DataClassItemJsonSchemaNested,
    PydanticModel,
    PydanticModelJsonSchemaNested,
    PydanticV1Model,
    PydanticV1ModelJsonSchemaNested,
    ScrapySubclassedItem,
    ScrapySubclassedItemJsonSchemaNested,
)

PYTHON_VERSION = sys.version_info[:2]


if ScrapySubclassedItem and AttrsItem:
    from scrapy import Field as ScrapyField
    from scrapy import Item as ScrapyItem

    class ScrapySubclassedItemCrossNested(ScrapyItem):
        nested: AttrsItemJsonSchemaNested = ScrapyField()


@dataclass
class Brand:
    name: str


@dataclass
class OptionalItemListNestedItem:
    is_nested: bool = True


@dataclass
class OptionalItemListItem:
    foo: Optional[list[OptionalItemListNestedItem]] = None


@dataclass
class RecursionItem:
    child: RecursionNestedItem
    sibling: RecursionItem


@dataclass
class RecursionNestedItem:
    parent: RecursionItem
    sibling: RecursionNestedItem


@dataclass
class SimpleItem:
    foo: str


class CustomMapping:  # noqa: PLW1641
    def __init__(self, data):
        self._data = dict(data)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __eq__(self, other):
        if isinstance(other, CustomMapping):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return NotImplemented

    def __ne__(self, other):
        eq = self.__eq__(other)
        if eq is NotImplemented:
            return NotImplemented
        return not eq


class SimpleEnum(Enum):
    foo = "foo"


if PydanticModel:

    class PydanticEnumModel(pydantic.BaseModel):
        enum: SimpleEnum


def check_schemas(actual, expected):
    """Helper function to check if the actual JSON schema matches the expected
    one.

    It uses json.dumps() WITHOUT sorting the keys, to ensure key sorting
    matches in both schemas as well. Maintaining the source order of fields can
    be important

    The indentation is set for better readability or mismatch output.
    """
    assert json.dumps(actual, indent=2) == json.dumps(expected, indent=2)


class JsonSchemaTestCase(unittest.TestCase):
    maxDiff = None

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_attrs_pydantic_enum(self):
        """This test exists to ensure that we do not let the JSON Schema
        generation of Pydantic item classes generate nested $defs (which we
        don’t since we do not run Pydantic’s JSON Schema generation but our
        own)."""
        import attrs

        @attrs.define
        class TestAttrsItem:
            pydantic: PydanticEnumModel

        actual = ItemAdapter.get_json_schema(TestAttrsItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pydantic": {
                    "type": "object",
                    "properties": {
                        "enum": {"type": "string", "enum": ["foo"]},
                    },
                    "required": ["enum"],
                }
            },
            "required": ["pydantic"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @unittest.skipIf(
        PYTHON_VERSION >= (3, 13), "It seems inspect can get the class code in Python 3.13+"
    )
    def test_unreachable_source(self):
        """Using inspect to get the item class source and find attribute
        docstrings is not always a possibility, e.g. when the item class is
        defined within a (test) method. In those cases, only the extraction of
        those docstrings should fail."""

        class ScrapySubclassedItemUnreachable(ScrapyItem):
            name: str = ScrapyField(json_schema_extra={"example": "Foo"})
            """Display name"""

        actual = ItemAdapter.get_json_schema(ScrapySubclassedItemUnreachable)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {
                    "example": "Foo",
                    "type": "string",
                }
            },
        }
        check_schemas(actual, expected)

    def test_recursion(self):
        actual = ItemAdapter.get_json_schema(RecursionItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "child": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "parent": {
                            "type": "object",
                        },
                        "sibling": {
                            "type": "object",
                        },
                    },
                    "required": ["parent", "sibling"],
                },
                "sibling": {
                    "type": "object",
                },
            },
            "required": ["child", "sibling"],
        }
        check_schemas(actual, expected)

    def test_nested_dict(self):
        @dataclass
        class TestItem:
            foo: dict

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "object",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_optional_item_list(self):
        actual = ItemAdapter.get_json_schema(OptionalItemListItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "anyOf": [
                        {
                            "type": "null",
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "is_nested": {
                                        "type": "boolean",
                                        "default": True,
                                    },
                                },
                            },
                        },
                    ],
                    "default": None,
                },
            },
        }
        check_schemas(actual, expected)

    def test_sequence_untyped(self):
        @dataclass
        class TestItem:
            foo: Sequence

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_tuple_ellipsis(self):
        @dataclass
        class TestItem:
            foo: tuple[Any, ...]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_tuple_multiple_types(self):
        @dataclass
        class TestItem:
            foo: tuple[str, int, int]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                    "items": {
                        "type": ["integer", "string"],
                    },
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_union_single(self):
        @dataclass
        class TestItem:
            foo: Union[str]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_custom_any_of(self):
        @dataclass
        class TestItem:
            foo: Union[str, SimpleItem] = field(
                metadata={"json_schema_extra": {"anyOf": []}},
            )

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"anyOf": []},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_set_untyped(self):
        @dataclass
        class TestItem:
            foo: set

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "array", "uniqueItems": True},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_mapping_untyped(self):
        @dataclass
        class TestItem:
            foo: Mapping

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "object"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_custom_mapping(self):
        @dataclass
        class TestItem:
            foo: CustomMapping

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "object"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_item_without_attributes(self):
        @dataclass
        class TestItem:
            pass

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
        }
        check_schemas(actual, expected)

    def test_typing_sequence_untyped(self):
        @dataclass
        class TestItem:
            foo: typing.Sequence

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_custom_items(self):
        @dataclass
        class TestItem:
            foo: typing.Sequence = field(metadata={"json_schema_extra": {"items": {}}})

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "items": {},
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @unittest.skipIf(PYTHON_VERSION < (3, 10), "Modern optional annotations require Python 3.10+")
    def test_modern_optional_annotations(self):
        import attr

        @attr.define
        class Product:
            name: str
            """Product name"""

            brand: Brand | None
            in_stock: bool = True

        actual = ItemAdapter.get_json_schema(Product)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string", "description": "Product name"},
                "brand": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"],
                        },
                    ]
                },
                "in_stock": {"type": "boolean", "default": True},
            },
            "required": ["name", "brand"],
        }
        check_schemas(actual, expected)

    def test_field_docstring_inheritance(self):
        """Test that field docstrings are inherited from parent classes."""

        @dataclass
        class ParentItem:
            foo: str
            """Parent item foo"""

        @dataclass
        class ChildItem(ParentItem):
            pass

        actual = ItemAdapter.get_json_schema(ChildItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string", "description": "Parent item foo"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_field_docstring_cleandoc(self):
        """Test that field docstrings are properly dedented and trimmed."""

        @dataclass
        class TestItem:
            foo: str
            """
            This is a multiline docstring.

            It has multiple paragraphs and indentation
            that should be cleaned up.
            """

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "string",
                    "description": (
                        "This is a multiline docstring.\n\n"
                        "It has multiple paragraphs and indentation\n"
                        "that should be cleaned up."
                    ),
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)


class CrossNestingTestCase(unittest.TestCase):
    """Test item nesting across different item types, with all supported types
    acting as parent or child in one test."""

    maxDiff = None

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_dataclass_pydantic1(self):
        @dataclass
        class TestItem:
            nested: PydanticV1ModelJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_attrs_pydantic2(self):
        import attrs

        @attrs.define
        class TestItem:
            nested: PydanticModelJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = AttrsAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"nested": {}},
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_scrapy_attrs(self):
        actual = ItemAdapter.get_json_schema(ScrapySubclassedItemCrossNested)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
        }
        check_schemas(actual, expected)

        actual = ScrapyItemAdapter.get_json_schema(ScrapySubclassedItemCrossNested)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"nested": {}},
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_pydantic1_scrapy(self):
        from . import pydantic_v1

        class TestItem(pydantic_v1.BaseModel):
            nested: ScrapySubclassedItemJsonSchemaNested

            class Config:
                arbitrary_types_allowed = True

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"default": True, "type": "boolean"},
                    },
                }
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = PydanticAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                # Scrapy item classes implement the Mapping interface, so
                # they are correctly recognized as objects even when there is
                # no access to ScrapyItemAdapter.
                "nested": {"type": "object"}
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_pydantic_dataclass(self):
        class TestItem(pydantic.BaseModel):
            nested: DataClassItemJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                },
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = PydanticAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {},
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_pydantic_scrapy(self):
        class TestItem(pydantic.BaseModel):
            nested: ScrapySubclassedItemJsonSchemaNested

            model_config = {
                "arbitrary_types_allowed": True,
            }

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"default": True, "type": "boolean"},
                    },
                },
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = PydanticAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {"type": "object"},
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @pytest.mark.filterwarnings("ignore:Mixing V1 models and V2 models")
    def test_pydantics(self):
        class TestItem(pydantic.BaseModel):
            nested: PydanticV1ModelJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                },
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        # Since PydanticAdapter is not version-specific, it works with both
        # Pydantic V1 and V2+ models.
        actual = PydanticAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                },
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)
