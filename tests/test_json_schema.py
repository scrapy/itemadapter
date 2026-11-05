from __future__ import annotations

import inspect
import json
import re
import typing
from collections.abc import Mapping, Sequence  # noqa: TC003
from dataclasses import dataclass, field, make_dataclass
from enum import Enum
from typing import Any, Generic, TypeVar, Union

import pytest

from itemadapter._imports import pydantic
from itemadapter._json_schema import json_schema_pattern
from itemadapter.adapter import (
    AttrsAdapter,
    DataclassAdapter,
    DictAdapter,
    ItemAdapter,
    PydanticAdapter,
    ScrapyItemAdapter,
)
from tests import (
    AttrsItem,
    AttrsItemJsonSchemaNested,
    DataClassItemJsonSchemaNested,
    PydanticModel,
    PydanticModelJsonSchemaNested,
    ScrapySubclassedItem,
    ScrapySubclassedItemJsonSchemaNested,
    requires_attrs,
    requires_pydantic,
    requires_scrapy,
)

_T = TypeVar("_T")


if ScrapySubclassedItem and AttrsItem:
    from scrapy import Field as ScrapyField
    from scrapy import Item as ScrapyItem

    class ScrapySubclassedItemCrossNested(ScrapyItem):
        nested: AttrsItemJsonSchemaNested = ScrapyField()


@dataclass
class Brand:
    name: str


@dataclass
class OptionalItemListNestedItem:
    is_nested: bool = True


@dataclass
class OptionalItemListItem:
    foo: list[OptionalItemListNestedItem] | None = None


T = typing.TypeVar("T")


@dataclass
class UnhandledTypeItem:
    """Type hints that map to no JSON Schema type."""

    mapping: typing.Mapping
    """A mapping with no key or value types."""
    meta: type[int]
    """A generic alias whose origin is neither a container nor a union."""
    var: T
    """A type variable, which is not a type."""


@dataclass
class ExplicitRequiredItem:
    __json_schema_extra__ = {"required": ["bar"]}

    foo: str
    bar: str = "asdf"


@dataclass
class MultiItemUnionItem:
    either: Brand | OptionalItemListNestedItem
    or_none: Brand | OptionalItemListNestedItem | None
    containers: list[int] | dict


@dataclass
class RecursionItem:
    child: RecursionNestedItem
    sibling: RecursionItem


@dataclass
class RecursionNestedItem:
    parent: RecursionItem
    sibling: RecursionNestedItem


@dataclass
class Node:
    parent: Node | None
    children: list[Node] | None


@dataclass
class SimpleItem:
    foo: str


@dataclass
class SameNameItem:
    foo: str


SameNameItem1 = SameNameItem


@dataclass
class SameNameItem:  # type: ignore[no-redef]  # pylint: disable=function-redefined
    bar: str


@dataclass
class SameNameParentItem:
    a: SameNameItem1
    b: SameNameItem1
    c: SameNameItem
    d: SameNameItem


class CustomMapping:  # noqa: PLW1641
    def __init__(self, data):
        self._data = dict(data)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def values(self):
        return self._data.values()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __eq__(self, other):
        if isinstance(other, CustomMapping):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return NotImplemented

    def __ne__(self, other):
        eq = self.__eq__(other)
        if eq is NotImplemented:
            return NotImplemented
        return not eq


class SimpleEnum(Enum):
    foo = "foo"


if PydanticModel:

    class PydanticEnumModel(pydantic.BaseModel):
        enum: SimpleEnum


def check_schemas(actual, expected):
    """Helper function to check if the actual JSON schema matches the expected
    one.

    It uses json.dumps() WITHOUT sorting the keys, to ensure key sorting
    matches in both schemas as well. Maintaining the source order of fields can
    be important

    The indentation is set for better readability or mismatch output.
    """
    assert json.dumps(actual, indent=2) == json.dumps(expected, indent=2)


@pytest.mark.parametrize(
    ("field_type", "expected"),
    [
        (int | float, {"type": ["number"]}),
        (float | int, {"type": ["number"]}),
        (int | float | None, {"type": ["null", "number"]}),
        (bool | int | float, {"type": ["boolean", "number"]}),
        (int | str, {"type": ["integer", "string"]}),
        (int | None, {"type": ["null", "integer"]}),
        (list[int | float], {"type": "array", "items": {"type": ["number"]}}),
        (tuple[int, float], {"type": "array", "items": {"type": ["number"]}}),
    ],
)
def test_numeric_union(field_type, expected):
    item_class = make_dataclass("NumericItem", [("value", field_type)])
    actual = ItemAdapter.get_json_schema(item_class)["properties"]["value"]
    check_schemas(actual, expected)


