from typing import Generator, Any

from datalib.database_types import NoData
from datalib.naming import TableNamer, StandardTableNamer
from datalib.queries import Query, QueryBundle
from datalib.abstract_database_components import (
    DatabaseRequestManger,
    QueryBundleTranslator,
    QueryTranslator,
    QueryToBeResolved,
    InsertionTranslator, SchemaTranslator,
)
from datalib.database_handle import DatabaseManager
from datalib.schema import TableStructure


class NoQueryBundleTranslator(QueryBundleTranslator[NoData]):
    """
    Dummy QueryTranslator class
    """
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[T, NoData]:
        return QueryToBeResolved[T, NoData](NoData())

    def translate_query_bundle[T](self, query: QueryBundle[T]) -> QueryToBeResolved[T, NoData]:
        return QueryToBeResolved[T, NoData](NoData())

class NoDatabaseRequestManager(DatabaseRequestManger[NoData]):
    """
    Dummy Database Manager class
    """
    def execute_query[T](self, query: QueryToBeResolved[T, NoData]) -> Generator[T]:
        def no_generator() -> Generator[T]:
            yield from list()

        return no_generator()

class NoInsertionTranslator(InsertionTranslator[NoData]):
    def translate_insertion(self, obj: Any) -> QueryToBeResolved[None, NoData]:
        return QueryToBeResolved[None, NoData](NoData())

class NoSchemaTranslator(SchemaTranslator[NoData]):
    def translate_schema(self, schema: TableStructure) -> QueryToBeResolved[None, NoData]:
        return QueryToBeResolved[None, NoData](NoData())

class NoSchema(TableStructure):
    # noinspection missing-constructor
    def __init__(self):
        ...

class NoDatabaseManager(DatabaseManager[NoData]):
    """
    Dummy Database Manager class
    """
    schema: TableStructure = NoSchema()
    field_namer: TableNamer = StandardTableNamer()
    query_resolver: QueryTranslator[NoData] = NoQueryBundleTranslator()
    insertion_translator: InsertionTranslator[NoData] = NoInsertionTranslator()
    database_request_manager: DatabaseRequestManger[NoData] = NoDatabaseRequestManager()
    schema_translator: SchemaTranslator[NoData] = NoSchemaTranslator()
