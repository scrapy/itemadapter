# Changelog

### 0.4.0 (2021-MM-DD)

Added `ItemAdapter.is_item_class` and `ItemAdapter.get_field_meta_from_class`
([#54](https://github.com/scrapy/itemadapter/pull/54))


### 0.3.0 (2021-07-15)

Added suport for `pydantic` models ([#53](https://github.com/scrapy/itemadapter/pull/53))


### 0.2.0 (2020-11-06)

Adapter interface: added the ability to support arbitrary types,
by implementing a MutableMapping-based interface.
By way of this change, now any type can be used as a Scrapy item.


### 0.1.1 (2020-09-28)

Dropped support for Python 3.5 (#38).

The new `get_field_meta_from_class` function offers the same functionality as
`ItemAdapter.get_field_meta` but for an item class, as opposed to an item
object (#34, #35).

`ItemAdapter.__repr__` no longer raises exceptions caused by the underlying
item (#31, #41).

Minor improvement to the release process (#37), and cleanup of test warnings (#40).


### 0.1.0 (2020-06-10)

Added `ItemAdapter.asdict`, which allows converting an item and all of its
nested items into `dict` objects (#27, #29).

Improved `ItemAdapter` performance by reducing time complexity for lookups and
traversals for dataclass and attrs items (#28).


### 0.0.8 (2020-05-22)

`ItemAdapter.field_names` now returns a `KeysView` instead of a `list`.

Minor CI and test changes.


### 0.0.7 (2020-05-22)

`ItemAdapter.get_field_meta` now returns an empty `MappingProxyType` object for
items without metadata support, instead of raising `TypeError`.

Improved the README and some docstrings.

Provided full test coverage, and refactored CI configuration, test
configuration and tests themselves.


### 0.0.6 (2020-05-09)

Added support for Scrapy’s `BaseItem`.

Refactored and extended tests.

Code style and documentation fixes.


### 0.0.5 (2020-04-28)

Removed support for `MutableMapping`.


### 0.0.4 (2020-04-28)

Removed metadata support for arbitrary mutable mappings.


### 0.0.3 (2020-04-27)

Rebuild for the Python Package Index.


### 0.0.2 (2020-04-27)

Split the implementation into several files for better code organization, and
without an impact on the existing API import paths.

Also improved the README.


### 0.0.1 (2020-04-25)

Initial release.
