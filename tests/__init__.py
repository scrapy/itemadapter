import importlib
import sys
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Optional

from itemadapter import ItemAdapter
from itemadapter._imports import pydantic, pydantic_v1


def make_mock_import(block_name: str) -> Callable:
    def mock_import(name: str, *args, **kwargs):
        """Prevent importing a specific module, let everything else pass."""
        if name.split(".")[0] == block_name:
            raise ImportError(name)
        return importlib.__import__(name, *args, **kwargs)

    return mock_import


@contextmanager
def clear_itemadapter_imports() -> Generator[None, None, None]:
    backup = {}
    for key in sys.modules.copy():
        if key.startswith("itemadapter"):
            backup[key] = sys.modules.pop(key)
    try:
        yield
    finally:
        sys.modules.update(backup)


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


try:
    import attr
except ImportError:
    AttrsItem = None
    AttrsItemNested = None
    AttrsItemWithoutInit = None
    AttrsItemSubclassed = None
    AttrsItemEmpty = None
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


if pydantic_v1 is None:
    PydanticV1Model = None
    PydanticV1SpecialCasesModel = None
    PydanticV1ModelNested = None
    PydanticV1ModelSubclassed = None
    PydanticV1ModelEmpty = None
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


if pydantic is None:
    PydanticModel = None
    PydanticSpecialCasesModel = None
    PydanticModelNested = None
    PydanticModelSubclassed = None
    PydanticModelEmpty = None
else:

    class PydanticModel(pydantic.BaseModel):
        name: Optional[str] = pydantic.Field(
            default_factory=lambda: None,
            serializer=str,
        )
        value: Optional[int] = pydantic.Field(
            default_factory=lambda: None,
            serializer=int,
        )

    class PydanticSpecialCasesModel(pydantic.BaseModel):
        special_cases: Optional[int] = pydantic.Field(
            default_factory=lambda: None,
            alias="special_cases",
            allow_mutation=False,
        )

        class Config:
            validate_assignment = True

    class PydanticModelNested(pydantic.BaseModel):
        nested: PydanticModel
        adapter: ItemAdapter
        dict_: dict
        list_: list
        set_: set
        tuple_: tuple
        int_: int

        class Config:
            arbitrary_types_allowed = True

    class PydanticModelSubclassed(PydanticModel):
        subclassed: bool = pydantic.Field(
            default_factory=lambda: True,
        )

    class PydanticModelEmpty(pydantic.BaseModel):
        pass


try:
    from scrapy.item import Field
    from scrapy.item import Item as ScrapyItem
except ImportError:
    ScrapyItem = None
    ScrapySubclassedItem = None
    ScrapySubclassedItemNested = None
    ScrapySubclassedItemSubclassed = None
    ScrapySubclassedItemEmpty = None
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
