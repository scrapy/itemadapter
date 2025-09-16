from types import MappingProxyType
from unittest import TestCase

import pytest

from itemadapter.utils import get_field_meta_from_class
from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    PydanticV1Model,
    ScrapyItem,
    ScrapySubclassedItem,
)


class DataclassTestCase(TestCase):
    def test_false(self):
        from itemadapter.adapter import DataclassAdapter

        assert not DataclassAdapter.is_item(int)
        assert not DataclassAdapter.is_item(sum)
        assert not DataclassAdapter.is_item(1234)
        assert not DataclassAdapter.is_item(object())
        assert not DataclassAdapter.is_item("a string")
        assert not DataclassAdapter.is_item(b"some bytes")
        assert not DataclassAdapter.is_item({"a": "dict"})
        assert not DataclassAdapter.is_item(["a", "list"])
        assert not DataclassAdapter.is_item(("a", "tuple"))
        assert not DataclassAdapter.is_item({"a", "set"})
        assert not DataclassAdapter.is_item(DataClassItem)

        try:
            import attrs  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not DataclassAdapter.is_item(AttrsItem())

        if PydanticModel is not None:
            assert not DataclassAdapter.is_item(PydanticModel())
        if PydanticV1Model is not None:
            assert not DataclassAdapter.is_item(PydanticV1Model())

        try:
            import scrapy  # noqa: F401  # pylint: disable=unused-import
        except ImportError:
            pass
        else:
            assert not DataclassAdapter.is_item(ScrapyItem())
            assert not DataclassAdapter.is_item(ScrapySubclassedItem())

    def test_true(self):
        from itemadapter.adapter import DataclassAdapter

        assert DataclassAdapter.is_item(DataClassItem())
        assert DataclassAdapter.is_item(DataClassItem(name="asdf", value=1234))
        # field metadata
        assert get_field_meta_from_class(DataClassItem, "name") == MappingProxyType(
            {"serializer": str}
        )
        assert get_field_meta_from_class(DataClassItem, "value") == MappingProxyType(
            {"serializer": int}
        )
        with pytest.raises(KeyError, match="DataClassItem does not support field: non_existent"):
            get_field_meta_from_class(DataClassItem, "non_existent")
