# attempt the following imports only once,
# to be imported from itemadapter's submodules

_scrapy_item_classes: tuple

try:
    import scrapy  # pylint: disable=W0611 (unused-import)
except ImportError:
    scrapy = None  # type: ignore [assignment]
    _scrapy_item_classes = ()
else:
    try:
        # handle deprecated base classes
        _base_item_cls = getattr(scrapy.item, "_BaseItem", scrapy.item.BaseItem)
    except AttributeError:
        _scrapy_item_classes = (scrapy.item.Item,)
    else:
        _scrapy_item_classes = (scrapy.item.Item, _base_item_cls)

try:
    import attr  # pylint: disable=W0611 (unused-import)
except ImportError:
    attr = None  # type: ignore [assignment]

try:
    import pydantic.v1 as pydantic_v1  # pylint: disable=W0611 (unused-import)
    import pydantic  # pylint: disable=W0611 (unused-import)
except ImportError:
    try:
        import pydantic as pydantic_v1  # pylint: disable=W0611 (unused-import)
        pydantic = None  # type: ignore [assignment]
    except ImportError:
        # Handle the case where neither pydantic.v1 nor pydantic is available
        pydantic_v1 = None
