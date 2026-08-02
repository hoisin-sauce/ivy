"""Database library base on class module structure in provided modules.
"""
import enum
import types
import typing
from dataclasses import dataclass
from typing import Type, Optional
from types import ModuleType
from collections.abc import Iterable
import const
import utils
import typeprocessing

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
        types_by_module: Iterable[Iterable[type]] = list(map(typeprocessing.get_types_in_module, modules))
        self.types: set[type] = utils.flatten_to_set(types_by_module)
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


@dataclass
class DataType:
    """
    Stores additional metadata about a type and its interactions with other types
    """
    class_type: type
    dependencies: set[Type]
    remaining_dependencies: set[Type]
    depended_by: set[Type]

    @staticmethod
    def build_datatype_from_type(class_type: type) -> "DataType":
        """
        Examines a type to find its dependencies and builds a metatype from them
        Args:
            class_type:
                The type to find dependencies for
        Returns:
            DataType object initialised with the dependencies
            and remaining dependencies set for the type. It is much simpler
            to add the types that it is depended on by once all datatypes have
            been built so this is done at another point.
        """
        dependencies: set[type] = typeprocessing.get_immediate_dependencies(class_type) - const.BASIC_TYPES
        datatype: DataType = DataType(class_type, dependencies, dependencies, set())
        return datatype

@dataclass
class Field:
    """
    Represents a field of a table
    """
    name: str
    datatype: type
    is_optional: bool = False

@dataclass
class ForeignKey:
    """
    Represents a foreign key to another table
    """
    to: "Table"
    is_optional: bool = False

class PrimaryKey:
    """
    Represents a primary key of a table
    """

class IterableField:
    """
    Indicates that there is an iterable link in the table
    As not obvious if the field doesn't exist
    """
    name: str

@dataclass
class Table:
    """
    Holds information about a table
    """
    name: str
    fields: list[Field | ForeignKey | PrimaryKey | IterableField]


