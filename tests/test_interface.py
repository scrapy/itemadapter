import unittest
from types import MappingProxyType
from typing import Any, Iterator, KeysView
from unittest import mock

from itemadapter.adapter import AdapterInterface, ItemAdapter


class AdapterInterfaceTest(unittest.TestCase):
    @mock.patch.multiple(AdapterInterface, __abstractmethods__=set())
    def test_interface_class_methods(self):
        with self.assertRaises(NotImplementedError):
            AdapterInterface.is_item(object())

    @mock.patch.multiple(AdapterInterface, __abstractmethods__=set())
    def test_interface_instance_methods(self):
        obj = AdapterInterface(object())
        with self.assertRaises(NotImplementedError):
            obj.get_field_meta("")
        with self.assertRaises(NotImplementedError):
            obj.field_names()
        with self.assertRaises(NotImplementedError):
            obj.asdict()


class FakeItemClass:
    _fields = {
        "name": {"serializer": str},
        "value": {"serializer": int},
    }

    def __init__(self, **kwargs) -> None:
        self._values = {**kwargs}


class FakeItemAdapter(AdapterInterface):
    @classmethod
    def is_item(cls, item: Any) -> bool:
        return isinstance(item, FakeItemClass)

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        if field_name in self.item._fields:
            return MappingProxyType(self.item._fields[field_name])
        else:
            return MappingProxyType({})

    def field_names(self) -> KeysView:
        return self.item._fields.keys()

    def asdict(self) -> dict:
        return self.item._values.copy()

    def __getitem__(self, field_name: str) -> Any:
        if field_name in self.item._fields:
            return self.item._values[field_name]
        else:
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


class FakeItemAdapterTest(unittest.TestCase):

    item_class = FakeItemClass

    def setUp(self):
        ItemAdapter.ADAPTER_CLASSES.appendleft(FakeItemAdapter)

    def tearDown(self):
        ItemAdapter.ADAPTER_CLASSES.popleft()

    def test_repr(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for FakeItemClass()>")
        adapter["name"] = "asdf"
        adapter["value"] = 1234
        self.assertEqual(repr(adapter), "<ItemAdapter for FakeItemClass(name='asdf', value=1234)>")

    def test_get_set_value(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        self.assertEqual(adapter.get("name"), None)
        self.assertEqual(adapter.get("value"), None)
        adapter["name"] = "asdf"
        adapter["value"] = 1234
        self.assertEqual(adapter.get("name"), "asdf")
        self.assertEqual(adapter.get("value"), 1234)
        self.assertEqual(adapter["name"], "asdf")
        self.assertEqual(adapter["value"], 1234)

    def test_get_set_value_init(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(adapter.get("name"), "asdf")
        self.assertEqual(adapter.get("value"), 1234)
        self.assertEqual(adapter["name"], "asdf")
        self.assertEqual(adapter["value"], 1234)

    def test_get_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with self.assertRaises(KeyError):
            adapter["undefined_field"]

    def test_as_dict(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(dict(name="asdf", value=1234), dict(adapter))

    def test_field_names(self):
        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertIsInstance(adapter.field_names(), KeysView)
        self.assertEqual(sorted(adapter.field_names()), ["name", "value"])

    def test_set_value_keyerror(self):
        item = self.item_class()
        adapter = ItemAdapter(item)
        with self.assertRaises(KeyError):
            adapter["undefined_field"] = "some value"

    def test_get_field_meta_defined_fields(self):
        adapter = ItemAdapter(self.item_class())
        self.assertEqual(adapter.get_field_meta("name"), MappingProxyType({"serializer": str}))
        self.assertEqual(adapter.get_field_meta("value"), MappingProxyType({"serializer": int}))

    def test_delitem_len_iter(self):
        item = self.item_class(name="asdf", value=1234)
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

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values"""
        adapter = ItemAdapter(self.item_class())
        with self.assertRaises(KeyError):
            adapter["name"]
