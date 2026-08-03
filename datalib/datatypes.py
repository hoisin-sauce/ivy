"""Stores the datatypes used to represent different parts of the modelling system
"""
from dataclasses import dataclass
from datalib import type_processing
from datalib import const

# Graph

@dataclass
class DataType:
    """
    Stores additional metadata about a type and its interactions with other types
    """
    class_type: type
    dependencies: set[type]
    remaining_dependencies: set[type]
    depended_by: set[type]

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
        dependencies: set[type] = type_processing.get_immediate_dependencies(class_type) - const.BASIC_TYPES
        datatype: DataType = DataType(class_type, dependencies, dependencies, set())
        return datatype

# Table Structure

class TableField:
    is_optional: bool = False

@dataclass
class Field(TableField):
    """
    Represents a field of a table
    """
    name: str
    datatype: type

@dataclass
class ForeignKey(TableField):
    """
    Represents a foreign key to another table
    """
    to: "Table"

class PrimaryKey(TableField):
    """
    Represents a primary key of a table
    """

@dataclass
class IterableField(TableField):
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
    fields: list[TableField]