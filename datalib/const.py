"""Stores constants being used for the database creation based on module types.
"""
import datalib.datatypes as datatypes

# BASIC TYPES
NONE_TYPE = type(None)

BASIC_TYPES = {str, int, bool, float, NONE_TYPE}
BASIC_TYPE_MAPPINGS = {
    str: "STRING",
    int: "INTEGER",
    bool: "BOOLEAN",
    float: "REAL",
}

# NAMING CONVENTIONS
