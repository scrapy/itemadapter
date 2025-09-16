from __future__ import annotations

import unittest
from collections.abc import Iterator, KeysView
from types import MappingProxyType
from typing import Any
from unittest import mock

import pytest

from itemadapter.adapter import AdapterInterface, ItemAdapter


class AdapterInterfaceTest(unittest.TestCase):
    @mock.patch.multiple(AdapterInterface, __abstractmethods__=set())
    def test_interface_class_methods(self):
        with pytest.raises(NotImplementedError):
            AdapterInterface.is_item(object())
        with pytest.raises(NotImplementedError):
            AdapterInterface.is_item_class(object)


class FakeItemClass:
    _fields = {
        "name": {"serializer": str},
        "value": {"serializer": int},
    }

    def __init__(self, **kwargs) -> None:
        self._values = {**kwargs}


class BaseFakeItemAdapter(AdapterInterface):
    """An adapter that only implements the required methods."""

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return issubclass(item_class, FakeItemClass)

    def __getitem__(self, field_name: str) -> Any:
        if field_name in self.item._fields:
            return self.item._values[field_name]
        raise KeyError(field_name)

    def __setitem__(self, field_name: str, value: Any) -> None:
        if field_name in self.item._fields:
            self.item._values[field_name] = value
        else:
            raise KeyError(field_name)

    def __delitem__(self, field_name: str) -> None:
        if field_name in self.item._fields and field_name in self.item._values:
            del self.item._values[field_name]
        else:
            raise KeyError(field_name)

    def __iter__(self) -> Iterator:
        return iter(self.item._values)

    def __len__(self) -> int:
        return len(self.item._values)


class FieldNamesFakeItemAdapter(BaseFakeItemAdapter):
    """An adapter that also implements the field_names method."""

    def field_names(self) -> KeysView:
        return KeysView({key.upper(): value for key, value in self.item._fields.items()})


class MetadataFakeItemAdapter(BaseFakeItemAdapter):
    """An adapter that also implements metadata-related methods."""

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        return MappingProxyType(item_class._fields.get(field_name) or {})


class BaseFakeItemAdapterTest(unittest.TestCase):
    item_class = FakeItemClass
    adapter_class = BaseFakeItemAdapter

    def setUp(self):
        ItemAdapter.ADAPTER_CLASSES.appendleft(self.adapter_class)

    def tearDown(self):
        ItemAdapter.ADAPTER_CLASSES.popleft()

    def test_repr(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        assert repr(adapter) == "<ItemAdapter for FakeItemClass()>"
        adapter["name"] = "asdf"
        adapter["value"] = 1234
        assert repr(adapter) == "<ItemAdapter for FakeItemClass(name='asdf', value=1234)>"

    def test_get_set_value(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        assert adapter.get("name") is None
        assert adapter.get("value") is None
        adapter["name"] = "asdf"
        adapter["value"] = 1234
        assert adapter.get("name") == "asdf"
        assert adapter.get("value") == 1234
        assert adapter["name"] == "asdf"
        assert adapter["value"] == 1234

    def test_get_set_value_init(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert adapter.get("name") == "asdf"
        assert adapter.get("value") == 1234
        assert adapter["name"] == "asdf"
        assert adapter["value"] == 1234

    def test_get_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with pytest.raises(KeyError):
            adapter["_undefined_"]

    def test_as_dict(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert dict(adapter) == {"name": "asdf", "value": 1234}

    def test_set_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with pytest.raises(KeyError):
            adapter["_undefined_"] = "some value"

    def test_delitem_len_iter(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert len(adapter) == 2
        assert sorted(iter(adapter)) == ["name", "value"]

        del adapter["name"]
        assert len(adapter) == 1
        assert sorted(iter(adapter)) == ["value"]

        del adapter["value"]
        assert len(adapter) == 0
        assert sorted(iter(adapter)) == []

        with pytest.raises(KeyError):
            del adapter["name"]
        with pytest.raises(KeyError):
            del adapter["value"]
        with pytest.raises(KeyError):
            del adapter["_undefined_"]

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values."""
        adapter = ItemAdapter(self.item_class())
        with pytest.raises(KeyError):
            adapter["name"]

    def test_get_field_meta(self):
        """Metadata is always empty for the default implementation."""
        adapter = ItemAdapter(self.item_class())
        assert adapter.get_field_meta("_undefined_") == MappingProxyType({})
        assert adapter.get_field_meta("name") == MappingProxyType({})
        assert adapter.get_field_meta("value") == MappingProxyType({})

    def test_get_field_meta_from_class(self):
        """Metadata is always empty for the default implementation."""
        assert ItemAdapter.get_field_meta_from_class(
            self.item_class, "_undefined_"
        ) == MappingProxyType({})
        assert ItemAdapter.get_field_meta_from_class(self.item_class, "name") == MappingProxyType(
            {}
        )
        assert ItemAdapter.get_field_meta_from_class(self.item_class, "value") == MappingProxyType(
            {}
        )

    def test_field_names(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert isinstance(adapter.field_names(), KeysView)
        assert sorted(adapter.field_names()) == ["name", "value"]


class MetadataFakeItemAdapterTest(BaseFakeItemAdapterTest):
    item_class = FakeItemClass
    adapter_class = MetadataFakeItemAdapter

    def test_get_field_meta(self):
        adapter = ItemAdapter(self.item_class())
        assert adapter.get_field_meta("_undefined_") == MappingProxyType({})
        assert adapter.get_field_meta("name") == MappingProxyType({"serializer": str})
        assert adapter.get_field_meta("value") == MappingProxyType({"serializer": int})

    def test_get_field_meta_from_class(self):
        assert ItemAdapter.get_field_meta_from_class(
            self.item_class, "_undefined_"
        ) == MappingProxyType({})
        assert ItemAdapter.get_field_meta_from_class(self.item_class, "name") == MappingProxyType(
            {"serializer": str}
        )
        assert ItemAdapter.get_field_meta_from_class(self.item_class, "value") == MappingProxyType(
            {"serializer": int}
        )


class FieldNamesFakeItemAdapterTest(BaseFakeItemAdapterTest):
    item_class = FakeItemClass
    adapter_class = FieldNamesFakeItemAdapter

    def test_field_names(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        assert isinstance(adapter.field_names(), KeysView)
        assert sorted(adapter.field_names()) == ["NAME", "VALUE"]
