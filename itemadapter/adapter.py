from __future__ import annotations

import ast
import dataclasses
import inspect
import operator
from abc import ABCMeta, abstractmethod
from collections import deque
from collections.abc import Iterable, Iterator, KeysView, Mapping, MutableMapping, Sequence
from collections.abc import Set as AbstractSet
from copy import copy
from enum import Enum
from textwrap import dedent
from types import MappingProxyType
from typing import (
    Any,
    Protocol,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    runtime_checkable,
)

try:
    from types import NoneType, UnionType  # pylint: disable=ungrouped-imports
except ImportError:  # Python < 3.10
    NoneType = type(None)  # type: ignore[misc]
    UnionType = type(Union)  # type: ignore[assignment,misc]

from itemadapter._imports import PydanticUndefined, PydanticV1Undefined, _scrapy_item_classes, attr
from itemadapter.utils import (
    _get_pydantic_model_metadata,
    _get_pydantic_v1_model_metadata,
    _is_attrs_class,
    _is_pydantic_model,
    _is_pydantic_v1_model,
)

__all__ = [
    "AdapterInterface",
    "AttrsAdapter",
    "DataclassAdapter",
    "DictAdapter",
    "ItemAdapter",
    "PydanticAdapter",
    "ScrapyItemAdapter",
]

_JSON_SCHEMA_SIMPLE_TYPE_MAPPING = {
    bool: "boolean",
    float: "number",
    int: "integer",
    NoneType: "null",
    str: "string",
}


@runtime_checkable
class ArrayProtocol(Protocol):
    def __iter__(self) -> Iterator[Any]: ...
    def __len__(self) -> int: ...
    def __contains__(self, item: Any) -> bool: ...


@runtime_checkable
class ObjectProtocol(Protocol):  # noqa: PLW1641
    def __getitem__(self, key: str) -> Any: ...
    def __iter__(self) -> Iterator[str]: ...
    def __len__(self) -> int: ...
    def __contains__(self, key: str) -> bool: ...
    def keys(self): ...
    def items(self): ...
    def values(self): ...
    def get(self, key: str, default: Any = ...): ...
    def __eq__(self, other): ...
    def __ne__(self, other): ...


def _is_json_schema_pattern(pattern: str) -> bool:
    # https://ecma-international.org/publications-and-standards/standards/ecma-262/
    #
    # Note: We allow word boundaries (\b, \B) in patterns even thought there is
    # a difference in behavior: in Python, they work with Unicode; in JSON
    # Schema, they only work with ASCII.
    unsupported = [
        "(?P<",  # named groups
        "(?<=",  # lookbehind
        "(?<!",  # negative lookbehind
        "(?>",  # atomic group
        "\\A",  # start of string
        "\\Z",  # end of string
        "(?i)",  # inline flags (case-insensitive, etc.)
        "(?m)",  # multiline
        "(?s)",  # dotall
        "(?x)",  # verbose
        "(?#",  # comments
    ]
    return not any(sub in pattern for sub in unsupported)


def _type_hint_to_json_schema_type(type_hint: Any) -> str | list[str] | None:
    if type_hint in _JSON_SCHEMA_SIMPLE_TYPE_MAPPING:
        return _JSON_SCHEMA_SIMPLE_TYPE_MAPPING[type_hint]
    return None


def _get_array_item_type(type_hint):
    args = get_args(type_hint)
    if not args:
        return Any
    if args[-1] is Ellipsis:
        args = args[:-1]
    unique_args = set(args)
    if len(unique_args) == 1:
        return next(iter(unique_args))
    return Union[tuple(unique_args)]


def _update_prop_from_pattern(prop: dict[str, Any], pattern: str) -> None:
    if _is_json_schema_pattern(pattern):
        prop.setdefault("pattern", pattern)


