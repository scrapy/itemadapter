import unittest
from types import MappingProxyType
from unittest import mock

from itemadapter.utils import (
    get_field_meta_from_class,
    is_attrs_instance,
    is_dataclass_instance,
    is_scrapy_item,
)

from tests import (
    AttrsItem,
    DataClassItem,
    requires_attr,
    requires_dataclasses,
    requires_scrapy,
    ScrapyItem,
    ScrapySubclassedItem,
    TestCase,
)


def mocked_import(name, *args, **kwargs):
    raise ImportError(name)


class FieldMetaFromClassTestCase(unittest.TestCase):
    def test_invalid_item_class(self):
        with self.assertRaises(TypeError, msg="1 is not a valid item class"):
            get_field_meta_from_class(1, "field")
        with self.assertRaises(TypeError, msg="list is not a valid item class"):
            get_field_meta_from_class(list, "field")

    def test_empty_meta_for_dict(self):
        class DictSubclass(dict):
            pass

        self.assertEqual(get_field_meta_from_class(DictSubclass, "name"), MappingProxyType({}))
        self.assertEqual(get_field_meta_from_class(dict, "name"), MappingProxyType({}))


class ItemLikeTestCase(unittest.TestCase):
    def test_false(self):
        from itemadapter.utils import is_item

        self.assertFalse(is_item(int))
        self.assertFalse(is_item(sum))
        self.assertFalse(is_item(1234))
        self.assertFalse(is_item(object()))
        self.assertFalse(is_item("a string"))
        self.assertFalse(is_item(b"some bytes"))
        self.assertFalse(is_item(["a", "list"]))
        self.assertFalse(is_item(("a", "tuple")))
        self.assertFalse(is_item({"a", "set"}))
        self.assertFalse(is_item(dict))
        self.assertFalse(is_item(ScrapyItem))
        self.assertFalse(is_item(DataClassItem))
        self.assertFalse(is_item(ScrapySubclassedItem))
        self.assertFalse(is_item(AttrsItem))

    def test_true_dict(self):
        from itemadapter.utils import is_item

        self.assertTrue(is_item({"a": "dict"}))

    @requires_scrapy
    def test_true_scrapy(self):
        from itemadapter.utils import is_item

        self.assertTrue(is_item(ScrapyItem()))
        self.assertTrue(is_item(ScrapySubclassedItem(name="asdf", value=1234)))

    @requires_dataclasses
    def test_true_dataclass(self):
        from itemadapter.utils import is_item

        self.assertTrue(is_item(DataClassItem(name="asdf", value=1234)))

    @requires_attr
    def test_true_attrs(self):
        from itemadapter.utils import is_item

        self.assertTrue(is_item(AttrsItem(name="asdf", value=1234)))


