from types import MappingProxyType

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
    requires_scrapy,
)


class TestScrapyItem:
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

    @requires_scrapy
    def test_module_import_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with monkeypatch.context() as m, clear_itemadapter_imports():
            m.setattr("builtins.__import__", make_mock_import("scrapy"))
            from itemadapter import utils
            from itemadapter.adapter import ScrapyItemAdapter

            assert not ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234))
            with pytest.raises(
                TypeError, match=r"tests.ScrapySubclassedItem'\> is not a valid item class"
            ):
                utils.get_field_meta_from_class(ScrapySubclassedItem, "name")

    @requires_scrapy
    def test_module_not_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from itemadapter.adapter import ScrapyItemAdapter

        monkeypatch.setattr("itemadapter.adapter._scrapy_item_classes", ())
        assert not ScrapyItemAdapter.is_item(ScrapySubclassedItem(name="asdf", value=1234))
        with pytest.raises(
            TypeError, match=r"tests.ScrapySubclassedItem'\> is not a valid item class"
        ):
            get_field_meta_from_class(ScrapySubclassedItem, "name")

    @requires_scrapy
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
