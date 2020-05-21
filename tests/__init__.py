try:
    import attr
except ImportError:
    AttrsItem = None
else:

    @attr.s
    class AttrsItem:
        name = attr.ib(default=None, metadata={"serializer": str})
        value = attr.ib(default=None, metadata={"serializer": int})


try:
    from dataclasses import make_dataclass, field
except ImportError:
    DataClassItem = None
else:
    DataClassItem = make_dataclass(
        "DataClassItem",
        [
            ("name", str, field(default_factory=lambda: None, metadata={"serializer": str})),
            ("value", int, field(default_factory=lambda: None, metadata={"serializer": int})),
        ],
    )


try:
    from scrapy.item import Item as ScrapyItem, Field
except ImportError:
    ScrapyItem = None
    ScrapySubclassedItem = None
else:

    class ScrapySubclassedItem(ScrapyItem):
        name = Field(serializer=str)
        value = Field(serializer=int)
