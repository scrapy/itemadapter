import unittest
from importlib import import_module
from types import MappingProxyType
from typing import KeysView

from tests import (
    AttrsItem,
    AttrsItemWithoutInit,
    DataClassItem,
    DataClassWithoutInit,
    requires_attr,
    requires_dataclasses,
    requires_scrapy,
    ScrapySubclassedItem,
    ScrapySubclassedItemNested,
    TestCase,
)


class ItemAdapterReprTestCase(TestCase):
    def test_repr_dict(self):
        from itemadapter.adapter import ItemAdapter

        item = dict(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for dict(name='asdf', value=1234)>")

    @requires_scrapy
    def test_repr_scrapy_item(self):
        from itemadapter.adapter import ItemAdapter

        item = ScrapySubclassedItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter), "<ItemAdapter for ScrapySubclassedItem(name='asdf', value=1234)>"
        )

    @requires_dataclasses
    def test_repr_dataclass(self):
        from itemadapter.adapter import ItemAdapter

        item = DataClassItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for DataClassItem(name='asdf', value=1234)>",
        )

    @requires_dataclasses
    def test_repr_dataclass_init_false(self):
        from itemadapter.adapter import ItemAdapter

        item = DataClassWithoutInit()
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for DataClassWithoutInit()>")
        adapter["name"] = "set after init"
        self.assertEqual(
            repr(adapter), "<ItemAdapter for DataClassWithoutInit(name='set after init')>"
        )

    @requires_attr
    def test_repr_attrs(self):
        from itemadapter.adapter import ItemAdapter

        item = AttrsItem(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(
            repr(adapter),
            "<ItemAdapter for AttrsItem(name='asdf', value=1234)>",
        )

    @requires_attr
    def test_repr_attrs_init_false(self):
        from itemadapter.adapter import ItemAdapter

        item = AttrsItemWithoutInit()
        adapter = ItemAdapter(item)
        self.assertEqual(repr(adapter), "<ItemAdapter for AttrsItemWithoutInit()>")
        adapter["name"] = "set after init"
        self.assertEqual(
            repr(adapter), "<ItemAdapter for AttrsItemWithoutInit(name='set after init')>"
        )


class ItemAdapterInitError(TestCase):
    def test_non_item(self):
        from itemadapter.adapter import ItemAdapter

        with self.assertRaises(TypeError):
            ItemAdapter(ScrapySubclassedItem)
        with self.assertRaises(TypeError):
            ItemAdapter(dict)
        with self.assertRaises(TypeError):
            ItemAdapter(1234)


class BaseTestMixin:

    item_class = None
    item_class_nested_path = None

    def setUp(self):
        super().setUp()
        if self.item_class is None:
            raise unittest.SkipTest()

    @property
    def item_class_nested(self):
        module_path, class_name = self.item_class_nested_path.rsplit(".", maxsplit=1)
        module = import_module(module_path)
        return getattr(module, class_name)

    def test_get_set_value(self):
        from itemadapter.adapter import ItemAdapter

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

        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(adapter.get("name"), "asdf")
        self.assertEqual(adapter.get("value"), 1234)
        self.assertEqual(adapter["name"], "asdf")
        self.assertEqual(adapter["value"], 1234)

    def test_get_value_keyerror(self):
        from itemadapter.adapter import ItemAdapter

        item = self.item_class()
        adapter = ItemAdapter(item)
        with self.assertRaises(KeyError):
            adapter["undefined_field"]

    def test_as_dict(self):
        from itemadapter.adapter import ItemAdapter

        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertEqual(dict(name="asdf", value=1234), dict(adapter))

    def test_as_dict_nested(self):
        from itemadapter.adapter import ItemAdapter

        item = self.item_class_nested(
            nested=self.item_class(name="asdf", value=1234),
            adapter=ItemAdapter(dict(foo="bar", nested_list=[1, 2, 3, 4, 5])),
            dict_={"foo": "bar", "answer": 42, "nested_dict": {"a": "b"}},
            list_=[1, 2, 3],
            set_={1, 2, 3},
            tuple_=(1, 2, 3),
            int_=123,
        )
        adapter = ItemAdapter(item)
        self.assertEqual(
            adapter.asdict(),
            dict(
                nested=dict(name="asdf", value=1234),
                adapter=dict(foo="bar", nested_list=[1, 2, 3, 4, 5]),
                dict_={"foo": "bar", "answer": 42, "nested_dict": {"a": "b"}},
                list_=[1, 2, 3],
                set_={1, 2, 3},
                tuple_=(1, 2, 3),
                int_=123,
            ),
        )

    def test_field_names(self):
        from itemadapter.adapter import ItemAdapter

        item = self.item_class(name="asdf", value=1234)
        adapter = ItemAdapter(item)
        self.assertIsInstance(adapter.field_names(), KeysView)
        self.assertEqual(sorted(adapter.field_names()), ["name", "value"])


class NonDictTestMixin(BaseTestMixin):
    def test_set_value_keyerror(self):
        from itemadapter.adapter import ItemAdapter

        item = self.item_class()
        adapter = ItemAdapter(item)
        with self.assertRaises(KeyError):
            adapter["undefined_field"] = "some value"

    def test_metadata_common(self):
        from itemadapter.adapter import ItemAdapter

        adapter = ItemAdapter(self.item_class())
        self.assertIsInstance(adapter.get_field_meta("name"), MappingProxyType)
        self.assertIsInstance(adapter.get_field_meta("value"), MappingProxyType)
        with self.assertRaises(KeyError):
            adapter.get_field_meta("undefined_field")

    def test_get_field_meta_defined_fields(self):
        from itemadapter.adapter import ItemAdapter

        adapter = ItemAdapter(self.item_class())
        self.assertEqual(adapter.get_field_meta("name"), MappingProxyType({"serializer": str}))
        self.assertEqual(adapter.get_field_meta("value"), MappingProxyType({"serializer": int}))

    def test_delitem_len_iter(self):
        from itemadapter.adapter import ItemAdapter

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


class DictTestCase(TestCase, BaseTestMixin):

    item_class = dict
    item_class_nested = dict

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values"""
        from itemadapter.adapter import ItemAdapter

        adapter = ItemAdapter(self.item_class())
        with self.assertRaises(KeyError):
            adapter["name"]

    def test_empty_metadata(self):
        from itemadapter.adapter import ItemAdapter

        adapter = ItemAdapter(self.item_class(name="foo", value=5))
        for field_name in ("name", "value", "undefined_field"):
            self.assertEqual(adapter.get_field_meta(field_name), MappingProxyType({}))

    def test_field_names_updated(self):
        from itemadapter.adapter import ItemAdapter

        item = self.item_class(name="asdf")
        field_names = ItemAdapter(item).field_names()
        self.assertEqual(sorted(field_names), ["name"])
        item["value"] = 1234
        self.assertEqual(sorted(field_names), ["name", "value"])


class ScrapySubclassedItemTestCase(NonDictTestMixin, TestCase):

    item_class = ScrapySubclassedItem
    item_class_nested = ScrapySubclassedItemNested

    def test_get_value_keyerror_item_dict(self):
        """Instantiate without default values"""
        from itemadapter.adapter import ItemAdapter

        adapter = ItemAdapter(self.item_class())
        with self.assertRaises(KeyError):
            adapter["name"]


class DataClassItemTestCase(NonDictTestMixin, TestCase):

    item_class = DataClassItem
    item_class_nested_path = "tests.dataclasses_utils.DataClassItemNested"


class AttrsItemTestCase(NonDictTestMixin, TestCase):

    item_class = AttrsItem
    item_class_nested_path = "tests.attr_utils.AttrsItemNested"
