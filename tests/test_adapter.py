from __future__ import annotations

import unittest
from collections.abc import KeysView
from types import MappingProxyType

import pytest

from itemadapter.adapter import ItemAdapter, PydanticAdapter
from tests import (
    AttrsItem,
    AttrsItemEmpty,
    AttrsItemJsonSchema,
    AttrsItemNested,
    AttrsItemSubclassed,
    AttrsItemWithoutInit,
    DataClassItem,
    DataClassItemEmpty,
    DataClassItemJsonSchema,
    DataClassItemNested,
    DataClassItemSubclassed,
    DataClassWithoutInit,
    PydanticModel,
    PydanticModelEmpty,
    PydanticModelJsonSchema,
    PydanticModelNested,
    PydanticModelSubclassed,
    PydanticV1Model,
    PydanticV1ModelEmpty,
    PydanticV1ModelJsonSchema,
    PydanticV1ModelNested,
    PydanticV1ModelSubclassed,
    ScrapySubclassedItem,
    ScrapySubclassedItemEmpty,
    ScrapySubclassedItemJsonSchema,
    ScrapySubclassedItemNested,
    ScrapySubclassedItemSubclassed,
)
from tests.test_json_schema import check_schemas


class ItemAdapterReprTestCase(unittest.TestCase):
    def test_repr_dict(self):
        item = {"name": "asdf", "value": 1234}
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for dict(name='asdf', value=1234)>"

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_repr_scrapy_item(self):
        item = ScrapySubclassedItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for ScrapySubclassedItem(name='asdf', value=1234)>"

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_repr_dataclass(self):
        item = DataClassItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for DataClassItem(name='asdf', value=1234)>"

    @unittest.skipIf(not DataClassWithoutInit, "dataclasses module is not available")
    def test_repr_dataclass_init_false(self):
        item = DataClassWithoutInit()
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for DataClassWithoutInit()>"
        adapter["name"] = "set after init"
        assert repr(adapter) == "<ItemAdapter for DataClassWithoutInit(name='set after init')>"

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_repr_attrs(self):
        item = AttrsItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for AttrsItem(name='asdf', value=1234)>"

    @unittest.skipIf(not AttrsItemWithoutInit, "attrs module is not available")
    def test_repr_attrs_init_false(self):
        item = AttrsItemWithoutInit()
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for AttrsItemWithoutInit()>"
        adapter["name"] = "set after init"
        assert repr(adapter) == "<ItemAdapter for AttrsItemWithoutInit(name='set after init')>"

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_repr_pydantic(self):
        item = PydanticV1Model(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for PydanticV1Model(name='asdf', value=1234)>"


class ItemAdapterInitError(unittest.TestCase):
    def test_non_item(self):
        with pytest.raises(TypeError):
            ItemAdapter(ScrapySubclassedItem)
        with pytest.raises(TypeError):
            ItemAdapter(dict)
        with pytest.raises(TypeError):
            ItemAdapter(1234)


class BaseTestMixin:
    maxDiff = None
    item_class = None
    item_class_nested = None
    item_class_json_schema = None

    def setUp(self):
        if self.item_class is None:
            raise unittest.SkipTest

    def test_get_set_value(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        assert adapter.get("name") is None
        assert adapter.get("value") is None
        adapter["name"] = "asdf"
        adapter["value"] = 1234
        assert adapter.get("name") == "asdf"
        assert adapter.get("value") == 1234
        assert adapter["name"] == "asdf"
        assert adapter["value"] == 1234

        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert adapter.get("name") == "asdf"
        assert adapter.get("value") == 1234
        assert adapter["name"] == "asdf"
        assert adapter["value"] == 1234

    def test_get_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with pytest.raises(KeyError):
            adapter["undefined_field"]

    def test_as_dict(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert dict(adapter) == {"name": "asdf", "value": 1234}

    def test_as_dict_nested(self):
        item = self.item_class_nested(
            nested=self.item_class(name="asdf", value=1234),
            adapter=ItemAdapter({"foo": "bar", "nested_list": [1, 2, 3, 4, 5]}),
            dict_={"foo": "bar", "answer": 42, "nested_dict": {"a": "b"}},
            list_=[1, 2, 3],
            set_={1, 2, 3},
            tuple_=(1, 2, 3),
            int_=123,
        )
        adapter = ItemAdapter(item)
        assert adapter.asdict() == {
            "nested": {"name": "asdf", "value": 1234},
            "adapter": {"foo": "bar", "nested_list": [1, 2, 3, 4, 5]},
            "dict_": {"foo": "bar", "answer": 42, "nested_dict": {"a": "b"}},
            "list_": [1, 2, 3],
            "set_": {1, 2, 3},
            "tuple_": (1, 2, 3),
            "int_": 123,
        }

    def test_field_names(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert isinstance(adapter.field_names(), KeysView)
        assert sorted(adapter.field_names()) == ["name", "value"]

    def test_json_schema(self):
        item_class = self.item_class_json_schema
        actual = ItemAdapter.get_json_schema(item_class)
        check_schemas(actual, self.expected_json_schema)

    def test_json_schema_empty(self):
        actual = ItemAdapter.get_json_schema(self.item_class_empty)
        expected = {"type": "object"}
        if self.item_class_empty is not dict and not PydanticAdapter.is_item_class(
            self.item_class_empty
        ):
            expected["additionalProperties"] = False
        check_schemas(actual, expected)


_NESTED_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "is_nested": {"type": "boolean", "default": True},
    },
}


class NonDictTestMixin(BaseTestMixin):
    item_class_subclassed = None
    item_class_empty = None
    expected_json_schema = {
        "llmHint": "Hi model!",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "name": {
                "type": "string",
                "title": "Name",
                "description": "Display name",
            },
            "value": {
                "default": None,
            },
            "color": {
                "type": "string",
                "enum": ["red", "green", "blue"],
            },
            "produced": {"type": "boolean"},
            "answer": {
                "type": ["null", "number", "string"],
            },
            "numbers": {"type": "array", "items": {"type": "number"}},
            "aliases": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "nested": _NESTED_JSON_SCHEMA,
            "nested_list": {
                "type": "array",
                "items": _NESTED_JSON_SCHEMA,
            },
            "nested_dict": {
                "type": "object",
                "additionalProperties": _NESTED_JSON_SCHEMA,
            },
            "nested_dict_list": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": _NESTED_JSON_SCHEMA,
                },
            },
        },
        "required": [
            "name",
            "color",
            "answer",
            "numbers",
            "aliases",
            "nested",
            "nested_list",
            "nested_dict",
            "nested_dict_list",
        ],
    }

    def test_set_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with pytest.raises(KeyError):
            adapter["undefined_field"] = "some value"

    def test_metadata_common(self):
        adapter = ItemAdapter(self.item_class())
        assert isinstance(adapter.get_field_meta("name"), MappingProxyType)
        assert isinstance(adapter.get_field_meta("value"), MappingProxyType)
        with pytest.raises(KeyError):
            adapter.get_field_meta("undefined_field")

    def test_get_field_meta_defined_fields(self):
        adapter = ItemAdapter(self.item_class())
        assert adapter.get_field_meta("name") == MappingProxyType({"serializer": str})
        assert adapter.get_field_meta("value") == MappingProxyType({"serializer": int})

    def test_delitem_len_iter(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert len(adapter) == 2
        assert sorted(iter(adapter)) == ["name", "value"]

        del adapter["name"]
        assert len(adapter) == 1
        assert sorted(iter(adapter)) == ["value"]

        del adapter["value"]
        assert len(adapter) == 0
        assert sorted(iter(adapter)) == []

        with pytest.raises(KeyError):
            del adapter["name"]
        with pytest.raises(KeyError):
            del adapter["value"]
        with pytest.raises(KeyError):
            del adapter["undefined_field"]

    def test_field_names_from_class(self):
        field_names = ItemAdapter.get_field_names_from_class(self.item_class)
        assert isinstance(field_names, list)
        assert sorted(field_names) == ["name", "value"]

    def test_field_names_from_class_nested(self):
        field_names = ItemAdapter.get_field_names_from_class(self.item_class_subclassed)
        assert isinstance(field_names, list)
        assert sorted(field_names) == ["name", "subclassed", "value"]

    def test_field_names_from_class_empty(self):
        field_names = ItemAdapter.get_field_names_from_class(self.item_class_empty)
        assert isinstance(field_names, list)
        assert field_names == []


class DictTestCase(unittest.TestCase, BaseTestMixin):
    item_class = dict
    item_class_nested = dict
    item_class_json_schema = dict
    item_class_empty = dict
    expected_json_schema = {"type": "object"}

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values."""
        adapter = ItemAdapter(self.item_class())
        with pytest.raises(KeyError):
            adapter["name"]

    def test_empty_metadata(self):
        adapter = ItemAdapter(self.item_class(name="foo", value=5))
        for field_name in ("name", "value", "undefined_field"):
            assert adapter.get_field_meta(field_name) == MappingProxyType({})

    def test_field_names_updated(self):
        item = self.item_class(name="asdf")
        field_names = ItemAdapter(item).field_names()
        assert sorted(field_names) == ["name"]
        item["value"] = 1234
        assert sorted(field_names) == ["name", "value"]

    def test_field_names_from_class(self):
        assert ItemAdapter.get_field_names_from_class(dict) is None


_SCRAPY_NESTED_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "is_nested": {"default": True, "type": "boolean"},
    },
}


class ScrapySubclassedItemTestCase(NonDictTestMixin, unittest.TestCase):
    item_class = ScrapySubclassedItem
    item_class_nested = ScrapySubclassedItemNested
    item_class_subclassed = ScrapySubclassedItemSubclassed
    item_class_empty = ScrapySubclassedItemEmpty
    item_class_json_schema = ScrapySubclassedItemJsonSchema
    expected_json_schema = {
        "llmHint": "Hi model!",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            **{
                k: NonDictTestMixin.expected_json_schema["properties"][k]
                for k in sorted(NonDictTestMixin.expected_json_schema["properties"])
            },
            # Different order since stuff defined in json_schema_extra comes
            # first.
            "name": {
                "title": "Name",
                "type": "string",
                "description": "Display name",
            },
            "nested": _SCRAPY_NESTED_JSON_SCHEMA,
            "nested_list": {
                "type": "array",
                "items": _SCRAPY_NESTED_JSON_SCHEMA,
            },
            "nested_dict": {
                "type": "object",
                "additionalProperties": _SCRAPY_NESTED_JSON_SCHEMA,
            },
            "nested_dict_list": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": _SCRAPY_NESTED_JSON_SCHEMA,
                },
            },
            # No type, since none was specified in json_schema_extra.
            "produced": {},
            # value comes last due to Scrapy items sorting fields
            # alphabetically. https://github.com/scrapy/scrapy/issues/7015
            "value": NonDictTestMixin.expected_json_schema["properties"]["value"],
        },
    }

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values."""
        adapter = ItemAdapter(self.item_class())
        with pytest.raises(KeyError):
            adapter["name"]


_PYDANTIC_NESTED_JSON_SCHEMA = {
    k: v for k, v in _NESTED_JSON_SCHEMA.items() if k != "additionalProperties"
}


class PydanticV1ModelTestCase(NonDictTestMixin, unittest.TestCase):
    item_class = PydanticV1Model
    item_class_nested = PydanticV1ModelNested
    item_class_subclassed = PydanticV1ModelSubclassed
    item_class_empty = PydanticV1ModelEmpty
    item_class_json_schema = PydanticV1ModelJsonSchema
    expected_json_schema = {
        **{
            k: v
            for k, v in NonDictTestMixin.expected_json_schema.items()
            if k not in {"additionalProperties"}
        },
        "properties": {
            **{
                k: v
                for k, v in NonDictTestMixin.expected_json_schema["properties"].items()
                if k not in {"nested", "nested_list", "nested_dict", "nested_dict_list"}
            },
            "nested": _PYDANTIC_NESTED_JSON_SCHEMA,
            "nested_list": {
                "type": "array",
                "items": _PYDANTIC_NESTED_JSON_SCHEMA,
            },
            "nested_dict": {
                "type": "object",
                "additionalProperties": _PYDANTIC_NESTED_JSON_SCHEMA,
            },
            "nested_dict_list": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": _PYDANTIC_NESTED_JSON_SCHEMA,
                },
            },
        },
        "required": [
            *NonDictTestMixin.expected_json_schema["required"][:2],
            "produced",
            *NonDictTestMixin.expected_json_schema["required"][2:],
        ],
    }

    def test_get_field_meta_defined_fields(self):
        adapter = ItemAdapter(self.item_class())

        name_actual = adapter.get_field_meta("name")
        name_expected = MappingProxyType(
            {
                "serializer": str,
                "default_factory": name_actual["default_factory"],
            }
        )
        assert name_expected == name_actual

        value_actual = adapter.get_field_meta("value")
        value_expected = MappingProxyType(
            {
                "serializer": int,
                "default_factory": value_actual["default_factory"],
            }
        )
        assert value_expected == value_actual


