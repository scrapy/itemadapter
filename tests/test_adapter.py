import unittest
from types import MappingProxyType

from itemadapter.adapter import ItemAdapter

from tests import AttrsItem, DataClassItem, ScrapySubclassedItem


class ItemAdapterReprTestCase(unittest.TestCase):
    def test_repr_dict_dict(self):
        item = dict(name="asdf")
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "ItemAdapter for type dict: {'name': 'asdf'}")

    def test_repr_dict_item(self):
        item = ScrapySubclassedItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "ItemAdapter for type ScrapySubclassedItem: {'name': 'asdf', 'value': 1234}",
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
            ItemAdapter(ScrapySubclassedItem)
        with self.assertRaises(TypeError):
            ItemAdapter(dict)
        with self.assertRaises(TypeError):
            ItemAdapter(1234)

    def test_get_set_value(self):
        for cls in filter(None, [ScrapySubclassedItem, dict, DataClassItem, AttrsItem]):
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

        for cls in filter(None, [ScrapySubclassedItem, dict, DataClassItem, AttrsItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(adapter.get("name"), "asdf")
            self.assertEqual(adapter.get("value"), 1234)
            self.assertEqual(adapter["name"], "asdf")
            self.assertEqual(adapter["value"], 1234)

    def test_get_value_keyerror_all(self):
        for cls in filter(None, [ScrapySubclassedItem, dict, DataClassItem, AttrsItem]):
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["undefined_field"]

    def test_get_value_keyerror_item_dict(self):
        """
        scrapy.item.Item and dicts can be initialized without default values for all fields
        """
        for cls in [ScrapySubclassedItem, dict]:
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["name"]

    def test_set_value_keyerror(self):
        for cls in filter(None, [ScrapySubclassedItem, DataClassItem, AttrsItem]):
            item = cls()
            adapter = ItemAdapter(item)
            with self.assertRaises(KeyError):
                adapter["undefined_field"] = "some value"

    def test_delitem_len_iter(self):
        for cls in filter(None, [ScrapySubclassedItem, dict, DataClassItem, AttrsItem]):
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
        for cls in filter(None, [ScrapySubclassedItem, dict, DataClassItem, AttrsItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertEqual(dict(name="asdf", value=1234), dict(adapter))

    def test_field_names(self):
        for cls in filter(None, [ScrapySubclassedItem, dict, DataClassItem, AttrsItem]):
            item = cls(name="asdf", value=1234)
            adapter = ItemAdapter(item)
            self.assertIsInstance(adapter.field_names(), list)
            self.assertEqual(sorted(adapter.field_names()), ["name", "value"])


class MetadataTestCase(unittest.TestCase):
    def test_meta_common(self):
        for cls in filter(None, [ScrapySubclassedItem, DataClassItem, AttrsItem]):
            adapter = ItemAdapter(cls())
            self.assertIsInstance(adapter.get_field_meta("name"), MappingProxyType)
            self.assertIsInstance(adapter.get_field_meta("value"), MappingProxyType)
            with self.assertRaises(KeyError):
                adapter.get_field_meta("undefined_field")

    def test_meta_dict(self):
        adapter = ItemAdapter(dict(name="foo", value=5))
        with self.assertRaises(TypeError):
            adapter.get_field_meta("name")
        with self.assertRaises(TypeError):
            adapter.get_field_meta("value")
        with self.assertRaises(TypeError):
            adapter.get_field_meta("undefined_field")

    def test_get_field_meta_defined_fields(self):
        for cls in filter(None, [ScrapySubclassedItem, DataClassItem, AttrsItem]):
            adapter = ItemAdapter(cls())
            self.assertEqual(adapter.get_field_meta("name"), MappingProxyType({"serializer": str}))
            self.assertEqual(
                adapter.get_field_meta("value"), MappingProxyType({"serializer": int})
            )
