from __future__ import annotations

import typing
from typing import Any

# attempt the following imports only once,
# to be imported from itemadapter's submodules


_scrapy_item_classes: tuple[type, ...]
scrapy: Any

try:
    import scrapy

    _scrapy_item_classes = (scrapy.item.Item,)
except ImportError:
    scrapy = None
    _scrapy_item_classes = ()

typing_extensions: Any
try:
    import typing_extensions
except ImportError:
    typing_extensions = None

# typing.is_typeddict() does not recognize typing_extensions.TypedDict
# subclasses, and typing.get_type_hints() does not strip
# typing_extensions.ReadOnly before Python 3.13.
if typing_extensions is None:
    _is_typeddict = typing.is_typeddict
    _get_type_hints = typing.get_type_hints
else:
    _is_typeddict = typing_extensions.is_typeddict
    _get_type_hints = typing_extensions.get_type_hints

attrs: Any
try:
    import attrs
except ImportError:
    attrs = None

pydantic: Any = None
PydanticUndefined: object = None

try:
    import pydantic  # noqa: F401
    from pydantic_core import PydanticUndefined  # noqa: F401
except ImportError:  # No pydantic
    pass
