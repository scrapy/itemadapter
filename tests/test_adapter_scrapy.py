import unittest
from types import MappingProxyType
from unittest import mock

import pytest

from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    ScrapyItem,
    ScrapySubclassedItem,
    clear_itemadapter_imports,
    make_mock_import,
)


class ScrapyItemTestCase(unittest.TestCase):
    def test_false(self):
        from itemadapter.adapter import ScrapyItemAdapter

        assert not ScrapyItemAdapter.is_item(int)
        assert not ScrapyItemAdapter.is_item(sum)
        assert not ScrapyItemAdapter.is_item(1234)
        assert not ScrapyItemAdapter.is_item(object())
        assert not ScrapyItemAdapter.is_item(DataClassItem())
        assert not ScrapyItemAdapter.is_item("a string")
        assert not ScrapyItemAdapter.is_item(b"some bytes")
        assert not ScrapyItemAdapter.is_item({"a": "dict"})
        assert not ScrapyItemAdapter.is_item(["a", "list"])
        assert not ScrapyItemAdapter.is_item(("a", "tuple"))
        assert not ScrapyItemAdapter.is_item({"a", "set"})
        assert not ScrapyItemAdapter.is_item(ScrapySubclassedItem)

        try:
            import attrs  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not ScrapyItemAdapter.is_item(AttrsItem())

        if PydanticModel is not None:
            assert not ScrapyItemAdapter.is_item(PydanticModel())

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @mock.patch("builtins.__import__", make_mock_import("scrapy"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter import utils
            from itemadapter.adapter import ScrapyItemAdapter

            assert not ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234))
            with pytest.raises(
                TypeError, match=r"tests.ScrapySubclassedItem'\> is not a valid item class"
            ):
                utils.get_field_meta_from_class(ScrapySubclassedItem, "name")

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @mock.patch("itemadapter.adapter._scrapy_item_classes", ())
    def test_module_not_available(self):
        from itemadapter.adapter import ScrapyItemAdapter

        assert not ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234))
        with pytest.raises(
            TypeError, match=r"tests.ScrapySubclassedItem'\> is not a valid item class"
        ):
            get_field_meta_from_class(ScrapySubclassedItem, "name")

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_true(self):
        from itemadapter.adapter import ScrapyItemAdapter

        assert ScrapyItemAdapter.is_item(ScrapyItem())
        assert ScrapyItemAdapter.is_item(ScrapySubclassedItem())
        assert ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234))
        # field metadata
        assert get_field_meta_from_class(ScrapySubclassedItem, "name") == MappingProxyType(
            {"serializer": str}
        )
        assert get_field_meta_from_class(ScrapySubclassedItem, "value") == MappingProxyType(
            {"serializer": int}
        )
