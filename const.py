import enum
import typing

class SQLFields(enum.Enum):
    required = "NOT NULL"
    primary = "PRIMARY KEY"
    autoincrement = "AUTO_INCREMENT"
    foreign_key = "FOREIGN KEY ({local_column_name}) REFERENCES {table_name} ({foreign_column_name})"
    integer = "INTEGER"
    string = "TEXT"
    real = "REAL"
    null = "NULL"
    blob = "BLOB"
    json = "JSON"
    in_range = "CHECK ({local_column_name} >= {minimum} AND {local_column_name} <= {maximum})"
    unique = "UNIQUE ({local_comma_separated_columns})"
    unique_with_primary = "UNIQUE ({local_comma_separated_columns})"



BASIC_TYPES = {str, int, bool, float, type(None), Ellipsis}
BASIC_TYPE_MAPPINGS = ...

NONE_TYPE = type(None)

TYPE_EXCEPTIONS = {...}
INHERIT_EXCEPTIONS = (enum.Enum,)

class SQLFieldDefaults(enum.Enum):
    PRIMARY_KEY_CONSTRUCTOR = [SQLFields.integer, SQLFields.primary, SQLFields.autoincrement]
    ORDERING_FIELD = [SQLFields.integer, SQLFields.required, SQLFields.unique_with_primary]