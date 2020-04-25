# itemadapter
[![version](https://img.shields.io/pypi/v/itemadapter.svg)](https://pypi.python.org/pypi/itemadapter)
[![pyversions](https://img.shields.io/pypi/pyversions/itemadapter.svg)](https://pypi.python.org/pypi/itemadapter)
[![actions](https://github.com/elacuesta/itemadapter/workflows/Build/badge.svg)](https://github.com/elacuesta/itemadapter/actions)
[![codecov](https://codecov.io/gh/elacuesta/itemadapter/branch/master/graph/badge.svg)](https://codecov.io/gh/elacuesta/itemadapter)


The `ItemAdapter` class is a wrapper for data container objects, providing a
common interface to handle objects of different types in an uniform manner,
regardless of their underlying implementation.

This package started as an initiative to
[support `dataclass` objects as items](https://github.com/scrapy/scrapy/pull/3881)
in [`Scrapy`](https://github.com/scrapy/scrapy). It was extracted out to a
standalone package in order to allow it to be used independently.

Currently supported types are:

* Classes that implement the [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) interface,
  including but not limited to:
  * [`scrapy.item.Item`](https://docs.scrapy.org/en/latest/topics/items.html)
  * [`dict`](https://docs.python.org/3/library/stdtypes.html#dict)
* [`dataclass`](https://docs.python.org/3/library/dataclasses.html)-based classes
* [`attrs`](https://www.attrs.org)-based classes


## Requirements

* Python 3.5+
* `dataclasses` ([stdlib](https://docs.python.org/3/library/dataclasses.html) in Python 3.7+,
  or its [backport](https://pypi.org/project/dataclasses/) in Python 3.6): optional, needed
  to interact with `dataclass`-based items
* [`attrs`](https://pypi.org/project/attrs/): optional, needed to interact with `attrs`-based items


## API

### `ItemAdapter` class

_class `itemadapter.ItemAdapter(item: Any)`_

`ItemAdapter` implements the
[`MutableMapping` interface](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping),
providing a `dict`-like API to manipulate data for the object it wraps
(which is modified in-place).

Two additional methods are available:

`get_field_meta(field_name: str) -> MappingProxyType`

Return a [`MappingProxyType`](https://docs.python.org/3/library/types.html#types.MappingProxyType)
object with metadata about the given field, or raise `TypeError` if the item class does not
support field metadata.

The returned value is taken from the following sources, depending on the item type:

* [`dataclasses.field.metadata`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field)
  for `dataclass`-based items
* [`attr.Attribute.metadata`](https://www.attrs.org/en/stable/examples.html#metadata)
  for `attrs`-based items
* [`scrapy.item.Field`](https://docs.scrapy.org/en/latest/topics/items.html#item-fields)
  for `scrapy.item.Item`s

`field_names() -> List[str]`

Return a list with the names of all the defined fields for the item.

### `is_item` function

_`itemadapter.is_item(obj: Any) -> bool`_

Return `True` if the given object belongs to one of the supported types,
`False` otherwise.


## Metadata support

`scrapy.item.Item`, `dataclass` and `attrs` objects allow the inclusion of
arbitrary field metadata, which can be retrieved with the
`ItemAdapter.get_field_meta` method. The definition procedure depends on the
underlying type.

#### `scrapy.item.Item` objects

```python
>>> from scrapy.item import Item, Field
>>> from itemadapter import ItemAdapter
>>> class InventoryItem(Item):
...     name = Field(serializer=str)
...     value = Field(serializer=int, limit=100)
...
>>> adapter = ItemAdapter(InventoryItem(name="foo", value=10))
>>> adapter.get_field_meta("name")
mappingproxy({'serializer': <class 'str'>})
>>> adapter.get_field_meta("value")
mappingproxy({'serializer': <class 'int'>, 'limit': 100})
```

#### `dataclass` objects

```python
>>> from dataclasses import dataclass, field
>>> @dataclass
... class InventoryItem:
...     name: str = field(metadata={"serializer": str})
...     value: int = field(metadata={"serializer": int, "limit": 100})
...
>>> adapter = ItemAdapter(InventoryItem(name="foo", value=10))
>>> adapter.get_field_meta("name")
mappingproxy({'serializer': <class 'str'>})
>>> adapter.get_field_meta("value")
mappingproxy({'serializer': <class 'int'>, 'limit': 100})
```

#### `attrs` objects

```python
>>> import attr
>>> @attr.s
... class InventoryItem:
...     name = attr.ib(metadata={"serializer": str})
...     value = attr.ib(metadata={"serializer": int})
...
>>> adapter = ItemAdapter(InventoryItem(name="foo", value=10))
>>> adapter.get_field_meta("name")
mappingproxy({'serializer': <class 'str'>})
>>> adapter.get_field_meta("value")
mappingproxy({'serializer': <class 'int'>})
```

#### Other types

In fact, any supported object with a `fields`
attribute which values are mappings works:

```python
>>> class DictWithFields(dict):
...     fields = {
...         "name": {"serializer": str},
...         "value": {"serializer": int, "limit": 100},
...     }
...
>>> adapter = ItemAdapter(DictWithFields(name="foo", value=10))
>>> adapter.get_field_meta("name")
mappingproxy({'serializer': <class 'str'>})
>>> adapter.get_field_meta("value")
mappingproxy({'serializer': <class 'int'>, 'limit': 100})
```


## Examples

### `scrapy.item.Item` objects

```python
>>> from scrapy.item import Item, Field
>>> from itemadapter import ItemAdapter
>>> class InventoryItem(Item):
...     name = Field()
...     price = Field()
...
>>> item = InventoryItem(name="foo", price=10)
>>> adapter = ItemAdapter(item)
>>> adapter.item is item
True
>>> adapter["name"]
'foo'
>>> adapter["name"] = "bar"
>>> adapter["price"] = 5
>>> item
{'name': 'bar', 'price': 5}
```

### `dict`

```python
>>> from itemadapter import ItemAdapter
>>> item = dict(name="foo", price=10)
>>> adapter = ItemAdapter(item)
>>> adapter.item is item
True
>>> adapter["name"]
'foo'
>>> adapter["name"] = "bar"
>>> adapter["price"] = 5
>>> item
{'name': 'bar', 'price': 5}
```

### `dataclass` objects

```python
>>> from dataclasses import dataclass
>>> from itemadapter import ItemAdapter
>>> @dataclass
... class InventoryItem:
...     name: str
...     price: int
...
>>> item = InventoryItem(name="foo", price=10)
>>> adapter = ItemAdapter(item)
>>> adapter.item is item
True
>>> adapter["name"]
'foo'
>>> adapter["name"] = "bar"
>>> adapter["price"] = 5
>>> item
InventoryItem(name='bar', price=5)
```

### `attrs` objects

```python
>>> import attr
>>> from itemadapter import ItemAdapter
>>> @attr.s
... class InventoryItem:
...     name = attr.ib()
...     price = attr.ib()
...
>>> item = InventoryItem(name="foo", price=10)
>>> adapter = ItemAdapter(item)
>>> adapter.item is item
True
>>> adapter["name"]
'foo'
>>> adapter["name"] = "bar"
>>> adapter["price"] = 5
>>> item
InventoryItem(name='bar', price=5)
```
