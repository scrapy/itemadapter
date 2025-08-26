from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional, Union

from itemadapter import ItemAdapter
from itemadapter._imports import pydantic, pydantic_v1

if TYPE_CHECKING:
    from collections.abc import Generator


def make_mock_import(block_name: str) -> Callable:
    def mock_import(name: str, *args, **kwargs):
        """Prevent importing a specific module, let everything else pass."""
        if name.split(".")[0] == block_name:
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
    answer: Union[str, float, int, None]
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
except ImportError:
    AttrsItem = None
    AttrsItemNested = None
    AttrsItemWithoutInit = None
    AttrsItemSubclassed = None
    AttrsItemEmpty = None
    AttrsItemJsonSchema = None
    AttrsItemJsonSchemaNested = None
else:

    @attr.s
    class AttrsItem:
        name = attr.ib(default=None, metadata={"serializer": str})
        value = attr.ib(default=None, metadata={"serializer": int})

    @attr.s
    class AttrsItemNested:
        nested = attr.ib(type=AttrsItem)
        adapter = attr.ib(type=ItemAdapter)
        dict_ = attr.ib(type=dict)
        list_ = attr.ib(type=list)
        set_ = attr.ib(type=set)
        tuple_ = attr.ib(type=tuple)
        int_ = attr.ib(type=int)

    @attr.s(init=False)
    class AttrsItemWithoutInit:
        name = attr.ib(default=None, metadata={"serializer": str})
        value = attr.ib(default=None, metadata={"serializer": int})

    @attr.s(init=False)
    class AttrsItemSubclassed(AttrsItem):
        subclassed = attr.ib(default=True, type=bool)

    @attr.s
    class AttrsItemEmpty:
        pass

    @attr.s
    class AttrsItemJsonSchemaNested:
        is_nested: bool = attr.ib(default=True)

    @attr.s
    class AttrsItemJsonSchema:
        __json_schema_extra__ = {
            "llmHint": "Hi model!",
        }
        name: str = attr.ib(metadata={"json_schema_extra": {"title": "Name"}})
        """Display name"""
        color: Color = attr.ib()
        answer: Union[str, float, int, None] = attr.ib()
        numbers: list[float] = attr.ib()
        aliases: dict[str, str] = attr.ib()
        nested: AttrsItemJsonSchemaNested = attr.ib()
        nested_list: list[AttrsItemJsonSchemaNested] = attr.ib()
        nested_dict: dict[str, AttrsItemJsonSchemaNested] = attr.ib()
        nested_dict_list: list[dict[str, AttrsItemJsonSchemaNested]] = attr.ib()
        value: Any = attr.ib(default=None)
        produced: bool = attr.ib(factory=lambda: True)


if pydantic_v1 is None:
    PydanticV1Model = None
    PydanticV1SpecialCasesModel = None
    PydanticV1ModelNested = None
    PydanticV1ModelSubclassed = None
    PydanticV1ModelEmpty = None
    PydanticV1ModelJsonSchema = None
    PydanticV1ModelJsonSchemaNested = None
else:

    class PydanticV1Model(pydantic_v1.BaseModel):
        name: Optional[str] = pydantic_v1.Field(
            default_factory=lambda: None,
            serializer=str,
        )
        value: Optional[int] = pydantic_v1.Field(
            default_factory=lambda: None,
            serializer=int,
        )

    class PydanticV1SpecialCasesModel(pydantic_v1.BaseModel):
        special_cases: Optional[int] = pydantic_v1.Field(
            default_factory=lambda: None,
            alias="special_cases",
            allow_mutation=False,
        )

        class Config:
            validate_assignment = True

    class PydanticV1ModelNested(pydantic_v1.BaseModel):
        nested: PydanticV1Model
        adapter: ItemAdapter
        dict_: dict
        list_: list
        set_: set
        tuple_: tuple
        int_: int

        class Config:
            arbitrary_types_allowed = True

    class PydanticV1ModelSubclassed(PydanticV1Model):
        subclassed: bool = pydantic_v1.Field(
            default_factory=lambda: True,
        )

    class PydanticV1ModelEmpty(pydantic_v1.BaseModel):
        pass

    class PydanticV1ModelJsonSchemaNested(pydantic_v1.BaseModel):
        is_nested: bool = True

    class PydanticV1ModelJsonSchema(pydantic_v1.BaseModel):
        name: str = pydantic_v1.Field(title="Name", description="Display name")
        value: Any = None
        color: Color
        produced: bool
        answer: Union[str, float, int, None]
        numbers: list[float]
        aliases: dict[str, str]
        nested: PydanticV1ModelJsonSchemaNested
        nested_list: list[PydanticV1ModelJsonSchemaNested]
        nested_dict: dict[str, PydanticV1ModelJsonSchemaNested]
        nested_dict_list: list[dict[str, PydanticV1ModelJsonSchemaNested]]

        class Config:
            schema_extra = {
                "llmHint": "Hi model!",
            }


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
        name: Optional[str] = pydantic.Field(
            default_factory=lambda: None,
            json_schema_extra={"serializer": str},
        )
        value: Optional[int] = pydantic.Field(
            default_factory=lambda: None,
            json_schema_extra={"serializer": int},
        )

    class PydanticSpecialCasesModel(pydantic.BaseModel):
        special_cases: Optional[int] = pydantic.Field(
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
        answer: Union[str, float, int, None]
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
        answer: Union[str, float, int, None] = Field()
        numbers: list[float] = Field()
        aliases: dict[str, str] = Field()
        nested: ScrapySubclassedItemJsonSchemaNested = Field()
        nested_list: list[ScrapySubclassedItemJsonSchemaNested] = Field()
        nested_dict: dict[str, ScrapySubclassedItemJsonSchemaNested] = Field()
        nested_dict_list: list[dict[str, ScrapySubclassedItemJsonSchemaNested]] = Field()
