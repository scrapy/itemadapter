# Changelog

### 0.14.0 (unreleased)

Removed support for Python 3.9 and 3.10, and added support for Python 3.15
([#112](https://github.com/scrapy/itemadapter/pull/112),
[#130](https://github.com/scrapy/itemadapter/pull/130),
[#137](https://github.com/scrapy/itemadapter/pull/137)).

Raised the minimum supported versions of optional dependencies: `attrs` 22.1.0
(was 20.1.0), `pydantic` 2.7 (was 1.8) and `scrapy` 2.7 (was 2.2)
([#137](https://github.com/scrapy/itemadapter/pull/137),
[#139](https://github.com/scrapy/itemadapter/pull/139),
[#140](https://github.com/scrapy/itemadapter/pull/140)).

Removed support for Pydantic 1 models, including `pydantic.v1` models from
Pydantic 2, and for `scrapy.item.BaseItem` subclasses that are not
`scrapy.Item` subclasses
([#139](https://github.com/scrapy/itemadapter/pull/139)).

`ItemAdapter.ADAPTER_CLASSES` is now a `tuple` instead of a
`collections.deque`, so it no longer supports `appendleft()` and other
in-place changes. To register an adapter class, reassign it instead, e.g.
`ItemAdapter.ADAPTER_CLASSES = (MyAdapter, *ItemAdapter.ADAPTER_CLASSES)`
([#118](https://github.com/scrapy/itemadapter/pull/118),
[#128](https://github.com/scrapy/itemadapter/pull/128)).

Which adapter class handles each item class is now cached, making
`ItemAdapter()` and `is_item()` faster. As a result, the `is_item_class()`
class method of adapter classes must return the same result every time it is
called with the same item class
([#128](https://github.com/scrapy/itemadapter/pull/128)).

Overriding the `is_item()` class method in an adapter class is deprecated,
override `is_item_class()` instead. Adapter classes that override `is_item()`
still work, but trigger a `DeprecationWarning` and disable the cache above
([#128](https://github.com/scrapy/itemadapter/pull/128)).

Added support for
[`TypedDict`](https://docs.python.org/3/library/typing.html#typing.TypedDict)
item classes, including `typing_extensions.TypedDict` ones: field names, field
metadata from the first mapping in
[`Annotated`](https://docs.python.org/3/library/typing.html#typing.Annotated)
type hints, and `get_json_schema()` support, which honors `Required` and
`NotRequired` ([#123](https://github.com/scrapy/itemadapter/pull/123)).

`get_json_schema()` is much faster on repeated calls, as field docstrings read
from source code are now cached
([#141](https://github.com/scrapy/itemadapter/pull/141)).

`get_json_schema()` no longer fails on unions of 2 or more non-simple types,
e.g. 2 item classes ([#123](https://github.com/scrapy/itemadapter/pull/123)).

`get_json_schema()` now maps `int | float` to `number` regardless of the order
of the union members; `float | int` already did
([#133](https://github.com/scrapy/itemadapter/pull/133)).

`get_json_schema()` now handles `attrs.validators.matches_re()` validators
better: patterns are anchored to match their match function (`re.fullmatch()`
by default), and patterns with flags that JSON Schema cannot express, e.g.
`re.IGNORECASE`, are left out
([#122](https://github.com/scrapy/itemadapter/pull/122)).

Improved type hints ([#138](https://github.com/scrapy/itemadapter/pull/138)).

### 0.13.1 (2026-01-08)

Fixed `get_json_schema()` to properly format multiline field docstrings using
`inspect.cleandoc()`, ensuring consistent indentation and whitespace handling
([#115](https://github.com/scrapy/itemadapter/pull/115)).

### 0.13.0 (2025-12-15)

Added support for Python 3.14 and removed support for [PyPy](https://pypy.org/)
3.10.

`get_json_schema()` no longer reports all `scrapy.Item` fields as required.

### 0.12.2 (2025-09-02)

The return value of `get_json_schema()` is now deterministic (deterministic
order of dict keys and list items).

### 0.12.1 (2025-08-08)

`get_json_schema()` now supports inherited field docstrings.

### 0.12.0 (2025-07-24)

Added support for [PyPy](https://pypy.org/) 3.11
([#97](https://github.com/scrapy/itemadapter/pull/97)).

Added a new `get_json_schema()` class method to `ItemAdapter` and all built-in
adapters to output a [JSON Schema](https://json-schema.org/) for a given item
class ([#101](https://github.com/scrapy/itemadapter/pull/101)).

Modernized the code base, now making full use of
[pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
and using [ruff](https://docs.astral.sh/ruff/)
([#96](https://github.com/scrapy/itemadapter/pull/96),
[#98](https://github.com/scrapy/itemadapter/pull/98)).

### 0.11.0 (2025-01-29)

Removed functions deprecated in 0.5.0:

- `itemadapter.utils.is_attrs_instance()`
- `itemadapter.utils.is_dataclass_instance()`
- `itemadapter.utils.is_pydantic_instance()`
- `itemadapter.utils.is_scrapy_item()`

([#93](https://github.com/scrapy/itemadapter/pull/93)).

Added support for Pydantic 2
([#91](https://github.com/scrapy/itemadapter/pull/91)).

Added `__all__` to the top-level module to improve type checks
([#90](https://github.com/scrapy/itemadapter/pull/90)).

Improved `pre-commit` and CI configuration
([#91](https://github.com/scrapy/itemadapter/pull/91),
[#92](https://github.com/scrapy/itemadapter/pull/92)).

### 0.10.0 (2024-11-29)

Dropped Python 3.8 support, added official Python 3.13 and PyPy 3.10 support
([#79](https://github.com/scrapy/itemadapter/pull/79),
[#87](https://github.com/scrapy/itemadapter/pull/87)).

Fixed the typing check when run with Scrapy 2.12.0+
([#88](https://github.com/scrapy/itemadapter/pull/88)).

Fixed `MANIFEST.in` that was missing some files
([#84](https://github.com/scrapy/itemadapter/pull/84)).

Enabled `pre-commit`
([#85](https://github.com/scrapy/itemadapter/pull/85)).

### 0.9.0 (2024-05-07)

Dropped Python 3.7 support, added official Python 3.12 support
([#75](https://github.com/scrapy/itemadapter/pull/75),
[#77](https://github.com/scrapy/itemadapter/pull/77)).

Updated the documentation and the type hint about `ItemAdapter.ADAPTER_CLASSES`
to say that subclasses can use any iterable, not just `collections.deque`
([#74](https://github.com/scrapy/itemadapter/pull/74)).

Documented that `Pydantic >= 2` is not supported yet
([#73](https://github.com/scrapy/itemadapter/pull/73)).

Updated CI configuration
([#77](https://github.com/scrapy/itemadapter/pull/77),
[#80](https://github.com/scrapy/itemadapter/pull/80)).

### 0.8.0 (2023-03-30)

Dropped Python 3.6 support, and made Python 3.11 support official
([#65](https://github.com/scrapy/itemadapter/pull/65),
[#66](https://github.com/scrapy/itemadapter/pull/66),
[#69](https://github.com/scrapy/itemadapter/pull/69)).

It is now possible to declare custom `ItemAdapter` subclasses with their own
`ADAPTER_CLASSES` attribute, allowing to support different item types in
different parts of the same code base
([#68](https://github.com/scrapy/itemadapter/pull/68)).

Improved type hint support
([#67](https://github.com/scrapy/itemadapter/pull/67)).

### 0.7.0 (2022-08-02)

ItemAdapter.get_field_names_from_class
([#64](https://github.com/scrapy/itemadapter/pull/64))

### 0.6.0 (2022-05-12)

Slight performance improvement
([#62](https://github.com/scrapy/itemadapter/pull/62))

### 0.5.0 (2022-03-18)

Improve performance by removing imports inside functions
([#60](https://github.com/scrapy/itemadapter/pull/60))

### 0.4.0 (2021-08-26)

Added `ItemAdapter.is_item_class` and `ItemAdapter.get_field_meta_from_class`
([#54](https://github.com/scrapy/itemadapter/pull/54))

### 0.3.0 (2021-07-15)

Added built-in support for `pydantic` models ([#53](https://github.com/scrapy/itemadapter/pull/53))

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
