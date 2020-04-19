"""
Simplified classes to mock the behaviour of scrapy.item.Item and scrapy.item.Field

See https://github.com/scrapy/scrapy/blob/master/scrapy/item.py
"""

from abc import ABCMeta
from collections.abc import MutableMapping


class Field(dict):
    pass


class ItemMeta(ABCMeta):
    def __new__(mcs, class_name, bases, attrs):
        new_bases = tuple(base._class for base in bases if hasattr(base, "_class"))
        _class = super(ItemMeta, mcs).__new__(mcs, "x_" + class_name, new_bases, attrs)

        new_attrs = {}
        fields = getattr(_class, "fields", {})
        for n in dir(_class):
            v = getattr(_class, n)
            if isinstance(v, Field):
                fields[n] = v
        new_attrs["fields"] = fields

        return super(ItemMeta, mcs).__new__(mcs, class_name, bases, new_attrs)


class DictItem(MutableMapping):

    fields = {}

    def __init__(self, *args, **kwargs):
        self._values = {}
        if args or kwargs:
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        if key in self.fields:
            self._values[key] = value
        else:
            raise KeyError("%s does not support field: %s" % (self.__class__.__name__, key))

    def __delitem__(self, key):
        del self._values[key]

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)


class Item(DictItem, metaclass=ItemMeta):
    pass
