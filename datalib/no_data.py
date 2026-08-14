from typing import Generator, Any

from datalib.const import NONE_TYPE
from datalib.database_types import NoData
from datalib.naming import TableNamer, StandardTableNamer
from datalib.queries import Query, QueryBundle
from datalib.abstract_database_components import (
    DatabaseRequestManger,
    QueryBundleTranslator,
    QueryTranslator,
    QueryToBeResolved,
    InsertionTranslator, SchemaTranslator, DatabaseOutput,
)
from datalib.database_manager import DatabaseManager
from datalib.schema import TableStructure


class NoQueryBundleTranslator(QueryBundleTranslator[NoData]):
    """
    Dummy QueryTranslator class
    """
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[T, NoData]:
        return QueryToBeResolved[T, NoData](NoData(), query.expected_type)

    def translate_query_bundle[T](self, query: QueryBundle[T]) -> QueryToBeResolved[T, NoData]:
        return QueryToBeResolved[T, NoData](NoData(), query.expected_type_signature)

class NoDatabaseRequestManager(DatabaseRequestManger[NoData, NoData]):
    """
    Dummy Database Manager class
    """
    def execute_query[T](self, query: QueryToBeResolved[T, NoData]) -> DatabaseOutput[NoData, T]:
        return DatabaseOutput[NoData, T](NoData(), query.expected_type)

class NoInsertionTranslator(InsertionTranslator[NoData]):
    def translate_insertion(self, obj: Any) -> QueryToBeResolved[None, NoData]:
        return QueryToBeResolved[None, NoData](NoData(), NONE_TYPE)

class NoSchemaTranslator(SchemaTranslator[NoData]):
    def translate_schema(self, schema: TableStructure) -> QueryToBeResolved[None, NoData]:
        return QueryToBeResolved[None, NoData](NoData(), NONE_TYPE)

class NoSchema(TableStructure):
    # noinspection missing-constructor
    def __init__(self):
        ...

class NoDatabaseManager(DatabaseManager[NoData, NoData]):
    """
    Dummy Database Manager class
    """
    schema: TableStructure = NoSchema()
    field_namer: TableNamer = StandardTableNamer()
    query_resolver: QueryTranslator[NoData] = NoQueryBundleTranslator()
    insertion_translator: InsertionTranslator[NoData] = NoInsertionTranslator()
    database_request_manager: DatabaseRequestManger[NoData, NoData] = NoDatabaseRequestManager()
    schema_translator: SchemaTranslator[NoData] = NoSchemaTranslator()
