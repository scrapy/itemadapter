from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import pytest

from itemadapter import ItemAdapter
from itemadapter._imports import pydantic

if TYPE_CHECKING:
    from collections.abc import Callable, Generator


def make_mock_import(block_name: str) -> Callable:
    def mock_import(name: str, *args, **kwargs):
        """Prevent importing a specific module, let everything else pass."""
        if name.split(".", maxsplit=1)[0] == block_name:
            raise ImportError(name)
        return importlib.__import__(name, *args, **kwargs)

    return mock_import


@contextmanager
def clear_itemadapter_imports() -> Generator[None]:
    backup = {}
    for key in sys.modules.copy():
        if key.startswith("itemadapter"):
            backup[key] = sys.modules.pop(key)
    try:
        yield
    finally:
        sys.modules.update(backup)


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


@dataclass
class DataClassItem:
    name: str = field(default_factory=lambda: None, metadata={"serializer": str})
    value: int = field(default_factory=lambda: None, metadata={"serializer": int})


@dataclass
class DataClassItemNested:
    nested: DataClassItem
    adapter: ItemAdapter
    dict_: dict
    list_: list
    set_: set
    tuple_: tuple
    int_: int


@dataclass(init=False)
class DataClassWithoutInit:
    name: str = field(metadata={"serializer": str})
    value: int = field(metadata={"serializer": int})


@dataclass
class DataClassItemSubclassed(DataClassItem):
    subclassed: bool = True


@dataclass
class DataClassItemEmpty:
    pass


@dataclass
class DataClassItemJsonSchemaNested:
    is_nested: bool = True


@dataclass
class DataClassItemJsonSchema:
    __json_schema_extra__ = {
        "llmHint": "Hi model!",
    }
    name: str = field(metadata={"json_schema_extra": {"title": "Name"}})
    """Display name"""
    color: Color
    answer: str | float | int | None
    numbers: list[float]
    aliases: dict[str, str]
    nested: DataClassItemJsonSchemaNested
    nested_list: list[DataClassItemJsonSchemaNested]
    nested_dict: dict[str, DataClassItemJsonSchemaNested]
    nested_dict_list: list[dict[str, DataClassItemJsonSchemaNested]]
    value: Any = None
    produced: bool = field(default_factory=lambda: True)


try:
    import attr
    import attrs
except ImportError:
    AttrsItem = None
    AttrsItemNested = None
    AttrsItemWithoutInit = None
    AttrsItemSubclassed = None
    AttrsItemEmpty = None
    AttrsItemJsonSchema = None
    AttrsItemJsonSchemaNested = None
    AttrsClassicItem = None
    AttrsClassicItemNested = None
    AttrsClassicItemWithoutInit = None
    AttrsClassicItemSubclassed = None
    AttrsClassicItemEmpty = None
    AttrsClassicItemJsonSchema = None
    AttrsClassicItemJsonSchemaNested = None
else:

    @attrs.define
    class AttrsItem:
        name = attrs.field(default=None, metadata={"serializer": str})
        value = attrs.field(default=None, metadata={"serializer": int})

    @attrs.define
    class AttrsItemNested:
        nested: AttrsItem
        adapter: ItemAdapter
        dict_: dict
        list_: list
        set_: set
        tuple_: tuple
        int_: int

    @attrs.define(init=False)
    class AttrsItemWithoutInit:
        name = attrs.field(default=None, metadata={"serializer": str})
        value = attrs.field(default=None, metadata={"serializer": int})

    @attrs.define(init=False)
    class AttrsItemSubclassed(AttrsItem):
        subclassed: bool = True

    @attrs.define
    class AttrsItemEmpty:
        pass

    @attrs.define
    class AttrsItemJsonSchemaNested:
        is_nested: bool = True

    @attrs.define
    class AttrsItemJsonSchema:
        __json_schema_extra__ = {
            "llmHint": "Hi model!",
        }
        name: str = attrs.field(metadata={"json_schema_extra": {"title": "Name"}})
        """Display name"""
        color: Color
        answer: str | float | int | None
        numbers: list[float]
        aliases: dict[str, str]
        nested: AttrsItemJsonSchemaNested
        nested_list: list[AttrsItemJsonSchemaNested]
        nested_dict: dict[str, AttrsItemJsonSchemaNested]
        nested_dict_list: list[dict[str, AttrsItemJsonSchemaNested]]
        value: Any = None
        produced: bool = attrs.field(factory=lambda: True)

    # Classic API (attr.s, attr.ib): dict-based classes, unlike the slotted
    # ones created by attrs.define.

    @attr.s
    class AttrsClassicItem:
        name = attr.ib(default=None, metadata={"serializer": str})
        value = attr.ib(default=None, metadata={"serializer": int})

    @attr.s
    class AttrsClassicItemNested:
        nested = attr.ib(type=AttrsClassicItem)
        adapter = attr.ib(type=ItemAdapter)
        dict_ = attr.ib(type=dict)
        list_ = attr.ib(type=list)
        set_ = attr.ib(type=set)
        tuple_ = attr.ib(type=tuple)
        int_ = attr.ib(type=int)

    @attr.s(init=False)
    class AttrsClassicItemWithoutInit:
        name = attr.ib(default=None, metadata={"serializer": str})
        value = attr.ib(default=None, metadata={"serializer": int})

    @attr.s(init=False)
    class AttrsClassicItemSubclassed(AttrsClassicItem):
        subclassed = attr.ib(default=True, type=bool)

    @attr.s
    class AttrsClassicItemEmpty:
        pass

    @attr.s
    class AttrsClassicItemJsonSchemaNested:
        is_nested: bool = attr.ib(default=True)

    @attr.s
    class AttrsClassicItemJsonSchema:
        __json_schema_extra__ = {
            "llmHint": "Hi model!",
        }
        name: str = attr.ib(metadata={"json_schema_extra": {"title": "Name"}})
        """Display name"""
        color: Color = attr.ib()
        answer: str | float | int | None = attr.ib()
        numbers: list[float] = attr.ib()
        aliases: dict[str, str] = attr.ib()
        nested: AttrsClassicItemJsonSchemaNested = attr.ib()
        nested_list: list[AttrsClassicItemJsonSchemaNested] = attr.ib()
        nested_dict: dict[str, AttrsClassicItemJsonSchemaNested] = attr.ib()
        nested_dict_list: list[dict[str, AttrsClassicItemJsonSchemaNested]] = attr.ib()
        value: Any = attr.ib(default=None)
        produced: bool = attr.ib(factory=lambda: True)


