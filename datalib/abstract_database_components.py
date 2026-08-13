""" Contains the abstract components that make up the standardised database control flow for modularity
"""
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Generator, Any
import typing

from datalib.queries import Query, QueryBundle
from datalib.schema import TableStructure


@dataclass
class QueryToBeResolved[ExpectedOutputObjectType, DatabaseExpectedDatatype]:
    """
    Intermediate datatype to allow for type checking between the class
    interpreting the query and the class executing that interpretation
    to allow for easier alignment
    """
    query_to_database: DatabaseExpectedDatatype

OutputType = typing.TypeVar("OutputType")
class QueryTranslator[OutputType](metaclass=ABCMeta):
    """
    Abstract class promising that it can convert a query to the specified
    output format
    """
    @abstractmethod
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[T, OutputType]:
        ...

class QueryBundleTranslator[OutputType](QueryTranslator[OutputType], metaclass=ABCMeta):
    """
    Abstract class to handle the translation of bundled queries to the
    specified output format
    """
    @abstractmethod
    def translate_query_bundle[T](self, query: QueryBundle[T]) -> QueryToBeResolved[T, OutputType]:
        ...

InputType = typing.TypeVar("InputType")
class DatabaseRequestManger[InputType](metaclass=ABCMeta):
    """
    Handles execution of actual queries on the database
    # TODO create lazy evaluation of subclass attributes
    """
    @abstractmethod
    def execute_query[T](self, query: QueryToBeResolved[T, InputType]) -> Generator[T]:
        ...

class InsertionTranslator[OutputType](metaclass=ABCMeta):
    """
    Abstract class used to translate an object to a query of the specified
    output format
    """
    @abstractmethod
    def translate_insertion(self, obj: Any) -> QueryToBeResolved[None, OutputType]:
        ...

class SchemaTranslator[OutputType](metaclass=ABCMeta):
    """
    Abstract class used to translate a schema object to a query of the
    specified
    """
    @abstractmethod
    def translate_schema(self, schema: TableStructure) -> QueryToBeResolved[None, OutputType]:
        ...