class PydanticModelTestCase(NonDictTestMixin, unittest.TestCase):
    item_class = PydanticModel
    item_class_nested = PydanticModelNested
    item_class_subclassed = PydanticModelSubclassed
    item_class_empty = PydanticModelEmpty
    item_class_json_schema = PydanticModelJsonSchema
    expected_json_schema = {
        **{
            k: v
            for k, v in NonDictTestMixin.expected_json_schema.items()
            if k not in {"additionalProperties"}
        },
        "properties": {
            **{
                k: v
                for k, v in NonDictTestMixin.expected_json_schema["properties"].items()
                if k not in {"nested", "nested_list", "nested_dict", "nested_dict_list"}
            },
            "nested": _PYDANTIC_NESTED_JSON_SCHEMA,
            "nested_list": {
                "type": "array",
                "items": _PYDANTIC_NESTED_JSON_SCHEMA,
            },
            "nested_dict": {
                "type": "object",
                "additionalProperties": _PYDANTIC_NESTED_JSON_SCHEMA,
            },
            "nested_dict_list": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": _PYDANTIC_NESTED_JSON_SCHEMA,
                },
            },
        },
        "required": NonDictTestMixin.expected_json_schema["required"],
    }

    def test_get_field_meta_defined_fields(self):
        adapter = ItemAdapter(self.item_class())
        assert adapter.get_field_meta("name")["json_schema_extra"] == MappingProxyType(
            {"serializer": str}
        )
        assert adapter.get_field_meta("value")["json_schema_extra"] == MappingProxyType(
            {"serializer": int}
        )


