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
    from dataclasses import make_dataclass, field
except ImportError:
    DataClassItem = None
    DataClassItemNested = None
    DataClassWithoutInit = None
else:
    DataClassItem = make_dataclass(
        cls_name="DataClassItem",
        fields=[
            ("name", str, field(default_factory=lambda: None, metadata={"serializer": str})),
            ("value", int, field(default_factory=lambda: None, metadata={"serializer": int})),
        ],
    )

    DataClassItemNested = make_dataclass(
        cls_name="DataClassItem",
        fields=[
            ("nested", DataClassItem),
            ("adapter", ItemAdapter),
            ("dict_", dict),
            ("list_", list),
            ("set_", set),
            ("tuple_", tuple),
            ("int_", int),
        ],
    )

    DataClassWithoutInit = make_dataclass(
        cls_name="DataClassWithoutInit",
        fields=[
            ("name", str, field(default_factory=lambda: None, metadata={"serializer": str})),
            ("value", int, field(default_factory=lambda: None, metadata={"serializer": int})),
        ],
        init=False,
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
        dict_ = Field()
        list_ = Field()
        set_ = Field()
        tuple_ = Field()
        int_ = Field()
