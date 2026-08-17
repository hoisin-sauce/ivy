from dataclasses import dataclass

class SQLString(str):
    ...

@dataclass
class SQLiteString:
    query_string: str
    inserted_values: dict[str, str]

class NoData:
    ...