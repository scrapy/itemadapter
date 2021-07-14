import unittest
from unittest import mock
from types import MappingProxyType

from itemadapter.utils import (
    get_field_meta_from_class,
    is_attrs_instance,
    is_dataclass_instance,
    is_item,
    is_pydantic_instance,
    is_scrapy_item,
)

from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    PydanticSpecialCasesModel,
    ScrapyItem,
    ScrapySubclassedItem,
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
        self.assertFalse(is_item(PydanticModel))

    def test_true_dict(self):
        self.assertTrue(is_item({"a": "dict"}))

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_true_scrapy(self):
        self.assertTrue(is_item(ScrapyItem()))
        self.assertTrue(is_item(ScrapySubclassedItem(name="asdf", value=1234)))

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_true_dataclass(self):
        self.assertTrue(is_item(DataClassItem(name="asdf", value=1234)))

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_true_attrs(self):
        self.assertTrue(is_item(AttrsItem(name="asdf", value=1234)))

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_true_pydantic(self):
        self.assertTrue(is_item(PydanticModel(name="asdf", value=1234)))


class AttrsTestCase(unittest.TestCase):
    def test_false(self):
        self.assertFalse(is_attrs_instance(int))
        self.assertFalse(is_attrs_instance(sum))
        self.assertFalse(is_attrs_instance(1234))
        self.assertFalse(is_attrs_instance(object()))
        self.assertFalse(is_attrs_instance(ScrapyItem()))
        self.assertFalse(is_attrs_instance(DataClassItem()))
        self.assertFalse(is_attrs_instance(PydanticModel()))
        self.assertFalse(is_attrs_instance(ScrapySubclassedItem()))
        self.assertFalse(is_attrs_instance("a string"))
        self.assertFalse(is_attrs_instance(b"some bytes"))
        self.assertFalse(is_attrs_instance({"a": "dict"}))
        self.assertFalse(is_attrs_instance(["a", "list"]))
        self.assertFalse(is_attrs_instance(("a", "tuple")))
        self.assertFalse(is_attrs_instance({"a", "set"}))
        self.assertFalse(is_attrs_instance(AttrsItem))

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_attrs_instance(AttrsItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="AttrsItem is not a valid item class"):
            get_field_meta_from_class(AttrsItem, "name")

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_true(self):
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


class DataclassTestCase(unittest.TestCase):
    def test_false(self):
        self.assertFalse(is_dataclass_instance(int))
        self.assertFalse(is_dataclass_instance(sum))
        self.assertFalse(is_dataclass_instance(1234))
        self.assertFalse(is_dataclass_instance(object()))
        self.assertFalse(is_dataclass_instance(ScrapyItem()))
        self.assertFalse(is_dataclass_instance(AttrsItem()))
        self.assertFalse(is_dataclass_instance(PydanticModel()))
        self.assertFalse(is_dataclass_instance(ScrapySubclassedItem()))
        self.assertFalse(is_dataclass_instance("a string"))
        self.assertFalse(is_dataclass_instance(b"some bytes"))
        self.assertFalse(is_dataclass_instance({"a": "dict"}))
        self.assertFalse(is_dataclass_instance(["a", "list"]))
        self.assertFalse(is_dataclass_instance(("a", "tuple")))
        self.assertFalse(is_dataclass_instance({"a", "set"}))
        self.assertFalse(is_dataclass_instance(DataClassItem))

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_dataclass_instance(DataClassItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="DataClassItem is not a valid item class"):
            get_field_meta_from_class(DataClassItem, "name")

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_true(self):
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


