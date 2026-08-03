from collections.abc import Iterable

from datalib.database_handle import DatabaseHandle
from typing import Any

from datalib.datatypes import Table, Query, TableField
from datalib.database_constraint import FieldConstraint


def get_table_create_start(table_name: str) -> str:
    return f"CREATE TABLE {table_name} (\n"
# noinspection unused-parameter
def get_table_create_end(table_name: str) -> str:
    return ");"

def get_table_field_create(field_name: str, field_type: str, constraints: Iterable[FieldConstraint]) -> str:
    return f"\t{field_name} {field_type} {" ".join([repr(i) for i in constraints])},"

class SQliteDatabaseHandle(DatabaseHandle):
    def initialise_database(self) -> None:
        creation_order = self.schema.get_tables_in_order()
        for table in creation_order:
            self.get_table_create_statement(table)

    def get_table_create_statement(self, table: Table) -> str:
        database_creation_string = get_table_create_start(table.name)
        for field in table.fields:
            constraints = self.get_field_constraints(field)
            field_name = self.get_name(field)
            field_type = self.get_type(field)
            database_creation_string += get_table_field_create(field_name, field_type, constraints)
        database_creation_string += get_table_create_end(table.name)
        return database_creation_string

    def get_field_constraints(self, field: TableField) -> Iterable[FieldConstraint]:
        ...

    def get_name(self, field: TableField) -> str:
        ...

    def get_type(self, field: TableField) -> str:
        ...

    def select(self, datatype: Iterable[type]) -> Query:
        ...

    def insert(self, objects: Iterable[Any]) -> None:
        ...