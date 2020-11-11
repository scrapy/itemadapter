from types import MappingProxyType
from typing import Any


def _get_scrapy_item_classes() -> tuple:
    try:
        import scrapy
    except ImportError:
        return ()
    else:
        try:
            _base_item_cls = getattr(scrapy.item, "_BaseItem", scrapy.item.BaseItem)  # deprecated
            return (scrapy.item.Item, _base_item_cls)
        except AttributeError:
            return (scrapy.item.Item,)


def _is_dataclass(obj: Any) -> bool:
    try:
        import dataclasses
    except ImportError:
        return False
    return dataclasses.is_dataclass(obj)


def _is_attrs_class(obj: Any) -> bool:
    try:
        import attr
    except ImportError:
        return False
    return attr.has(obj)


def is_dataclass_instance(obj: Any) -> bool:
    """
    Return True if the given object is a dataclass object, False otherwise.

    In py36, this function returns False if the "dataclasses" backport is not available.

    Taken from https://docs.python.org/3/library/dataclasses.html#dataclasses.is_dataclass.
    """
    return _is_dataclass(obj) and not isinstance(obj, type)


def is_attrs_instance(obj: Any) -> bool:
    """
    Return True if the given object is a attrs-based object, False otherwise.
    """
    return _is_attrs_class(obj) and not isinstance(obj, type)


def is_scrapy_item(obj: Any) -> bool:
    """
    Return True if the given object is a Scrapy item, False otherwise.
    """
    try:
        import scrapy
    except ImportError:
        return False
    if isinstance(obj, scrapy.item.Item):
        return True
    try:
        # handle deprecated BaseItem
        BaseItem = getattr(scrapy.item, "_BaseItem", scrapy.item.BaseItem)
        return isinstance(obj, BaseItem)
    except AttributeError:
        return False


def is_item(obj: Any) -> bool:
    """
    Return True if the given object belongs to one of the supported types, False otherwise.

    Alias for ItemAdapter.is_item
    """
    from itemadapter.adapter import ItemAdapter

    return ItemAdapter.is_item(obj)


def get_field_meta_from_class(item_class: type, field_name: str) -> MappingProxyType:
    """
    Return a read-only mapping with metadata for the given field name, within the given item class.
    If there is no metadata for the field, or the item class does not support field metadata,
    an empty object is returned.

    Field metadata is taken from different sources, depending on the item type:
    * scrapy.item.Item: corresponding scrapy.item.Field object
    * dataclass items: "metadata" attribute for the corresponding field
    * attrs items: "metadata" attribute for the corresponding field

    The returned value is an instance of types.MappingProxyType, i.e. a dynamic read-only view
    of the original mapping, which gets automatically updated if the original mapping changes.
    """
    if issubclass(item_class, _get_scrapy_item_classes()):
        return MappingProxyType(item_class.fields[field_name])  # type: ignore
    elif _is_dataclass(item_class):
        from dataclasses import fields

        for field in fields(item_class):
            if field.name == field_name:
                return field.metadata  # type: ignore
        raise KeyError("%s does not support field: %s" % (item_class.__name__, field_name))
    elif _is_attrs_class(item_class):
        from attr import fields_dict

        try:
            return fields_dict(item_class)[field_name].metadata  # type: ignore
        except KeyError:
            raise KeyError("%s does not support field: %s" % (item_class.__name__, field_name))
    elif issubclass(item_class, dict):
        return MappingProxyType({})
    else:
        raise TypeError("%s is not a valid item class" % (item_class,))
