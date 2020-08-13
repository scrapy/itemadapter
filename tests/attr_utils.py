"""Code for attr.s tests that must only be imported from within tests because
it imports from itemadapter."""

import attr

from itemadapter import ItemAdapter

from tests import AttrsItem


@attr.s
class AttrsItemNested:
    nested = attr.ib(type=AttrsItem)
    adapter = attr.ib(type=ItemAdapter)
    dict_ = attr.ib(type=dict)
    list_ = attr.ib(type=list)
    set_ = attr.ib(type=set)
    tuple_ = attr.ib(type=tuple)
    int_ = attr.ib(type=int)
