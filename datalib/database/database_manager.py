from abc import ABCMeta
from collections.abc import Iterable
from typing import Any, Optional, Generator

import datalib.structure.schema
import datalib.structure.naming.naming
from datalib.queries.deterministic.queries import Query
from datalib.database.abstract_database_components import QueryTranslator, \
    DatabaseRequestManger, \
    QueryToBeResolved, InsertionTranslator, SchemaTranslator, \
    DatabaseOutputProcessor


class DatabaseManager[DatabaseInteractionType, DataProcessingType](metaclass=ABCMeta):
    schema: datalib.structure.schema.TableStructure
    field_namer: datalib.structure.naming.naming.TableNamer
    query_resolver: QueryTranslator[DatabaseInteractionType]
    insertion_translator: InsertionTranslator[DatabaseInteractionType]
    database_request_manager: DatabaseRequestManger[DatabaseInteractionType, DataProcessingType] # TODO Note allow for a memory option when implementing sqlite
    database_output_processor: DatabaseOutputProcessor[DataProcessingType]
    schema_translator: SchemaTranslator[DatabaseInteractionType]

    def __post_init__(self) -> None:
        self.initialise_database()

    def initialise_database(self) -> None:
        # TODO write implementation and figure out schema conflict resolution strategies
        # When clashes exist with an already existing database
        ...

    def select[T](self, datatype: type[T]) -> Query[T]:
        return Query(datatype, self.execute_query)

    # TODO implement better failure detection
    def insert(self, objects: Iterable[Any] | Any) -> Optional[bool]:
        if isinstance(objects, Iterable):
            for obj in objects:
                self.insert_single(obj)
            return True

        self.insert_single(objects)
        return True

    def execute_query[T](self, query: Query[T]) -> Generator[T, None, None]:
        query_representation: QueryToBeResolved[T, DatabaseInteractionType] = self.query_resolver.translate_query(query)
        database_output: DataProcessingType = self.database_request_manager.execute_query(query_representation)
        return self.database_output_processor.get_output(database_output)

    def insert_single(self, obj: Any) -> None:
        insertion_representation: DatabaseInteractionType = self.insertion_translator.translate_insertion(obj)
        self.database_request_manager.execute_query(insertion_representation)