class TestJsonSchema:
    @requires_attrs
    @requires_pydantic
    def test_attrs_pydantic_enum(self):
        """This test exists to ensure that we do not let the JSON Schema
        generation of Pydantic item classes generate nested $defs (which we
        don’t since we do not run Pydantic’s JSON Schema generation but our
        own)."""
        import attrs

        @attrs.define
        class TestAttrsItem:
            pydantic: PydanticEnumModel

        actual = ItemAdapter.get_json_schema(TestAttrsItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "pydantic": {
                    "type": "object",
                    "properties": {
                        "enum": {"type": "string", "enum": ["foo"]},
                    },
                    "required": ["enum"],
                }
            },
            "required": ["pydantic"],
        }
        check_schemas(actual, expected)

    @requires_scrapy
    def test_unreachable_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reading the item class source to find attribute docstrings is not
        always a possibility, e.g. for classes defined in a REPL. In those
        cases, only the extraction of those docstrings should fail."""

        class ScrapySubclassedItemUnreachable(ScrapyItem):
            name: str = ScrapyField(json_schema_extra={"example": "Foo"})
            """Display name"""

        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {
                    "example": "Foo",
                    "type": "string",
                }
            },
        }
        for exception in (OSError, TypeError):

            def getsource(_obj: Any, _exception: type[Exception] = exception) -> str:
                raise _exception

            with monkeypatch.context() as m:
                m.setattr(inspect, "getsource", getsource)
                actual = ItemAdapter.get_json_schema(ScrapySubclassedItemUnreachable)
            check_schemas(actual, expected)

    def test_recursion(self):
        actual = ItemAdapter.get_json_schema(RecursionItem)
        expected = {
            "$defs": {
                "RecursionItem": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "child": {"$ref": "#/$defs/RecursionNestedItem"},
                        "sibling": {"$ref": "#/$defs/RecursionItem"},
                    },
                    "required": ["child", "sibling"],
                },
                "RecursionNestedItem": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "parent": {"$ref": "#/$defs/RecursionItem"},
                        "sibling": {"$ref": "#/$defs/RecursionNestedItem"},
                    },
                    "required": ["parent", "sibling"],
                },
            },
            "$ref": "#/$defs/RecursionItem",
        }
        check_schemas(actual, expected)

    def test_self_recursion(self):
        """A class that is only referenced from itself, as in the example of
        https://github.com/scrapy/itemadapter/issues/103"""
        actual = ItemAdapter.get_json_schema(Node)
        expected = {
            "$defs": {
                "Node": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "parent": {
                            "anyOf": [{"type": "null"}, {"$ref": "#/$defs/Node"}],
                        },
                        "children": {
                            "anyOf": [
                                {"type": "null"},
                                {"type": "array", "items": {"$ref": "#/$defs/Node"}},
                            ],
                        },
                    },
                    "required": ["parent", "children"],
                },
            },
            "$ref": "#/$defs/Node",
        }
        check_schemas(actual, expected)

    def test_reused_item_class(self):
        """An item class used more than once is defined once in $defs and
        referenced from every use."""

        @dataclass
        class TestItem:
            a: SimpleItem
            b: SimpleItem

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "$defs": {
                "SimpleItem": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"foo": {"type": "string"}},
                    "required": ["foo"],
                },
            },
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "a": {"$ref": "#/$defs/SimpleItem"},
                "b": {"$ref": "#/$defs/SimpleItem"},
            },
            "required": ["a", "b"],
        }
        check_schemas(actual, expected)

    def test_adapter_class_entry_point(self):
        """An adapter class can be the entry point, instead of ItemAdapter."""

        @dataclass
        class TestItem:
            a: SimpleItem
            b: SimpleItem

        actual = DataclassAdapter.get_json_schema(TestItem)
        expected = {
            "$defs": {
                "SimpleItem": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"foo": {"type": "string"}},
                    "required": ["foo"],
                },
            },
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "a": {"$ref": "#/$defs/SimpleItem"},
                "b": {"$ref": "#/$defs/SimpleItem"},
            },
            "required": ["a", "b"],
        }
        check_schemas(actual, expected)

        check_schemas(DictAdapter.get_json_schema(dict), {"type": "object"})

    def test_same_name_item_classes(self):
        """Different item classes that share a name get different definition
        names."""
        actual = ItemAdapter.get_json_schema(SameNameParentItem)
        expected = {
            "$defs": {
                "SameNameItem": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"foo": {"type": "string"}},
                    "required": ["foo"],
                },
                "SameNameItem_2": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"bar": {"type": "string"}},
                    "required": ["bar"],
                },
            },
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "a": {"$ref": "#/$defs/SameNameItem"},
                "b": {"$ref": "#/$defs/SameNameItem"},
                "c": {"$ref": "#/$defs/SameNameItem_2"},
                "d": {"$ref": "#/$defs/SameNameItem_2"},
            },
            "required": ["a", "b", "c", "d"],
        }
        check_schemas(actual, expected)

    def test_nested_dict(self):
        @dataclass
        class TestItem:
            foo: dict

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "object",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_optional_item_list(self):
        actual = ItemAdapter.get_json_schema(OptionalItemListItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "anyOf": [
                        {
                            "type": "null",
                        },
                        {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "is_nested": {
                                        "type": "boolean",
                                        "default": True,
                                    },
                                },
                            },
                        },
                    ],
                    "default": None,
                },
            },
        }
        check_schemas(actual, expected)

    def test_sequence_untyped(self):
        @dataclass
        class TestItem:
            foo: Sequence

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_tuple_ellipsis(self):
        @dataclass
        class TestItem:
            foo: tuple[Any, ...]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_tuple_multiple_types(self):
        @dataclass
        class TestItem:
            foo: tuple[str, int, int]

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                    "items": {
                        "type": ["integer", "string"],
                    },
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_type_var(self):
        # this tests the update_prop_from_type() branch where prop_type is not a type

        @dataclass
        class TestItem(Generic[_T]):
            foo: _T

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_union_single(self):
        @dataclass
        class TestItem:
            foo: Union[str]  # noqa: UP007

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_custom_any_of(self):
        @dataclass
        class TestItem:
            foo: str | SimpleItem = field(
                metadata={"json_schema_extra": {"anyOf": []}},
            )

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"anyOf": []},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_set_untyped(self):
        @dataclass
        class TestItem:
            foo: set

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "array", "uniqueItems": True},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_mapping_untyped(self):
        @dataclass
        class TestItem:
            foo: Mapping

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "object"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_custom_mapping(self):
        @dataclass
        class TestItem:
            foo: CustomMapping

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "object"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_item_without_attributes(self):
        @dataclass
        class TestItem:
            pass

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
        }
        check_schemas(actual, expected)

    def test_typing_sequence_untyped(self):
        @dataclass
        class TestItem:
            foo: typing.Sequence

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_custom_items(self):
        @dataclass
        class TestItem:
            foo: typing.Sequence = field(metadata={"json_schema_extra": {"items": {}}})

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "items": {},
                    "type": "array",
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @requires_attrs
    def test_modern_optional_annotations(self):
        import attrs

        @attrs.define
        class Product:
            name: str
            """Product name"""

            brand: Brand | None
            in_stock: bool = True

        actual = ItemAdapter.get_json_schema(Product)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string", "description": "Product name"},
                "brand": {
                    "anyOf": [
                        {"type": "null"},
                        {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {"name": {"type": "string"}},
                            "required": ["name"],
                        },
                    ]
                },
                "in_stock": {"type": "boolean", "default": True},
            },
            "required": ["name", "brand"],
        }
        check_schemas(actual, expected)

    def test_field_docstring_inheritance(self):
        """Test that field docstrings are inherited from parent classes."""

        @dataclass
        class ParentItem:
            foo: str
            """Parent item foo"""

        @dataclass
        class ChildItem(ParentItem):
            pass

        actual = ItemAdapter.get_json_schema(ChildItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string", "description": "Parent item foo"},
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    def test_field_docstring_source_reads(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The source of each class in the MRO of an item class is read once,
        not once per field, and not again on later calls."""

        @dataclass
        class ParentItem:
            foo: str
            """Parent item foo"""

        @dataclass
        class ChildItem(ParentItem):
            bar: str
            baz: str
            """Child item baz"""

        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string", "description": "Parent item foo"},
                "bar": {"type": "string"},
                "baz": {"type": "string", "description": "Child item baz"},
            },
            "required": ["foo", "bar", "baz"],
        }
        original_getsource = inspect.getsource
        calls = []

        def getsource(obj: Any) -> str:
            calls.append(obj)
            return original_getsource(obj)

        with monkeypatch.context() as m:
            m.setattr(inspect, "getsource", getsource)
            check_schemas(ItemAdapter.get_json_schema(ChildItem), expected)
            check_schemas(ItemAdapter.get_json_schema(ChildItem), expected)
        assert calls == list(ChildItem.__mro__)

    def test_field_docstring_cleandoc(self):
        """Test that field docstrings are properly dedented and trimmed."""

        @dataclass
        class TestItem:
            foo: str
            """
            This is a multiline docstring.

            It has multiple paragraphs and indentation
            that should be cleaned up.
            """

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {
                    "type": "string",
                    "description": (
                        "This is a multiline docstring.\n\n"
                        "It has multiple paragraphs and indentation\n"
                        "that should be cleaned up."
                    ),
                },
            },
            "required": ["foo"],
        }
        check_schemas(actual, expected)


class TestCrossNesting:
    """Test item nesting across different item types, with all supported types
    acting as parent or child in one test."""

    @requires_pydantic
    @requires_attrs
    def test_attrs_pydantic(self):
        import attrs

        @attrs.define
        class TestItem:
            nested: PydanticModelJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = AttrsAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"nested": {}},
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @requires_scrapy
    @requires_attrs
    def test_scrapy_attrs(self):
        actual = ItemAdapter.get_json_schema(ScrapySubclassedItemCrossNested)  # pylint: disable=possibly-used-before-assignment
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                }
            },
        }
        check_schemas(actual, expected)

        actual = ScrapyItemAdapter.get_json_schema(ScrapySubclassedItemCrossNested)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"nested": {}},
        }
        check_schemas(actual, expected)

    @requires_pydantic
    def test_pydantic_dataclass(self):
        class TestItem(pydantic.BaseModel):
            nested: DataClassItemJsonSchemaNested

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"type": "boolean", "default": True},
                    },
                },
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = PydanticAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {},
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

    @requires_pydantic
    @requires_scrapy
    def test_pydantic_scrapy(self):
        class TestItem(pydantic.BaseModel):
            nested: ScrapySubclassedItemJsonSchemaNested

            model_config = {
                "arbitrary_types_allowed": True,
            }

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "is_nested": {"default": True, "type": "boolean"},
                    },
                },
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)

        actual = PydanticAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {
                "nested": {"type": "object"},
            },
            "required": ["nested"],
        }
        check_schemas(actual, expected)


class TestJsonSchemaEdgeCase:
    """Inputs that map to no JSON Schema output, or that the JSON Schema
    generation cannot take at face value."""

    def test_unhandled_types(self):
        actual = ItemAdapter.get_json_schema(UnhandledTypeItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "mapping": {
                    "type": "object",
                    "description": "A mapping with no key or value types.",
                },
                "meta": {
                    "description": (
                        "A generic alias whose origin is neither a container nor a union."
                    )
                },
                "var": {"description": "A type variable, which is not a type."},
            },
            "required": ["mapping", "meta", "var"],
        }
        check_schemas(actual, expected)

    def test_multi_item_union(self):
        """Unions keep the declaration order of their members, and only get a
        leading entry for their simple types if they have any."""
        actual = ItemAdapter.get_json_schema(MultiItemUnionItem)
        brand_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        nested_schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"is_nested": {"type": "boolean", "default": True}},
        }
        brand_ref = {"$ref": "#/$defs/Brand"}
        nested_ref = {"$ref": "#/$defs/OptionalItemListNestedItem"}
        expected = {
            "$defs": {"Brand": brand_schema, "OptionalItemListNestedItem": nested_schema},
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "either": {"anyOf": [brand_ref, nested_ref]},
                "or_none": {"anyOf": [{"type": "null"}, brand_ref, nested_ref]},
                "containers": {
                    "anyOf": [
                        {"type": "array", "items": {"type": "integer"}},
                        {"type": "object"},
                    ]
                },
            },
            "required": ["either", "or_none", "containers"],
        }
        check_schemas(actual, expected)

    def test_explicit_required(self):
        """An explicit required list in the class metadata is not overridden."""
        actual = ItemAdapter.get_json_schema(ExplicitRequiredItem)
        expected = {
            "required": ["bar"],
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "foo": {"type": "string"},
                "bar": {"type": "string", "default": "asdf"},
            },
        }
        check_schemas(actual, expected)

    def test_source_of_a_different_class(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reading the item class source can find the source of a different
        class, e.g. for classes that are renamed after their definition. Only
        the extraction of attribute docstrings should be affected."""

        @dataclass
        class RenamedItem:
            foo: str
            """Foo"""

        source = "@dataclass\nclass SomethingElse:\n    foo: str\n    '''Bar'''\n"
        with monkeypatch.context() as m:
            m.setattr(inspect, "getsource", lambda _obj: source)
            actual = ItemAdapter.get_json_schema(RenamedItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"foo": {"type": "string"}},
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @requires_attrs
    def test_attrs_unhandled_validator(self):
        """Validators that map to no JSON Schema keyword are ignored."""
        import attrs

        @attrs.define
        class TestAttrsItem:
            foo: str = attrs.field(validator=attrs.validators.instance_of(str))

        actual = ItemAdapter.get_json_schema(TestAttrsItem)
        expected = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"foo": {"type": "string"}},
            "required": ["foo"],
        }
        check_schemas(actual, expected)

    @requires_pydantic
    def test_pydantic_general_metadata_without_pattern(self):
        """General metadata that carries no pattern maps to no JSON Schema
        keyword."""

        class TestItem(pydantic.BaseModel):
            foo: float = pydantic.Field(allow_inf_nan=False)

        actual = ItemAdapter.get_json_schema(TestItem)
        expected = {
            "type": "object",
            "properties": {"foo": {"type": "number"}},
            "required": ["foo"],
        }
        check_schemas(actual, expected)


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        # Shared syntax.
        (r"^[A-Za-z]+$", r"^[A-Za-z]+$"),
        (r"\bD\d{2}\b", r"\bD\d{2}\b"),
        (r"a(b|c)?(?:d)(?=e)(?!f)\.\\", r"a(b|c)?(?:d)(?=e)(?!f)\.\\"),
        (r"\x41\u00e9\t\n", r"\x41\u00e9\t\n"),
        (r"(a)\1", r"(a)\1"),
        (r"[a\]b^-]", r"[a\]b^-]"),
        (r"[a.b]", r"[a.b]"),
        (r"(?<=a)b", r"(?<=a)b"),
        (r"(?<!a)b", r"(?<!a)b"),
        (r"a{2", r"a{2"),
        # Translated syntax.
        (r"\Aab\Z", r"^ab$"),
        (r"(?P<year>\d{4})", r"(\d{4})"),
        (r"a(?#comment)b", r"ab"),
        (r"(?s)a.b", r"a[\s\S]b"),
        (re.compile(r"a.b", re.DOTALL), r"a[\s\S]b"),
        ("(?x)a  # comment\n  \\d+", r"a\d+"),
        (re.compile("a  # comment\n  b", re.VERBOSE), r"ab"),
        (r"(?ax)a b", r"ab"),
        ("(?x)a # unterminated comment", "a"),
        # Python-only syntax.
        (r"\a", None),
        (r"[\a]", None),
        (r"\N{BULLET}", None),
        (r"\U0001F600", None),
        (r"(?P=name)", None),
        (r"(?i)a", None),
        (re.compile(r"a", re.IGNORECASE), None),
        (r"(?m)a", None),
        (r"(?i:a)", None),
        (r"(?>a)", None),
        (r"a*+", None),
        (r"a{2,3}+", None),
        # Syntax that both dialects accept with a different meaning.
        (r"[]]", None),
        (r"[^]]", None),
        (r"\0", None),
        (r"\01", None),
        (r"(?x)a{2, 3}", None),
        # Malformed patterns.
        ("\\", None),
        (r"[abc", None),
        (r"\x4", None),
        (r"(?#unterminated", None),
        (r"(?P<unterminated", None),
    ],
)
def test_json_schema_pattern(pattern: str | re.Pattern[str], expected: str | None) -> None:
    assert json_schema_pattern(pattern) == expected
