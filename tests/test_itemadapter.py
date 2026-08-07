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

    def test_clone(self):
        adapter = ItemAdapter({"foo": "bar"})
        clone = adapter.clone()
        assert isinstance(clone, ItemAdapter)
        assert clone is not adapter
        assert clone.item is not adapter.item
        assert dict(clone) == {"foo": "bar"}

    def test_clone_subclass(self):
        adapter = DictOnlyItemAdapter({"foo": "bar"})
        clone = adapter.clone()
        assert clone.__class__ is DictOnlyItemAdapter
        assert clone.item is not adapter.item
        assert dict(clone) == {"foo": "bar"}
