from collections.abc import KeysView, MutableMapping
from types import MappingProxyType
from typing import Any, Iterator

from .utils import (
    get_field_meta_from_class,
    is_attrs_instance,
    is_dataclass_instance,
    is_item,
    is_scrapy_item,
)


class ItemAdapter(MutableMapping):
    """
    Wrapper class to interact with data container objects. It provides a common interface
    to extract and set data without having to take the object's type into account.
    """

    def __init__(self, item: Any) -> None:
        if not is_item(item):
            raise TypeError("Expected a valid item, got %r instead: %s" % (type(item), item))
        self.item = item
        # store a reference to the fields to avoid O(n) lookups and O(n^2) traversals
        self._fields_dict = {}  # type: dict
        if is_dataclass_instance(self.item):
            import dataclasses

            self._fields_dict = {field.name: field for field in dataclasses.fields(self.item)}
        elif is_attrs_instance(self.item):
            import attr

            self._fields_dict = attr.fields_dict(self.item.__class__)

    def __repr__(self) -> str:
        values = ", ".join(["%s=%r" % (key, value) for key, value in self.items()])
        return "<ItemAdapter for %s(%s)>" % (self.item.__class__.__name__, values)

    def __getitem__(self, field_name: str) -> Any:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            if field_name in self._fields_dict:
                return getattr(self.item, field_name)
            raise KeyError(field_name)
        return self.item[field_name]

    def __setitem__(self, field_name: str, value: Any) -> None:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            if field_name in self._fields_dict:
                setattr(self.item, field_name, value)
            else:
                raise KeyError(
                    "%s does not support field: %s" % (self.item.__class__.__name__, field_name)
                )
        else:
            self.item[field_name] = value

    def __delitem__(self, field_name: str) -> None:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            if field_name in self._fields_dict:
                try:
                    delattr(self.item, field_name)
                except AttributeError:
                    raise KeyError(field_name)
            else:
                raise KeyError(
                    "%s does not support field: %s" % (self.item.__class__.__name__, field_name)
                )
        else:
            del self.item[field_name]

    def __iter__(self) -> Iterator:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            return iter(attr for attr in self._fields_dict if hasattr(self.item, attr))
        return iter(self.item)

    def __len__(self) -> int:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            return len(list(iter(self)))
        return len(self.item)

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        """
        Return a read-only mapping with metadata for the given field name. If there is no metadata
        for the field, or the wrapped item does not support field metadata, an empty object is
        returned.

        Field metadata is taken from different sources, depending on the item type:
        * scrapy.item.Item: corresponding scrapy.item.Field object
        * dataclass items: "metadata" attribute for the corresponding field
        * attrs items: "metadata" attribute for the corresponding field

        The returned value is an instance of types.MappingProxyType, i.e. a dynamic read-only view
        of the original mapping, which gets automatically updated if the original mapping changes.
        """
        return get_field_meta_from_class(self.item.__class__, field_name)

    def field_names(self) -> KeysView:
        """
        Return read-only key view with the names of all the defined fields for the item
        """
        if is_scrapy_item(self.item):
            return KeysView(self.item.fields)
        elif is_dataclass_instance(self.item):
            return KeysView(self._fields_dict)
        elif is_attrs_instance(self.item):
            return KeysView(self._fields_dict)
        else:
            return KeysView(self.item)

    def asdict(self) -> dict:
        """
        Return a dict object with the contents of the adapter. This works slightly different than
        calling `dict(adapter)`: it's applied recursively to nested items (if there are any).
        """
        return {key: _asdict(value) for key, value in self.items()}


def _asdict(obj: Any) -> Any:
    """
    Helper for ItemAdapter.asdict
    """
    if isinstance(obj, dict):
        return {key: _asdict(value) for key, value in obj.items()}
    elif isinstance(obj, (list, set, tuple)):
        return obj.__class__(_asdict(x) for x in obj)
    elif isinstance(obj, ItemAdapter):
        return obj.asdict()
    elif is_item(obj):
        return ItemAdapter(obj).asdict()
    else:
        return obj