def _update_prop_from_union(prop: dict[str, Any], prop_type: Any, state: _JsonSchemaState) -> None:
    prop_types = set(get_args(prop_type))
    if int in prop_types and float in prop_types:
        prop_types.remove(int)
    simple_types = [
        _JSON_SCHEMA_SIMPLE_TYPE_MAPPING[t]
        for t in prop_types
        if t in _JSON_SCHEMA_SIMPLE_TYPE_MAPPING
    ]
    complex_types = [t for t in prop_types if t not in _JSON_SCHEMA_SIMPLE_TYPE_MAPPING]
    if not complex_types:
        prop.setdefault("type", simple_types)
        return
    new_any_of: list[dict[str, Any]] = []
    any_of = prop.setdefault("anyOf", new_any_of)
    if any_of is not new_any_of:
        return
    any_of.append({"type": simple_types if len(simple_types) > 1 else simple_types[0]})
    for complex_type in complex_types:
        complex_prop: dict[str, Any] = {}
        _update_prop_from_type(complex_prop, complex_type, state)
        any_of.append(complex_prop)


def _update_prop_from_origin(
    prop: dict[str, Any], origin: Any, prop_type: Any, state: _JsonSchemaState
) -> None:
    if isinstance(origin, type):
        if issubclass(origin, (Sequence, AbstractSet)):
            prop.setdefault("type", "array")
            if issubclass(origin, AbstractSet):
                prop.setdefault("uniqueItems", True)
            items = prop.setdefault("items", {})
            item_type = _get_array_item_type(prop_type)
            _update_prop_from_type(items, item_type, state)
            return
        if issubclass(origin, Mapping):
            prop.setdefault("type", "object")
            args = get_args(prop_type)
            if args:
                assert len(args) == 2
                value_type = args[1]
                props = prop.setdefault("additionalProperties", {})
                _update_prop_from_type(props, value_type, state)
            return
    if origin in (UnionType, Union):
        _update_prop_from_union(prop, prop_type, state)


def _update_prop_from_type(prop: dict[str, Any], prop_type: Any, state: _JsonSchemaState) -> None:
    if (origin := get_origin(prop_type)) is not None:
        _update_prop_from_origin(prop, origin, prop_type, state)
        return
    if isinstance(prop_type, type):
        if state.adapter.is_item_class(prop_type):
            if prop_type in state.containers:
                prop.setdefault("type", "object")
                return
            state.containers.add(prop_type)
            subschema = state.adapter.get_json_schema(
                prop_type,
                _state=state,
            )
            state.containers.remove(prop_type)
            for k, v in subschema.items():
                prop.setdefault(k, v)
            return
        if issubclass(prop_type, Enum):
            values = [item.value for item in prop_type]
            prop.setdefault("enum", values)
            value_types = tuple({type(v) for v in values})
            prop_type = value_types[0] if len(value_types) == 1 else Union[value_types]
            _update_prop_from_type(prop, prop_type, state)
            return
        if not issubclass(prop_type, str):
            if isinstance(prop_type, ObjectProtocol):
                prop.setdefault("type", "object")
                return
            if isinstance(prop_type, ArrayProtocol):
                prop.setdefault("type", "array")
                prop.setdefault("items", {})
                if issubclass(prop_type, AbstractSet):
                    prop.setdefault("uniqueItems", True)
                return
    json_schema_type = _type_hint_to_json_schema_type(prop_type)
    if json_schema_type is not None:
        prop.setdefault("type", json_schema_type)


def _setdefault_attribute_types_on_schema(
    schema: dict[str, Any], item_class: type, state: _JsonSchemaState
) -> None:
    props = schema.get("properties", {})
    attribute_type_hints = get_type_hints(item_class)
    for prop_name, prop in props.items():
        if prop_name not in attribute_type_hints:
            continue
        prop_type = attribute_type_hints[prop_name]
        _update_prop_from_type(prop, prop_type, state)


