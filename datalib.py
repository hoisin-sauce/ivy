import types
import typing
from dataclasses import dataclass
from typing import Any, Type, Mapping, Self
from types import ModuleType, UnionType, GenericAlias
from collections.abc import Iterable
import const
import utils
import enum

class FailedDatabaseInitialisationError(Exception):
    ...

class Database:
    def __init__(self, modules: Iterable[ModuleType]) -> None:
        types_by_module: Iterable[Iterable[Type]] = list(map(get_types_in_module, modules))
        self.types: set[Type] = utils.flatten_to_set(types_by_module)
        self.datatype_map: dict[Type, DataType] = dict()
        self._initialise_datatype_map()
        self._introduce_backwards_dependencies()

    def _initialise_datatype_map(self) -> None:
        unresolved_types: list[Type] = list(self.types)

        while unresolved_types:
            class_type = unresolved_types.pop(0)
            datatype: DataType = DataType.build_datatype_from_type(class_type)

            # update structure with any new types found
            new_types = datatype.dependencies - self.types
            self.types = self.types.union(new_types)
            map(lambda x:unresolved_types.append(x), new_types)

            self.datatype_map[class_type] = datatype

    def _introduce_backwards_dependencies(self) -> None:
        for datatype, datatype_information in self.datatype_map.items():
            map(lambda x: self.datatype_map[x].depended_by.add(datatype), datatype_information.dependencies)

    def get_build_order(self) -> list[Type]:
        completable: list[Type] = [i for i in self.types if not self.datatype_map[i].remaining_dependencies]
        build_order: list[Type] = list()
        while completable:
            processing: Type = completable.pop(0)

            build_order.append(processing)

            for class_type in self.datatype_map[processing].depended_by:
                self.datatype_map[class_type].remaining_dependencies -= processing
                if not self.datatype_map[class_type].remaining_dependencies:
                    completable.append(class_type)

        if uninitialised := set(build_order) - self.types:
            failed_initialised_cause = {self.datatype_map[i].remaining_dependencies for i in uninitialised}
            raise FailedDatabaseInitialisationError(f"Classes {uninitialised} could not be initialised due to {failed_initialised_cause} still remaining as dependencies")

        return build_order


@dataclass
class DataType:
    class_type: Type
    dependencies: set[Type]
    remaining_dependencies: set[Type]
    depended_by: set[Type]

    @staticmethod
    def build_datatype_from_type(class_type: Type) -> "DataType":
        dependencies: set[Type] = get_immediate_dependencies(class_type) - const.BASIC_TYPES
        datatype: DataType = DataType(class_type, dependencies, dependencies, set())
        return datatype

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
