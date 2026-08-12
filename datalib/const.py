"""Stores constants being used for the database creation based on module types.
"""
# Note that we need to refactor this into state to allow for different databases to hold type
# This may require different graph types

# BASIC TYPES
NONE_TYPE = type(None)

BASIC_TYPES = {str, int, bool, float, NONE_TYPE}
BASIC_TYPE_MAPPINGS = {
    str: "STRING",
    int: "INTEGER",
    bool: "BOOLEAN",
    float: "REAL",
}
