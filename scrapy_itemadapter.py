from collections.abc import MutableMapping
from typing import Any, Iterator, List, Optional


def _is_dataclass_instance(obj: Any) -> bool:
    """
    Return True if *obj* is a dataclass object, False otherwise.

    This function will always return False in py35 (in any case, the syntax for field definition
    raises SyntaxError) and in py36 if the "dataclasses" backport module is not available.

    Taken from https://docs.python.org/3/library/dataclasses.html#dataclasses.is_dataclass.
    """
    try:
        from dataclasses import is_dataclass
    except ImportError:
        return False
    else:
        return is_dataclass(obj) and not isinstance(obj, type)


class ItemAdapter(MutableMapping):
    """
    Wrapper class to interact with items. It provides a common interface for components
    such as middlewares and pipelines to extract and set data without having to take
    the item's implementation (scrapy.Item, dict, dataclass) into account.
    """

    def __init__(self, item: Any) -> None:
        if not isinstance(item, MutableMapping) and not _is_dataclass_instance(item):
            raise TypeError("Expected a valid item, got %r instead: %s" % (type(item), item))
        self.item = item

    def __repr__(self) -> str:
        return "ItemAdapter for type %s: %r" % (self.item.__class__.__name__, self.item)

    def __getitem__(self, field_name: str) -> Any:
        if _is_dataclass_instance(self.item):
            if field_name in iter(self):
                return getattr(self.item, field_name)
            raise KeyError(field_name)
        return self.item[field_name]

    def __setitem__(self, field_name: str, value: Any) -> None:
        if _is_dataclass_instance(self.item):
            if field_name in iter(self):
                setattr(self.item, field_name, value)
            else:
                raise KeyError(
                    "%s does not support field: %s" % (self.item.__class__.__name__, field_name)
                )
        else:
            self.item[field_name] = value

    def __delitem__(self, field_name: str) -> None:
        if _is_dataclass_instance(self.item):
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
        if _is_dataclass_instance(self.item):
            return iter(attr for attr in dir(self.item) if attr in self.field_names())
        return iter(self.item)

    def __len__(self) -> int:
        if _is_dataclass_instance(self.item):
            return len(list(iter(self)))
        return len(self.item)

    def get_field(self, field_name: str) -> Optional[Any]:
        """
        Return the appropriate class:`scrapy.item.Field` object if the wrapped item has a Mapping
        attribute called "fields" and the requested field name can be found in it, None otherwise.
        """
        try:
            return self.item.fields.get(field_name)
        except AttributeError:
            return None

    def field_names(self) -> List[str]:
        """
        Return a list with the names of all the defined fields for the item
        """
        if _is_dataclass_instance(self.item):
            from dataclasses import fields

            return [field.name for field in fields(self.item)]
        elif isinstance(self.item, dict):
            return list(self.item.keys())
        else:
            try:
                return list(self.item.fields.keys())
            except AttributeError:
                return []
