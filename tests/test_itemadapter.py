from typing import Any

import pytest

from itemadapter.adapter import DictAdapter, ItemAdapter
from tests import DataClassItem


class DictOnlyItemAdapter(ItemAdapter):
    ADAPTER_CLASSES = [DictAdapter]


class EmptyDictAdapter(DictAdapter):
    """An adapter that only handles empty dicts, which it can only tell on an
    item basis."""

    @classmethod
    def is_item(cls, item: Any) -> bool:
        return isinstance(item, dict) and not item


class TestItemAdapter:
    def test_repr(self):
        adapter = ItemAdapter({"foo": "bar"})
        assert repr(adapter) == "<ItemAdapter for dict(foo='bar')>"

    def test_adapter_classes_change(self):
        item = DataClassItem()
        adapter_classes = ItemAdapter.ADAPTER_CLASSES
        assert ItemAdapter.is_item(item)
        ItemAdapter.ADAPTER_CLASSES = (DictAdapter,)
        try:
            assert not ItemAdapter.is_item(item)
        finally:
            ItemAdapter.ADAPTER_CLASSES = adapter_classes
        assert ItemAdapter.is_item(item)

    def test_repr_subclass(self):
        adapter = DictOnlyItemAdapter({"foo": "bar"})
        assert repr(adapter) == "<DictOnlyItemAdapter for dict(foo='bar')>"

    def test_is_item_override(self):
        class EmptyDictItemAdapter(ItemAdapter):
            ADAPTER_CLASSES = (EmptyDictAdapter,)

        with pytest.warns(DeprecationWarning, match="EmptyDictAdapter"):
            assert EmptyDictItemAdapter.is_item({})
        assert not EmptyDictItemAdapter.is_item({"foo": "bar"})
        assert isinstance(EmptyDictItemAdapter({}).adapter, EmptyDictAdapter)
        with pytest.raises(TypeError, match="No adapter found"):
            EmptyDictItemAdapter({"foo": "bar"})
