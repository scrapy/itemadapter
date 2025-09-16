import importlib
import importlib.metadata
import unittest
from types import MappingProxyType
from unittest import mock

import pytest
from packaging.version import Version

from itemadapter.adapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    PydanticV1Model,
    ScrapyItem,
    ScrapySubclassedItem,
    clear_itemadapter_imports,
    make_mock_import,
)
from tests.test_json_schema import check_schemas


class AttrsTestCase(unittest.TestCase):
    def test_false(self):
        from itemadapter.adapter import AttrsAdapter

        assert not AttrsAdapter.is_item(int)
        assert not AttrsAdapter.is_item(sum)
        assert not AttrsAdapter.is_item(1234)
        assert not AttrsAdapter.is_item(object())
        assert not AttrsAdapter.is_item(DataClassItem())
        assert not AttrsAdapter.is_item("a string")
        assert not AttrsAdapter.is_item(b"some bytes")
        assert not AttrsAdapter.is_item({"a": "dict"})
        assert not AttrsAdapter.is_item(["a", "list"])
        assert not AttrsAdapter.is_item(("a", "tuple"))
        assert not AttrsAdapter.is_item({"a", "set"})
        assert not AttrsAdapter.is_item(AttrsItem)

        if PydanticModel is not None:
            assert not AttrsAdapter.is_item(PydanticModel())
        if PydanticV1Model is not None:
            assert not AttrsAdapter.is_item(PydanticV1Model())

        try:
            import scrapy  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not AttrsAdapter.is_item(ScrapyItem())
            assert not AttrsAdapter.is_item(ScrapySubclassedItem())

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("builtins.__import__", make_mock_import("attr"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter.adapter import AttrsAdapter

            assert not AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234))
            with pytest.raises(RuntimeError, match="attr module is not available"):
                AttrsAdapter(AttrsItem(name="asdf", value=1234))
            with pytest.raises(RuntimeError, match="attr module is not available"):
                AttrsAdapter.get_field_meta_from_class(AttrsItem, "name")
            with pytest.raises(RuntimeError, match="attr module is not available"):
                AttrsAdapter.get_field_names_from_class(AttrsItem)
            with pytest.raises(TypeError, match=r"'tests.AttrsItem'\> is not a valid item class"):
                get_field_meta_from_class(AttrsItem, "name")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("itemadapter.utils.attr", None)
    def test_module_not_available(self):
        from itemadapter.adapter import AttrsAdapter

        assert not AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234))
        with pytest.raises(TypeError, match=r"'tests.AttrsItem'\> is not a valid item class"):
            get_field_meta_from_class(AttrsItem, "name")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_true(self):
        from itemadapter.adapter import AttrsAdapter

        assert AttrsAdapter.is_item(AttrsItem())
        assert AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234))
        # field metadata
        assert get_field_meta_from_class(AttrsItem, "name") == MappingProxyType(
            {"serializer": str}
        )
        assert get_field_meta_from_class(AttrsItem, "value") == MappingProxyType(
            {"serializer": int}
        )
        with pytest.raises(KeyError, match="AttrsItem does not support field: non_existent"):
            get_field_meta_from_class(AttrsItem, "non_existent")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_json_schema_validators(self):
        import attr
        from attr import validators

        ATTRS_VERSION = Version(importlib.metadata.version("attrs"))

        @attr.s
        class ItemClass:
            # String with min/max length and regex pattern
            name: str = attr.ib(
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
            age: int = attr.ib(
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
            color: str = attr.ib(validator=validators.in_(["red", "green", "blue"]))
            # Unsupported pattern [(?i)]
            year: str = attr.ib(
                validator=[
                    validators.matches_re(r"(?i)\bY\d{4}\b"),
                ],
            )
            # Len limits on sequences/sets.
            tags: set[str] = attr.ib(
                validator=validators.max_len(50) if Version("21.3.0") <= ATTRS_VERSION else [],
            )

        actual = ItemAdapter.get_json_schema(ItemClass)
        expected = {
            "type": "object",
            "additionalProperties": False,
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
                "color": {"type": "string", "enum": ["red", "green", "blue"]},
                "year": {
                    "type": "string",
                },
                "tags": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {
                        "type": "string",
                    },
                    **({"maxItems": 50} if Version("21.3.0") <= ATTRS_VERSION else {}),
                },
            },
            "required": ["name", "age", "color", "year", "tags"],
        }
        check_schemas(actual, expected)
