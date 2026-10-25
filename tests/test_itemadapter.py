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

    def test_adapter_classes_change(self, monkeypatch: pytest.MonkeyPatch) -> None:
        item = DataClassItem()
        assert ItemAdapter.is_item(item)
        with monkeypatch.context() as m:
            m.setattr(ItemAdapter, "ADAPTER_CLASSES", (DictAdapter,))
            assert not ItemAdapter.is_item(item)
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