class AttrsTestCase(TestCase):
    def test_false(self):
        from itemadapter.utils import is_attrs_instance

        self.assertFalse(is_attrs_instance(int))
        self.assertFalse(is_attrs_instance(sum))
        self.assertFalse(is_attrs_instance(1234))
        self.assertFalse(is_attrs_instance(object()))
        self.assertFalse(is_attrs_instance("a string"))
        self.assertFalse(is_attrs_instance(b"some bytes"))
        self.assertFalse(is_attrs_instance({"a": "dict"}))
        self.assertFalse(is_attrs_instance(["a", "list"]))
        self.assertFalse(is_attrs_instance(("a", "tuple")))
        self.assertFalse(is_attrs_instance({"a", "set"}))
        self.assertFalse(is_attrs_instance(AttrsItem))

    @requires_attr
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_attrs_instance(AttrsItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="AttrsItem is not a valid item class"):
            get_field_meta_from_class(AttrsItem, "name")

    @requires_attr
    def test_true(self):
        from itemadapter.utils import is_attrs_instance

        self.assertTrue(is_attrs_instance(AttrsItem()))
        self.assertTrue(is_attrs_instance(AttrsItem(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(AttrsItem, "name"), MappingProxyType({"serializer": str})
        )
        self.assertEqual(
            get_field_meta_from_class(AttrsItem, "value"), MappingProxyType({"serializer": int})
        )
        with self.assertRaises(KeyError, msg="AttrsItem does not support field: non_existent"):
            get_field_meta_from_class(AttrsItem, "non_existent")


class DataclassTestCase(TestCase):
    def test_false(self):
        from itemadapter.utils import is_dataclass_instance

        self.assertFalse(is_dataclass_instance(int))
        self.assertFalse(is_dataclass_instance(sum))
        self.assertFalse(is_dataclass_instance(1234))
        self.assertFalse(is_dataclass_instance(object()))
        self.assertFalse(is_dataclass_instance("a string"))
        self.assertFalse(is_dataclass_instance(b"some bytes"))
        self.assertFalse(is_dataclass_instance({"a": "dict"}))
        self.assertFalse(is_dataclass_instance(["a", "list"]))
        self.assertFalse(is_dataclass_instance(("a", "tuple")))
        self.assertFalse(is_dataclass_instance({"a", "set"}))
        self.assertFalse(is_dataclass_instance(DataClassItem))

    @requires_dataclasses
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_dataclass_instance(DataClassItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="DataClassItem is not a valid item class"):
            get_field_meta_from_class(DataClassItem, "name")

    @requires_dataclasses
    def test_true(self):
        from itemadapter.utils import is_dataclass_instance

        self.assertTrue(is_dataclass_instance(DataClassItem()))
        self.assertTrue(is_dataclass_instance(DataClassItem(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(DataClassItem, "name"), MappingProxyType({"serializer": str})
        )
        self.assertEqual(
            get_field_meta_from_class(DataClassItem, "value"),
            MappingProxyType({"serializer": int}),
        )
        with self.assertRaises(KeyError, msg="DataClassItem does not support field: non_existent"):
            get_field_meta_from_class(DataClassItem, "non_existent")


class ScrapyItemTestCase(TestCase):
    def test_false(self):
        from itemadapter.utils import is_scrapy_item

        self.assertFalse(is_scrapy_item(int))
        self.assertFalse(is_scrapy_item(sum))
        self.assertFalse(is_scrapy_item(1234))
        self.assertFalse(is_scrapy_item(object()))
        self.assertFalse(is_scrapy_item("a string"))
        self.assertFalse(is_scrapy_item(b"some bytes"))
        self.assertFalse(is_scrapy_item({"a": "dict"}))
        self.assertFalse(is_scrapy_item(["a", "list"]))
        self.assertFalse(is_scrapy_item(("a", "tuple")))
        self.assertFalse(is_scrapy_item({"a", "set"}))
        self.assertFalse(is_scrapy_item(ScrapySubclassedItem))

    @requires_scrapy
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_scrapy_item(ScrapySubclassedItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="ScrapySubclassedItem is not a valid item class"):
            get_field_meta_from_class(ScrapySubclassedItem, "name")

    @requires_scrapy
    def test_true(self):
        from itemadapter.utils import is_scrapy_item

        self.assertTrue(is_scrapy_item(ScrapyItem()))
        self.assertTrue(is_scrapy_item(ScrapySubclassedItem()))
        self.assertTrue(is_scrapy_item(ScrapySubclassedItem(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(ScrapySubclassedItem, "name"),
            MappingProxyType({"serializer": str}),
        )
        self.assertEqual(
            get_field_meta_from_class(ScrapySubclassedItem, "value"),
            MappingProxyType({"serializer": int}),
        )


try:
    import scrapy
except ImportError:
    scrapy = None


class ScrapyDeprecatedBaseItemTestCase(TestCase):
    """
    Tests for deprecated classes. These will go away once the upstream classes
    are removed.
    """

    required_extra_modules = ("scrapy",)

    @unittest.skipIf(
        not hasattr(scrapy.item, "_BaseItem"),
        "scrapy.item._BaseItem not available",
    )
    def test_deprecated_underscore_baseitem(self):
        from itemadapter.utils import is_scrapy_item

        class SubClassed_BaseItem(scrapy.item._BaseItem):
            pass

        self.assertTrue(is_scrapy_item(scrapy.item._BaseItem()))
        self.assertTrue(is_scrapy_item(SubClassed_BaseItem()))

    @unittest.skipIf(
        not hasattr(scrapy.item, "BaseItem"),
        "scrapy.item.BaseItem not available",
    )
    def test_deprecated_baseitem(self):
        from itemadapter.utils import is_scrapy_item

        class SubClassedBaseItem(scrapy.item.BaseItem):
            pass

        self.assertTrue(is_scrapy_item(scrapy.item.BaseItem()))
        self.assertTrue(is_scrapy_item(SubClassedBaseItem()))

    def test_removed_baseitem(self):
        """
        Mock the scrapy.item module so it does not contain the deprecated _BaseItem class
        """
        from itemadapter.utils import is_scrapy_item

        class MockItemModule:
            Item = ScrapyItem

        with mock.patch("scrapy.item", MockItemModule):
            self.assertFalse(is_scrapy_item(dict()))
            self.assertEqual(
                get_field_meta_from_class(ScrapySubclassedItem, "name"),
                MappingProxyType({"serializer": str}),
            )
            self.assertEqual(
                get_field_meta_from_class(ScrapySubclassedItem, "value"),
                MappingProxyType({"serializer": int}),
            )