class DataClassItemTestCase(NonDictTestMixin, unittest.TestCase):
    item_class = DataClassItem
    item_class_nested = DataClassItemNested
    item_class_subclassed = DataClassItemSubclassed
    item_class_empty = DataClassItemEmpty
    item_class_json_schema = DataClassItemJsonSchema
    expected_json_schema = {
        **NonDictTestMixin.expected_json_schema,
        "properties": {
            **{
                k: v
                for k, v in NonDictTestMixin.expected_json_schema["properties"].items()
                if k not in {"value", "produced"}
            },
            # Title is set through json_schema_extra, so it comes first.
            "name": {"title": "Name", "type": "string", "description": "Display name"},
            # value and produced come last because they have a default value,
            # and dataclass does not support values without a default after
            # values with a default.
            "value": NonDictTestMixin.expected_json_schema["properties"]["value"],
            "produced": NonDictTestMixin.expected_json_schema["properties"]["produced"],
        },
        "required": NonDictTestMixin.expected_json_schema["required"],
    }


class AttrsItemTestCase(NonDictTestMixin, unittest.TestCase):
    item_class = AttrsItem
    item_class_nested = AttrsItemNested
    item_class_subclassed = AttrsItemSubclassed
    item_class_empty = AttrsItemEmpty
    item_class_json_schema = AttrsItemJsonSchema
    expected_json_schema = DataClassItemTestCase.expected_json_schema
