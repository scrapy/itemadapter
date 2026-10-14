from __future__ import annotations

from dataclasses import field, make_dataclass
from typing import TYPE_CHECKING, Any

import pytest

import itemadapter
from itemadapter import ItemAdapter
from itemadapter._imports import attrs, pydantic, scrapy

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from pytest_codspeed import BenchmarkFixture

# Number of calls per benchmark. Kept the same for every scenario so that the
# results of different scenarios can be compared to each other.
CALLS = 100


def _dict_class(index: int) -> type:
    return type(f"DictItem{index}", (dict,), {})


def _dataclass_class(index: int) -> type:
    return make_dataclass(
        f"DataClassItem{index}",
        [("name", str, field(default=None)), ("value", int, field(default=None))],
    )


def _non_item_class(index: int) -> type:
    return type(f"NonItem{index}", (), {})


def _attrs_class(index: int) -> type:
    return attrs.make_class(
        f"AttrsItem{index}",
        {"name": attrs.field(default=None), "value": attrs.field(default=None)},
    )


def _pydantic_class(index: int) -> type:
    return pydantic.create_model(f"PydanticModel{index}", name=(str, None), value=(int, None))


def _scrapy_class(index: int) -> type:
    return type(scrapy.Item)(
        f"ScrapyItem{index}",
        (scrapy.Item,),
        {"name": scrapy.Field(), "value": scrapy.Field()},
    )


ITEM_CLASS_FACTORIES: dict[str, Callable[[int], type]] = {
    "dict": _dict_class,
    "dataclass": _dataclass_class,
    "non-item": _non_item_class,
}
if attrs is not None:
    ITEM_CLASS_FACTORIES["attrs"] = _attrs_class
if pydantic is not None:
    ITEM_CLASS_FACTORIES["pydantic"] = _pydantic_class
if scrapy is not None:
    ITEM_CLASS_FACTORIES["scrapy"] = _scrapy_class

item_class_factory = pytest.mark.parametrize(
    "factory",
    ITEM_CLASS_FACTORIES.values(),
    ids=list(ITEM_CLASS_FACTORIES),
)
is_item_function = pytest.mark.parametrize(
    "func",
    [ItemAdapter.is_item, itemadapter.is_item],
    ids=["ItemAdapter.is_item", "is_item"],
)


@is_item_function
@item_class_factory
def test_shared_class(
    benchmark: BenchmarkFixture,
    factory: Callable[[int], type],
    func: Callable[[Any], bool],
) -> None:
    """Items all share a single class, as in most real usage."""
    item_class = factory(0)
    items = [item_class() for _ in range(CALLS)]

    @benchmark
    def _() -> None:
        for item in items:
            func(item)


@is_item_function
@item_class_factory
def test_distinct_classes(
    benchmark: BenchmarkFixture,
    factory: Callable[[int], type],
    func: Callable[[Any], bool],
) -> None:
    """Every item has a class that no earlier call has seen.

    Item classes are built by a setup callback, which runs before every round
    and outside the measured window, so that their creation is not measured and
    the measured calls cannot benefit from earlier ones.
    """

    def setup() -> tuple[tuple[Any, ...], dict[str, Any]]:
        return ([factory(index)() for index in range(CALLS)],), {}

    def call(items: Sequence[Any]) -> None:
        for item in items:
            func(item)

    benchmark.pedantic(call, setup=setup)
