import enum

class SQL(enum.Enum):
    INTEGER = "INTEGER"

NONE_TYPE = type(None)

BASIC_TYPES = {str, int, bool, float, NONE_TYPE}
BASIC_TYPE_MAPPINGS = ...

