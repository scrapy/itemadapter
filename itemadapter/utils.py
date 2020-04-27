from collections.abc import MutableMapping
from typing import Any


def is_dataclass_instance(obj: Any) -> bool:
    """
    Return True if the given object is a dataclass object, False otherwise.

    This function always returns False in py35. In py36, it returns False
    if the "dataclasses" backport is not available.

    Taken from https://docs.python.org/3/library/dataclasses.html#dataclasses.is_dataclass.
    """
    try:
        import dataclasses
    except ImportError:
        return False
    else:
        return dataclasses.is_dataclass(obj) and not isinstance(obj, type)


def is_attrs_instance(obj: Any) -> bool:
    """
    Return True if the given object is a attrs-based object, False otherwise.
    """
    try:
        import attr
    except ImportError:
        return False
    else:
        return attr.has(obj) and not isinstance(obj, type)


def is_item(obj: Any) -> bool:
    """
    Return True if the given object belongs to one of the supported types, False otherwise.
    """
    return isinstance(obj, MutableMapping) or is_dataclass_instance(obj) or is_attrs_instance(obj)