def _setdefault_attribute_docstrings_on_schema(schema: dict[str, Any], item_class: type) -> None:
    props = schema.get("properties", {})
    attribute_names = set(props)
    if not attribute_names:
        return
    try:
        source = inspect.getsource(item_class)
    except OSError:
        return
    tree = ast.parse(dedent(source))
    try:
        class_node = tree.body[0]
    except IndexError:  # pragma: no cover
        # This can be reproduced with the doctests of the README, but the
        # coverage data does not seem to include those.
        return
    assert isinstance(class_node, ast.ClassDef)
    for node in ast.iter_child_nodes(class_node):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            attr_name = node.targets[0].id
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            attr_name = node.target.id
        else:
            continue
        if attr_name not in attribute_names:
            continue
        next_idx = class_node.body.index(node) + 1
        if next_idx >= len(class_node.body):
            continue
        next_node = class_node.body[next_idx]
        if (
            isinstance(next_node, ast.Expr)
            and isinstance(next_node.value, ast.Constant)
            and isinstance(next_node.value.value, str)
        ):
            props[attr_name].setdefault("description", next_node.value.value)


class AdapterInterface(MutableMapping, metaclass=ABCMeta):
    """Abstract Base Class for adapters.

    An adapter that handles a specific type of item should inherit from this
    class and implement the abstract methods defined here, plus the
    abtract methods inherited from the MutableMapping base class.
    """

    def __init__(self, item: Any) -> None:
        self.item = item

    @classmethod
    @abstractmethod
    def is_item_class(cls, item_class: type) -> bool:
        """Return True if the adapter can handle the given item class, False otherwise."""
        raise NotImplementedError

    @classmethod
    def is_item(cls, item: Any) -> bool:
        """Return True if the adapter can handle the given item, False otherwise."""
        return cls.is_item_class(item.__class__)

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        return MappingProxyType({})

    @classmethod
    def get_field_names_from_class(cls, item_class: type) -> list[str] | None:
        """Return a list of fields defined for ``item_class``.
        If a class doesn't support fields, None is returned."""
        return None

    @classmethod
    def get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        item_class_meta = getattr(item_class, "__metadata__", {})
        schema = copy(item_class_meta.get("json_schema_extra", {}))
        schema.setdefault("type", "object")
        schema.setdefault("additionalProperties", False)
        fields_meta = {
            field_name: cls.get_field_meta_from_class(item_class, field_name)
            for field_name in cls.get_field_names_from_class(item_class) or ()
        }
        if not fields_meta:
            return schema
        schema["properties"] = {
            field_name: copy(field_meta.get("json_schema_extra", {}))
            for field_name, field_meta in fields_meta.items()
        }
        required = [
            field_name
            for field_name, field_data in schema["properties"].items()
            if "default" not in field_data
        ]
        if required:
            schema.setdefault("required", required)
        return schema

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        """Return metadata for the given field name, if available."""
        return self.get_field_meta_from_class(self.item.__class__, field_name)

    def field_names(self) -> KeysView:
        """Return a dynamic view of the item's field names."""
        return self.keys()  # type: ignore[return-value]


class _MixinAttrsDataclassAdapter:
    _fields_dict: dict
    item: Any

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        return self._fields_dict[field_name].metadata

    def field_names(self) -> KeysView:
        return KeysView(self._fields_dict)

    def __getitem__(self, field_name: str) -> Any:
        if field_name in self._fields_dict:
            return getattr(self.item, field_name)
        raise KeyError(field_name)

    def __setitem__(self, field_name: str, value: Any) -> None:
        if field_name in self._fields_dict:
            setattr(self.item, field_name, value)
        else:
            raise KeyError(f"{self.item.__class__.__name__} does not support field: {field_name}")

    def __delitem__(self, field_name: str) -> None:
        if field_name in self._fields_dict:
            try:
                if hasattr(self.item, field_name):
                    delattr(self.item, field_name)
                else:
                    raise AttributeError
            except AttributeError as ex:
                raise KeyError(field_name) from ex
        else:
            raise KeyError(f"{self.item.__class__.__name__} does not support field: {field_name}")

    def __iter__(self) -> Iterator:
        return iter(attr for attr in self._fields_dict if hasattr(self.item, attr))

    def __len__(self) -> int:
        return len(list(iter(self)))


