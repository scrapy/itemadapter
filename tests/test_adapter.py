import sys
import unittest
from types import MappingProxyType

import attr
from scrapy.item import Item, Field

from itemadapter.adapter import ItemAdapter
from itemadapter.exceptions import NoMetadataSupport


try:
    from dataclasses import make_dataclass, field
except ImportError:
    DataClassItem = None
else:
    DataClassItem = make_dataclass(
        "DataClassItem",
        [
            ("name", str, field(default_factory=lambda: None, metadata={"serializer": str})),
            ("value", int, field(default_factory=lambda: None, metadata={"serializer": int})),
        ],
    )


@attr.s
class AttrsItem:
    name = attr.ib(default=None, metadata={"serializer": str})
    value = attr.ib(default=None, metadata={"serializer": int})


class ScrapyItem(Item):
    name = Field(serializer=str)
    value = Field(serializer=int)


def mocked_import(name, *args, **kwargs):
    raise ImportError(name)


class ItemAdapterReprTestCase(unittest.TestCase):
    @unittest.skipIf(sys.version_info.minor < 6, "dicts are not guaranteed to be ordered in py<36")
    def test_repr_dict_dict(self):
        item = dict(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter), "ItemAdapter for type dict: {'name': 'asdf', 'value': 1234}"
        )

    def test_repr_dict_item(self):
        item = ScrapyItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter), "ItemAdapter for type ScrapyItem: {'name': 'asdf', 'value': 1234}"
        )

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_repr_dataclass(self):
        item = DataClassItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "ItemAdapter for type DataClassItem: DataClassItem(name='asdf', value=1234)",
        )

    def test_repr_attrs(self):
        item = AttrsItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter), "ItemAdapter for type AttrsItem: AttrsItem(name='asdf', value=1234)",
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
        for cls in filter(None, [ScrapyItem, dict, DataClassItem, AttrsItem]):
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

        for cls in filter(None, [ScrapyItem, dict, DataClassItem, AttrsItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(adapter.get("name"), "asdf")
            self.assertEqual(adapter.get("value"), 1234)
            self.assertEqual(adapter["name"], "asdf")
            self.assertEqual(adapter["value"], 1234)

    def test_get_value_keyerror_all(self):
        for cls in filter(None, [ScrapyItem, dict, DataClassItem, AttrsItem]):
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["undefined_field"]

    def test_get_value_keyerror_item_dict(self):
        """
        scrapy.item.Item and dicts can be initialized without default values for all fields
        """
        for cls in [ScrapyItem, dict]:
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["name"]

    def test_set_value_keyerror(self):
        for cls in filter(None, [ScrapyItem, DataClassItem, AttrsItem]):
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["undefined_field"] = "some value"

    def test_delitem_len_iter(self):
        for cls in filter(None, [ScrapyItem, dict, DataClassItem, AttrsItem]):
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

    def test_as_dict(self):
        for cls in filter(None, [ScrapyItem, dict, DataClassItem, AttrsItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(dict(name="asdf", value=1234), dict(adapter))

    def test_field_names(self):
        for cls in filter(None, [ScrapyItem, dict, DataClassItem, AttrsItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertIsInstance(adapter.field_names(), list)
            self.assertEqual(sorted(adapter.field_names()), ["name", "value"])


class MetadataTestCase(unittest.TestCase):
    def test_meta_common(self):
        for cls in filter(None, [ScrapyItem, DataClassItem, AttrsItem]):
            adapter = ItemAdapter(cls())
            self.assertIsInstance(adapter.get_field_meta("name"), MappingProxyType)
            self.assertIsInstance(adapter.get_field_meta("value"), MappingProxyType)
            with self.assertRaises(KeyError):
                adapter.get_field_meta("undefined_field")

    def test_meta_dict(self):
        adapter = ItemAdapter(dict(name="foo", value=5))
        with self.assertRaises(NoMetadataSupport):
            adapter.get_field_meta("name")
        with self.assertRaises(NoMetadataSupport):
            adapter.get_field_meta("value")
        with self.assertRaises(NoMetadataSupport):
            adapter.get_field_meta("undefined_field")

    def test_get_field_meta_defined_fields(self):
        for cls in filter(None, [ScrapyItem, DataClassItem, AttrsItem]):
            adapter = ItemAdapter(cls())
            self.assertEqual(adapter.get_field_meta("name"), MappingProxyType({"serializer": str}))
            self.assertEqual(
                adapter.get_field_meta("value"), MappingProxyType({"serializer": int})
            )
