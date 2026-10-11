from __future__ import annotations

import typing
from collections.abc import Mapping
from types import MappingProxyType
from typing import Annotated, Any, NotRequired, Required, get_args, get_origin

from itemadapter._imports import (
    PydanticUndefined,
    PydanticV1Undefined,
    _get_type_hints,
    attr,
    pydantic,
    pydantic_v1,
    typing_extensions,
)


def _is_attrs_class(obj: Any) -> bool:
    if attr is None:
        return False
    return attr.has(obj)


def _is_pydantic_model(obj: Any) -> bool:
    if pydantic is None:
        return False
    return issubclass(obj, pydantic.BaseModel)


def _is_pydantic_v1_model(obj: Any) -> bool:
    if pydantic_v1 is None:
        return False
    return issubclass(obj, pydantic_v1.BaseModel)


def _get_pydantic_model_metadata(item_model: Any, field_name: str) -> MappingProxyType:
    metadata = {}
    field = item_model.model_fields[field_name]

    for attribute in [
        "alias_priority",
        "alias",
        "allow_inf_nan",
        "annotation",
        "coerce_numbers_to_str",
        "decimal_places",
        "default_factory",
        "deprecated",
        "description",
        "discriminator",
        "examples",
        "exclude",
        "fail_fast",
        "field_title_generator",
        "frozen",
        "ge",
        "gt",
        "init_var",
        "init",
        "json_schema_extra",
        "kw_only",
        "le",
        "lt",
        "max_digits",
        "max_length",
        "min_length",
        "multiple_of",
        "pattern",
        "repr",
        "serialization_alias",
        "strict",
        "title",
        "union_mode",
        "validate_default",
        "validation_alias",
    ]:
        if hasattr(field, attribute) and (value := getattr(field, attribute)) is not None:
            metadata[attribute] = value

    for attribute, default_value in [
        ("default", PydanticUndefined),
        ("metadata", []),
    ]:
        if hasattr(field, attribute) and (value := getattr(field, attribute)) != default_value:
            metadata[attribute] = value

    return MappingProxyType(metadata)


def _get_pydantic_v1_model_metadata(item_model: Any, field_name: str) -> MappingProxyType:
    metadata = {}
    field = item_model.__fields__[field_name]
    field_info = field.field_info

    for attribute in [
        "alias",
        "const",
        "description",
        "ge",
        "gt",
        "le",
        "lt",
        "max_items",
        "max_length",
        "min_items",
        "min_length",
        "multiple_of",
        "regex",
        "title",
    ]:
        value = getattr(field_info, attribute)
        if value is not None:
            metadata[attribute] = value

    if (value := field_info.default) not in (PydanticV1Undefined, Ellipsis):
        metadata["default"] = value

    if value := field.default_factory is not None:
        metadata["default_factory"] = value

    if not field_info.allow_mutation:
        metadata["allow_mutation"] = field_info.allow_mutation
    metadata.update(field_info.extra)

    return MappingProxyType(metadata)


_EMPTY_METADATA: MappingProxyType = MappingProxyType({})
_READ_ONLY = {getattr(typing, "ReadOnly", None), getattr(typing_extensions, "ReadOnly", None)}
_READ_ONLY.discard(None)


def _split_typed_dict_hint(type_hint: Any) -> tuple[MappingProxyType, bool | None]:
    """Return the metadata and the requiredness of a ``TypedDict`` field, given
    its type hint including extras.

    The metadata is the first mapping in the metadata of an
    :data:`~typing.Annotated` type hint. The requiredness is ``None`` unless
    the type hint is wrapped in :data:`~typing.Required` or
    :data:`~typing.NotRequired`.
    """
    metadata = None
    required = None
    while True:
        origin = get_origin(type_hint)
        if origin is Annotated:
            if metadata is None:
                metadata = next(
                    (entry for entry in type_hint.__metadata__ if isinstance(entry, Mapping)),
                    None,
                )
            type_hint = type_hint.__origin__
        # Required and NotRequired are missing from __required_keys__ and
        # __optional_keys__ when annotations are postponed, hence the need to
        # read requiredness from type hints as well.
        elif origin is Required or origin is NotRequired:
            required = origin is Required
            type_hint = get_args(type_hint)[0]
        elif origin in _READ_ONLY:
            type_hint = get_args(type_hint)[0]
        else:
            break
    return MappingProxyType(metadata) if metadata is not None else _EMPTY_METADATA, required


def _get_typed_dict_field_metadata(item_class: Any, field_name: str) -> MappingProxyType:
    type_hints = _get_type_hints(item_class, include_extras=True)
    if field_name not in type_hints:
        raise KeyError(f"{item_class.__name__} does not support field: {field_name}")
    return _split_typed_dict_hint(type_hints[field_name])[0]
