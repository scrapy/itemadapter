import re
import unittest
from types import MappingProxyType
from unittest import mock

import pytest

from itemadapter.adapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsClassicItem,
    AttrsItem,
    DataClassItem,
    PydanticModel,
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

        try:
            import scrapy  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not AttrsAdapter.is_item(ScrapyItem())
            assert not AttrsAdapter.is_item(ScrapySubclassedItem())

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("builtins.__import__", make_mock_import("attrs"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter import utils
            from itemadapter.adapter import AttrsAdapter

            assert not AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234))
            with pytest.raises(RuntimeError, match="attrs module is not available"):
                AttrsAdapter(AttrsItem(name="asdf", value=1234))
            with pytest.raises(RuntimeError, match="attrs module is not available"):
                AttrsAdapter.get_field_meta_from_class(AttrsItem, "name")
            with pytest.raises(RuntimeError, match="attrs module is not available"):
                AttrsAdapter.get_field_names_from_class(AttrsItem)
            with pytest.raises(TypeError, match=r"'tests.AttrsItem'\> is not a valid item class"):
                utils.get_field_meta_from_class(AttrsItem, "name")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("itemadapter._utils.attrs", None)
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

    @unittest.skipIf(not AttrsClassicItem, "attrs module is not available")
    def test_true_classic(self):
        from itemadapter.adapter import AttrsAdapter

        assert AttrsAdapter.is_item(AttrsClassicItem())
        assert AttrsAdapter.is_item(AttrsClassicItem(name="asdf", value=1234))
        assert not AttrsAdapter.is_item(AttrsClassicItem)
        # field metadata
        assert get_field_meta_from_class(AttrsClassicItem, "name") == MappingProxyType(
            {"serializer": str}
        )
        assert get_field_meta_from_class(AttrsClassicItem, "value") == MappingProxyType(
            {"serializer": int}
        )
        with pytest.raises(
            KeyError, match="AttrsClassicItem does not support field: non_existent"
        ):
            get_field_meta_from_class(AttrsClassicItem, "non_existent")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_json_schema_validators(self):
        import attrs
        from attrs import validators

        @attrs.define
        class ItemClass:
            # String with min/max length and regex pattern
            name: str = attrs.field(
                validator=[
                    validators.min_len(3),
                    validators.max_len(10),
                    validators.matches_re(r"^[A-Za-z]+$"),
                ],
            )
            # Integer with minimum, maximum, exclusive minimum, exclusive maximum
            age: int = attrs.field(
                validator=[
                    validators.ge(18),
                    validators.le(99),
                    validators.gt(17),
                    validators.lt(100),
                ],
            )
            # Enum (membership)
            color: str = attrs.field(validator=validators.in_(["red", "green", "blue"]))
            # Unsupported pattern [(?i)]
            year: str = attrs.field(
                validator=[
                    validators.matches_re(r"(?i)\bY\d{4}\b"),
                ],
            )
            # Unsupported flags
            month: str = attrs.field(
                validator=[
                    validators.matches_re(r"\bM\d{2}\b", flags=re.IGNORECASE),
                ],
            )
            # Unanchored pattern
            day: str = attrs.field(
                validator=[
                    validators.matches_re(r"\bD\d{2}\b", func=re.search),
                ],
            )
            # Prefix-anchored pattern
            hour: str = attrs.field(
                validator=[
                    validators.matches_re(r"H\d{2}", func=re.match),
                ],
            )
            # Len limits on sequences/sets.
            tags: set[str] = attrs.field(
                validator=validators.max_len(50),
            )

        actual = ItemAdapter.get_json_schema(ItemClass)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 10,
                    "pattern": "^(?:^[A-Za-z]+$)$",
                },
                "age": {
                    "type": "integer",
                    "minimum": 18,
                    "maximum": 99,
                    "exclusiveMinimum": 17,
                    "exclusiveMaximum": 100,
                },
                "color": {"type": "string", "enum": ["red", "green", "blue"]},
                "year": {
                    "type": "string",
                },
                "month": {
                    "type": "string",
                },
                "day": {
                    "type": "string",
                    "pattern": r"\bD\d{2}\b",
                },
                "hour": {
                    "type": "string",
                    "pattern": r"^(?:H\d{2})",
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
            "required": ["name", "age", "color", "year", "month", "day", "hour", "tags"],
        }
        check_schemas(actual, expected)
