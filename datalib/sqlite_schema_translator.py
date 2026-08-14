from collections.abc import Iterable
from dataclasses import dataclass

import datalib.const as const
from datalib.abstract_database_components import SchemaTranslator, QueryToBeResolved

from datalib.database_types import SQLiteString
from datalib.datatypes import (Table, TableField, PrimaryKey, ForeignKey,
                               IterableField, Field)
from datalib.database_constraint import *
import datalib.database_constraint as database_constraint
from datalib.schema import TableStructure


def get_table_create_start(table_name: str) -> str:
    return f"CREATE TABLE {table_name} (\n"

def get_table_create_end(table_name: str) -> str:
    del table_name
    return ");"

def get_table_field_create(field_name: str, field_type: str,
                           constraints: Iterable[FieldConstraint]) -> str:
    return f"\t{field_name} {field_type} {" ".join([repr(i) for i in constraints])},\n"

def get_table_constraint_create(constraint: TableConstraint) -> str:
    return f"\t{constraint},\n"

@dataclass
class SQLiteSchemaTranslator(SchemaTranslator[SQLiteString]):
    primary_key_handler: PrimaryKeyResolver

    def translate_schema(self, schema: TableStructure) -> QueryToBeResolved[None, SQLiteString]:
        return SQLiteTranslatedSchema(
            schema=schema,
            primary_key_handler=self.primary_key_handler,
        ).get_query()

@dataclass
class SQLiteTranslatedSchema:
    primary_key_handler: PrimaryKeyResolver
    schema: TableStructure

    def get_query(self) -> QueryToBeResolved[None, SQLiteString]:
        creation_order = self.schema.get_tables_in_order()
        table_create_statements: list[str] = list()
        for table in creation_order:
            table_create_statements.append(self.get_table_create_statement(table))

        schema_string = "\n".join(table_create_statements)
        return QueryToBeResolved(SQLiteString(schema_string), const.NONE_TYPE)

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

        if database_creation_string[-2] == ",":
            database_creation_string = database_creation_string[:-2] + "\n"

        database_creation_string += get_table_create_end(table.name)
        return database_creation_string

    def get_field_constraints(self, field: TableField) -> Iterable[DatabaseConstraint]:
        del self # Ha! now it's not static
        constraints = list()

        if not field.is_optional:
            constraints.append(MandatoryFieldConstraint())

        if isinstance(field, PrimaryKey):
            # TODO Aren't we meant to have a class to handle this
            constraints.append(PrimaryKeyConstraint())

        if isinstance(field, ForeignKey):
            field: ForeignKey
            foreign_table_name: str = field.to.name
            foreign_primary_key: str = field.to.get_primary_key().name
            constraints.append(ForeignKeyConstraint(field_name=field.name,
                table_name=foreign_table_name,
                table_primary_key_field_name=foreign_primary_key))

        return constraints

    def get_name(self, field: TableField, table: Table) -> str:
        del table # In case it needs to be re-introduced without having to redundantly change the function shape back and again

        if hasattr(field, "name"):
            return field.name

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
