from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Callable, Any
from types import UnionType, GenericAlias

from datalib.queries.speculative import condition_specifier

@dataclass
class AbstractAttribute[T](metaclass=ABCMeta):
    name: str
    attribute_type: type | UnionType | GenericAlias
    datatype_converter: "DatatypeConverter"
    supported_specialisations: dict[condition_specifier.AccessMethod, Callable[[Any], list[type]]]

    @abstractmethod
    def get_next(self, access_method: condition_specifier.AccessMethod, parameter: Any) -> list["AbstractAttribute[Any]"]:
        ...


class AbstractAttributeTypeManager[T](metaclass=ABCMeta):
    ...

class DatatypeConverter:
    ...

class SchemaCondition:
    ...

class ConditionVerifier:
    ...