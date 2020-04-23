# scrapy-itemadapter
[![actions](https://github.com/elacuesta/scrapy-itemadapter/workflows/Build/badge.svg)](https://github.com/elacuesta/scrapy-itemadapter/actions)
[![codecov](https://codecov.io/gh/elacuesta/scrapy-itemadapter/branch/master/graph/badge.svg)](https://codecov.io/gh/elacuesta/scrapy-itemadapter)


The `ItemAdapter` class is a wrapper for Scrapy items, which provides a common
interface to handle different types of items in an uniform manner, regardless
of their underlying implementation. Currently supported item types are:

* Classes inheriting from [`scrapy.item.Item`](https://docs.scrapy.org/en/latest/topics/items.html)
* Regular [dictionaries](https://docs.python.org/3/library/stdtypes.html#dict) (in fact, any class
  that implements the [`MutableMapping` interface](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping))
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

_class `scrapy_itemadapter.ItemAdapter(item: Any)`_

`ItemAdapter` implements the
[`MutableMapping` interface](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping),
providing a `dict`-like API to manipulate data for the object it wraps
(which is modified in-place).

Two additional methods are available:

`get_field(field_name: str) -> Optional[Any]`

Return the appropriate object if the wrapped item has a `Mapping` attribute
called "fields" and the requested field name can be found in it,
`None` otherwise.

`field_names() -> List[str]`

Return a list with the names of all the defined fields for the item.

### `is_item` function

_`scrapy_itemadapter.is_item(obj: Any) -> bool`_

Return `True` if the given object belongs to one of the supported types,
`False` otherwise.


## Examples

### `scrapy.item.Item` objects

```python
>>> from scrapy.item import Item, Field
>>> from scrapy_itemadapter import ItemAdapter
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
>>> from scrapy_itemadapter import ItemAdapter
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
>>> from scrapy_itemadapter import ItemAdapter
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
>>> from scrapy_itemadapter import ItemAdapter
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
