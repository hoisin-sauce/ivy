import enum
import types
import typing
from dataclasses import dataclass
from mimetypes import add_type
from typing import Type, Optional
from types import ModuleType
from collections.abc import Iterable
import const
import utils
import typeprocessing
import sys

class FailedDatabaseInitialisationError(Exception):
    ...

class ClassDependencyGraph:
    def __init__(self, modules: Iterable[ModuleType]) -> None:
        types_by_module: Iterable[Iterable[Type]] = list(map(typeprocessing.get_types_in_module, modules))
        self.types: set[Type] = utils.flatten_to_set(types_by_module)
        self.datatype_map: dict[Type, DataType] = dict()
        self._initialise_datatype_map()
        self._introduce_backwards_dependencies()
        self._build_order: list[type] = self._get_build_order()

    def get_datatype_instance(self, class_type: type) -> "DataType":
        """

        Args:
            class_type:

        Returns:

        """
        return self.datatype_map[class_type]

    def get_build_order(self) -> list[type]:
        """
        Fetches the order that the dependencies need to be created in the database
        Returns:
            A list in an order such that no class depends on a class declared after it
        """
        return self._build_order

    def _initialise_datatype_map(self) -> None:
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
    class_type: type
    dependencies: set[Type]
    remaining_dependencies: set[Type]
    depended_by: set[Type]

    @staticmethod
    def build_datatype_from_type(class_type: type) -> "DataType":
        dependencies: set[type] = typeprocessing.get_immediate_dependencies(class_type) - const.BASIC_TYPES
        datatype: DataType = DataType(class_type, dependencies, dependencies, set())
        return datatype

@dataclass
class Field:
    name: str
    datatype: type
    is_optional: bool = False

@dataclass
class ForeignKey:
    to: "Table"
    is_optional: bool = False

class PrimaryKey:
    ...

@dataclass
class Table:
    name: str
    fields: Iterable[Field | ForeignKey | PrimaryKey]


class TableStructure:
    def __init__(self, graph: ClassDependencyGraph):
        self.tables: list[Table] = list()
        self.enum_lookups: dict[str, dict] = dict()
        self.table_lookups: dict[type, Table] = dict()
        base_table_order = graph.get_build_order()
        for datatype in base_table_order:
            self.add_table(datatype)

    def add_table(self, datatype: type) -> Table:
        fields = typing.get_type_hints(datatype).items()
        direct_fields: list[Field | ForeignKey | PrimaryKey] = [PrimaryKey()]
        tables_after: list[Table] = list()

        name = datatype.__module__ + "__" + datatype.__name__ if datatype.__module__ != TableStructure.__module__ else datatype.__name__

        table = Table(
            name=name,
            fields=direct_fields
        )

        for field_name, datatype_ in fields:
            field: Optional[Field | ForeignKey]
            table_after: Optional[Table]
            field, table_after = self.get_field(field_name, datatype_, parent=table)

            if field:
                direct_fields.append(field)

            if table_after:
                tables_after.append(table_after)

        self.table_lookups[datatype] = table
        self.tables.append(table)

        self.tables.extend(tables_after)

        return table

    def get_field(self, field_name: str, field_type, parent: Table) -> tuple[Optional[Field | ForeignKey], Optional[Table]]:
        if field_type in const.BASIC_TYPES:
            return Field(name = field_name, datatype=field_type), None

        if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
            return self.get_enum_field(field_name, field_type), None

        if type(origin_type := typing.get_origin(field_type)) == type and \
                issubclass(origin_type, Iterable):
            return None, self.get_iter_field(field_name, field_type, parent)

        if origin_type in (types.UnionType, typing.Union):
            return self.get_union_field(field_name, field_type, parent)

        # We are at a simple custom class
        try:
            table_referenced = self.table_lookups[field_type]
        except Exception as e:
            print(self.table_lookups)
            print(self.table_lookups.keys())
            raise e
        return ForeignKey(table_referenced), None

    def get_union_field(self, field_name: str, field_type, parent: Table) -> tuple[Optional[Field | ForeignKey], Optional[Table]]:
        possible_types = typing.get_args(field_type)

        if const.NONE_TYPE in possible_types:
            possible_types = list(possible_types)
            possible_types.remove(const.NONE_TYPE)

            field_link, table = self.get_field(field_name, get_union_type(possible_types), parent)
            if field_link:
                field_link.is_optional = True

            return field_link, table

        class UnionAlias:
            union_member_number: int

        union_name = parent.name + "_" + field_name
        UnionAlias.__name__ = union_name + "__union_selector__"
        # errors
        table_reference = self.add_table(UnionAlias)

        number_mapping: dict[int, str] = dict()

        for i, datatype in enumerate(possible_types):
            cls = get_field_type(
                union_name + f"__union_member_{datatype.__name__}__",
                [datatype, UnionAlias])
            self.add_table(cls)
            number_mapping[i] = datatype.__name__

        return ForeignKey(table_reference), None

    def get_enum_field(self, field_name: str, field_type):
        # handle enum
        # push a new table to the creation queue

        class EnumAlias:
            member_name: str

        EnumAlias.__name__ = "__enum__" + field_name

        enum_table = self.add_table(EnumAlias)
        self.enum_lookups[field_name] = field_type._member_map_

        return ForeignKey(enum_table)

    def get_iter_field(self, field_name: str, field_type, parent: Table):
        # we need to create one table to store the inside of the iterable
        # we then need to create one table to store the link from the iterable
        # to the

        iterator_types: Iterable[type] = typing.get_args(field_type)

        class IterMemberAlias:
            ...

        IterMemberAlias.__annotations__ = {f"option_{i}": v for i, v in
                                           enumerate(iterator_types)}
        IterMemberAlias.__name__ = parent.name +  field_name + "__iter_inner__"

        table_to_reference = self.add_table(IterMemberAlias)

        many_to_many = Table(
            name=field_type.__module__ + "__iter_link__" + field_name,
            fields=[ForeignKey(parent), ForeignKey(table_to_reference)])

        return many_to_many

# TODO find better name
def get_field_type(name: str, datatypes: list[type]) -> type:
    class Alias:
        ...

    Alias.__annotations__ = {i.__name__: i  for i in datatypes}
    Alias.__name__ = name

    return Alias

def get_union_type(datatypes: list[type]):
    if len(datatypes) == 1:
        return datatypes[0]

    base_type = typing.Union[datatypes[0], datatypes[1]]

    for datatype in datatypes[2:]:
        base_type = typing.Union[base_type, datatype]

    return base_type
