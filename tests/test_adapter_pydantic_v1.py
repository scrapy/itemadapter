import unittest
from types import MappingProxyType
from unittest import mock

import pytest

from itemadapter.adapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticV1Model,
    PydanticV1SpecialCasesModel,
    ScrapyItem,
    ScrapySubclassedItem,
    clear_itemadapter_imports,
    make_mock_import,
)
from tests.test_json_schema import check_schemas


class PydanticTestCase(unittest.TestCase):
    def test_false(self):
        from itemadapter.adapter import PydanticAdapter

        assert not PydanticAdapter.is_item(int)
        assert not PydanticAdapter.is_item(sum)
        assert not PydanticAdapter.is_item(1234)
        assert not PydanticAdapter.is_item(object())
        assert not PydanticAdapter.is_item(DataClassItem())
        assert not PydanticAdapter.is_item("a string")
        assert not PydanticAdapter.is_item(b"some bytes")
        assert not PydanticAdapter.is_item({"a": "dict"})
        assert not PydanticAdapter.is_item(["a", "list"])
        assert not PydanticAdapter.is_item(("a", "tuple"))
        assert not PydanticAdapter.is_item({"a", "set"})
        assert not PydanticAdapter.is_item(PydanticV1Model)

        try:
            import attrs  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not PydanticAdapter.is_item(AttrsItem())

        try:
            import scrapy  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not PydanticAdapter.is_item(ScrapyItem())
            assert not PydanticAdapter.is_item(ScrapySubclassedItem())

    @unittest.skipIf(not PydanticV1Model, "pydantic <2 module is not available")
    @mock.patch("builtins.__import__", make_mock_import("pydantic"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter.adapter import PydanticAdapter

            assert not PydanticAdapter.is_item(PydanticV1Model(name="asdf", value=1234))
            with pytest.raises(
                TypeError, match=r"tests.PydanticV1Model'\> is not a valid item class"
            ):
                get_field_meta_from_class(PydanticV1Model, "name")

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    @mock.patch("itemadapter.utils.pydantic", None)
    @mock.patch("itemadapter.utils.pydantic_v1", None)
    def test_module_not_available(self):
        from itemadapter.adapter import PydanticAdapter

        assert not PydanticAdapter.is_item(PydanticV1Model(name="asdf", value=1234))
        with pytest.raises(TypeError, match=r"tests.PydanticV1Model'\> is not a valid item class"):
            get_field_meta_from_class(PydanticV1Model, "name")

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_true(self):
        from itemadapter.adapter import PydanticAdapter

        assert PydanticAdapter.is_item(PydanticV1Model())
        assert PydanticAdapter.is_item(PydanticV1Model(name="asdf", value=1234))
        # field metadata
        actual = get_field_meta_from_class(PydanticV1Model, "name")
        assert actual == MappingProxyType(
            {"serializer": str, "default_factory": actual["default_factory"]}
        )
        actual = get_field_meta_from_class(PydanticV1Model, "value")
        assert actual == MappingProxyType(
            {"serializer": int, "default_factory": actual["default_factory"]}
        )
        actual = get_field_meta_from_class(PydanticV1SpecialCasesModel, "special_cases")
        assert actual == MappingProxyType(
            {
                "alias": "special_cases",
                "allow_mutation": False,
                "default_factory": actual["default_factory"],
            }
        )
        with pytest.raises(KeyError, match="PydanticV1Model does not support field: non_existent"):
            get_field_meta_from_class(PydanticV1Model, "non_existent")

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_json_schema_forbid(self):
        from itemadapter._imports import pydantic_v1

        class Item(pydantic_v1.BaseModel):
            foo: str

            class Config:
                extra = "forbid"

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

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_json_schema_field_deprecated_bool(self):
        from itemadapter._imports import pydantic_v1

        class Item(pydantic_v1.BaseModel):
            foo: str = pydantic_v1.Field(deprecated=True)

        actual = ItemAdapter.get_json_schema(Item)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string", "deprecated": True},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_json_schema_field_deprecated_str(self):
        from itemadapter._imports import pydantic_v1

        class Item(pydantic_v1.BaseModel):
            foo: str = pydantic_v1.Field(deprecated="Use something else")

        actual = ItemAdapter.get_json_schema(Item)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string", "deprecated": True},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_json_schema_field_default_factory(self):
        from itemadapter._imports import pydantic_v1

        class Item(pydantic_v1.BaseModel):
            foo: str = pydantic_v1.Field(default_factory=lambda: "bar")

        actual = ItemAdapter.get_json_schema(Item)
        expected = {
            "type": "object",
            "properties": {
                "foo": {"type": "string"},
            },
        }
        check_schemas(actual, expected)

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
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
            tags: set[str] = pydantic_v1.Field(max_items=50)

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
                    "items": {
                        "type": "string",
                    },
                    "maxItems": 50,
                },
            },
            "required": ["name", "age1", "age2", "tags"],
        }
        check_schemas(actual, expected)
