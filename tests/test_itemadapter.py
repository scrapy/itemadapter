import unittest

from itemadapter.adapter import ItemAdapter, DictAdapter


class DictOnlyItemAdapter(ItemAdapter):
    ADAPTER_CLASSES = [DictAdapter]


class ItemAdapterTestCase(unittest.TestCase):
    def test_repr(self):
        adapter = ItemAdapter(dict(foo="bar"))
        self.assertEqual(repr(adapter), "<ItemAdapter for dict(foo='bar')>")

    def test_repr_subclass(self):
        adapter = DictOnlyItemAdapter(dict(foo="bar"))
        self.assertEqual(repr(adapter), "<DictOnlyItemAdapter for dict(foo='bar')>")