class TableStructure:
    """
    Creates a module of the table structure based on the required order of
    tables provided by ClassDependencyGraph object supplied to it
    """
    def __init__(self, graph: ClassDependencyGraph):
        self.tables: list[Table] = list()
        self.enum_lookups: dict[str, dict] = dict()
        self.table_lookups: dict[type, Table] = dict()
        base_table_order = graph.get_build_order()
        for datatype in base_table_order:
            self.add_table(datatype)

    def add_table(self, datatype: type) -> Table:
        """
        Add a table to the data structure representing the provided datatype
        Args:
            datatype:
                the datatype to be added to the structure
        Returns:
            A reference to the object storing the metadata about the table
        """
        fields = typing.get_type_hints(datatype).items()
        tables_after: list[Table] = list()

        # Name the table whilst trying to avoid adding this modules name to it
        name = datatype.__module__ + "__" + datatype.__name__ if datatype.__module__ != TableStructure.__module__ else datatype.__name__

        table = Table(
            name=name,
            fields=[PrimaryKey()]
        )

        # Update table the required fields, making use of recursion to add
        # References from tables used to normalise more complex typehints
        # In before the table is added itself
        for field_name, datatype_ in fields:
            field: ForeignKey| Field | IterableField
            table_after: Optional[Table]
            field, table_after = self.get_field(field_name, datatype_, parent=table)

            if field:
                table.fields.append(field)

            if table_after:
                tables_after.append(table_after)

        self.table_lookups[datatype] = table
        self.tables.append(table)

        # Many-to-Many resolving fields need to reference the database itself
        # As such they should be added in afterwards
        self.tables.extend(tables_after)

        return table

    def get_field(self, field_name: str, field_type:type, parent: Table) -> tuple[Field | ForeignKey | IterableField, Optional[Table]]:
        """
        Fetches the field object to be added to the table. Creates an object if
        not necessary.
        Args:
            field_name
                The name of the field to be added. Will not be the same as the
                actual field in the table as formatting will be applied to
                disambiguate between modules and fields
            field_type
                The datatype of the field to be added.
            parent
                The parent table that the field will be added to. This allows
                for the creation of tables which resolve many-to-many relations

        Returns:
            A tuple containing:

            An object representing the type of field that needs to be added to
            the database.

            An optional table argument which represents a table that many need
            to be added after the parent table is initialised to allow for
            many-to-many relations to be resolved properly
        """
        # A simple field
        if field_type in const.BASIC_TYPES:
            return Field(name = field_name, datatype=field_type), None

        # A field which can only express one of a few fixed values
        if isinstance(field_type, type) and issubclass(field_type, enum.Enum):
            return self.get_enum_field(field_name, field_type), None

        # A field which represents an iterable object
        # noinspection bad-argument-type
        if type(origin_type := typing.get_origin(field_type)) == type and \
                issubclass(origin_type, Iterable):
            field_type: Iterable
            return self.get_iter_field(field_name, field_type, parent)

        # A field which when represented in code could be one of many types
        if origin_type in (types.UnionType, typing.Union):
            return self.get_union_field(field_name, field_type, parent)

        # A field which represents another class
        table_referenced = self.table_lookups[field_type]
        return ForeignKey(table_referenced), None

    def get_union_field(self, field_name: str, field_type, parent: Table) -> tuple[Field | ForeignKey | IterableField, Optional[Table]]:
        """
        Handles creating a field for a type which is a Union of multiple types
        Args:
            field_name
                The name of the field to be added.
            field_type:
                The datatype of the field to be added.
            parent:
                The parent table that the field will be added to.
        Returns:

        """
        possible_types = typing.get_args(field_type)

        # TODO refactor into separate function for readability
        # If the field contains a NoneType value then it is optional
        # We need to return the resolved inner field with the is_optional flag
        # Set to true
        if const.NONE_TYPE in possible_types:
            possible_types = list(possible_types)
            possible_types.remove(const.NONE_TYPE)

            field_link, table = self.get_field(field_name, get_union_type(possible_types), parent)
            if field_link:
                field_link.is_optional = True

            return field_link, table

        # Class used to create a table to link to by all the possible types
        class UnionAlias:
            union_member_number: int

        # Set the name of the type to allow for the table to be named by the
        # add_table method
        union_name = parent.name + "_" + field_name
        UnionAlias.__name__ = union_name + "__union_selector__"
        table_reference = self.add_table(UnionAlias)

        # Unused - may be necessary
        # Records the mapping of table numbers to their names
        number_mapping: dict[int, str] = dict()

        for i, datatype in enumerate(possible_types):
            cls = create_annotated_datatype(
                union_name + f"__union_member_{datatype.__name__}__",
                [datatype, UnionAlias])
            self.add_table(cls)
            number_mapping[i] = datatype.__name__

        # TODO store number mapping somewhere appropriate
        return ForeignKey(table_reference), None

    def get_enum_field(self, field_name: str, field_type) -> ForeignKey:
        """
        Handles creating a field for a type which is an Enum of multiple types
        Args:
            field_name
                The name of the field to be added.
            field_type
                The type of the data in field to be added.

        Returns:
            A foreign key to the table created to resolve the dependencies in the enum
        """
        # handle enum
        # push a new table to the creation queue

        class EnumAlias:
            member_name: str

        EnumAlias.__name__ = "__enum__" + field_name

        enum_table = self.add_table(EnumAlias)
        # noinspection protected-member
        self.enum_lookups[field_name] = field_type._member_map_

        return ForeignKey(enum_table)

    def get_iter_field(self, field_name: str, field_type:Iterable, parent: Table) -> tuple[IterableField, Table]:
        """
        Handles creating a field for a type which is an iterable that can
        contain multiple values (handles maps intrinsically)
        Args:
            field_name
                The name of the field to be added.
            field_type
                The iterable datatype to be processed.
            parent:
                The parent table the field is going to be added to.
        Returns:

        """
        # we need to create one table to store the inside of the iterable
        # we then need to create one table to store the link from the iterable
        # to the

        iterator_types: Iterable[type] = typing.get_args(field_type)

        class IterMemberAlias:
            ...

        # Set the provided classes that we see to a set of types for each
        # Datatype the tuple of the iterable stores
        IterMemberAlias.__annotations__ = {f"option_{i}": v for i, v in
                                           enumerate(iterator_types)}
        IterMemberAlias.__name__ = parent.name +  field_name + "__iter_inner__"

        table_to_reference = self.add_table(IterMemberAlias)

        many_to_many = Table(
            name=field_type.__module__ + "__iter_link__" + field_name,
            fields=[ForeignKey(parent), ForeignKey(table_to_reference)])

        return IterableField(field_name), many_to_many

def create_annotated_datatype(name: str, datatypes: Iterable[type]) -> type:
    """
    Creates an annotated dummy datatype with annotations according to the
    provided datatypes.
    Args:
        name
            Name of the dummy datatype
        datatypes
            Iterable of datatypes to be added to the annotated datatype

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

    Alias.__annotations__ = {i.__name__: i  for i in datatypes}
    Alias.__name__ = name

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
