import unittest
import warnings
from types import MappingProxyType
from unittest import mock

from itemadapter.adapter import DataclassAdapter
from itemadapter.utils import get_field_meta_from_class

from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    ScrapyItem,
    ScrapySubclassedItem,
)


class DataclassTestCase(unittest.TestCase):
    def test_false(self):
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

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    @mock.patch("itemadapter.utils.dataclasses", None)
    def test_module_not_available(self):
        self.assertFalse(DataclassAdapter.is_item(DataClassItem(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="DataClassItem is not a valid item class"):
            get_field_meta_from_class(DataClassItem, "name")

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_true(self):
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

    def test_deprecated_is_instance(self):
        from itemadapter.utils import is_dataclass_instance

        with warnings.catch_warnings(record=True) as caught:
            is_dataclass_instance(1)
            self.assertEqual(len(caught), 1)
            self.assertTrue(issubclass(caught[0].category, DeprecationWarning))
            self.assertEqual(
                "itemadapter.utils.is_dataclass_instance is deprecated"
                " and it will be removed in a future version",
                str(caught[0].message),
            )
