import unittest
from types import MappingProxyType

from itemadapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class, is_item
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticV1Model,
    ScrapyItem,
    ScrapySubclassedItem,
)


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
        self.assertFalse(is_item(PydanticV1Model))
        self.assertFalse(ItemAdapter.is_item_class(list))
        self.assertFalse(ItemAdapter.is_item_class(int))
        self.assertFalse(ItemAdapter.is_item_class(tuple))

    def test_true_dict(self):
        self.assertTrue(is_item({"a": "dict"}))
        self.assertTrue(ItemAdapter.is_item_class(dict))

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_true_scrapy(self):
        self.assertTrue(is_item(ScrapyItem()))
        self.assertTrue(is_item(ScrapySubclassedItem(name="asdf", value=1234)))
        self.assertTrue(ItemAdapter.is_item_class(ScrapyItem))
        self.assertTrue(ItemAdapter.is_item_class(ScrapySubclassedItem))

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_true_dataclass(self):
        self.assertTrue(is_item(DataClassItem(name="asdf", value=1234)))
        self.assertTrue(ItemAdapter.is_item_class(DataClassItem))

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_true_attrs(self):
        self.assertTrue(is_item(AttrsItem(name="asdf", value=1234)))
        self.assertTrue(ItemAdapter.is_item_class(AttrsItem))

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_true_pydantic(self):
        self.assertTrue(is_item(PydanticV1Model(name="asdf", value=1234)))
        self.assertTrue(ItemAdapter.is_item_class(PydanticV1Model))
