import unittest
import warnings
from types import MappingProxyType
from unittest import mock

from itemadapter.utils import get_field_meta_from_class

from tests import (
    AttrsItem,
    DataClassItem,
    PydanticModel,
    PydanticSpecialCasesModel,
    ScrapyItem,
    ScrapySubclassedItem,
    make_mock_import,
    clear_itemadapter_imports,
)


class PydanticTestCase(unittest.TestCase):
    def test_false(self):
        from itemadapter.adapter import PydanticAdapter

        self.assertFalse(PydanticAdapter.is_item(int))
        self.assertFalse(PydanticAdapter.is_item(sum))
        self.assertFalse(PydanticAdapter.is_item(1234))
        self.assertFalse(PydanticAdapter.is_item(object()))
        self.assertFalse(PydanticAdapter.is_item(ScrapyItem()))
        self.assertFalse(PydanticAdapter.is_item(AttrsItem()))
        self.assertFalse(PydanticAdapter.is_item(DataClassItem()))
        self.assertFalse(PydanticAdapter.is_item(ScrapySubclassedItem()))
        self.assertFalse(PydanticAdapter.is_item("a string"))
        self.assertFalse(PydanticAdapter.is_item(b"some bytes"))
        self.assertFalse(PydanticAdapter.is_item({"a": "dict"}))
        self.assertFalse(PydanticAdapter.is_item(["a", "list"]))
        self.assertFalse(PydanticAdapter.is_item(("a", "tuple")))
        self.assertFalse(PydanticAdapter.is_item({"a", "set"}))
        self.assertFalse(PydanticAdapter.is_item(PydanticModel))

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @mock.patch("builtins.__import__", make_mock_import("pydantic"))
    def test_module_import_error(self):
        with clear_itemadapter_imports():
            from itemadapter.adapter import PydanticAdapter

            self.assertFalse(PydanticAdapter.is_item(PydanticModel(name="asdf", value=1234)))
            with self.assertRaises(TypeError, msg="PydanticModel is not a valid item class"):
                get_field_meta_from_class(PydanticModel, "name")

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    @mock.patch("itemadapter.utils.pydantic", None)
    def test_module_not_available(self):
        from itemadapter.adapter import PydanticAdapter

        self.assertFalse(PydanticAdapter.is_item(PydanticModel(name="asdf", value=1234)))
        with self.assertRaises(TypeError, msg="PydanticModel is not a valid item class"):
            get_field_meta_from_class(PydanticModel, "name")

    @unittest.skipIf(not PydanticModel, "pydantic module is not available")
    def test_true(self):
        from itemadapter.adapter import PydanticAdapter

        self.assertTrue(PydanticAdapter.is_item(PydanticModel()))
        self.assertTrue(PydanticAdapter.is_item(PydanticModel(name="asdf", value=1234)))
        # field metadata
        self.assertEqual(
            get_field_meta_from_class(PydanticModel, "name"),
            MappingProxyType({"serializer": str}),
        )
        self.assertEqual(
            get_field_meta_from_class(PydanticModel, "value"),
            MappingProxyType({"serializer": int}),
        )
        self.assertEqual(
            get_field_meta_from_class(PydanticSpecialCasesModel, "special_cases"),
            MappingProxyType({"alias": "special_cases", "frozen": False}),
        )
        with self.assertRaises(KeyError, msg="PydanticModel does not support field: non_existent"):
            get_field_meta_from_class(PydanticModel, "non_existent")

    def test_deprecated_is_instance(self):
        from itemadapter.utils import is_pydantic_instance

        with warnings.catch_warnings(record=True) as caught:
            is_pydantic_instance(1)
            self.assertEqual(len(caught), 1)
            self.assertTrue(issubclass(caught[0].category, DeprecationWarning))
            self.assertEqual(
                "itemadapter.utils.is_pydantic_instance is deprecated"
                " and it will be removed in a future version",
                str(caught[0].message),
            )