class AttrsAdapter(_MixinAttrsDataclassAdapter, AdapterInterface):
    def __init__(self, item: Any) -> None:
        super().__init__(item)
        if attr is None:
            raise RuntimeError("attr module is not available")
        # store a reference to the item's fields to avoid O(n) lookups and O(n^2) traversals
        self._fields_dict = attr.fields_dict(self.item.__class__)

    @classmethod
    def is_item(cls, item: Any) -> bool:
        return _is_attrs_class(item) and not isinstance(item, type)

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return _is_attrs_class(item_class)

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        if attr is None:
            raise RuntimeError("attr module is not available")
        try:
            return attr.fields_dict(item_class)[field_name].metadata
        except KeyError as ex:
            raise KeyError(f"{item_class.__name__} does not support field: {field_name}") from ex

    @classmethod
    def get_field_names_from_class(cls, item_class: type) -> list[str] | None:
        if attr is None:
            raise RuntimeError("attr module is not available")
        return [a.name for a in attr.fields(item_class)]

    @classmethod
    def get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        item_class_meta = getattr(item_class, "__metadata__", {})
        schema = copy(item_class_meta.get("json_schema_extra", {}))
        schema.setdefault("type", "object")
        schema.setdefault("additionalProperties", False)
        fields = attr.fields(item_class)
        if not fields:
            return schema

        from attr import resolve_types

        resolve_types(item_class)  # Ensure field.type annotations are resolved

        schema["properties"] = {
            field.name: copy(field.metadata.get("json_schema_extra", {})) for field in fields
        }
        default_factory_fields: set[str] = set()
        for field in fields:
            prop = schema["properties"][field.name]
            cls._update_prop(prop, field, _state, default_factory_fields)
        required = [
            field_name
            for field_name, data in schema["properties"].items()
            if ("default" not in data and field_name not in default_factory_fields)
        ]
        if required:
            schema["required"] = required
        _setdefault_attribute_docstrings_on_schema(schema, item_class)
        return schema

    @classmethod
    def _update_prop(
        cls,
        prop: dict[str, Any],
        field: attr.Attribute,
        state: _JsonSchemaState,
        default_factory_fields: set[str],
    ) -> None:
        if isinstance(field.default, attr.Factory):
            default_factory_fields.add(field.name)
        elif field.default is not attr.NOTHING:
            prop.setdefault("default", field.default)
        _update_prop_from_type(prop, field.type, state)
        cls._update_prop_validation(prop, field)

    _NUMBER_VALIDATORS = {
        operator.ge: "minimum",
        operator.gt: "exclusiveMinimum",
        operator.le: "maximum",
        operator.lt: "exclusiveMaximum",
    }

    @classmethod
    def _update_prop_validation(
        cls,
        prop: dict[str, Any],
        field: attr.Attribute,
    ) -> None:
        if not field.validator:
            return
        if type(field.validator).__name__ == "_AndValidator":
            validators = field.validator._validators
        else:
            validators = [field.validator]
        for validator in validators:
            validator_type_name = type(validator).__name__
            if validator_type_name == "_NumberValidator":
                key = cls._NUMBER_VALIDATORS.get(validator.compare_func)
                if not key:  # pragma: no cover
                    continue
                prop.setdefault(key, validator.bound)
            elif validator_type_name == "_InValidator":
                prop.setdefault("enum", list(validator.options))
            elif validator_type_name == "_MinLengthValidator":
                key = "minLength" if field.type is str else "minItems"
                prop.setdefault(key, validator.min_length)
            elif validator_type_name == "_MaxLengthValidator":
                key = "maxLength" if field.type is str else "maxItems"
                prop.setdefault(key, validator.max_length)
            elif validator_type_name == "_MatchesReValidator":
                pattern_obj = getattr(validator, "pattern", None) or validator.regex
                _update_prop_from_pattern(prop, pattern_obj.pattern)


