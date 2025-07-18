import importlib.metadata
import sys
import unittest
from collections.abc import KeysView
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from packaging.version import Version

from itemadapter.adapter import ItemAdapter
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
    DataClassItemJsonSchemaNested,
    DataClassItemNested,
    DataClassItemSubclassed,
    DataClassWithoutInit,
    PydanticModel,
    PydanticModelEmpty,
    PydanticModelJsonSchema,
    PydanticModelJsonSchemaNested,
    PydanticModelNested,
    PydanticModelSubclassed,
    PydanticV1Model,
    PydanticV1ModelEmpty,
    PydanticV1ModelJsonSchema,
    PydanticV1ModelJsonSchemaNested,
    PydanticV1ModelNested,
    PydanticV1ModelSubclassed,
    ScrapySubclassedItem,
    ScrapySubclassedItemCrossNested,
    ScrapySubclassedItemEmpty,
    ScrapySubclassedItemJsonSchema,
    ScrapySubclassedItemJsonSchemaNested,
    ScrapySubclassedItemNested,
    ScrapySubclassedItemSubclassed,
)

PYTHON_VERSION = sys.version_info[:2]
try:
    ATTRS_VERSION = Version(importlib.metadata.version("attrs"))
except importlib.metadata.PackageNotFoundError:
    ATTRS_VERSION = None


class ItemAdapterReprTestCase(unittest.TestCase):
    def test_repr_dict(self):
        item = {"name": "asdf", "value": 1234}
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for dict(name='asdf', value=1234)>")

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_repr_scrapy_item(self):
        item = ScrapySubclassedItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for ScrapySubclassedItem(name='asdf', value=1234)>",
        )

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_repr_dataclass(self):
        item = DataClassItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for DataClassItem(name='asdf', value=1234)>",
        )

    @unittest.skipIf(not DataClassWithoutInit, "dataclasses module is not available")
    def test_repr_dataclass_init_false(self):
        item = DataClassWithoutInit()
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for DataClassWithoutInit()>")
        adapter["name"] = "set after init"
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for DataClassWithoutInit(name='set after init')>",
        )

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_repr_attrs(self):
        item = AttrsItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for AttrsItem(name='asdf', value=1234)>",
        )

    @unittest.skipIf(not AttrsItemWithoutInit, "attrs module is not available")
    def test_repr_attrs_init_false(self):
        item = AttrsItemWithoutInit()
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for AttrsItemWithoutInit()>")
        adapter["name"] = "set after init"
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for AttrsItemWithoutInit(name='set after init')>",
        )

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_repr_pydantic(self):
        item = PydanticV1Model(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for PydanticV1Model(name='asdf', value=1234)>",
        )


class ItemAdapterInitError(unittest.TestCase):
    def test_non_item(self):
        with self.assertRaises(TypeError):
            ItemAdapter(ScrapySubclassedItem)
        with self.assertRaises(TypeError):
            ItemAdapter(dict)
        with self.assertRaises(TypeError):
            ItemAdapter(1234)


