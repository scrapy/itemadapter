from itemadapter.adapter import ItemAdapter


try:
    import attr
except ImportError:
    AttrsItem = None
    AttrsItemNested = None
else:

    @attr.s
    class AttrsItem:
        name = attr.ib(default=None, metadata={"serializer": str})
        value = attr.ib(default=None, metadata={"serializer": int})

    @attr.s
    class AttrsItemNested:
        nested = attr.ib(type=AttrsItem)
        adapter = attr.ib(type=ItemAdapter)
        list_ = attr.ib(type=list)
        set_ = attr.ib(type=set)
        tuple_ = attr.ib(type=tuple)
        int_ = attr.ib(type=int)


try:
    from dataclasses import make_dataclass, field
except ImportError:
    DataClassItem = None
    DataClassItemNested = None
else:
    DataClassItem = make_dataclass(
        "DataClassItem",
        [
            ("name", str, field(default_factory=lambda: None, metadata={"serializer": str})),
            ("value", int, field(default_factory=lambda: None, metadata={"serializer": int})),
        ],
    )

    DataClassItemNested = make_dataclass(
        "DataClassItem",
        [
            ("nested", DataClassItem),
            ("adapter", ItemAdapter),
            ("list_", list),
            ("set_", set),
            ("tuple_", tuple),
            ("int_", int),
        ],
    )


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
        list_ = Field()
        set_ = Field()
        tuple_ = Field()
        int_ = Field()