class DataclassAdapter(_MixinAttrsDataclassAdapter, AdapterInterface):
    def __init__(self, item: Any) -> None:
        super().__init__(item)
        # store a reference to the item's fields to avoid O(n) lookups and O(n^2) traversals
        self._fields_dict = {field.name: field for field in dataclasses.fields(self.item)}

    @classmethod
    def is_item(cls, item: Any) -> bool:
        return dataclasses.is_dataclass(item) and not isinstance(item, type)

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return dataclasses.is_dataclass(item_class)

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        for field in dataclasses.fields(item_class):
            if field.name == field_name:
                return field.metadata
        raise KeyError(f"{item_class.__name__} does not support field: {field_name}")

    @classmethod
    def get_field_names_from_class(cls, item_class: type) -> list[str] | None:
        return [a.name for a in dataclasses.fields(item_class)]

    @classmethod
    def get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        item_class_meta = getattr(item_class, "__metadata__", {})
        schema = copy(item_class_meta.get("json_schema_extra", {}))
        schema.setdefault("type", "object")
        schema.setdefault("additionalProperties", False)
        fields = dataclasses.fields(item_class)
        resolved_field_types = get_type_hints(item_class)
        default_factory_fields = set()
        if fields:
            schema["properties"] = {
                field.name: copy(field.metadata.get("json_schema_extra", {})) for field in fields
            }
            for field in fields:
                prop = schema["properties"][field.name]
                if field.default_factory is not dataclasses.MISSING:
                    default_factory_fields.add(field.name)
                elif field.default is not dataclasses.MISSING:
                    prop.setdefault("default", field.default)
                field_type = resolved_field_types.get(field.name)
                if field_type is not None:
                    _update_prop_from_type(prop, field_type, _state)
            required = [
                field_name
                for field_name, data in schema["properties"].items()
                if ("default" not in data and field_name not in default_factory_fields)
            ]
            if required:
                schema["required"] = required
        _setdefault_attribute_docstrings_on_schema(schema, item_class)
        return schema


