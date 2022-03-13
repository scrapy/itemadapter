# attempt the following imports only once,
# to be imported from itemadapter's submodules

try:
    import scrapy  # pylint: disable=W0611 (unused-import)
except ImportError:
    scrapy = None  # type: ignore [assignment]

try:
    import dataclasses  # pylint: disable=W0611 (unused-import)
except ImportError:
    dataclasses = None  # type: ignore [assignment]

try:
    import attr  # pylint: disable=W0611 (unused-import)
except ImportError:
    attr = None  # type: ignore [assignment]

try:
    import pydantic  # pylint: disable=W0611 (unused-import)
except ImportError:
    pydantic = None  # type: ignore [assignment]
