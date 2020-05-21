from collections.abc import MutableMapping
from types import MappingProxyType
from typing import Any, Iterator, List

from .utils import is_item, is_attrs_instance, is_dataclass_instance, is_scrapy_item


class ItemAdapter(MutableMapping):
    """
    Wrapper class to interact with data container objects. It provides a common interface
    to extract and set data without having to take the object's type into account.
    """

    def __init__(self, item: Any) -> None:
        if not is_item(item):
            raise TypeError("Expected a valid item, got %r instead: %s" % (type(item), item))
        self.item = item

    def __repr__(self) -> str:
        return "ItemAdapter for type %s: %r" % (self.item.__class__.__name__, self.item)

    def __getitem__(self, field_name: str) -> Any:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            if field_name in iter(self):
                return getattr(self.item, field_name)
            raise KeyError(field_name)
        return self.item[field_name]

    def __setitem__(self, field_name: str, value: Any) -> None:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            if field_name in iter(self):
                setattr(self.item, field_name, value)
            else:
                raise KeyError(
                    "%s does not support field: %s" % (self.item.__class__.__name__, field_name)
                )
        else:
            self.item[field_name] = value

    def __delitem__(self, field_name: str) -> None:
        if is_dataclass_instance(self.item) or is_attrs_instance(self.item):
            if field_name in self.field_names():
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
            return iter(attr for attr in dir(self.item) if attr in self.field_names())
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
        if is_scrapy_item(self.item):
            return MappingProxyType(self.item.fields[field_name])
        elif is_dataclass_instance(self.item):
            from dataclasses import fields

            for field in fields(self.item):
                if field.name == field_name:
                    return field.metadata  # type: ignore
            raise KeyError(
                "%s does not support field: %s" % (self.item.__class__.__name__, field_name)
            )
        elif is_attrs_instance(self.item):
            from attr import fields_dict

            try:
                return fields_dict(self.item.__class__)[field_name].metadata  # type: ignore
            except KeyError:
                raise KeyError(
                    "%s does not support field: %s" % (self.item.__class__.__name__, field_name)
                )
        else:
            return MappingProxyType({})

    def field_names(self) -> List[str]:
        """
        Return a list with the names of all the defined fields for the item
        """
        if is_scrapy_item(self.item):
            return list(self.item.fields.keys())
        elif is_dataclass_instance(self.item):
            import dataclasses

            return [field.name for field in dataclasses.fields(self.item)]
        elif is_attrs_instance(self.item):
            import attr

            return [field.name for field in attr.fields(self.item.__class__)]
        else:
            return list(self.item.keys())
