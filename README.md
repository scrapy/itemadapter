# itemadapter
[![version](https://img.shields.io/pypi/v/itemadapter.svg)](https://pypi.python.org/pypi/itemadapter)
[![pyversions](https://img.shields.io/pypi/pyversions/itemadapter.svg)](https://pypi.python.org/pypi/itemadapter)
[![actions](https://github.com/scrapy/itemadapter/workflows/Build/badge.svg)](https://github.com/scrapy/itemadapter/actions)
[![codecov](https://codecov.io/gh/scrapy/itemadapter/branch/master/graph/badge.svg)](https://codecov.io/gh/scrapy/itemadapter)


The `ItemAdapter` class is a wrapper for data container objects, providing a
common interface to handle objects of different types in an uniform manner,
regardless of their underlying implementation.

Currently supported types are:

* [`dict`](https://docs.python.org/3/library/stdtypes.html#dict)
* [`scrapy.item.Item`](https://docs.scrapy.org/en/latest/topics/items.html#scrapy.item.Item)
* [`dataclass`](https://docs.python.org/3/library/dataclasses.html)-based classes
* [`attrs`](https://www.attrs.org)-based classes


## Requirements

* Python 3.5+
* [`scrapy`](https://scrapy.org/): optional, needed to interact with `scrapy` items
* `dataclasses` ([stdlib](https://docs.python.org/3/library/dataclasses.html) in Python 3.7+,
  or its [backport](https://pypi.org/project/dataclasses/) in Python 3.6): optional, needed
  to interact with `dataclass`-based items
* [`attrs`](https://pypi.org/project/attrs/): optional, needed to interact with `attrs`-based items


## Installation

`itemadapter` is available on [`PyPI`](https://pypi.python.org/pypi/itemadapter), it can be installed with `pip`:

```
pip install itemadapter
```


## License

`itemadapter` is distributed under a [BSD-3](https://opensource.org/licenses/BSD-3-Clause) license.


## Basic usage

The following is a simple example using a `dataclass` object.
Consider the following type definition:

```python
from dataclasses import dataclass
from itemadapter import ItemAdapter, is_item

@dataclass
class InventoryItem:
    name: str
    price: float
    stock: int
```

The `ItemAdapter` object can be treated much like a dictionary:

```python
>>> obj = InventoryItem(name='foo', price=20.5, stock=10)
>>> is_item(obj)
True
>>> adapter = ItemAdapter(obj)
>>> len(adapter)
3
>>> adapter["name"]
'foo'
>>> adapter.get("price")
20.5
```

The wrapped object is modified in-place:
```python
>>> adapter["name"] = "bar"
>>> adapter.update({"price": 12.7, "stock": 9})
>>> adapter.item
InventoryItem(name='bar', price=12.7, stock=9)
>>> adapter.item is obj
True
```

### Converting to dictionary

Passing an `ItemAdapter` to the `dict` built-in will create a new dictionary:

```python
>>> dict(adapter)
{'name': 'bar', 'price': 12.7, 'stock': 9}
```

For more examples using different types, refer to the [examples section](#more-examples) below.


## Public API

### `ItemAdapter` class

_class `itemadapter.adapter.ItemAdapter(item: Any)`_

`ItemAdapter` implements the
[`MutableMapping` interface](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping),
providing a `dict`-like API to manipulate data for the object it wraps
(which is modified in-place).

Two additional methods are available:

`get_field_meta(field_name: str) -> MappingProxyType`

Return a [`MappingProxyType`](https://docs.python.org/3/library/types.html#types.MappingProxyType)
object, which is a read-only mapping with metadata about the given field. If the item class does not
support field metadata, or there is no metadata for the given field, an empty object is returned.

The returned value is taken from the following sources, depending on the item type:

* [`scrapy.item.Field`](https://docs.scrapy.org/en/latest/topics/items.html#item-fields)
for `scrapy.item.Item`s
* [`dataclasses.field.metadata`](https://docs.python.org/3/library/dataclasses.html#dataclasses.field)
  for `dataclass`-based items
* [`attr.Attribute.metadata`](https://www.attrs.org/en/stable/examples.html#metadata)
  for `attrs`-based items

`field_names() -> List[str]`

Return a list with the names of all the defined fields for the item.

### `is_item` function

_`itemadapter.utils.is_item(obj: Any) -> bool`_

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
...     value = attr.ib(metadata={"serializer": int, "limit": 100})
...
>>> adapter = ItemAdapter(InventoryItem(name="foo", value=10))
>>> adapter.get_field_meta("name")
mappingproxy({'serializer': <class 'str'>})
>>> adapter.get_field_meta("value")
mappingproxy({'serializer': <class 'int'>})
```


## More examples

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
