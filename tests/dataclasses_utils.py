"""Code for dataclass tests that must only be imported from within tests
because it imports from itemadapter."""

from dataclasses import make_dataclass

from itemadapter import ItemAdapter

from tests import DataClassItem


DataClassItemNested = make_dataclass(
    "DataClassItem",
    [
        ("nested", DataClassItem),
        ("adapter", ItemAdapter),
        ("dict_", dict),
        ("list_", list),
        ("set_", set),
        ("tuple_", tuple),
        ("int_", int),
    ],
)
