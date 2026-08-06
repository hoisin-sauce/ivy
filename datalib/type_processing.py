"""Utility module for dealing with type functionality not provided by typing or types.
"""
import types
import typing
from typing import Any, Mapping, Optional
from types import ModuleType, UnionType, GenericAlias
from collections.abc import Iterable
import datalib.db_utils as db_utils
import enum

def is_type(obj: Any) -> bool:
    """
    Checks if an object is a type
    Args:
        obj:
            The object to be checked
    Returns:
        Boolean indicating if the object is a type
    """
    return isinstance(obj, type)

def get_types_in_module(module: ModuleType) -> list[type]:
    """
    Returns a list of all classes/types defined in the module provided
    Args:
        module:
            The module to be checked
    Returns:
        A list of all classes/types defined in the module
    """
    defined_types: list[type] = []
    for i in dir(module):
        if not is_type(datatype := getattr(module, i)):
            continue

        if not datatype.__module__ == module.__name__:
            continue

        defined_types.append(datatype)

    return defined_types

def get_immediate_dependencies(class_type: type) -> set[type]:
    """
    Returns a set of all types that are attributes of provided class
    Args:
        class_type
            The class to be checked for dependencies
    Returns:
        A set of the discovered types
    Raises:
        NotImplementedError: If the type contains a value that cannot be resolved
    """
    # We handle enums by checking the type of their child elements
    # This is incase an enum points to a newly defined class and as such
    # That table needs to be declared first before we can point to it
    if issubclass(class_type, enum.Enum):
        return {type(v.value) for v in class_type._member_map_.values()}

    type_hints: Mapping[str, type | UnionType | GenericAlias] = \
        typing.get_type_hints(class_type)
    argument_types: Iterable[type | UnionType | GenericAlias] = \
        type_hints.values()
    try:
        return db_utils.flatten_to_set(map(resolve_type, argument_types))
    except NotImplementedError as e:
        raise ExceptionGroup(
            f"Exception occurred whilst processing "
            "{class_type.__name__} of type {type(class_type).__name__}", [e]
        )


# noinspection protected-member,unresolved-references
def resolve_type(datatype: typing.Union[types.UnionType, types.GenericAlias, type]) -> Iterable[type]:
    """
    Returns the types that compose the provided datatype, if simple the provided datatype is returned alone
    Args:
        datatype
            The datatype to be decomposed into its component types
    Returns:
        An iterable containing the types that compose the provided datatype.
    """
    meta_type = type(datatype)

    if meta_type ==  types.UnionType or meta_type == typing._UnionGenericAlias:
        datatype: types.UnionType | typing._UnionGenericAlias
        return db_utils.flatten_to_set(map(resolve_type, resolve_union_type(datatype)))

    if meta_type == types.GenericAlias:
        datatype: types.GenericAlias
        return db_utils.flatten_to_set(map(resolve_type, resolve_generic_alias(datatype)))

    datatype: type
    # TODO double check that enums are being adequately decomposed
    if meta_type == enum.EnumType:
        return (datatype,)

    if meta_type == type:
        return (datatype,)

    raise NotImplementedError(f"Type {meta_type} has not been implemented")

def resolve_union_type(class_type: types.UnionType) -> Iterable[type]:
    """
    Returns the types that are combined in a UnionType
    Args:
        class_type
            The type to be decomposed
    Returns:
        An iterable of the types that were in the UnionType
    """
    return typing.get_args(class_type)

def resolve_generic_alias(datatype: types.GenericAlias) -> Iterable[type]:
    """
    Returns the types that are combined in a GenericAlias
    Currently supported types:
        Iterable, Mapping
    Args:
        datatype:
            The type to be decomposed
    Returns:
        An iterable of the types that were in the GenericAlias
    Raises:
        NotImplementedError: If the type contains a value that cannot be resolved.
    """
    if issubclass(alias := typing.get_origin(datatype), Iterable):
        return typing.get_args(datatype)

    if issubclass(alias, Mapping):
        return typing.get_args(datatype)

    raise NotImplementedError(f"Type {alias.__name__} has not been implemented")

def create_annotated_datatype(name: str, datatypes: Iterable[type] | Mapping[
    str, type], module: Optional[str]=None) -> type:
    """
    Creates an annotated dummy datatype with annotations according to the
    provided datatypes and optional labels.
    Args:
        name
            Name of the dummy datatype
        datatypes
            Iterable of datatypes or Mapping of names to datatypes to be added to the annotated datatype
        module
            Optional module name for the class

    Returns:
        A dummy datatype with the provided annotations

        Example
            create_annotated_datatype("IntegerStringPair", [int, str])
                ->
            class IntegerStringPair:
                int: int
                str: str
    """

    class Alias:
        ...

    if isinstance(datatypes, Mapping):
        Alias.__annotations__ = {k: v for k, v in datatypes.items()}
    else:
        Alias.__annotations__ = {i: i for i in datatypes if
                                 isinstance(i, tuple)}
    Alias.__name__ = name

    if module is not None:
        Alias.__module__ = module

    return Alias


# noinspection type-hints
def get_union_type(datatypes: list[type]):
    """
    Returns a type which is the union of the types provided.
    Args:
        datatypes:
            The types to be unionised.
    Returns:
        A typing.Union object with all the required datatypes
    """
    if len(datatypes) == 1:
        return datatypes[0]

    base_type = typing.Union[datatypes[0], datatypes[1]]

    for datatype in datatypes[2:]:
        base_type = typing.Union[base_type, datatype]

    return base_type
