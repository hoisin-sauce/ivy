from abc import ABCMeta, abstractmethod
from collections.abc import Iterable, Callable
from dataclasses import dataclass
from typing import Any

import datalib.schema
import datalib.naming
from datalib.queries import DatabaseInterface, Query


@dataclass
class DatabaseManager[DatabaseType](metaclass=ABCMeta):
    schema: datalib.schema.TableStructure
    field_namer: datalib.naming.FieldNamer
    database_interface: DatabaseInterface[DatabaseType]

    def __post_init__(self) -> None:
        # Needs more complex logic to verify that database is created, no changes etc.
        self.initialise_database()

    @abstractmethod
    def initialise_database(self) -> None:
        ...

    @abstractmethod
    def select[T](self, datatype: T) -> Query[T]:
        ...

    @abstractmethod
    def insert(self, objects: Iterable[Any]) -> None:
        ...

class QueryExecutor(metaclass=ABCMeta):
    @abstractmethod
    def execute(self, query: Query, database: DatabaseManager) -> Any:
        ...