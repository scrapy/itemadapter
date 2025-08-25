import unittest
from types import MappingProxyType
from typing import Optional
from unittest import mock

from itemadapter.adapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    PydanticSpecialCasesModel,
    ScrapyItem,
    ScrapySubclassedItem,
    clear_itemadapter_imports,
    make_mock_import,
)
from tests.test_json_schema import check_schemas


class PydanticTestCase(unittest.TestCase):
    maxDiff = None

    def test_false(self):
        from itemadapter.adapter import PydanticAdapter

        self.assertFalse(PydanticAdapter.is_item(int))
        self.assertFalse(PydanticAdapter.is_item(sum))
        self.assertFalse(PydanticAdapter.is_item(1234))
        self.assertFalse(PydanticAdapter.is_item(object()))
        self.assertFalse(PydanticAdapter.is_item(DataClassItem()))
        self.assertFalse(PydanticAdapter.is_item("a string"))
        self.assertFalse(PydanticAdapter.is_item(b"some bytes"))
        self.assertFalse(PydanticAdapter.is_item({"a": "dict"}))
        self.assertFalse(PydanticAdapter.is_item(["a", "list"]))
        self.assertFalse(PydanticAdapter.is_item(("a", "tuple")))
        self.assertFalse(PydanticAdapter.is_item({"a", "set"}))
        self.assertFalse(PydanticAdapter.is_item(PydanticModel))

        try:
            import attrs  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            self.assertFalse(PydanticAdapter.is_item(AttrsItem()))

        try:
            import scrapy  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            self.assertFalse(PydanticAdapter.is_item(ScrapyItem()))
            self.assertFalse(PydanticAdapter.is_item(ScrapySubclassedItem()))

    @unittest.skipIf(not PydanticModel, "pydantic <2 module is not available")
    @mock.patch("builtins.__import__", make_mock_import("pydantic"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter.adapter import PydanticAdapter

            self.assertFalse(PydanticAdapter.is_item(PydanticModel(name="asdf", value=1234)))
            with self.assertRaises(TypeError, msg="PydanticModel is not a valid item class"):
                get_field_meta_from_class(PydanticModel, "name")

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @mock.patch("itemadapter.utils.pydantic", None)
    @mock.patch("itemadapter.utils.pydantic_v1", None)
    def test_module_not_available(self):
        from itemadapter.adapter import PydanticAdapter

        self.assertFalse(PydanticAdapter.is_item(PydanticModel(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="PydanticModel is not a valid item class"):
            get_field_meta_from_class(PydanticModel, "name")

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_true(self):
        from itemadapter.adapter import PydanticAdapter

        self.assertTrue(PydanticAdapter.is_item(PydanticModel()))
        self.assertTrue(PydanticAdapter.is_item(PydanticModel(name="asdf", value=1234)))
        # field metadata
        mapping_proxy_type = get_field_meta_from_class(PydanticModel, "name")
        self.assertEqual(
            mapping_proxy_type,
            MappingProxyType(
                {
                    "annotation": Optional[str],
                    "default_factory": mapping_proxy_type["default_factory"],
                    "json_schema_extra": {"serializer": str},
                    "repr": True,
                }
            ),
        )
        mapping_proxy_type = get_field_meta_from_class(PydanticModel, "value")
        self.assertEqual(
            get_field_meta_from_class(PydanticModel, "value"),
            MappingProxyType(
                {
                    "annotation": Optional[int],
                    "default_factory": mapping_proxy_type["default_factory"],
                    "json_schema_extra": {"serializer": int},
                    "repr": True,
                }
            ),
        )
        mapping_proxy_type = get_field_meta_from_class(PydanticSpecialCasesModel, "special_cases")
        self.assertEqual(
            mapping_proxy_type,
            MappingProxyType(
                {
                    "annotation": Optional[int],
                    "alias": "special_cases",
                    "alias_priority": 2,
                    "default_factory": mapping_proxy_type["default_factory"],
                    "validation_alias": "special_cases",
                    "serialization_alias": "special_cases",
                    "frozen": True,
                    "repr": True,
                }
            ),
        )
        with self.assertRaises(KeyError, msg="PydanticModel does not support field: non_existent"):
            get_field_meta_from_class(PydanticModel, "non_existent")

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_json_schema_forbid(self):
        from itemadapter._imports import pydantic

        class Item(pydantic.BaseModel):
            foo: str

            model_config = {
                "extra": "forbid",
            }

        actual = ItemAdapter.get_json_schema(Item)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_json_schema_field_deprecated_bool(self):
        from itemadapter._imports import pydantic

        class Item(pydantic.BaseModel):
            foo: str = pydantic.Field(deprecated=True)

        actual = ItemAdapter.get_json_schema(Item)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string", "deprecated": True},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_json_schema_field_deprecated_str(self):
        from itemadapter._imports import pydantic

        class Item(pydantic.BaseModel):
            foo: str = pydantic.Field(deprecated="Use something else")

        actual = ItemAdapter.get_json_schema(Item)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string", "deprecated": True},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
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
                    "exclusiveMinimum": 17,
                    "minimum": 18,
                    "exclusiveMaximum": 100,
                    "maximum": 99,
                },
                "tags": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                    },
                    "maxItems": 50,
                },
            },
            "required": ["name", "age", "tags"],
        }
        check_schemas(actual, expected)
