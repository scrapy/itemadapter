import unittest
from types import MappingProxyType
from unittest import mock

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
            get_field_meta_from_class(AttrsItem, "name"), MappingProxyType({"serializer": str})
        )
        self.assertEqual(
            get_field_meta_from_class(AttrsItem, "value"), MappingProxyType({"serializer": int})
        )
        with self.assertRaises(KeyError, msg="AttrsItem does not support field: non_existent"):
            get_field_meta_from_class(AttrsItem, "non_existent")