if pydantic is None:
    PydanticModel = None
    PydanticSpecialCasesModel = None
    PydanticModelNested = None
    PydanticModelSubclassed = None
    PydanticModelEmpty = None
    PydanticModelJsonSchema = None
    PydanticModelJsonSchemaNested = None
else:

    class PydanticModel(pydantic.BaseModel):
        name: str | None = pydantic.Field(
            default_factory=lambda: None,
            json_schema_extra={"serializer": str},
        )
        value: int | None = pydantic.Field(
            default_factory=lambda: None,
            json_schema_extra={"serializer": int},
        )

    class PydanticSpecialCasesModel(pydantic.BaseModel):
        special_cases: int | None = pydantic.Field(
            default_factory=lambda: None,
            alias="special_cases",
            frozen=True,
        )

        model_config = {
            "validate_assignment": True,
        }

    class PydanticModelNested(pydantic.BaseModel):
        nested: PydanticModel
        adapter: ItemAdapter
        dict_: dict
        list_: list
        set_: set
        tuple_: tuple
        int_: int

        model_config = {
            "arbitrary_types_allowed": True,
        }

    class PydanticModelSubclassed(PydanticModel):
        subclassed: bool = pydantic.Field(
            default_factory=lambda: True,
        )

    class PydanticModelEmpty(pydantic.BaseModel):
        pass

    class PydanticModelJsonSchemaNested(pydantic.BaseModel):
        is_nested: bool = True

    class PydanticModelJsonSchema(pydantic.BaseModel):
        name: str = pydantic.Field(description="Display name", title="Name")
        value: Any = None
        color: Color
        produced: bool = pydantic.Field(default_factory=lambda: True)
        answer: str | float | int | None
        numbers: list[float]
        aliases: dict[str, str]
        nested: PydanticModelJsonSchemaNested
        nested_list: list[PydanticModelJsonSchemaNested]
        nested_dict: dict[str, PydanticModelJsonSchemaNested]
        nested_dict_list: list[dict[str, PydanticModelJsonSchemaNested]]

        model_config = {
            "json_schema_extra": {
                "llmHint": "Hi model!",
            },
        }


try:
    from scrapy.item import Field
    from scrapy.item import Item as ScrapyItem
except ImportError:
    ScrapyItem = None
    ScrapySubclassedItem = None
    ScrapySubclassedItemNested = None
    ScrapySubclassedItemSubclassed = None
    ScrapySubclassedItemEmpty = None
    ScrapySubclassedItemJsonSchema = None
    ScrapySubclassedItemJsonSchemaNested = None
else:

    class ScrapySubclassedItem(ScrapyItem):
        name = Field(serializer=str)
        value = Field(serializer=int)

    class ScrapySubclassedItemNested(ScrapyItem):
        nested = Field()
        adapter = Field()
        dict_ = Field()
        list_ = Field()
        set_ = Field()
        tuple_ = Field()
        int_ = Field()

    class ScrapySubclassedItemSubclassed(ScrapySubclassedItem):
        subclassed = Field()

    class ScrapySubclassedItemEmpty(ScrapyItem):
        pass

    class ScrapySubclassedItemJsonSchemaNested(ScrapyItem):
        is_nested: bool = Field(
            json_schema_extra={
                "default": True,
            },
        )

    class ScrapySubclassedItemJsonSchema(ScrapyItem):
        __json_schema_extra__ = {
            "llmHint": "Hi model!",
        }

        name: str = Field(
            json_schema_extra={
                "title": "Name",
            },
        )
        """Display name"""

        value = Field(
            json_schema_extra={
                "default": None,
            },
        )
        color: Color = Field()
        produced = Field()
        answer: str | float | int | None = Field()
        numbers: list[float] = Field()
        aliases: dict[str, str] = Field()
        nested: ScrapySubclassedItemJsonSchemaNested = Field()
        nested_list: list[ScrapySubclassedItemJsonSchemaNested] = Field()
        nested_dict: dict[str, ScrapySubclassedItemJsonSchemaNested] = Field()
        nested_dict_list: list[dict[str, ScrapySubclassedItemJsonSchemaNested]] = Field()


requires_attrs = pytest.mark.skipif(AttrsItem is None, reason="attrs module is not available")
requires_pydantic = pytest.mark.skipif(
    PydanticModel is None, reason="pydantic module is not available"
)
requires_scrapy = pytest.mark.skipif(
    ScrapySubclassedItem is None, reason="scrapy module is not available"
)
