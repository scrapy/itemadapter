from __future__ import annotations

import sys
import unittest
from collections.abc import Mapping, Sequence  # noqa: TC003
from dataclasses import dataclass, field
from typing import Any, Optional, Union

from itemadapter.adapter import ItemAdapter
from tests import (
    AttrsItem,
    PydanticEnumModel,
    PydanticModel,
    ScrapySubclassedItem,
    SetList,
)

PYTHON_VERSION = sys.version_info[:2]


@dataclass
class RecursionNestedItem:
    parent: RecursionItem
    sibling: RecursionNestedItem


@dataclass
class RecursionItem:
    child: RecursionNestedItem
    sibling: RecursionItem


@dataclass
class OptionalItemListNestedItem:
    is_nested: bool = True


@dataclass
class OptionalItemListItem:
    foo: Optional[list[OptionalItemListNestedItem]] = None


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


class JsonSchemaTestCase(unittest.TestCase):
    maxDiff = None

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_attrs_pydantic_enum(self):
        """This test exists to ensure that we do not let the JSON Schema
        generation of Pydantic item classes generated nested $defs (which we
        don’t since we do not run Pydantic’s JSON Schema generation but our
        own)."""
        import attrs

        @attrs.define
        class TestAttrsItem:
            pydantic: PydanticEnumModel

        actual = ItemAdapter.get_json_schema(TestAttrsItem)
        expected = {
            "type": "object",
            "properties": {
                "pydantic": {
                    "type": "object",
                    "properties": {
                        "enum": {"enum": ["foo"], "type": "string"},
                    },
                    "required": ["enum"],
                }
            },
            "required": ["pydantic"],
            "additionalProperties": False,
        }
        self.assertEqual(actual, expected)

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @unittest.skipIf(
        PYTHON_VERSION >= (3, 13), "It seems inspect can get the class code in Python 3.13+"
    )
    def test_unreachable_source(self):
        """Using inspect to get the item class source and find attribute
        docstrings is not always a possibility, e.g. when the item class is
        defined within a (test) method. In those cases, only the extraction of
        those docstrings should fail."""
        from scrapy.item import Field, Item

        class ScrapySubclassedItemUnreachable(Item):
            name: str = Field(json_schema_extra={"example": "Foo"})
            """Display name"""

        actual = ItemAdapter.get_json_schema(ScrapySubclassedItemUnreachable)
        expected = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "example": "Foo",
                }
            },
            "required": ["name"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_recursion(self):
        actual = ItemAdapter.get_json_schema(RecursionItem)
        expected = {
            "type": "object",
            "properties": {
                "child": {
                    "type": "object",
                    "properties": {
                        "parent": {
                            "type": "object",
                        },
                        "sibling": {
                            "type": "object",
                        },
                    },
                    "required": ["parent", "sibling"],
                    "additionalProperties": False,
                },
                "sibling": {
                    "type": "object",
                },
            },
            "required": ["child", "sibling"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_nested_dict(self):
        @dataclass
        class TestItem:
            foo: dict

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "object",
                },
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_optional_item_list(self):
        actual = ItemAdapter.get_json_schema(OptionalItemListItem)
        expected = {
            "type": "object",
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
                                "properties": {
                                    "is_nested": {
                                        "type": "boolean",
                                        "default": True,
                                    },
                                },
                                "additionalProperties": False,
                            },
                        },
                    ],
                    "default": None,
                },
            },
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_sequence_untyped(self):
        @dataclass
        class TestItem:
            foo: Sequence

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "array",
                    "items": {},
                },
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_tuple_ellipsis(self):
        @dataclass
        class TestItem:
            foo: tuple[Any, ...]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "array",
                    "items": {},
                },
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_tuple_multiple_types(self):
        @dataclass
        class TestItem:
            foo: tuple[str, int, int]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {
                    "type": "array",
                    "items": {"type": SetList(["string", "integer"])},
                },
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_union_single(self):
        @dataclass
        class TestItem:
            foo: Union[str]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string"},
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_custom_any_of(self):
        @dataclass
        class TestItem:
            foo: Union[str, SimpleItem] = field(
                metadata={"json_schema_extra": {"anyOf": []}},
            )

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"anyOf": []},
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_set_untyped(self):
        @dataclass
        class TestItem:
            foo: set

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "array", "items": {}, "uniqueItems": True},
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_mapping_untyped(self):
        @dataclass
        class TestItem:
            foo: Mapping

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "object"},
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_custom_mapping(self):
        @dataclass
        class TestItem:
            foo: CustomMapping

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "object"},
            },
            "required": ["foo"],
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)

    def test_item_without_attributes(self):
        @dataclass
        class TestItem:
            pass

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
        }
        self.assertEqual(expected, actual)
