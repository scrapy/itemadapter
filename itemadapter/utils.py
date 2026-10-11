from __future__ import annotations

from typing import TYPE_CHECKING, Any

from itemadapter.adapter import ItemAdapter

if TYPE_CHECKING:
    from types import MappingProxyType

__all__ = ["get_field_meta_from_class", "is_item"]


def is_item(obj: object) -> bool:
    """Return True if the given object belongs to one of the supported types, False otherwise.

    Alias for ItemAdapter.is_item
    """
    return ItemAdapter.is_item(obj)


def get_field_meta_from_class(item_class: type, field_name: str) -> MappingProxyType[str, Any]:
    """Return a read-only mapping with metadata for the given field name, within the given
    item class. If there is no metadata for the field, or the item class does not support
    field metadata, an empty object is returned.

    Field metadata is taken from different sources, depending on the item type:
    * scrapy.item.Item: corresponding scrapy.item.Field object
    * dataclass items: "metadata" attribute for the corresponding field
    * attrs items: "metadata" attribute for the corresponding field
    * pydantic models: corresponding pydantic.field.FieldInfo/ModelField object

    The returned value is an instance of types.MappingProxyType, i.e. a dynamic read-only view
    of the original mapping, which gets automatically updated if the original mapping changes.
    """
    return ItemAdapter.get_field_meta_from_class(item_class, field_name)
