from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Callable
from dataclasses import dataclass
from typing import Any

import datalib.schema
from datalib.datatypes import Query
import datalib.naming


@dataclass
class DatabaseHandle(metaclass=ABCMeta):
    schema: datalib.schema.TableStructure
    field_namer: datalib.naming.FieldNamer

    def __post_init__(self) -> None:
        self.initialise_database()

    @abstractmethod
    def initialise_database(self) -> None:
        ...

    @abstractmethod
    def select(self, datatype: Iterable[type]) -> Query:
        ...

    @abstractmethod
    def insert(self, objects: Iterable[Any]) -> None:
        ...

class QueryExecutor(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, query: Query, database: DatabaseHandle) -> Any:
        ...
