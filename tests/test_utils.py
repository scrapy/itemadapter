from types import MappingProxyType

import pytest

from itemadapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class, is_item
from tests import (
    AttrsClassicItem,
    AttrsItem,
    DataClassItem,
    PydanticModel,
    ScrapyItem,
    ScrapySubclassedItem,
    requires_attrs,
    requires_pydantic,
    requires_scrapy,
)


class TestFieldMetaFromClass:
    def test_invalid_item_class(self):
        with pytest.raises(TypeError, match=r"issubclass\(\) arg 1 must be a class"):
            get_field_meta_from_class(1, "field")
        with pytest.raises(TypeError, match=r"'list'\> is not a valid item class"):
            get_field_meta_from_class(list, "field")

    def test_empty_meta_for_dict(self):
        class DictSubclass(dict):
            pass

        assert get_field_meta_from_class(DictSubclass, "name") == MappingProxyType({})
        assert get_field_meta_from_class(dict, "name") == MappingProxyType({})


class TestItemLike:
    def test_false(self):
        assert not is_item(int)
        assert not is_item(sum)
        assert not is_item(1234)
        assert not is_item(object())
        assert not is_item("a string")
        assert not is_item(b"some bytes")
        assert not is_item(["a", "list"])
        assert not is_item(("a", "tuple"))
        assert not is_item({"a", "set"})
        assert not is_item(dict)
        assert not is_item(ScrapyItem)
        assert not is_item(DataClassItem)
        assert not is_item(ScrapySubclassedItem)
        assert not is_item(AttrsItem)
        assert not is_item(PydanticModel)
        assert not ItemAdapter.is_item_class(list)
        assert not ItemAdapter.is_item_class(int)
        assert not ItemAdapter.is_item_class(tuple)

    def test_true_dict(self):
        assert is_item({"a": "dict"})
        assert ItemAdapter.is_item_class(dict)

    @requires_scrapy
    def test_true_scrapy(self):
        assert is_item(ScrapyItem())
        assert is_item(ScrapySubclassedItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(ScrapyItem)
        assert ItemAdapter.is_item_class(ScrapySubclassedItem)

    def test_true_dataclass(self):
        assert is_item(DataClassItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(DataClassItem)

    @requires_attrs
    def test_true_attrs(self):
        assert is_item(AttrsItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(AttrsItem)
        assert is_item(AttrsClassicItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(AttrsClassicItem)

    @requires_pydantic
    def test_true_pydantic(self):
        assert is_item(PydanticModel(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(PydanticModel)
