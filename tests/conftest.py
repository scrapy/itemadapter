import pytest

from itemadapter._json_schema import get_attr_docstrings
from itemadapter.adapter import _find_adapter_class, _has_item_overrides


@pytest.fixture(autouse=True)
def _clear_adapter_class_cache():
    """Keep tests that change which item types are supported, e.g. by patching
    an optional import out, from seeing results cached by earlier tests."""
    _find_adapter_class.cache_clear()
    _has_item_overrides.cache_clear()


@pytest.fixture(autouse=True)
def _clear_attr_docstring_cache():
    """Keep tests that mock reading class sources from seeing attribute
    docstrings cached by earlier tests, and the other way around."""
    get_attr_docstrings.cache_clear()
