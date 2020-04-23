# itemadapter
[![actions](https://github.com/elacuesta/itemadapter/workflows/Build/badge.svg)](https://github.com/elacuesta/itemadapter/actions)
[![codecov](https://codecov.io/gh/elacuesta/itemadapter/branch/master/graph/badge.svg)](https://codecov.io/gh/elacuesta/itemadapter)


The `ItemAdapter` class is a wrapper for Scrapy items, which provides a common
interface to handle different types of items in an uniform manner, regardless
of their underlying implementation. Currently supported item types are:

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

The returned value is taken from the following sources, according to the item implementation:

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

### `dict`s

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

### `dataclass`-based items

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

### `attrs`-based items

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
