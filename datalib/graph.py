from typing import Type
from types import ModuleType
from collections.abc import Iterable
import datalib.db_utils as db_utils
from datalib import type_processing
from datalib.datatypes import DataType

class FailedDatabaseInitialisationError(Exception):
    """
    Indicates that a database could not be initialised
    """
    ...


class ClassDependencyGraph:
    """
    Takes in an iterable of modules and works out that tables must be created
    in to create a database that models the class structure inside the modules
    """
    def __init__(self, modules: Iterable[ModuleType]) -> None:
        types_by_module: Iterable[Iterable[type]] = list(map(
            type_processing.get_types_in_module, modules))
        self.types: set[type] = db_utils.flatten_to_set(types_by_module)
        self.datatype_map: dict[type, DataType] = dict()
        self._initialise_datatype_map()
        self._introduce_backwards_dependencies()
        self._build_order: list[type] = self._get_build_order()

    def get_build_order(self) -> list[type]:
        """
        Fetches the order that the dependencies need to be created in the database
        Returns:
            A list in an order such that no class depends on a class declared after it
        """
        return self._build_order

    def _initialise_datatype_map(self) -> None:
        """
        Initialises the datatype_map dictionary mapping the separate datatypes
        to type encapsulating their dependencies and what depends on them,
        forming a node in a graph with arrows pointing to and away from it
        """
        unresolved_types: list[Type] = list(self.types)

        while unresolved_types:
            class_type = unresolved_types.pop(0)
            datatype: DataType = DataType.build_datatype_from_type(class_type)

            # update structure with any new types found
            new_types = datatype.dependencies - self.types
            self.types = self.types.union(new_types)
            for _type in new_types:
                unresolved_types.append(_type)

            self.datatype_map[class_type] = datatype

    def _introduce_backwards_dependencies(self) -> None:
        """
        Goes through all types added and informs all of its dependencies that it depends on them
        """
        for datatype, datatype_information in self.datatype_map.items():
            for dependency in datatype_information.dependencies:
                self.datatype_map[dependency].depended_by.add(datatype)

    def _get_build_order(self) -> list[Type]:
        """
        Calculates the required build order from a state where the dependencies
        and depended on values are set within the object
        TODO maybe refactor so that this can be run multiple times, however not feasible in general
        Returns:
            A list returning the build order ensures that no item will depend on
            items after it.
        Raises:
            FailedDatabaseInitialisationError
                If the graph is circular
        """
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