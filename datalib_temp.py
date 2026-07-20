import types
import typing
from dataclasses import dataclass
from typing import Any, Type, Mapping, Self
from types import ModuleType, UnionType, GenericAlias
from collections.abc import Iterable
import utils
import enum

class Database:
    def __init__(self, modules: Iterable[ModuleType]) -> None:
        types_by_module: Iterable[Iterable[Type]] = list(map(get_types_in_module, modules))
        self.types = utils.flatten_to_set(types_by_module)
        self.datatype_map: dict[Type, DataType] = dict(map(DataType.build_datatype_from_type, self.types))
        self._introduce_backwards_dependencies()

    def _introduce_backwards_dependencies(self):
        for datatype, datatype_information in self.datatype_map.items():
            map(lambda x: self.datatype_map[x].depended_by.append(datatype), datatype_information.dependencies)

@dataclass
class DataType:
    class_type: type
    dependencies: list[type]
    remaining_dependencies: list[type]
    depended_by: list[type]

    @staticmethod
    def build_datatype_from_type(class_type: Type) -> (Type, 'DataType'):
        dependencies: list[Type] = list(get_immediate_dependencies(class_type))
        datatype: DataType = DataType(class_type, dependencies, dependencies, list())
        return class_type, datatype

def is_type(obj: Any):
    return isinstance(obj, type)

def get_types_in_module(module: ModuleType) -> list[Type]:
    return [_type for i in dir(module) if is_type(_type := getattr(module, i))]

def get_immediate_dependencies(class_type: Type) -> Iterable[Type]:
    # We handle enums by checking the type of their child elements
    # This is incase an enum points to a newly defined class and as such
    # That table needs to be declared first before we can point to it
    if issubclass(class_type, enum.Enum):
        return {type(v.value) for v in class_type._member_map_.values()}

    type_hints: Mapping[str, Type | UnionType | GenericAlias] = typing.get_type_hints(class_type)
    argument_types: Iterable[Type | UnionType | GenericAlias] = type_hints.values()
    return utils.flatten_to_set(map(resolve_type, argument_types))


def resolve_type(class_type: typing.Union[types.UnionType, types.GenericAlias, Type]) -> Iterable[Type]:
    match meta_type := type(class_type):

        case types.UnionType:
            return utils.flatten_to_set(map(resolve_type, resolve_union_type(class_type)))

        case types.GenericAlias:
            return utils.flatten_to_set(map(resolve_type, resolve_generic_alias(class_type)))

        case _:
            if meta_type == type:
                return (class_type,)
            raise NotImplementedError(f"Type {meta_type} has not been implemented")

def resolve_union_type(class_type: types.UnionType) -> Iterable[Type]:
    return typing.get_args(class_type)

def resolve_generic_alias(class_type: types.GenericAlias) -> Iterable[Type]:
    if isinstance(alias := typing.get_origin(class_type), Iterable):
        return typing.get_args(class_type)

    raise NotImplementedError(f"Type {alias} has not been implemented")
