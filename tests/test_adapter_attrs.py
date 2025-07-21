import importlib
import importlib.metadata
import unittest
from types import MappingProxyType
from unittest import mock

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


class AttrsTestCase(unittest.TestCase):
    def test_false(self):
        from itemadapter.adapter import AttrsAdapter

        self.assertFalse(AttrsAdapter.is_item(int))
        self.assertFalse(AttrsAdapter.is_item(sum))
        self.assertFalse(AttrsAdapter.is_item(1234))
        self.assertFalse(AttrsAdapter.is_item(object()))
        self.assertFalse(AttrsAdapter.is_item(DataClassItem()))
        self.assertFalse(AttrsAdapter.is_item("a string"))
        self.assertFalse(AttrsAdapter.is_item(b"some bytes"))
        self.assertFalse(AttrsAdapter.is_item({"a": "dict"}))
        self.assertFalse(AttrsAdapter.is_item(["a", "list"]))
        self.assertFalse(AttrsAdapter.is_item(("a", "tuple")))
        self.assertFalse(AttrsAdapter.is_item({"a", "set"}))
        self.assertFalse(AttrsAdapter.is_item(AttrsItem))

        if PydanticModel is not None:
            self.assertFalse(AttrsAdapter.is_item(PydanticModel()))
        if PydanticV1Model is not None:
            self.assertFalse(AttrsAdapter.is_item(PydanticV1Model()))

        try:
            import scrapy  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            self.assertFalse(AttrsAdapter.is_item(ScrapyItem()))
            self.assertFalse(AttrsAdapter.is_item(ScrapySubclassedItem()))

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("builtins.__import__", make_mock_import("attr"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter.adapter import AttrsAdapter

            self.assertFalse(AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234)))
            with self.assertRaises(RuntimeError, msg="attr module is not available"):
                AttrsAdapter(AttrsItem(name="asdf", value=1234))
            with self.assertRaises(RuntimeError, msg="attr module is not available"):
                AttrsAdapter.get_field_meta_from_class(AttrsItem, "name")
            with self.assertRaises(RuntimeError, msg="attr module is not available"):
                AttrsAdapter.get_field_names_from_class(AttrsItem)
            with self.assertRaises(TypeError, msg="AttrsItem is not a valid item class"):
                get_field_meta_from_class(AttrsItem, "name")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("itemadapter.utils.attr", None)
    def test_module_not_available(self):
        from itemadapter.adapter import AttrsAdapter

        self.assertFalse(AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="AttrsItem is not a valid item class"):
            get_field_meta_from_class(AttrsItem, "name")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_true(self):
        from itemadapter.adapter import AttrsAdapter

        self.assertTrue(AttrsAdapter.is_item(AttrsItem()))
        self.assertTrue(AttrsAdapter.is_item(AttrsItem(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(AttrsItem, "name"),
            MappingProxyType({"serializer": str}),
        )
        self.assertEqual(
            get_field_meta_from_class(AttrsItem, "value"),
            MappingProxyType({"serializer": int}),
        )
        with self.assertRaises(KeyError, msg="AttrsItem does not support field: non_existent"):
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
                "color": {"enum": ["red", "green", "blue"], "type": "string"},
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
