import unittest
from collections import deque

from itemadapter.adapter import ItemAdapter, DictAdapter

from tests import DataClassItem


class DictOnlyItemAdapter(ItemAdapter):
    ADAPTER_CLASSES = deque([DictAdapter])


class ItemAdapterTestCase(unittest.TestCase):
    def test_repr(self):
        adapter = ItemAdapter(dict(foo="bar"))
        self.assertEqual(repr(adapter), "<ItemAdapter for dict(foo='bar')>")

    def test_repr_subclass(self):
        adapter = DictOnlyItemAdapter(dict(foo="bar"))
        self.assertEqual(repr(adapter), "<DictOnlyItemAdapter for dict(foo='bar')>")

    def test_as_dict_subclass(self):
        """'asdict' method of ItemAdapter subclasses handles items even
        if they're not handled by the subclass itself.
        """
        item = dict(
            foo="bar",
            dataclass_item=DataClassItem(name="asdf", value="qwerty"),
            itemadapter=ItemAdapter({"a": 1, "b": 2}),
        )
        self.assertEqual(
            DictOnlyItemAdapter(item).asdict(),
            dict(
                foo="bar",
                dataclass_item=dict(name="asdf", value="qwerty"),
                itemadapter={"a": 1, "b": 2},
            ),
        )
