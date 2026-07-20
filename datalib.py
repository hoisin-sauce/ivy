from dataclasses import dataclass
from typing import Type
from types import ModuleType
from collections.abc import Iterable
import const
import utils
import typeprocessing

class FailedDatabaseInitialisationError(Exception):
    ...

class Database:
    def __init__(self, modules: Iterable[ModuleType]) -> None:
        types_by_module: Iterable[Iterable[Type]] = list(map(typeprocessing.get_types_in_module, modules))
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
            for dependency in datatype_information.dependencies:
                self.datatype_map[dependency].depended_by.add(datatype)

    def get_build_order(self) -> list[Type]:
        completable: list[Type] = [i for i in self.types if not self.datatype_map[i].remaining_dependencies]
        build_order: list[Type] = list()
        while completable:
            processing: Type = completable.pop(0)

            build_order.append(processing)

            for class_type in self.datatype_map[processing].depended_by:
                self.datatype_map[class_type].remaining_dependencies -= {
                    processing}
                if not self.datatype_map[class_type].remaining_dependencies:
                    completable.append(class_type)

        if uninitialised := self.types - set(build_order):
            failed_initialised_cause = {i: self.datatype_map[i].remaining_dependencies for i in uninitialised}
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
        dependencies: set[Type] = typeprocessing.get_immediate_dependencies(class_type) - const.BASIC_TYPES
        datatype: DataType = DataType(class_type, dependencies, dependencies, set())
        return datatype
