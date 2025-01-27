from types import MappingProxyType
from unittest import TestCase

from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    ScrapyItem,
    ScrapySubclassedItem,
)


class DataclassTestCase(TestCase):
    def test_false(self):
        from itemadapter.adapter import DataclassAdapter

        self.assertFalse(DataclassAdapter.is_item(int))
        self.assertFalse(DataclassAdapter.is_item(sum))
        self.assertFalse(DataclassAdapter.is_item(1234))
        self.assertFalse(DataclassAdapter.is_item(object()))
        self.assertFalse(DataclassAdapter.is_item(ScrapyItem()))
        self.assertFalse(DataclassAdapter.is_item(AttrsItem()))
        self.assertFalse(DataclassAdapter.is_item(PydanticModel()))
        self.assertFalse(DataclassAdapter.is_item(ScrapySubclassedItem()))
        self.assertFalse(DataclassAdapter.is_item("a string"))
        self.assertFalse(DataclassAdapter.is_item(b"some bytes"))
        self.assertFalse(DataclassAdapter.is_item({"a": "dict"}))
        self.assertFalse(DataclassAdapter.is_item(["a", "list"]))
        self.assertFalse(DataclassAdapter.is_item(("a", "tuple")))
        self.assertFalse(DataclassAdapter.is_item({"a", "set"}))
        self.assertFalse(DataclassAdapter.is_item(DataClassItem))

    def test_true(self):
        from itemadapter.adapter import DataclassAdapter

        self.assertTrue(DataclassAdapter.is_item(DataClassItem()))
        self.assertTrue(DataclassAdapter.is_item(DataClassItem(name="asdf", value=1234)))
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
