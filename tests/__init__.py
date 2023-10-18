import importlib
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Generator, Optional

from itemadapter import ItemAdapter


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
    for key in sys.modules.copy().keys():
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


try:
    from pydantic import ConfigDict, BaseModel, Field as PydanticField
except ImportError:
    PydanticModel = None
    PydanticSpecialCasesModel = None
    PydanticModelNested = None
    PydanticModelSubclassed = None
    PydanticModelEmpty = None
else:

    class PydanticModel(BaseModel):
        name: Optional[str] = PydanticField(
            default_factory=lambda: None,
            serializer=str,
        )
        value: Optional[int] = PydanticField(
            default_factory=lambda: None,
            serializer=int,
        )

    class PydanticSpecialCasesModel(BaseModel):
        special_cases: Optional[int] = PydanticField(
            default_factory=lambda: None,
            alias="special_cases",
            frozen=False,
        )
        model_config = ConfigDict(validate_assignment=True)

    class PydanticModelNested(BaseModel):
        nested: PydanticModel
        adapter: ItemAdapter
        dict_: dict
        list_: list
        set_: set
        tuple_: tuple
        int_: int
        model_config = ConfigDict(arbitrary_types_allowed=True)

    class PydanticModelSubclassed(PydanticModel):
        subclassed: bool = PydanticField(
            default_factory=lambda: True,
        )

    class PydanticModelEmpty(BaseModel):
        pass


try:
    from scrapy.item import Item as ScrapyItem, Field
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
