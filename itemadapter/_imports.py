from __future__ import annotations

import sys
from typing import Any

# attempt the following imports only once,
# to be imported from itemadapter's submodules


_scrapy_item_classes: tuple
scrapy: Any

try:
    import scrapy
except ImportError:
    _scrapy_item_classes = ()
    scrapy = None
else:
    try:
        # handle deprecated base classes
        _base_item_cls = getattr(
            scrapy.item,
            "_BaseItem",
            scrapy.item.BaseItem,
        )
    except AttributeError:
        _scrapy_item_classes = (scrapy.item.Item,)
    else:
        _scrapy_item_classes = (scrapy.item.Item, _base_item_cls)

attr: Any
try:
    import attr
except ImportError:
    attr = None

pydantic: Any = None
PydanticUndefined: Any = None

pydantic_v1: Any = None
PydanticV1Undefined: Any = None

# pydantic v1 doesn't support Python 3.14+, on older Python versions we try to find both
if sys.version_info < (3, 14):
    try:
        import pydantic
    except ImportError:  # No pydantic
        pass
    else:
        try:
            import pydantic.v1 as pydantic_v1
        except ImportError:  # Pydantic <1.10.17
            pydantic_v1 = pydantic
            pydantic = None
        else:  # Pydantic 1.10.17+
            if not hasattr(pydantic.BaseModel, "model_fields"):  # Pydantic >=1.10.17,<2
                pydantic_v1 = pydantic
                pydantic = None
            # else Pydantic >=2

    try:
        from pydantic.v1.fields import Undefined as PydanticV1Undefined
        from pydantic_core import PydanticUndefined
    except ImportError:  # Pydantic < 2.0
        try:
            from pydantic.fields import (  # type: ignore[attr-defined,no-redef]
                Undefined as PydanticUndefined,
            )

            PydanticV1Undefined = PydanticUndefined
        except ImportError:
            pass
else:
    try:
        import pydantic
        from pydantic_core import PydanticUndefined
    except ImportError:  # No pydantic
        pass
