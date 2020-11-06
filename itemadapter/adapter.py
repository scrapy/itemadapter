from abc import abstractmethod, ABCMeta
from collections import deque
from collections.abc import KeysView, MutableMapping
from types import MappingProxyType
from typing import Any, Iterator

from itemadapter.utils import (
    is_attrs_instance,
    is_dataclass_instance,
    is_item,
    is_scrapy_item,
)


__all__ = [
    "AdapterInterface",
    "AttrsAdapter",
    "DataclassAdapter",
    "DictAdapter",
    "ItemAdapter",
    "ScrapyItemAdapter",
]


class AdapterInterface(MutableMapping, metaclass=ABCMeta):
    """
    Abstract Base Class for adapters.

    An adapter that handles a specific type of item should inherit from this
    class and implement the abstract methods defined here, plus the
    abtract methods inherited from the MutableMapping base class.
    """

    def __init__(self, item: Any) -> None:
        self.item = item

    @classmethod
    @abstractmethod
    def is_item(cls, item: Any) -> bool:
        """
        Return True if the adapter can handle the given item, False otherwise
        """
        raise NotImplementedError()

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        """
        Return metadata for the given field name, if available
        """
        return MappingProxyType({})

    def field_names(self) -> KeysView:
        """
        Return a dynamic view of the item's field names
        """
        return self.keys()  # type: ignore


class _MixinAttrsDataclassAdapter:

    _fields_dict: dict
    item: Any

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        return self._fields_dict[field_name].metadata  # type: ignore

    def field_names(self) -> KeysView:
        return KeysView(self._fields_dict)

    def __getitem__(self, field_name: str) -> Any:
        if field_name in self._fields_dict:
            return getattr(self.item, field_name)
        raise KeyError(field_name)

    def __setitem__(self, field_name: str, value: Any) -> None:
        if field_name in self._fields_dict:
            setattr(self.item, field_name, value)
        else:
            raise KeyError(f"{self.item.__class__.__name__} does not support field: {field_name}")

    def __delitem__(self, field_name: str) -> None:
        if field_name in self._fields_dict:
            try:
                delattr(self.item, field_name)
            except AttributeError:
                raise KeyError(field_name)
        else:
            raise KeyError(f"{self.item.__class__.__name__} does not support field: {field_name}")

    def __iter__(self) -> Iterator:
        return iter(attr for attr in self._fields_dict if hasattr(self.item, attr))

    def __len__(self) -> int:
        return len(list(iter(self)))


class AttrsAdapter(_MixinAttrsDataclassAdapter, AdapterInterface):
    def __init__(self, item: Any) -> None:
        super().__init__(item)
        import attr

        # store a reference to the item's fields to avoid O(n) lookups and O(n^2) traversals
        self._fields_dict = attr.fields_dict(self.item.__class__)

    @classmethod
    def is_item(cls, item: Any) -> bool:
        return is_attrs_instance(item)


class DataclassAdapter(_MixinAttrsDataclassAdapter, AdapterInterface):
    def __init__(self, item: Any) -> None:
        super().__init__(item)
        import dataclasses

        # store a reference to the item's fields to avoid O(n) lookups and O(n^2) traversals
        self._fields_dict = {field.name: field for field in dataclasses.fields(self.item)}

    @classmethod
    def is_item(cls, item: Any) -> bool:
        return is_dataclass_instance(item)


class _MixinDictScrapyItemAdapter:

    _fields_dict: dict
    item: Any

    def __getitem__(self, field_name: str) -> Any:
        return self.item[field_name]

    def __setitem__(self, field_name: str, value: Any) -> None:
        self.item[field_name] = value

    def __delitem__(self, field_name: str) -> None:
        del self.item[field_name]

    def __iter__(self) -> Iterator:
        return iter(self.item)

    def __len__(self) -> int:
        return len(self.item)


class DictAdapter(_MixinDictScrapyItemAdapter, AdapterInterface):
    @classmethod
    def is_item(cls, item: Any) -> bool:
        return isinstance(item, dict)

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        return MappingProxyType({})

    def field_names(self) -> KeysView:
        return KeysView(self.item)


class ScrapyItemAdapter(_MixinDictScrapyItemAdapter, AdapterInterface):
    @classmethod
    def is_item(cls, item: Any) -> bool:
        return is_scrapy_item(item)

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        return MappingProxyType(self.item.fields[field_name])

    def field_names(self) -> KeysView:
        return KeysView(self.item.fields)


class ItemAdapter(MutableMapping):
    """
    Wrapper class to interact with data container objects. It provides a common interface
    to extract and set data without having to take the object's type into account.
    """

    ADAPTER_CLASSES = deque(
        [
            ScrapyItemAdapter,
            DictAdapter,
            DataclassAdapter,
            AttrsAdapter,
        ]
    )

    def __init__(self, item: Any) -> None:
        self.adapter_class = None
        for cls in self.ADAPTER_CLASSES:
            if cls.is_item(item):
                self.adapter = cls(item)  # type: ignore
                break
        else:
            raise TypeError(f"No adapter found for objects of type: {type(item)} ({item})")

    @classmethod
    def is_item(self, item: Any) -> bool:
        for cls in self.ADAPTER_CLASSES:
            if cls.is_item(item):
                return True
        return False

    @property
    def item(self) -> Any:
        return self.adapter.item

    def __repr__(self) -> str:
        values = ", ".join(["%s=%r" % (key, value) for key, value in self.items()])
        return f"<ItemAdapter for {self.item.__class__.__name__}({values})>"

    def __getitem__(self, field_name: str) -> Any:
        return self.adapter.__getitem__(field_name)

    def __setitem__(self, field_name: str, value: Any) -> None:
        self.adapter.__setitem__(field_name, value)

    def __delitem__(self, field_name: str) -> None:
        self.adapter.__delitem__(field_name)

    def __iter__(self) -> Iterator:
        return self.adapter.__iter__()

    def __len__(self) -> int:
        return self.adapter.__len__()

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
        return self.adapter.get_field_meta(field_name)

    def field_names(self) -> KeysView:
        """
        Return read-only key view with the names of all the defined fields for the item
        """
        return self.adapter.field_names()

    def asdict(self) -> dict:
        """
        Return a dict object with the contents of the adapter. This works slightly different than
        calling `dict(adapter)`: it's applied recursively to nested items (if there are any).
        """
        return {key: _asdict(value) for key, value in self.items()}  # type: ignore


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
