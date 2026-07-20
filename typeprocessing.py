import types
import typing
from typing import Any, Type, Mapping
from types import ModuleType, UnionType, GenericAlias
from collections.abc import Iterable
import utils
import enum

def is_type(obj: Any):
    return isinstance(obj, type)

def get_types_in_module(module: ModuleType) -> list[Type]:
    return [_type for i in dir(module) if is_type(_type := getattr(module, i))]

def get_immediate_dependencies(class_type: Type) -> set[Type]:
    # We handle enums by checking the type of their child elements
    # This is incase an enum points to a newly defined class and as such
    # That table needs to be declared first before we can point to it
    if issubclass(class_type, enum.Enum):
        return {type(v.value) for v in class_type._member_map_.values()}

    type_hints: Mapping[str, Type | UnionType | GenericAlias] = typing.get_type_hints(class_type)
    argument_types: Iterable[Type | UnionType | GenericAlias] = type_hints.values()
    try:
        return utils.flatten_to_set(map(resolve_type, argument_types))
    except NotImplementedError as e:
        raise ExceptionGroup(f"Exception occured whilst processing {class_type} of type {type(class_type)}", [e])


def resolve_type(class_type: typing.Union[types.UnionType, types.GenericAlias, Type, type]) -> Iterable[Type]:
    match meta_type := type(class_type):

        case types.UnionType | typing._UnionGenericAlias:
            return utils.flatten_to_set(map(resolve_type, resolve_union_type(class_type)))

        case types.GenericAlias:
            return utils.flatten_to_set(map(resolve_type, resolve_generic_alias(class_type)))

        case enum.EnumType:
            return (class_type,)

        case _:
            if meta_type == type:
                return (class_type,)
            raise NotImplementedError(f"Type {meta_type} has not been implemented")

def resolve_union_type(class_type: types.UnionType) -> Iterable[Type]:
    return typing.get_args(class_type)

def resolve_generic_alias(class_type: types.GenericAlias) -> Iterable[Type]:
    if issubclass(alias := typing.get_origin(class_type), Iterable):
        return typing.get_args(class_type)

    if issubclass(alias, Mapping):
        return typing.get_args(class_type)

    raise NotImplementedError(f"Type {alias} has not been implemented")