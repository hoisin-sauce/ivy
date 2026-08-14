import types
import typing
from dataclasses import dataclass
from enum import StrEnum
from collections.abc import Iterable, Generator
from typing import Any, Unpack, Tuple, overload, Self, Callable, TypeVar
from types import GenericAlias
from datalib import type_processing
# TODO cleanup how imports are managed
# TODO implement __all__ to limit what can be imported from this module
# TODO allow for functions applied to data like count(*) to be expressed


class ConditionCombination(StrEnum):
    AND = "AND"
    OR = "OR"

class ConditionOperator(StrEnum):
    EQUALS = "="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_THAN_OR_EQUALS = "<="
    GREATER_THAN_OR_EQUALS = ">="


class Query[T]:
    """
    Abstract query class representing a query for data in a single class
    with any number of applied conditions

    Example::
        >>> class A:
        >>>     a: int
        >>>     b: int
        >>>
        >>> make_subscriptable_table(A)
        >>> obj_attribute: ObjectAttribute = A["a"]
        >>> condition: Condition = obj_attribute == 2
        >>> T = TypeVar("T")
        >>> query_executor: Callable[[Query[T]], Generator[T]]
        >>> query = Query(A, query_executor)
        >>> query.where(condition)
        >>> # Or in one line
        >>> query = Query(A, query_executor).where(A["a"]==1)

    To construct a query for instances of A where the 'a' field is equal to 1

    As a standard practice queries should not be created except by a database
    object, e.g.

    Example::
        >>> from datalib.database_handle import DatabaseManager
        >>> IntermediateType = TypeVar("IntermediateType")
        >>> db: DatabaseManager[IntermediateType] # Database handle
        >>> db.select(A).where(A["a"]==1) == query

    Which should allow for simpler, more pythonic interaction and less
    boilerplate
    """
    conditions: "list[Condition]" # is this the right way to store them?
    executor: Callable[["Query[T]"], Generator[T]]
    expected_type: type

    # TODO make queries subscriptable

    def __init__(self, expected_type: type[T], executor: Callable[["Query[T]"], Generator[T]]) -> None:
        assert isinstance(expected_type, type) or type(expected_type) == types.GenericAlias
        self.conditions = list()
        self.executor = executor
        self.expected_type = expected_type

    def get_values(self) -> Generator[T]:
        """
        Execute the query and return an object that returns the query value
        Returns:
            Generator which yields the type specified at query creation

            Examples::
                >>> process_query: Callable[["Query[T]"], Generator[T]]
                >>> query = Query(int, process_query)
                >>> values: list[T] = list(query.get_values())
        """
        return self.executor(self)

    def where(self, condition_checker: "Condition") -> "Query[T]":
        self.conditions.append(condition_checker)
        return self

    def __repr__(self) -> str:
        return f"SELECTING {self.expected_type.__name__} WHERE {self.conditions}"

class QueryBundle[*Ts]:
    """
    Group of queries that can be executed simultaneously
    """
    # TODO include a where field which would allow for applying filters using data from combined queries
    expected_types: tuple[*Ts]
    queries: tuple[Query, ...]

    def __init__(self, elements: tuple[Query, ...]) -> None: # TODO do not expose
        assert all(map(lambda x: isinstance(x, Query), elements)), "Query bundles can only contain queries"
        assert len(set(map(lambda x: x.executor, elements))) == 1, "Queries in a query bundle must share the same executor"
        self.expected_types = tuple(q.expected_type for q in elements)
        self.queries = elements

    @overload
    @classmethod
    def create[A](cls, elements: tuple["Query[A]"]) -> "QueryBundle[A]": ...
    @overload
    @classmethod
    def create[A, B](cls, elements: tuple["Query[A]", "Query[B]"]) -> "QueryBundle[A, B]": ...
    @overload
    @classmethod
    def create[A, B, C](cls, elements: tuple["Query[A]", "Query[B]", "Query[C]"]) -> "QueryBundle[A, B, C]": ...
    @overload
    @classmethod
    def create[A, B, C, D](cls, elements: tuple["Query[A]", "Query[B]", "Query[C]", "Query[D]"]) -> "QueryBundle[A, B, C, D]": ...
    @overload
    @classmethod
    def create[A, B, C, D, E](cls, elements: tuple["Query[A]", "Query[B]", "Query[C]", "Query[D]", "Query[E]"]) -> "QueryBundle[A, B, C, D, E]": ...

    @classmethod
    def create(cls,
               elements: tuple[Query[Any], ...]) -> "QueryBundle":
        return cls(elements)

