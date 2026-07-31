from __future__ import annotations

import typing
import unittest
from typing import Annotated, TypedDict
from unittest import mock

import pytest

from itemadapter.adapter import DictAdapter, ItemAdapter
from itemadapter.utils import get_field_meta_from_class
from tests import clear_itemadapter_imports, make_mock_import
from tests.test_json_schema import check_schemas

try:
    from typing_extensions import NotRequired, Required
except ImportError:  # Python 3.11+ without typing_extensions
    NotRequired = getattr(typing, "NotRequired", None)
    Required = getattr(typing, "Required", None)


class TypedDictItem(TypedDict):
    name: str
    """Display name"""
    value: Annotated[int, {"json_schema_extra": {"minimum": 0}}]


class TypedDictItemNested(TypedDict):
    nested: TypedDictItem
    tags: list[str]
    brand: str | None


class TypedDictItemRecursive(TypedDict):
    child: TypedDictItemRecursive


class TypedDictItemOptionalNested(TypedDict):
    nested: TypedDictItem | None


class TypedDictItemBase(TypedDict):
    base: int


class TypedDictItemSubclass(TypedDictItemBase, total=False):
    __json_schema_extra__ = {"title": "Subclass"}
    optional: str


class TypedDictTestCase(unittest.TestCase):
    maxDiff = None

    def test_is_item_class(self):
        assert ItemAdapter.is_item_class(TypedDictItem)
        assert DictAdapter.is_item_class(TypedDictItem)
        assert ItemAdapter._get_adapter_class(TypedDictItem) is DictAdapter

    def test_instances_are_dicts(self):
        """TypedDict instances are plain dicts at run time, with no reference to
        the TypedDict subclass they were declared as, so they are handled like
        any other dict."""
        item: TypedDictItem = {"name": "asdf", "value": 1234}
        adapter = ItemAdapter(item)
        assert isinstance(adapter.adapter, DictAdapter)
        assert adapter["name"] == "asdf"
        adapter["undeclared"] = True
        assert adapter.item == {"name": "asdf", "value": 1234, "undeclared": True}

    def test_get_field_names_from_class(self):
        assert ItemAdapter.get_field_names_from_class(TypedDictItem) == ["name", "value"]
        assert ItemAdapter.get_field_names_from_class(TypedDictItemSubclass) == [
            "base",
            "optional",
        ]

    def test_get_field_names_from_class_dict(self):
        assert ItemAdapter.get_field_names_from_class(dict) is None

    def test_get_field_meta_from_class(self):
        assert get_field_meta_from_class(TypedDictItem, "value") == {
            "json_schema_extra": {"minimum": 0}
        }
        assert get_field_meta_from_class(TypedDictItem, "name") == {}
        with pytest.raises(KeyError, match="TypedDictItem does not support field: non_existent"):
            get_field_meta_from_class(TypedDictItem, "non_existent")

    def test_get_field_meta_from_class_dict(self):
        assert get_field_meta_from_class(dict, "any") == {}

    def test_get_field_meta_from_class_non_mapping_annotation(self):
        class TypedDictItemStringAnnotation(TypedDict):
            name: Annotated[str, "not metadata"]

        assert get_field_meta_from_class(TypedDictItemStringAnnotation, "name") == {}

    def test_json_schema(self):
        actual = ItemAdapter.get_json_schema(TypedDictItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string", "description": "Display name"},
                "value": {"minimum": 0, "type": "integer"},
            },
            "required": ["name", "value"],
        }
        check_schemas(actual, expected)

    def test_json_schema_nested(self):
        actual = ItemAdapter.get_json_schema(TypedDictItemNested)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "description": "Display name"},
                        "value": {"minimum": 0, "type": "integer"},
                    },
                    "required": ["name", "value"],
                },
                "tags": {"type": "array", "items": {"type": "string"}},
                "brand": {"type": ["null", "string"]},
            },
            "required": ["nested", "tags", "brand"],
        }
        check_schemas(actual, expected)

    def test_json_schema_total_false(self):
        actual = ItemAdapter.get_json_schema(TypedDictItemSubclass)
        expected = {
            "title": "Subclass",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "base": {"type": "integer"},
                "optional": {"type": "string"},
            },
            "required": ["base"],
        }
        check_schemas(actual, expected)

    def test_json_schema_no_required_fields(self):
        class TypedDictItemAllOptional(TypedDict, total=False):
            optional: str

        actual = ItemAdapter.get_json_schema(TypedDictItemAllOptional)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"optional": {"type": "string"}},
        }
        check_schemas(actual, expected)

    def test_json_schema_no_fields(self):
        class TypedDictItemEmpty(TypedDict):
            pass

        actual = ItemAdapter.get_json_schema(TypedDictItemEmpty)
        expected = {"type": "object", "additionalProperties": False}
        check_schemas(actual, expected)

    def test_json_schema_dict(self):
        check_schemas(ItemAdapter.get_json_schema(dict), {"type": "object"})

    def test_json_schema_recursion(self):
        actual = ItemAdapter.get_json_schema(TypedDictItemRecursive)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"child": {"type": "object"}},
            "required": ["child"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(NotRequired is None, "Required and NotRequired are not available")
    def test_json_schema_not_required(self):
        class TypedDictItemNotRequired(TypedDict):
            required: int
            optional: NotRequired[Annotated[str, {"json_schema_extra": {"minLength": 2}}]]
            unannotated: NotRequired[float]

        assert get_field_meta_from_class(TypedDictItemNotRequired, "optional") == {
            "json_schema_extra": {"minLength": 2}
        }
        actual = ItemAdapter.get_json_schema(TypedDictItemNotRequired)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "required": {"type": "integer"},
                "optional": {"minLength": 2, "type": "string"},
                "unannotated": {"type": "number"},
            },
            "required": ["required"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(Required is None, "Required and NotRequired are not available")
    def test_json_schema_required(self):
        """Required and NotRequired from typing_extensions are missing from
        __required_keys__ and __optional_keys__ when the TypedDict subclass
        inherits from typing.TypedDict, so requiredness is read from the field
        type hints as well."""

        class TypedDictItemRequired(TypedDict, total=False):
            required: Required[int]
            optional: str

        actual = ItemAdapter.get_json_schema(TypedDictItemRequired)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "required": {"type": "integer"},
                "optional": {"type": "string"},
            },
            "required": ["required"],
        }
        check_schemas(actual, expected)

    @mock.patch("builtins.__import__", make_mock_import("typing_extensions"))
    def test_typing_extensions_import_error(self):
        with clear_itemadapter_imports():
            import itemadapter.adapter

            names = itemadapter.adapter.ItemAdapter.get_field_names_from_class(TypedDictItem)
            assert names == ["name", "value"]


class TypedDictCrossNestingTestCase(unittest.TestCase):
    maxDiff = None

    def test_typed_dict_in_dataclass(self):
        from dataclasses import dataclass

        @dataclass
        class DataClassItemTypedDictNested:
            nested: TypedDictItem

        actual = ItemAdapter.get_json_schema(DataClassItemTypedDictNested)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "description": "Display name"},
                        "value": {"minimum": 0, "type": "integer"},
                    },
                    "required": ["name", "value"],
                }
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    def test_optional_typed_dict(self):
        actual = ItemAdapter.get_json_schema(TypedDictItemOptionalNested)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "name": {"type": "string", "description": "Display name"},
                                "value": {"minimum": 0, "type": "integer"},
                            },
                            "required": ["name", "value"],
                        },
                    ]
                }
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)
