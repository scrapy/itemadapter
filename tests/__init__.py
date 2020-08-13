import os
import sys
from unittest import skipIf, TestCase as _TestCase


try:
    import attr
except ImportError:
    AttrsItem = None
else:
    if os.environ.get("ITEMADAPTER_NO_EXTRA_DEPS"):
        AttrsItem = None
    else:

        @attr.s
        class AttrsItem:
            name = attr.ib(default=None, metadata={"serializer": str})
            value = attr.ib(default=None, metadata={"serializer": int})


try:
    from dataclasses import field, make_dataclass
except ImportError:
    DataClassItem = None
else:
    if os.environ.get("ITEMADAPTER_NO_EXTRA_DEPS") and (3, 6) <= sys.version_info < (3, 7):
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
    ScrapySubclassedItemNested = None
else:
    if os.environ.get("ITEMADAPTER_NO_EXTRA_DEPS"):
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


class ImportRaiser:
    def __init__(self, *packages):
        self.packages = set(packages)

    def find_spec(self, fullname, path, target=None):
        if fullname in self.packages:
            raise ImportError


class TestCase(_TestCase):
    """Custom TestCase subclass which handles disabling installed extra
    packages during tests when ITEMADAPTER_NO_EXTRA_DEPS is set, as well as
    disabling test cases that require one or more unavailable extra
    dependencies.

    This is needed to disable packages that cannot be uninstalled because
    pytest depends on them.
    """

    _extra_modules = ("attr", "scrapy")

    def setUp(self):
        super().setUp()

        required_extra_modules = getattr(self, "required_extra_modules", None)
        if required_extra_modules:
            requirement_map = {
                "attr": AttrsItem,
                "dataclasses": DataClassItem,
                "scrapy": ScrapyItem,
            }
            unknown_extra_modules = [
                module for module in required_extra_modules if module not in requirement_map
            ]
            if unknown_extra_modules:
                raise NotImplementedError(
                    "Unknown extra modules: {}".format(unknown_extra_modules)
                )
            unavaliable_extra_modules = [
                module for module in required_extra_modules if not requirement_map[module]
            ]
            if unavaliable_extra_modules:
                self.skipTest("cannot import; {}".format(", ".join(unavaliable_extra_modules)))

        self._removed_modules = {}
        if os.environ.get("ITEMADAPTER_NO_EXTRA_DEPS"):
            if (3, 6) <= sys.version_info < (3, 7):
                self._extra_modules = self._extra_modules + ("dataclasses",)
            sys.meta_path.insert(0, ImportRaiser(*self._extra_modules))
            for package in self._extra_modules:
                if package in sys.modules:
                    self._removed_modules[package] = sys.modules[package]
                    del sys.modules[package]

    def tearDown(self):
        super().tearDown()

        if os.environ.get("ITEMADAPTER_NO_EXTRA_DEPS"):
            del sys.meta_path[0]
            for package in self._extra_modules:
                if package in self._removed_modules:
                    sys.modules[package] = self._removed_modules[package]


requires_attr = skipIf(not AttrsItem, "cannot import attr")
requires_dataclasses = skipIf(not DataClassItem, "cannot import dataclasses")
requires_scrapy = skipIf(not ScrapyItem, "cannot import scrapy")
