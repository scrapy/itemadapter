from typing import Optional

from itemadapter.adapter import ItemAdapter


try:
    import attr
except ImportError:
    AttrsItem = None
    AttrsItemNested = None
    AttrsItemWithoutInit = None
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


try:
    from dataclasses import dataclass, field
except ImportError:
    DataClassItem = None
    DataClassItemNested = None
    DataClassWithoutInit = None
else:

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


try:
    from pydantic import BaseModel, Field as PydanticField
except ImportError:
    PydanticModel = None
    PydanticSpecialCasesModel = None
    PydanticModelNested = None
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
            allow_mutation=False,
        )

        class Config:
            validate_assignment = True

    class PydanticModelNested(BaseModel):
        nested: PydanticModel
        adapter: ItemAdapter
        dict_: dict
        list_: list
        set_: set
        tuple_: tuple
        int_: int

        class Config:
            arbitrary_types_allowed = True


try:
    from scrapy.item import Item as ScrapyItem, Field
except ImportError:
    ScrapyItem = None
    ScrapySubclassedItem = None
    ScrapySubclassedItemNested = None
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
