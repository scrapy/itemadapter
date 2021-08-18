import unittest
import warnings
from types import MappingProxyType
from unittest import mock

from itemadapter.adapter import ScrapyItemAdapter
from itemadapter.utils import get_field_meta_from_class

from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    ScrapyItem,
    ScrapySubclassedItem,
    mocked_import,
)


class ScrapyItemTestCase(unittest.TestCase):
    def test_false(self):
        self.assertFalse(ScrapyItemAdapter.is_item(int))
        self.assertFalse(ScrapyItemAdapter.is_item(sum))
        self.assertFalse(ScrapyItemAdapter.is_item(1234))
        self.assertFalse(ScrapyItemAdapter.is_item(object()))
        self.assertFalse(ScrapyItemAdapter.is_item(AttrsItem()))
        self.assertFalse(ScrapyItemAdapter.is_item(DataClassItem()))
        self.assertFalse(ScrapyItemAdapter.is_item(PydanticModel()))
        self.assertFalse(ScrapyItemAdapter.is_item("a string"))
        self.assertFalse(ScrapyItemAdapter.is_item(b"some bytes"))
        self.assertFalse(ScrapyItemAdapter.is_item({"a": "dict"}))
        self.assertFalse(ScrapyItemAdapter.is_item(["a", "list"]))
        self.assertFalse(ScrapyItemAdapter.is_item(("a", "tuple")))
        self.assertFalse(ScrapyItemAdapter.is_item({"a", "set"}))
        self.assertFalse(ScrapyItemAdapter.is_item(ScrapySubclassedItem))

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="ScrapySubclassedItem is not a valid item class"):
            get_field_meta_from_class(ScrapySubclassedItem, "name")

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_true(self):
        self.assertTrue(ScrapyItemAdapter.is_item(ScrapyItem()))
        self.assertTrue(ScrapyItemAdapter.is_item(ScrapySubclassedItem()))
        self.assertTrue(ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(ScrapySubclassedItem, "name"),
            MappingProxyType({"serializer": str}),
        )
        self.assertEqual(
            get_field_meta_from_class(ScrapySubclassedItem, "value"),
            MappingProxyType({"serializer": int}),
        )

    def test_deprecated_is_instance(self):
        from itemadapter.utils import is_scrapy_item

        with warnings.catch_warnings(record=True) as caught:
            is_scrapy_item(1)
            self.assertEqual(len(caught), 1)
            self.assertTrue(issubclass(caught[0].category, DeprecationWarning))
            self.assertEqual(
                "itemadapter.utils.is_scrapy_item is deprecated"
                " and it will be removed in a future version",
                str(caught[0].message),
            )


try:
    import scrapy
except ImportError:
    scrapy = None


class ScrapyDeprecatedBaseItemTestCase(unittest.TestCase):
    """Tests for deprecated classes. These will go away once the upstream classes are removed."""

    @unittest.skipIf(
        scrapy is None or not hasattr(scrapy.item, "_BaseItem"),
        "scrapy.item._BaseItem not available",
    )
    def test_deprecated_underscore_baseitem(self):
        class SubClassed_BaseItem(scrapy.item._BaseItem):
            pass

        self.assertTrue(ScrapyItemAdapter.is_item(scrapy.item._BaseItem()))
        self.assertTrue(ScrapyItemAdapter.is_item(SubClassed_BaseItem()))

    @unittest.skipIf(
        scrapy is None or not hasattr(scrapy.item, "BaseItem"),
        "scrapy.item.BaseItem not available",
    )
    def test_deprecated_baseitem(self):
        class SubClassedBaseItem(scrapy.item.BaseItem):
            pass

        self.assertTrue(ScrapyItemAdapter.is_item(scrapy.item.BaseItem()))
        self.assertTrue(ScrapyItemAdapter.is_item(SubClassedBaseItem()))

    @unittest.skipIf(scrapy is None, "scrapy module is not available")
    def test_removed_baseitem(self):
        """Mock the scrapy.item module so it does not contain the deprecated _BaseItem class."""

        class MockItemModule:
            Item = ScrapyItem

        with mock.patch("scrapy.item", MockItemModule):
            self.assertFalse(ScrapyItemAdapter.is_item(dict()))
            self.assertEqual(
                get_field_meta_from_class(ScrapySubclassedItem, "name"),
                MappingProxyType({"serializer": str}),
            )
            self.assertEqual(
                get_field_meta_from_class(ScrapySubclassedItem, "value"),
                MappingProxyType({"serializer": int}),
            )