class PydanticAdapter(AdapterInterface):
    item: Any

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return _is_pydantic_model(item_class) or _is_pydantic_v1_model(item_class)

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        try:
            try:
                return _get_pydantic_model_metadata(item_class, field_name)
            except AttributeError:
                return _get_pydantic_v1_model_metadata(item_class, field_name)
        except KeyError as ex:
            raise KeyError(f"{item_class.__name__} does not support field: {field_name}") from ex

    @classmethod
    def get_field_names_from_class(cls, item_class: type) -> list[str] | None:
        try:
            return list(item_class.model_fields.keys())  # type: ignore[attr-defined]
        except AttributeError:
            return list(item_class.__fields__.keys())  # type: ignore[attr-defined]

    @classmethod
    def get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        if _is_pydantic_model(item_class):
            return cls._get_json_schema(item_class, _state=_state)
        return cls._get_json_schema_v1(item_class, _state=_state)

    @classmethod
    def _get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        schema = copy(
            item_class.model_config.get("json_schema_extra", {})  # type: ignore[attr-defined]
        )
        extra = item_class.model_config.get("extra")  # type: ignore[attr-defined]
        schema.setdefault("type", "object")
        if extra == "forbid":
            schema.setdefault("additionalProperties", False)
        fields = {
            name: cls.get_field_meta_from_class(item_class, name)
            for name in cls.get_field_names_from_class(item_class) or ()
        }
        if not fields:
            return schema
        schema["properties"] = {
            name: copy(metadata.get("json_schema_extra", {})) for name, metadata in fields.items()
        }
        default_factory_fields: set[str] = set()
        for name, metadata in fields.items():
            prop = schema["properties"][name]
            cls._update_prop(prop, name, metadata, _state, default_factory_fields)
        required = [
            field_name
            for field_name, data in schema["properties"].items()
            if ("default" not in data and field_name not in default_factory_fields)
        ]
        if required:
            schema["required"] = required
        _setdefault_attribute_docstrings_on_schema(schema, item_class)
        return schema

    @classmethod
    def _update_prop(
        cls,
        prop: dict[str, Any],
        name: str,
        metadata: MappingProxyType,
        _state: _JsonSchemaState,
        default_factory_fields: set[str],
    ) -> None:
        if "default_factory" in metadata:
            default_factory_fields.add(name)
        elif "default" in metadata and metadata["default"] is not PydanticUndefined:
            prop.setdefault("default", metadata["default"])
        if "annotation" in metadata:
            field_type = metadata["annotation"]
            if field_type is not None:
                _update_prop_from_type(prop, field_type, _state)
        if "metadata" in metadata:
            cls._update_prop_validation(prop, metadata["metadata"], field_type)
        for metadata_key, json_schema_field in (
            ("description", "description"),
            ("examples", "examples"),
            ("title", "title"),
        ):
            if metadata_key in metadata:
                prop.setdefault(json_schema_field, metadata[metadata_key])
        if "deprecated" in metadata:
            prop.setdefault("deprecated", bool(metadata["deprecated"]))

    @classmethod
    def _update_prop_validation(
        cls,
        prop: dict[str, Any],
        metadata: Sequence[Any],
        field_type: type,
    ) -> None:
        for metadata_item in metadata:
            metadata_item_type = type(metadata_item).__name__
            if metadata_item_type == "_PydanticGeneralMetadata":
                if "pattern" in metadata_item.__dict__:
                    pattern = metadata_item.__dict__["pattern"]
                    _update_prop_from_pattern(prop, pattern)
            elif metadata_item_type == "MinLen":
                key = "minLength" if field_type is str else "minItems"
                prop.setdefault(key, metadata_item.min_length)
            elif metadata_item_type == "MaxLen":
                key = "maxLength" if field_type is str else "maxItems"
                prop.setdefault(key, metadata_item.max_length)
            else:
                for metadata_key, json_schema_field in (
                    ("ge", "minimum"),
                    ("gt", "exclusiveMinimum"),
                    ("le", "maximum"),
                    ("lt", "exclusiveMaximum"),
                ):
                    if metadata_item_type == metadata_key.capitalize():
                        prop.setdefault(json_schema_field, getattr(metadata_item, metadata_key))

    @classmethod
    def _get_json_schema_v1(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        schema = copy(
            getattr(item_class.Config, "schema_extra", {})  # type: ignore[attr-defined]
        )
        extra = getattr(item_class.Config, "extra", None)  # type: ignore[attr-defined]
        schema.setdefault("type", "object")
        if extra == "forbid":
            schema.setdefault("additionalProperties", False)
        fields = {
            name: cls.get_field_meta_from_class(item_class, name)
            for name in cls.get_field_names_from_class(item_class) or ()
        }
        if not fields:
            return schema
        schema["properties"] = {
            name: copy(metadata.get("json_schema_extra", {})) for name, metadata in fields.items()
        }
        default_factory_fields: set[str] = set()
        field_type_hints = get_type_hints(item_class)
        for name, metadata in fields.items():
            prop = schema["properties"][name]
            cls._update_prop_v1(
                prop, name, metadata, field_type_hints, default_factory_fields, _state
            )
        required = [
            field_name
            for field_name, data in schema["properties"].items()
            if ("default" not in data and field_name not in default_factory_fields)
        ]
        if required:
            schema["required"] = required
        _setdefault_attribute_docstrings_on_schema(schema, item_class)
        return schema

    @classmethod
    def _update_prop_v1(  # pylint: disable=too-many-positional-arguments,too-many-arguments
        cls,
        prop: dict[str, Any],
        name: str,
        metadata: Mapping[str, Any],
        field_type_hints: dict[str, Any],
        default_factory_fields: set[str],
        state: _JsonSchemaState,
    ) -> None:
        if "default_factory" in metadata:
            default_factory_fields.add(name)
        elif "default" in metadata and metadata["default"] not in (
            Ellipsis,
            PydanticV1Undefined,
        ):
            prop.setdefault("default", metadata["default"])
        field_type = field_type_hints[name]
        if field_type is not None:
            _update_prop_from_type(prop, field_type, state)
        for metadata_key, json_schema_field in (
            ("ge", "minimum"),
            ("gt", "exclusiveMinimum"),
            ("le", "maximum"),
            ("lt", "exclusiveMaximum"),
            ("description", "description"),
            ("examples", "examples"),
            ("title", "title"),
        ):
            if metadata_key in metadata:
                prop.setdefault(json_schema_field, metadata[metadata_key])
        for prefix in ("min", "max"):
            if f"{prefix}_length" in metadata:
                key = f"{prefix}Length" if field_type is str else f"{prefix}Items"
                prop.setdefault(key, metadata[f"{prefix}_length"])
            elif f"{prefix}_items" in metadata:
                prop.setdefault(f"{prefix}Items", metadata[f"{prefix}_items"])
        for metadata_key in ("pattern", "regex"):
            if metadata_key in metadata:
                pattern = metadata[metadata_key]
                _update_prop_from_pattern(prop, pattern)
                break
        if "deprecated" in metadata:
            prop.setdefault("deprecated", bool(metadata["deprecated"]))

    def field_names(self) -> KeysView:
        try:
            return KeysView(self.item.__class__.model_fields)
        except AttributeError:
            return KeysView(self.item.__fields__)

    def __getitem__(self, field_name: str) -> Any:
        try:
            self.item.__class__.model_fields  # noqa: B018
        except AttributeError:
            if field_name in self.item.__fields__:
                return getattr(self.item, field_name)
        else:
            if field_name in self.item.__class__.model_fields:
                return getattr(self.item, field_name)
        raise KeyError(field_name)

    def __setitem__(self, field_name: str, value: Any) -> None:
        try:
            self.item.__class__.model_fields  # noqa: B018
        except AttributeError:
            if field_name in self.item.__fields__:
                setattr(self.item, field_name, value)
                return
        else:
            if field_name in self.item.__class__.model_fields:
                setattr(self.item, field_name, value)
                return
        raise KeyError(f"{self.item.__class__.__name__} does not support field: {field_name}")

    def __delitem__(self, field_name: str) -> None:
        try:
            self.item.__class__.model_fields  # noqa: B018
        except AttributeError as ex:
            if field_name in self.item.__fields__:
                try:
                    if hasattr(self.item, field_name):
                        delattr(self.item, field_name)
                        return
                    raise AttributeError from ex
                except AttributeError as ex2:
                    raise KeyError(field_name) from ex2
        else:
            if field_name in self.item.__class__.model_fields:
                try:
                    if hasattr(self.item, field_name):
                        delattr(self.item, field_name)
                        return
                    raise AttributeError
                except AttributeError as ex:
                    raise KeyError(field_name) from ex
        raise KeyError(f"{self.item.__class__.__name__} does not support field: {field_name}")

    def __iter__(self) -> Iterator:
        try:
            return iter(
                attr for attr in self.item.__class__.model_fields if hasattr(self.item, attr)
            )
        except AttributeError:
            return iter(attr for attr in self.item.__fields__ if hasattr(self.item, attr))

    def __len__(self) -> int:
        return len(list(iter(self)))


class _MixinDictScrapyItemAdapter:
    _fields_dict: dict
    item: Any

    def __getitem__(self, field_name: str) -> Any:
        return self.item[field_name]

    def __setitem__(self, field_name: str, value: Any) -> None:
        self.item[field_name] = value

    def __delitem__(self, field_name: str) -> None:
        del self.item[field_name]

    def __iter__(self) -> Iterator:
        return iter(self.item)

    def __len__(self) -> int:
        return len(self.item)


class DictAdapter(_MixinDictScrapyItemAdapter, AdapterInterface):
    @classmethod
    def is_item(cls, item: Any) -> bool:
        return isinstance(item, dict)

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return issubclass(item_class, dict)

    @classmethod
    def get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        return {"type": "object"}

    def field_names(self) -> KeysView:
        return KeysView(self.item)


class ScrapyItemAdapter(_MixinDictScrapyItemAdapter, AdapterInterface):
    @classmethod
    def is_item(cls, item: Any) -> bool:
        return isinstance(item, _scrapy_item_classes)

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return issubclass(item_class, _scrapy_item_classes)

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        return MappingProxyType(item_class.fields[field_name])  # type: ignore[attr-defined]

    @classmethod
    def get_field_names_from_class(cls, item_class: type) -> list[str] | None:
        return list(item_class.fields.keys())  # type: ignore[attr-defined]

    @classmethod
    def get_json_schema(cls, item_class: type, *, _state: _JsonSchemaState) -> dict[str, Any]:
        schema = super().get_json_schema(item_class, _state=_state)
        _setdefault_attribute_types_on_schema(schema, item_class, _state)
        _setdefault_attribute_docstrings_on_schema(schema, item_class)
        return schema

    def field_names(self) -> KeysView:
        return KeysView(self.item.fields)


@dataclasses.dataclass
class _JsonSchemaState:
    adapter: type[ItemAdapter]
    containers: set[type] = dataclasses.field(default_factory=set)


class ItemAdapter(MutableMapping):
    """Wrapper class to interact with data container objects. It provides a common interface
    to extract and set data without having to take the object's type into account.
    """

    ADAPTER_CLASSES: Iterable[type[AdapterInterface]] = deque(
        [
            ScrapyItemAdapter,
            DictAdapter,
            DataclassAdapter,
            AttrsAdapter,
            PydanticAdapter,
        ]
    )

    def __init__(self, item: Any) -> None:
        for cls in self.ADAPTER_CLASSES:
            if cls.is_item(item):
                self.adapter = cls(item)
                break
        else:
            raise TypeError(f"No adapter found for objects of type: {type(item)} ({item})")

    @classmethod
    def is_item(cls, item: Any) -> bool:
        return any(adapter_class.is_item(item) for adapter_class in cls.ADAPTER_CLASSES)

    @classmethod
    def is_item_class(cls, item_class: type) -> bool:
        return any(
            adapter_class.is_item_class(item_class) for adapter_class in cls.ADAPTER_CLASSES
        )

    @classmethod
    def _get_adapter_class(cls, item_class: type) -> type[AdapterInterface]:
        for adapter_class in cls.ADAPTER_CLASSES:
            if adapter_class.is_item_class(item_class):
                return adapter_class
        raise TypeError(f"{item_class} is not a valid item class")

    @classmethod
    def get_field_meta_from_class(cls, item_class: type, field_name: str) -> MappingProxyType:
        adapter_class = cls._get_adapter_class(item_class)
        return adapter_class.get_field_meta_from_class(item_class, field_name)

    @classmethod
    def get_field_names_from_class(cls, item_class: type) -> list[str] | None:
        adapter_class = cls._get_adapter_class(item_class)
        return adapter_class.get_field_names_from_class(item_class)

    @classmethod
    def get_json_schema(
        cls, item_class: type, *, _state: _JsonSchemaState | None = None
    ) -> dict[str, Any]:
        _state = _state or _JsonSchemaState(adapter=cls, containers={item_class})
        adapter_class = cls._get_adapter_class(item_class)
        return adapter_class.get_json_schema(item_class, _state=_state)

    @property
    def item(self) -> Any:
        return self.adapter.item

    def __repr__(self) -> str:
        values = ", ".join([f"{key}={value!r}" for key, value in self.items()])
        return f"<{self.__class__.__name__} for {self.item.__class__.__name__}({values})>"

    def __getitem__(self, field_name: str) -> Any:
        return self.adapter.__getitem__(field_name)

    def __setitem__(self, field_name: str, value: Any) -> None:
        self.adapter.__setitem__(field_name, value)

    def __delitem__(self, field_name: str) -> None:
        self.adapter.__delitem__(field_name)

    def __iter__(self) -> Iterator:
        return self.adapter.__iter__()

    def __len__(self) -> int:
        return self.adapter.__len__()

    def get_field_meta(self, field_name: str) -> MappingProxyType:
        """Return metadata for the given field name."""
        return self.adapter.get_field_meta(field_name)

    def field_names(self) -> KeysView:
        """Return read-only key view with the names of all the defined fields for the item."""
        return self.adapter.field_names()

    def asdict(self) -> dict:
        """Return a dict object with the contents of the adapter. This works slightly different
        than calling `dict(adapter)`: it's applied recursively to nested items (if there are any).
        """
        return {key: self._asdict(value) for key, value in self.items()}

    @classmethod
    def _asdict(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {key: cls._asdict(value) for key, value in obj.items()}
        if isinstance(obj, (list, set, tuple)):
            return obj.__class__(cls._asdict(x) for x in obj)
        if isinstance(obj, cls):
            return obj.asdict()
        if cls.is_item(obj):
            return cls(obj).asdict()
        return obj
