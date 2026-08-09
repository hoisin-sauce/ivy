from abc import ABCMeta, abstractmethod
import typing
from dataclasses import dataclass
from enum import Enum
from collections.abc import Iterable, Generator
from typing import Any, Unpack, Tuple
from datalib.database_types import SQLiteString, NoData


class ConditionCombination(Enum):
    AND = "AND"
    OR = "OR"

class ConditionOperator(Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_THAN_OR_EQUALS = "<="
    GREATER_THAN_OR_EQUALS = ">="


class Query[T]:
    conditions: "list[Condition]"
    executor: "DatabaseInterface"
    expected_type: type

    def __init__(self, expected_type: type, database_interface: "DatabaseInterface"):
        assert isinstance(expected_type, type)
        assert isinstance(database_interface, DatabaseInterface)
        self.executor = database_interface
        self.conditions = list()
        self.expected_type = expected_type

    def get_value(self) -> Generator[T]:
        return self.executor.execute_query(self)

    def where(self, condition_checker: "Condition") -> "Query[T]":
        assert issubclass()
        self.conditions.append(condition_checker)
        return self

def combine_queries[Q, T](query_1: Query[Q], query_2: Query[T]) -> Query[tuple[Q, T]]:
    assert query_1.executor is query_2.executor, "Combined queries must execute together"
    assert isinstance(query_1.expected_type, type)
    assert isinstance(query_2.expected_type, type)
    # For some reason my linter doesnt think the explicitly declared types are types
    # noinspection type-hints
    expected_type = tuple[query_1.expected_type, query_2.expected_type]
    return Query(expected_type, query_1.executor)


@dataclass
class Condition:
    left: "DatabaseField | Condition"
    right: "DatabaseField | type | Condition | Any"
    operator: ConditionOperator | ConditionCombination

    def __and__(self, other: "Condition") -> "Condition":
        return Condition(self, other, ConditionCombination.AND)

    def __or__(self, other: "Condition") -> "Condition":
        return Condition(self, other, ConditionCombination.OR)

@dataclass
class DatabaseField: # How do we deal with iterables or other such things
    table_type: type
    field_name: str

    def __eq__(self, other):
        assert isinstance(other, (DatabaseField, type)), "Can only compare with other fields or types"
        return Condition(self, other, ConditionOperator.EQUALS)

    def __leq__(self, other):
        assert isinstance(other, (DatabaseField, type)), "Can only compare with other fields or types"
        return Condition(self, other, ConditionOperator.LESS_THAN_OR_EQUALS)

    def __geq__(self, other):
        assert isinstance(other, (DatabaseField, type)), "Can only compare with other fields or types"
        return Condition(self, other, ConditionOperator.GREATER_THAN_OR_EQUALS)

    def __lt__(self, other):
        assert isinstance(other, (DatabaseField, type)), "Can only compare with other fields or types"
        return Condition(self, other, ConditionOperator.LESS_THAN)

    def __gt__(self, other):
        assert isinstance(other, (DatabaseField, type)), "Can only compare with other fields or types"
        return Condition(self, other, ConditionOperator.GREATER_THAN)

def make_subscriptable_table(t: type):
    def get_database_field(name: str) -> DatabaseField:
        assert name in typing.get_type_hints(t), "Field must be an attribute of the base class"
        return DatabaseField(t, name)

    # noinspection unresolved-references
    t.__class_getitem__= get_database_field


@dataclass
class QueryToBeResolved[ExpectedOutputObjectType, DatabaseExpectedDatatype]:
    query_to_database: DatabaseExpectedDatatype

OutputType = typing.TypeVar("OutputType")
class QueryTranslator[OutputType](metaclass=ABCMeta):
    @abstractmethod
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[T, OutputType]:
        ...

InputType = typing.TypeVar("InputType")
class DatabaseRequestManger[InputType](metaclass=ABCMeta):
    @abstractmethod
    def execute_query[T](self, query: QueryToBeResolved[T, InputType]) -> Generator[T]:
        ...

class DatabaseInterface[DatabaseInteractionType](metaclass=ABCMeta):
    query_resolver: QueryTranslator[DatabaseInteractionType]
    database_request_manager: DatabaseRequestManger[DatabaseInteractionType]

    def execute_query[T](self, query: Query[T]) -> Generator[T]:
        query_representation: DatabaseInteractionType = self.query_resolver.translate_query(query)
        return self.database_request_manager.execute_query(query_representation)

class NoQueryTranslator(QueryTranslator[NoData]):
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[T, NoData]:
        return QueryToBeResolved[T, NoData](query)

class NoDatabaseTranslator(DatabaseRequestManger[NoData]):
    def execute_query[T](self, query: QueryToBeResolved[T, NoData]) -> Generator[T]:
        def no_generator() -> Generator[T]:
            raise StopIteration

        return no_generator()

class NoDatabaseInterface(DatabaseInterface[NoData]):
    query_resolver: QueryTranslator[NoData] = NoQueryTranslator()
    database_request_manager: DatabaseRequestManger[NoData] = NoDatabaseTranslator()
