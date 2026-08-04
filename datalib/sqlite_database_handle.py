from collections.abc import Iterable
from dataclasses import dataclass

import datalib.const as const
from datalib.database_handle import DatabaseHandle
from typing import Any

from datalib.datatypes import (Table, Query, TableField, PrimaryKey, ForeignKey,
                               IterableField, Field)
from datalib.database_constraint import FieldConstraint, DatabaseConstraint, \
    ForeignKeyConstraint, MandatoryFieldConstraint, PrimaryKeyConstraint, \
    TableConstraint, PrimaryKeyResolver
import datalib.database_constraint as database_constraint


def get_table_create_start(table_name: str) -> str:
    return f"CREATE TABLE {table_name} (\n"
# noinspection unused-parameter
def get_table_create_end(table_name: str) -> str:
    return ");"

def get_table_field_create(field_name: str, field_type: str,
                           constraints: Iterable[FieldConstraint]) -> str:
    return f"\t{field_name} {field_type} {" ".join([repr(i) for i in constraints])},\n"

def get_table_constraint_create(constraint: TableConstraint) -> str:
    return f"\t{constraint},\n"

@dataclass
class SQliteDatabaseHandle(DatabaseHandle):
    primary_key_handler: PrimaryKeyResolver

    def initialise_database(self) -> None:
        creation_order = self.schema.get_tables_in_order()
        for table in creation_order:
            self.get_table_create_statement(table)

    def get_table_create_statement(self, table: Table) -> str:
        database_creation_string = get_table_create_start(table.name)
        table_constraints: list[TableConstraint] = list()

        for field in table.fields:

            if not self.field_included(field):
                continue

            constraints = self.get_field_constraints(field)
            field_name = self.get_name(table=table, field=field)
            field_type = self.get_type(field)

            individual_table_constraints, field_constraints = \
                database_constraint.filter_table_field_constraints(constraints)

            table_constraints.extend(individual_table_constraints)

            database_creation_string += get_table_field_create(
                field_name, field_type, field_constraints)

        for table_constraint in table_constraints:
            database_creation_string += get_table_constraint_create(table_constraint)

        database_creation_string += get_table_create_end(table.name)
        return database_creation_string

    def get_field_constraints(self, field: TableField) -> Iterable[DatabaseConstraint]:
        constraints = list()

        if not field.is_optional:
            constraints.append(MandatoryFieldConstraint())

        if isinstance(field, PrimaryKey):
            constraints.append(PrimaryKeyConstraint())

        if isinstance(field, ForeignKey):
            field: ForeignKey
            foreign_table_name: str = field.to.name
            foreign_primary_key: str = self.field_namer.name_primary_key(field.to)
            constraints.append(ForeignKeyConstraint(field_name=field.name,
                table_name=foreign_table_name,
                table_primary_key_field_name=foreign_primary_key))

        return constraints

    def get_name(self, field: TableField, table: Table) -> str:
        if hasattr(field, "name"):
            return field.name

        if isinstance(field, PrimaryKey):
            return self.field_namer.name_primary_key(table)

        raise NotImplementedError(
            f"Field type {type(field).__name__} not supported for Sqlite database")

    def field_included(self, field: TableField) -> bool:
        del self
        if isinstance(field, IterableField):
            return False

        return True

    def get_type(self, field: TableField) -> str:
        if isinstance(field, Field):
            return const.BASIC_TYPE_MAPPINGS[field.datatype]

        if isinstance(field, (PrimaryKey, ForeignKey)):
            return const.BASIC_TYPE_MAPPINGS[
                self.primary_key_handler.get_primary_key_type()
            ]

        raise NotImplementedError("Field type not supported for Sqlite database")

    def select(self, datatype: Iterable[type]) -> Query:
        ...

    def insert(self, objects: Iterable[Any]) -> None:
        ...
