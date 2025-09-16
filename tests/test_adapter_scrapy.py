import unittest
from types import MappingProxyType
from unittest import mock

import pytest

from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    PydanticV1Model,
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
        if PydanticV1Model is not None:
            assert not ScrapyItemAdapter.is_item(PydanticV1Model())

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    @mock.patch("builtins.__import__", make_mock_import("scrapy"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter.adapter import ScrapyItemAdapter

            assert not ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234))
            with pytest.raises(
                TypeError, match=r"tests.ScrapySubclassedItem'\> is not a valid item class"
            ):
                get_field_meta_from_class(ScrapySubclassedItem, "name")

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


try:
    import scrapy
except ImportError:
    scrapy = None


class ScrapyDeprecatedBaseItemTestCase(unittest.TestCase):
    """Tests for deprecated classes. These will go away once the upstream classes are removed."""

    @unittest.skipIf(
        scrapy is None or not hasattr(scrapy.item, "_BaseItem"),
        "scrapy.item._BaseItem not available",
    )
    def test_deprecated_underscore_baseitem(self):
        from itemadapter.adapter import ScrapyItemAdapter

        class SubClassed_BaseItem(scrapy.item._BaseItem):
            pass

        assert ScrapyItemAdapter.is_item(scrapy.item._BaseItem())
        assert ScrapyItemAdapter.is_item(SubClassed_BaseItem())

    @unittest.skipIf(
        scrapy is None or not hasattr(scrapy.item, "BaseItem"),
        "scrapy.item.BaseItem not available",
    )
    def test_deprecated_baseitem(self):
        from itemadapter.adapter import ScrapyItemAdapter

        class SubClassedBaseItem(scrapy.item.BaseItem):
            pass

        assert ScrapyItemAdapter.is_item(scrapy.item.BaseItem())
        assert ScrapyItemAdapter.is_item(SubClassedBaseItem())

    @unittest.skipIf(scrapy is None, "scrapy module is not available")
    def test_removed_baseitem(self):
        """Mock the scrapy.item module so it does not contain the deprecated _BaseItem class."""
        from itemadapter.adapter import ScrapyItemAdapter

        class MockItemModule:
            Item = ScrapyItem

        with mock.patch("scrapy.item", MockItemModule):
            assert not ScrapyItemAdapter.is_item({})
            assert get_field_meta_from_class(ScrapySubclassedItem, "name") == MappingProxyType(
                {"serializer": str}
            )
            assert get_field_meta_from_class(ScrapySubclassedItem, "value") == MappingProxyType(
                {"serializer": int}
            )
