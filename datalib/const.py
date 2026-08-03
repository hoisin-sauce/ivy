"""Stores constants being used for the database creation based on module types.
"""
import datalib.datatypes as datatypes

# BASIC TYPES
NONE_TYPE = type(None)

BASIC_TYPES = {str, int, bool, float, NONE_TYPE}
BASIC_TYPE_MAPPINGS = ...

DEFAULT_TYPES = {
    datatypes.PrimaryKey: int,
    datatypes.ForeignKey: int,
}
# NAMING CONVENTIONS