Bundle = QueryBundle.create # TODO Only expose this

@dataclass
class Condition:
    """
    A condition applied as part of a query
    """
    left: "ObjectAttribute | Condition"
    right: "ObjectAttribute | type | Condition | Any"
    operator: ConditionOperator | ConditionCombination

    def __post_init__(self) -> None:
        assert isinstance(self.operator, (ConditionCombination, ConditionOperator))

    def __and__(self, other: "Condition") -> "Condition":
        return Condition(self, other, ConditionCombination.AND)

    def __or__(self, other: "Condition") -> "Condition":
        return Condition(self, other, ConditionCombination.OR)

    def __repr__(self) -> str:
        return f"{self.left} {self.operator.value()} {self.right}"

# We are deliberately not making this interact as expected with comparitors to allow for syntax with the module
# noinspection method-overriding
@dataclass
class ObjectAttribute: # How do we deal with iterables or other such things
    """
    Represents a database field # TODO resolve duplication about how database fields are represented
    Does not support comparison except in creating conditions based on the
    attribute described by the object.
    All comparisons will effectively evaluate to true as they are overloaded

    Example::
        >>> class A:
        >>>     a: int
        >>>     b: int
        >>>
        >>> make_subscriptable_table(A)
        >>> obj_attribute: ObjectAttribute = A["a"]
        >>> condition: Condition = obj_attribute == 2
    """
    object_type: "type | ObjectAttribute"
    attribute_name: str

    @property
    def attribute_type(self) -> "type | GenericAlias":
        object_type = self.object_type.attribute_type if isinstance(self.object_type, ObjectAttribute) else self.object_type
        hints = typing.get_type_hints(object_type)
        attribute_type = hints[self.attribute_name]
        assert isinstance(attribute_type, (type, GenericAlias))
        return attribute_type

    def is_valid_other(self, other):
        return isinstance(other, (ObjectAttribute, type, self.attribute_type))

    def __ne__(self, other) -> Condition:
        assert self.is_valid_other(other), "Can only compare with other fields or types, or constants of the same type"
        return Condition(self, other, ConditionOperator.EQUALS)

    def __eq__(self, other) -> Condition:
        assert self.is_valid_other(other), "Can only compare with other fields or types, or constants of the same type"
        return Condition(self, other, ConditionOperator.EQUALS)

    def __leq__(self, other) -> Condition:
        assert self.is_valid_other(other), "Can only compare with other fields or types, or constants of the same type"
        return Condition(self, other, ConditionOperator.LESS_THAN_OR_EQUALS)

    def __geq__(self, other) -> Condition:
        assert self.is_valid_other(other), "Can only compare with other fields or types, or constants of the same type"
        return Condition(self, other, ConditionOperator.GREATER_THAN_OR_EQUALS)

    def __lt__(self, other) -> Condition:
        assert self.is_valid_other(other), "Can only compare with other fields or types, or constants of the same type"
        return Condition(self, other, ConditionOperator.LESS_THAN)

    def __gt__(self, other) -> Condition:
        assert self.is_valid_other(other), "Can only compare with other fields or types, or constants of the same type"
        return Condition(self, other, ConditionOperator.GREATER_THAN)

    def __getitem__(self, item) -> "ObjectAttribute":
        # TODO verify implementation
        if isinstance(attr_type := self.attribute_type, type):
            assert item in typing.get_type_hints(attr_type), "Field must be an attribute of the base class"
            return ObjectAttribute(self, item)
        raise NotImplementedError("Need to implement subsequent getitem calls")

    def __getattr__(self, item):
        return getattr(getattr(self.object_type, self.attribute_name), item)

def make_subscriptable_table(t: type):
    def get_database_field(name: str) -> ObjectAttribute:
        assert name in typing.get_type_hints(t), "Field must be an attribute of the base class"
        return ObjectAttribute(t, name)

    # noinspection unresolved-references
    t.__class_getitem__= get_database_field

def make_module_subscriptable(module: types.ModuleType):
    for type_ in type_processing.get_types_in_module(module):
        make_subscriptable_table(type_)