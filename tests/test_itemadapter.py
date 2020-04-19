# -*- coding: utf-8 -*-
import sys
import unittest

from tests.mock_classes import Item, Field
from scrapy_itemadapter import _is_dataclass_instance, ItemAdapter


try:
    from dataclasses import make_dataclass, field
except ImportError:
    DataClassItem = None
else:
    DataClassItem = make_dataclass(
        "DataClassItem",
        [
            ("name", str, field(default_factory=lambda: None)),
            ("value", int, field(default_factory=lambda: None)),
        ],
    )


class ExampleItem(Item):
    name = Field(serializer=str)
    value = Field(serializer=int)


class DataclassTestCase(unittest.TestCase):
    def test_false_always(self):
        """These objects should return False whether or not the dataclasses module is available"""
        self.assertFalse(_is_dataclass_instance(int))
        self.assertFalse(_is_dataclass_instance(sum))
        self.assertFalse(_is_dataclass_instance(1234))
        self.assertFalse(_is_dataclass_instance(object()))
        self.assertFalse(_is_dataclass_instance(Item()))
        self.assertFalse(_is_dataclass_instance(ExampleItem()))
        self.assertFalse(_is_dataclass_instance("a string"))
        self.assertFalse(_is_dataclass_instance(b"some bytes"))
        self.assertFalse(_is_dataclass_instance({"a": "dict"}))
        self.assertFalse(_is_dataclass_instance(["a", "list"]))
        self.assertFalse(_is_dataclass_instance(("a", "tuple")))
        self.assertFalse(_is_dataclass_instance({"a", "set"}))

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_false_only_if_installed(self):
        self.assertFalse(_is_dataclass_instance(DataClassItem))

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_true_only_if_installed(self):
        self.assertTrue(_is_dataclass_instance(DataClassItem()))
        self.assertTrue(_is_dataclass_instance(DataClassItem(name="asdf", value=1234)))


class ItemAdapterReprTestCase(unittest.TestCase):
    @unittest.skipIf(sys.version_info.minor < 6, "dicts are not guaranteed to be ordered in py<36")
    def test_repr_dict_dict(self):
        item = dict(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter), "ItemAdapter for type dict: {'name': 'asdf', 'value': 1234}"
        )

    def test_repr_dict_item(self):
        item = ExampleItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter), "ItemAdapter for type ExampleItem: {'name': 'asdf', 'value': 1234}"
        )

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_repr_dataclass(self):
        item = DataClassItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "ItemAdapter for type DataClassItem: DataClassItem(name='asdf', value=1234)",
        )


class ItemAdapterTestCase(unittest.TestCase):
    def test_non_item(self):
        with self.assertRaises(TypeError):
            ItemAdapter(Item)
        with self.assertRaises(TypeError):
            ItemAdapter(dict)
        with self.assertRaises(TypeError):
            ItemAdapter(1234)

    def test_get_set_value(self):
        for cls in filter(None, [ExampleItem, dict, DataClassItem]):
            item = cls()
            adapter = ItemAdapter(item)
            self.assertEqual(adapter.get("name"), None)
            self.assertEqual(adapter.get("value"), None)
            adapter["name"] = "asdf"
            adapter["value"] = 1234
            self.assertEqual(adapter.get("name"), "asdf")
            self.assertEqual(adapter.get("value"), 1234)
            self.assertEqual(adapter["name"], "asdf")
            self.assertEqual(adapter["value"], 1234)

        for cls in filter(None, [ExampleItem, dict, DataClassItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(adapter.get("name"), "asdf")
            self.assertEqual(adapter.get("value"), 1234)
            self.assertEqual(adapter["name"], "asdf")
            self.assertEqual(adapter["value"], 1234)

    def test_get_value_keyerror_all(self):
        for cls in filter(None, [ExampleItem, dict, DataClassItem]):
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["undefined_field"]

    def test_get_value_keyerror_item_dict(self):
        for cls in [ExampleItem, dict]:
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["name"]

    def test_set_value_keyerror(self):
        for cls in filter(None, [ExampleItem, DataClassItem]):
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["undefined_field"] = "some value"

    def test_delitem_len_iter(self):
        for cls in filter(None, [ExampleItem, dict, DataClassItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(len(adapter), 2)
            self.assertEqual(sorted(list(iter(adapter))), ["name", "value"])

            del adapter["name"]
            self.assertEqual(len(adapter), 1)
            self.assertEqual(sorted(list(iter(adapter))), ["value"])

            del adapter["value"]
            self.assertEqual(len(adapter), 0)
            self.assertEqual(sorted(list(iter(adapter))), [])

            with self.assertRaises(KeyError):
                del adapter["name"]
            with self.assertRaises(KeyError):
                del adapter["value"]
            with self.assertRaises(KeyError):
                del adapter["undefined_field"]

    def test_get_field(self):
        for cls in filter(None, [dict, DataClassItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertIsNone(adapter.get_field("undefined_field"))
            self.assertIsNone(adapter.get_field("name"))
            self.assertIsNone(adapter.get_field("value"))

        item = ExampleItem()
        adapter = ItemAdapter(item)
        self.assertIsNone(adapter.get_field("undefined_field"))
        self.assertIsInstance(adapter.get_field("name"), Field)
        self.assertIsInstance(adapter.get_field("value"), Field)
        self.assertIs(adapter.get_field("name")["serializer"], str)
        self.assertIs(adapter.get_field("value")["serializer"], int)

    def test_as_dict(self):
        for cls in filter(None, [ExampleItem, dict, DataClassItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(dict(name="asdf", value=1234), dict(adapter))

    def test_field_names(self):
        for cls in filter(None, [ExampleItem, dict, DataClassItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertIsInstance(adapter.field_names(), list)
            self.assertEqual(sorted(adapter.field_names()), ["name", "value"])
