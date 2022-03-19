import unittest

from itemadapter.adapter import ItemAdapter


class SubclassedItemAdapter(ItemAdapter):
    pass


class ItemAdapterTestCase(unittest.TestCase):
    def test_repr(self):
        adapter = ItemAdapter(dict(foo="bar"))
        self.assertEqual(repr(adapter), "<ItemAdapter for dict(foo='bar')>")

    def test_repr_subclass(self):
        adapter = SubclassedItemAdapter(dict(foo="bar"))
        self.assertEqual(repr(adapter), "<SubclassedItemAdapter for dict(foo='bar')>")
