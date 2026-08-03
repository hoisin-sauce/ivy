"""Database library base on class module structure in provided modules.
"""
import enum
import types
import typing
from typing import Optional
from collections.abc import Iterable
import datalib.const as const
from datalib import type_processing
from datalib.graph import ClassDependencyGraph
from datalib.datatypes import Table, PrimaryKey, ForeignKey, Field, IterableField, \
    TableField
from datalib.naming import Namer

class TableStructure:
    """
    Creates a module of the table structure based on the required order of
    tables provided by ClassDependencyGraph object supplied to it
    """

    def __init__(self, graph: ClassDependencyGraph, namer: Namer):
        self.tables: list[Table] = list()
        self.enum_lookups: dict[str, dict] = dict()
        self.table_lookups: dict[type, Table] = dict()
        self.namer = namer
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
        if datatype.__module__ != TableStructure.__module__:
            name = self.namer.name_table_with_module(datatype)
        else:
            name = self.namer.name_table_without_module(datatype)

        table = Table(
            name=name,
            fields=[PrimaryKey()]
        )

        # Update table the required fields, making use of recursion to add
        # References from tables used to normalise more complex typehints
        # In before the table is added itself
        for field_name, datatype_ in fields:
            field: TableField
            table_after: Optional[Table]
            field, table_after = self.get_field(field_name, datatype_,
                                                parent=table)

            assert not isinstance(field,
                                  PrimaryKey), "Get field should not return a PrimaryKey"

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

    def get_field(self, field_name: str, field_type: type, parent: Table) -> \
        tuple[TableField, Optional[Table]]:
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
            return Field(name=field_name, datatype=field_type), None

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

    def get_union_field(self, field_name: str, field_type, parent: Table) -> \
        tuple[TableField, Optional[Table]]:
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

        # If the field contains a NoneType value then it is optional
        # We need to return the resolved inner field with the is_optional flag
        # Set to true
        if const.NONE_TYPE in possible_types:
            return self.get_optional_field(field_name, possible_types, parent)

        # Set the name of the type to allow for the table to be named by the
        # add_table method
        union_alias_attributes = {"union_member_number": int}
        union_alias_name = self.namer.name_union_selector(parent, field_name)

        union_alias = type_processing.create_annotated_datatype(union_alias_name,
                                                                union_alias_attributes)

        table_reference = self.add_table(union_alias)

        # Unused - may be necessary
        # Records the mapping of table numbers to their names
        number_mapping: dict[int, str] = dict()

        for i, datatype in enumerate(possible_types):
            cls = type_processing.create_annotated_datatype(
                self.namer.name_union_member(parent, field_name, datatype),
                [datatype, union_alias])
            self.add_table(cls)
            number_mapping[i] = datatype.__name__

        # TODO store number mapping somewhere appropriate
        return ForeignKey(table_reference), None

    def get_optional_field(self, field_name: str, possible_types: Iterable[type], parent: Table) -> tuple[TableField, Optional[Table]]:
        possible_types = list(possible_types)
        possible_types.remove(const.NONE_TYPE)

        field_link, table = self.get_field(field_name,
                                           type_processing.get_union_type(
                                               possible_types),
                                           parent)
        if field_link:
            field_link.is_optional = True

        return field_link, table

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

        enum_alias_attributes = {"member_name": str}

        enum_alias = type_processing.create_annotated_datatype(self.namer.name_enum_alias(field_name),
                                                               enum_alias_attributes)

        enum_table = self.add_table(enum_alias)
        # noinspection protected-member
        self.enum_lookups[field_name] = field_type._member_map_

        return ForeignKey(enum_table)

    def get_iter_field(self, field_name: str, field_type: type[Iterable],
                       parent: Table) -> tuple[IterableField, Table]:
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
        # to the parent

        iterator_types: Iterable[type] = typing.get_args(field_type)

        # Set the provided classes that we see to a set of types for each
        # Datatype the tuple of the iterable stores
        iterator_attributes = {f"option_{i}": v for i, v in
                               enumerate(iterator_types)}

        iter_member_alias = type_processing.create_annotated_datatype(
            self.namer.name_iterator_inner(parent, field_name),
            iterator_attributes
        )

        table_to_reference = self.add_table(iter_member_alias)

        many_to_many = Table(
            name=self.namer.name_iterator_link_table(parent, field_name, field_type),
            fields=[ForeignKey(parent), ForeignKey(table_to_reference)])

        return IterableField(field_name), many_to_many

