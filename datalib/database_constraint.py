from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Iterable


def filter_table_field_constraints(constraints: Iterable["DatabaseConstraint"]
    ) -> tuple[Iterable["TableConstraint"], Iterable["FieldConstraint"]]:
    """
    Splits constraints into table and field constraints
    Args:
        constraints:
            An iterable of DatabaseConstraint objects
    Returns:
        A tuple in the format of (table_constraints, field_constraints)
        Where table_constraints contains subclasses of TableConstraint and
        field_constraints contains subclasses of FieldConstraint.
    """
    table_constraints = []
    field_constraints = []
    for constraint in constraints:
        if isinstance(constraint, TableConstraint):
            table_constraints.append(constraint)

        if isinstance(constraint, FieldConstraint):
            field_constraints.append(constraint)

    return table_constraints, field_constraints


class DatabaseConstraint(metaclass=ABCMeta):
    """
    Abstract class representing a constraint on a database
    """
    @abstractmethod
    def __repr__(self) -> str:
        ...

class FieldConstraint(DatabaseConstraint, metaclass=ABCMeta):
    """
    Abstract class representing a constraint on a field
    """
    ...

class TableConstraint(DatabaseConstraint, metaclass=ABCMeta):
    """
    Abstract class representing a constraint on a table
    """
    ...

class PrimaryKeyConstraint(FieldConstraint):
    """
    Class representing that a primary key constraint is present on this field
    """
    def __repr__(self) -> str: # TODO refactor into a per database handling of how this constraint should be approached
        return "PRIMARY KEY"

class MandatoryFieldConstraint(FieldConstraint):
    """
    Class representing that this field is mandatory
    """
    def __repr__(self) -> str:
        return "NOT NULL"


@dataclass
class ForeignKeyConstraint(TableConstraint):
    field_name: str
    table_name: str
    table_primary_key_field_name: str

    def __repr__(self) -> str:
        return (f"FOREIGN KEY ({self.field_name}) "
                f"REFERENCES "
                f"{self.table_name}({self.table_primary_key_field_name})")

class PrimaryKeyResolver(metaclass=ABCMeta):
    key_type: type
    def get_primary_key_type(self) -> type:
        return self.key_type

class StandardPrimaryKeyResolver(PrimaryKeyResolver):
    key_type = int

__all__ = [
    "DatabaseConstraint", "FieldConstraint", "TableConstraint",
    "PrimaryKeyConstraint", "MandatoryFieldConstraint", "ForeignKeyConstraint",
    "PrimaryKeyResolver", "StandardPrimaryKeyResolver"]