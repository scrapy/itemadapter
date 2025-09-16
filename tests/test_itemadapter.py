import unittest

from itemadapter.adapter import DictAdapter, ItemAdapter


class DictOnlyItemAdapter(ItemAdapter):
    ADAPTER_CLASSES = [DictAdapter]


class ItemAdapterTestCase(unittest.TestCase):
    def test_repr(self):
        adapter = ItemAdapter({"foo": "bar"})
        assert repr(adapter) == "<ItemAdapter for dict(foo='bar')>"

    def test_repr_subclass(self):
        adapter = DictOnlyItemAdapter({"foo": "bar"})
        assert repr(adapter) == "<DictOnlyItemAdapter for dict(foo='bar')>"
