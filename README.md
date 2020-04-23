# scrapy-itemadapter
[![actions](https://github.com/elacuesta/scrapy-itemadapter/workflows/Build/badge.svg)](https://github.com/elacuesta/scrapy-itemadapter/actions)
[![codecov](https://codecov.io/gh/elacuesta/scrapy-itemadapter/branch/master/graph/badge.svg)](https://codecov.io/gh/elacuesta/scrapy-itemadapter)


The `scrapy_itemadapter.ItemAdapter` class wraps Scrapy items. It aims to provide a common
interface to handle different types of items in an uniform manner. Currently supported item
types are:

* Classes inheriting from [`scrapy.item.Item`](https://docs.scrapy.org/en/latest/topics/items.html)
* [`dict`](https://docs.python.org/3/library/stdtypes.html#dict) objects
* [`dataclass`](https://docs.python.org/3/library/dataclasses.html)-based objects
* [`attrs`](https://www.attrs.org)-based classes


## API

### `scrapy_itemadapter.ItemAdapter`

The `ItemAdapter` class implements the
[`MutableMapping` interface](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping),
providing a `dict`-like API to manipulate data for the objects it adapts.

Two additional methods are defined:

`scrapy_itemadapter.ItemAdapter.get_field(field_name: str) -> Optional[Any]`

_Return the appropriate object if the wrapped item has a Mapping attribute
called "fields" and the requested field name can be found in it,
None otherwise._


`scrapy_itemadapter.ItemAdapter.field_names() -> List[str]`

_Return a list with the names of all the defined fields for the item_


### `scrapy_itemadapter.ItemAdapter.is_item`

`scrapy_itemadapter.ItemAdapter.is_item(obj: Any) -> bool`

_Helper function which returns `True` if the given object can be handled as
an item, `False` otherwise_


## Examples

### scrapy.item.Item objects

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

### Dictionaries

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


### dataclass-based items

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

### attrs-based items

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