class PydanticTestCase(unittest.TestCase):
    def test_false(self):
        self.assertFalse(is_pydantic_instance(int))
        self.assertFalse(is_pydantic_instance(sum))
        self.assertFalse(is_pydantic_instance(1234))
        self.assertFalse(is_pydantic_instance(object()))
        self.assertFalse(is_pydantic_instance(ScrapyItem()))
        self.assertFalse(is_pydantic_instance(AttrsItem()))
        self.assertFalse(is_pydantic_instance(DataClassItem()))
        self.assertFalse(is_pydantic_instance(ScrapySubclassedItem()))
        self.assertFalse(is_pydantic_instance("a string"))
        self.assertFalse(is_pydantic_instance(b"some bytes"))
        self.assertFalse(is_pydantic_instance({"a": "dict"}))
        self.assertFalse(is_pydantic_instance(["a", "list"]))
        self.assertFalse(is_pydantic_instance(("a", "tuple")))
        self.assertFalse(is_pydantic_instance({"a", "set"}))
        self.assertFalse(is_pydantic_instance(PydanticModel))

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_pydantic_instance(PydanticModel(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="PydanticModel is not a valid item class"):
            get_field_meta_from_class(PydanticModel, "name")

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_true(self):
        self.assertTrue(is_pydantic_instance(PydanticModel()))
        self.assertTrue(is_pydantic_instance(PydanticModel(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(PydanticModel, "name"),
            MappingProxyType({"serializer": str}),
        )
        self.assertEqual(
            get_field_meta_from_class(PydanticModel, "value"),
            MappingProxyType({"serializer": int}),
        )
        self.assertEqual(
            get_field_meta_from_class(PydanticSpecialCasesModel, "special_cases"),
            MappingProxyType({"alias": "special_cases", "allow_mutation": False}),
        )
        with self.assertRaises(KeyError, msg="PydanticModel does not support field: non_existent"):
            get_field_meta_from_class(PydanticModel, "non_existent")


class ScrapyItemTestCase(unittest.TestCase):
    def test_false(self):
        self.assertFalse(is_scrapy_item(int))
        self.assertFalse(is_scrapy_item(sum))
        self.assertFalse(is_scrapy_item(1234))
        self.assertFalse(is_scrapy_item(object()))
        self.assertFalse(is_scrapy_item(AttrsItem()))
        self.assertFalse(is_scrapy_item(DataClassItem()))
        self.assertFalse(is_scrapy_item(PydanticModel()))
        self.assertFalse(is_scrapy_item("a string"))
        self.assertFalse(is_scrapy_item(b"some bytes"))
        self.assertFalse(is_scrapy_item({"a": "dict"}))
        self.assertFalse(is_scrapy_item(["a", "list"]))
        self.assertFalse(is_scrapy_item(("a", "tuple")))
        self.assertFalse(is_scrapy_item({"a", "set"}))
        self.assertFalse(is_scrapy_item(ScrapySubclassedItem))

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @mock.patch("builtins.__import__", mocked_import)
    def test_module_not_available(self):
        self.assertFalse(is_scrapy_item(ScrapySubclassedItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="ScrapySubclassedItem is not a valid item class"):
            get_field_meta_from_class(ScrapySubclassedItem, "name")

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_true(self):
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


class ScrapyDeprecatedBaseItemTestCase(unittest.TestCase):
    """Tests for deprecated classes. These will go away once the upstream classes are removed."""

    @unittest.skipIf(
        scrapy is None or not hasattr(scrapy.item, "_BaseItem"),
        "scrapy.item._BaseItem not available",
    )
    def test_deprecated_underscore_baseitem(self):
        class SubClassed_BaseItem(scrapy.item._BaseItem):
            pass

        self.assertTrue(is_scrapy_item(scrapy.item._BaseItem()))
        self.assertTrue(is_scrapy_item(SubClassed_BaseItem()))

    @unittest.skipIf(
        scrapy is None or not hasattr(scrapy.item, "BaseItem"),
        "scrapy.item.BaseItem not available",
    )
    def test_deprecated_baseitem(self):
        class SubClassedBaseItem(scrapy.item.BaseItem):
            pass

        self.assertTrue(is_scrapy_item(scrapy.item.BaseItem()))
        self.assertTrue(is_scrapy_item(SubClassedBaseItem()))

    @unittest.skipIf(scrapy is None, "scrapy module is not available")
    def test_removed_baseitem(self):
        """Mock the scrapy.item module so it does not contain the deprecated _BaseItem class."""

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