class BaseTestMixin:
    item_class = None
    item_class_nested = None
    maxDiff = None

    def setUp(self):
        if self.item_class is None:
            raise unittest.SkipTest

    def test_get_set_value(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        self.assertEqual(adapter.get("name"), None)
        self.assertEqual(adapter.get("value"), None)
        adapter["name"] = "asdf"
        adapter["value"] = 1234
        self.assertEqual(adapter.get("name"), "asdf")
        self.assertEqual(adapter.get("value"), 1234)
        self.assertEqual(adapter["name"], "asdf")
        self.assertEqual(adapter["value"], 1234)

        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(adapter.get("name"), "asdf")
        self.assertEqual(adapter.get("value"), 1234)
        self.assertEqual(adapter["name"], "asdf")
        self.assertEqual(adapter["value"], 1234)

    def test_get_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with self.assertRaises(KeyError):
            adapter["undefined_field"]

    def test_as_dict(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual({"name": "asdf", "value": 1234}, dict(adapter))

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
        self.assertEqual(
            adapter.asdict(),
            {
                "nested": {"name": "asdf", "value": 1234},
                "adapter": {"foo": "bar", "nested_list": [1, 2, 3, 4, 5]},
                "dict_": {"foo": "bar", "answer": 42, "nested_dict": {"a": "b"}},
                "list_": [1, 2, 3],
                "set_": {1, 2, 3},
                "tuple_": (1, 2, 3),
                "int_": 123,
            },
        )

    def test_field_names(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertIsInstance(adapter.field_names(), KeysView)
        self.assertEqual(sorted(adapter.field_names()), ["name", "value"])


class SetList(list):
    def __eq__(self, other):
        return set(self) == set(other)

    def __hash__(self):
        return hash(frozenset(self))


_NESTED_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "is_nested": {"type": "boolean", "default": True},
    },
    "additionalProperties": False,
}


class CustomItemClassTestMixin(BaseTestMixin):
    item_class_subclassed = None
    item_class_empty = None
    expected_json_schema = {
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
                "type": SetList(["string", "null", "number"]),
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
        "type": "object",
        "llmHint": "Hi model!",
    }

    def test_set_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with self.assertRaises(KeyError):
            adapter["undefined_field"] = "some value"

    def test_metadata_common(self):
        adapter = ItemAdapter(self.item_class())
        self.assertIsInstance(adapter.get_field_meta("name"), MappingProxyType)
        self.assertIsInstance(adapter.get_field_meta("value"), MappingProxyType)
        with self.assertRaises(KeyError):
            adapter.get_field_meta("undefined_field")

    def test_get_field_meta_defined_fields(self):
        adapter = ItemAdapter(self.item_class())
        self.assertEqual(adapter.get_field_meta("name"), MappingProxyType({"serializer": str}))
        self.assertEqual(adapter.get_field_meta("value"), MappingProxyType({"serializer": int}))

    def test_delitem_len_iter(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(len(adapter), 2)
        self.assertEqual(sorted(iter(adapter)), ["name", "value"])

        del adapter["name"]
        self.assertEqual(len(adapter), 1)
        self.assertEqual(sorted(iter(adapter)), ["value"])

        del adapter["value"]
        self.assertEqual(len(adapter), 0)
        self.assertEqual(sorted(iter(adapter)), [])

        with self.assertRaises(KeyError):
            del adapter["name"]
        with self.assertRaises(KeyError):
            del adapter["value"]
        with self.assertRaises(KeyError):
            del adapter["undefined_field"]

    def test_field_names_from_class(self):
        field_names = ItemAdapter.get_field_names_from_class(self.item_class)
        assert isinstance(field_names, list)
        self.assertEqual(sorted(field_names), ["name", "value"])

    def test_field_names_from_class_nested(self):
        field_names = ItemAdapter.get_field_names_from_class(self.item_class_subclassed)
        assert isinstance(field_names, list)
        self.assertEqual(sorted(field_names), ["name", "subclassed", "value"])

    def test_field_names_from_class_empty(self):
        field_names = ItemAdapter.get_field_names_from_class(self.item_class_empty)
        assert isinstance(field_names, list)
        self.assertEqual(field_names, [])

    def test_json_schema(self):
        item_class = self.item_class_json_schema
        actual = ItemAdapter.get_json_schema(item_class)
        self.assertEqual(self.expected_json_schema, actual)


class DictTestCase(unittest.TestCase, BaseTestMixin):
    item_class = dict
    item_class_nested = dict

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values."""
        adapter = ItemAdapter(self.item_class())
        with self.assertRaises(KeyError):
            adapter["name"]

    def test_empty_metadata(self):
        adapter = ItemAdapter(self.item_class(name="foo", value=5))
        for field_name in ("name", "value", "undefined_field"):
            self.assertEqual(adapter.get_field_meta(field_name), MappingProxyType({}))

    def test_field_names_updated(self):
        item = self.item_class(name="asdf")
        field_names = ItemAdapter(item).field_names()
        self.assertEqual(sorted(field_names), ["name"])
        item["value"] = 1234
        self.assertEqual(sorted(field_names), ["name", "value"])

    def test_field_names_from_class(self):
        assert ItemAdapter.get_field_names_from_class(dict) is None

    def test_json_schema(self):
        actual = ItemAdapter.get_json_schema(dict)
        expected = {"type": "object"}
        self.assertEqual(expected, actual)


class DataClassItemTestCase(CustomItemClassTestMixin, unittest.TestCase):
    item_class = DataClassItem
    item_class_nested = DataClassItemNested
    item_class_subclassed = DataClassItemSubclassed
    item_class_empty = DataClassItemEmpty
    item_class_json_schema = DataClassItemJsonSchema


class AttrsItemTestCase(CustomItemClassTestMixin, unittest.TestCase):
    item_class = AttrsItem
    item_class_nested = AttrsItemNested
    item_class_subclassed = AttrsItemSubclassed
    item_class_empty = AttrsItemEmpty
    item_class_json_schema = AttrsItemJsonSchema

    def test_json_schema_validators(self):
        import attr
        from attr import validators

        @attr.s
        class ItemClass:
            # String with min/max length and regex pattern
            name = attr.ib(
                type=str,
                validator=[
                    *(
                        validators.min_len(3)
                        for _ in range(1)
                        if Version("22.1.0") <= ATTRS_VERSION
                    ),
                    *(
                        validators.max_len(10)
                        for _ in range(1)
                        if Version("21.3.0") <= ATTRS_VERSION
                    ),
                    validators.matches_re(r"^[A-Za-z]+$"),
                ],
            )
            # Integer with minimum, maximum, exclusive minimum, exclusive maximum
            age = attr.ib(
                type=int,
                validator=[
                    validators.ge(18),
                    validators.le(99),
                    validators.gt(17),
                    validators.lt(100),
                ]
                if Version("21.3.0") <= ATTRS_VERSION
                else [],
            )
            # Enum (membership)
            color = attr.ib(validator=validators.in_(["red", "green", "blue"]))
            # Unsupported pattern [(?i)]
            year = attr.ib(
                type=str,
                validator=[
                    validators.matches_re(r"(?i)\bY\d{4}\b"),
                ],
            )
            # Len limits on sequences/sets.
            tags = attr.ib(
                type=set[str],
                validator=validators.max_len(50) if Version("21.3.0") <= ATTRS_VERSION else [],
            )

        actual = ItemAdapter.get_json_schema(ItemClass)
        expected = {
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    **({"minLength": 3} if Version("22.1.0") <= ATTRS_VERSION else {}),
                    **({"maxLength": 10} if Version("21.3.0") <= ATTRS_VERSION else {}),
                    "pattern": "^[A-Za-z]+$",
                },
                "age": {
                    "type": "integer",
                    **(
                        {
                            "minimum": 18,
                            "maximum": 99,
                            "exclusiveMinimum": 17,
                            "exclusiveMaximum": 100,
                        }
                        if Version("21.3.0") <= ATTRS_VERSION
                        else {}
                    ),
                },
                "color": {"enum": ["red", "green", "blue"]},
                "year": {
                    "type": "string",
                },
                "tags": {
                    "type": "array",
                    "uniqueItems": True,
                    **({"maxItems": 50} if Version("21.3.0") <= ATTRS_VERSION else {}),
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["name", "age", "color", "year", "tags"],
        }
        self.assertEqual(expected, actual)


_PYDANTIC_NESTED_JSON_SCHEMA = {
    k: v for k, v in _NESTED_JSON_SCHEMA.items() if k != "additionalProperties"
}


class PydanticV1ModelTestCase(CustomItemClassTestMixin, unittest.TestCase):
    item_class = PydanticV1Model
    item_class_nested = PydanticV1ModelNested
    item_class_subclassed = PydanticV1ModelSubclassed
    item_class_empty = PydanticV1ModelEmpty
    item_class_json_schema = PydanticV1ModelJsonSchema
    expected_json_schema = {
        **{
            k: v
            for k, v in CustomItemClassTestMixin.expected_json_schema.items()
            if k not in {"additionalProperties", "properties"}
        },
        "properties": {
            **{
                k: v
                for k, v in CustomItemClassTestMixin.expected_json_schema["properties"].items()
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
            *CustomItemClassTestMixin.expected_json_schema["required"][:2],
            "produced",
            *CustomItemClassTestMixin.expected_json_schema["required"][2:],
        ],
    }

    def test_json_schema_validators(self):
        from itemadapter._imports import pydantic_v1

        class Model(pydantic_v1.BaseModel):
            # String with min/max length and regex pattern
            name: str = pydantic_v1.Field(
                min_length=3,
                max_length=10,
                pattern=r"^[A-Za-z]+$",
            )
            # Integer with minimum, maximum, exclusive minimum, exclusive maximum
            age1: int = pydantic_v1.Field(
                gt=17,
                lt=100,
            )
            age2: int = pydantic_v1.Field(
                ge=18,
                le=99,
            )
            # Sequence with max_items
            tags: set[str] = pydantic_v1.Field(max_length=50)

        actual = ItemAdapter.get_json_schema(Model)
        expected = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 10,
                    "pattern": "^[A-Za-z]+$",
                },
                "age1": {
                    "type": "integer",
                    "exclusiveMinimum": 17,
                    "exclusiveMaximum": 100,
                },
                "age2": {
                    "type": "integer",
                    "minimum": 18,
                    "maximum": 99,
                },
                "tags": {
                    "type": "array",
                    "uniqueItems": True,
                    "maxItems": 50,
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["name", "age1", "age2", "tags"],
        }
        self.assertEqual(expected, actual)


class PydanticModelTestCase(CustomItemClassTestMixin, unittest.TestCase):
    item_class = PydanticModel
    item_class_nested = PydanticModelNested
    item_class_subclassed = PydanticModelSubclassed
    item_class_empty = PydanticModelEmpty
    item_class_json_schema = PydanticModelJsonSchema
    expected_json_schema = {
        **{
            k: v
            for k, v in CustomItemClassTestMixin.expected_json_schema.items()
            if k not in {"additionalProperties", "properties"}
        },
        "properties": {
            **{
                k: v
                for k, v in CustomItemClassTestMixin.expected_json_schema["properties"].items()
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
    }

    def test_get_field_meta_defined_fields(self):
        adapter = ItemAdapter(self.item_class())
        self.assertEqual(
            adapter.get_field_meta("name")["json_schema_extra"],
            MappingProxyType({"serializer": str}),
        )
        self.assertEqual(
            adapter.get_field_meta("value")["json_schema_extra"],
            MappingProxyType({"serializer": int}),
        )

    def test_json_schema_validators(self):
        from itemadapter._imports import pydantic

        class Model(pydantic.BaseModel):
            # String with min/max length and regex pattern
            name: str = pydantic.Field(
                min_length=3,
                max_length=10,
                pattern=r"^[A-Za-z]+$",
            )
            # Integer with minimum, maximum, exclusive minimum, exclusive maximum
            age: int = pydantic.Field(
                ge=18,
                le=99,
                gt=17,
                lt=100,
            )
            # Sequence with max_items
            tags: set[str] = pydantic.Field(max_length=50)

        actual = ItemAdapter.get_json_schema(Model)
        expected = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 10,
                    "pattern": "^[A-Za-z]+$",
                },
                "age": {
                    "type": "integer",
                    "minimum": 18,
                    "maximum": 99,
                    "exclusiveMinimum": 17,
                    "exclusiveMaximum": 100,
                },
                "tags": {
                    "type": "array",
                    "uniqueItems": True,
                    "maxItems": 50,
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["name", "age", "tags"],
        }
        self.assertEqual(expected, actual)


class ScrapySubclassedItemTestCase(CustomItemClassTestMixin, unittest.TestCase):
    item_class = ScrapySubclassedItem
    item_class_nested = ScrapySubclassedItemNested
    item_class_subclassed = ScrapySubclassedItemSubclassed
    item_class_empty = ScrapySubclassedItemEmpty
    item_class_json_schema = ScrapySubclassedItemJsonSchema
    expected_json_schema = {
        **{
            k: v
            for k, v in CustomItemClassTestMixin.expected_json_schema.items()
            if k not in {"properties"}
        },
        "properties": {
            **{
                k: v
                for k, v in CustomItemClassTestMixin.expected_json_schema["properties"].items()
                if k != "produced"
            },
            # No type, since none was specified in json_schema_extra.
            "produced": {},
        },
        # Scrapy items seem to sort fields alphabetically. produced is required
        # because there is no default factory support in Scrapy.
        "required": sorted(
            CustomItemClassTestMixin.expected_json_schema["required"] + ["produced"]
        ),
        "llmHint": "Hi model!",
    }

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values."""
        adapter = ItemAdapter(self.item_class())
        with self.assertRaises(KeyError):
            adapter["name"]


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
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
            "required": ["nested"],
            "additionalProperties": False,
        }
        self.assertEqual(actual, expected)

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
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
            "required": ["nested"],
            "additionalProperties": False,
        }
        self.assertEqual(actual, expected)

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_scrapy_attrs(self):
        actual = ItemAdapter.get_json_schema(ScrapySubclassedItemCrossNested)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                    "additionalProperties": False,
                }
            },
            "required": ["nested"],
            "additionalProperties": False,
        }
        self.assertEqual(actual, expected)

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
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                    "additionalProperties": False,
                }
            },
            "required": ["nested"],
        }
        self.assertEqual(expected, actual)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_pydantic_dataclass(self):
        # Note: Works due to built-in dataclass support in Pydantic.
        from . import pydantic

        class TestItem(pydantic.BaseModel):
            nested: DataClassItemJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["nested"],
        }
        self.assertEqual(expected, actual)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_pydantic_scrapy(self):
        from . import pydantic

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
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["nested"],
        }
        self.assertEqual(expected, actual)


@dataclass
class RecursionNestedItem:
    parent: "RecursionItem"
    sibling: "RecursionNestedItem"


@dataclass
class RecursionItem:
    child: RecursionNestedItem
    sibling: "RecursionItem"


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

        from . import pydantic

        class TestEnum(Enum):
            foo = "foo"

        class TestPydanticModel(pydantic.BaseModel):
            enum: TestEnum

        @attrs.define
        class TestAttrsItem:
            pydantic: TestPydanticModel

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
