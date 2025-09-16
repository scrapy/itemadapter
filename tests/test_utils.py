import unittest
from types import MappingProxyType

import pytest

from itemadapter import ItemAdapter
from itemadapter.utils import get_field_meta_from_class, is_item
from tests import AttrsItem, DataClassItem, PydanticV1Model, ScrapyItem, ScrapySubclassedItem


class FieldMetaFromClassTestCase(unittest.TestCase):
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


class ItemLikeTestCase(unittest.TestCase):
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
        assert not is_item(PydanticV1Model)
        assert not ItemAdapter.is_item_class(list)
        assert not ItemAdapter.is_item_class(int)
        assert not ItemAdapter.is_item_class(tuple)

    def test_true_dict(self):
        assert is_item({"a": "dict"})
        assert ItemAdapter.is_item_class(dict)

    @unittest.skipIf(not ScrapySubclassedItem, "scrapy module is not available")
    def test_true_scrapy(self):
        assert is_item(ScrapyItem())
        assert is_item(ScrapySubclassedItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(ScrapyItem)
        assert ItemAdapter.is_item_class(ScrapySubclassedItem)

    @unittest.skipIf(not DataClassItem, "dataclasses module is not available")
    def test_true_dataclass(self):
        assert is_item(DataClassItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(DataClassItem)

    @unittest.skipIf(not AttrsItem, "attrs module is not available")
    def test_true_attrs(self):
        assert is_item(AttrsItem(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(AttrsItem)

    @unittest.skipIf(not PydanticV1Model, "pydantic module is not available")
    def test_true_pydantic(self):
        assert is_item(PydanticV1Model(name="asdf", value=1234))
        assert ItemAdapter.is_item_class(PydanticV1Model)
