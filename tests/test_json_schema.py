from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from typing import Optional

from itemadapter.adapter import ItemAdapter
from tests import (
    AttrsItem,
    PydanticEnumModel,
    PydanticModel,
    ScrapySubclassedItem,
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
