from abc import ABCMeta, abstractmethod
from typing import Any, Callable
from types import UnionType, GenericAlias

from datalib.queries.speculative.attribute import Attribute

import warnings
warnings.warn("This is a test module and should not be used, will be removed in later versions", DeprecationWarning, stacklevel=2)

class AttributeInstanceHandler[T](metaclass=ABCMeta):
    """
    Object to handle managing attribute representations for attributes of a specific type

    Attributes:
        for_type
            the type of attribute that this instance handles
    """
    for_type: type[T]

    @abstractmethod
    def instantiate_attributes(self, attribute_name: str, attribute_type: T) -> list[Attribute]:
        ...


class SpecialisedAttribute[T](metaclass=ABCMeta):
    for_type: type[T]
    supported_specialisations: dict[tuple[type | UnionType | GenericAlias, ...], Callable[[Any], list[Attribute]]]

    @classmethod
    def instantiate_of_type(cls):
        ...

    def applies_to(self, other: Any) -> bool:
        return isinstance(other, self.for_type)

    def can_specialise_with(self, *args) -> bool:
        return map_to_types(args) in self.supported_specialisations

    def specialise_with(self, *args) -> list[Attribute]:
        if not self.can_specialise_with(*args):
            return list()

        return self.supported_specialisations[map_to_types(args)](args)


def map_to_types(args) -> tuple[type, ...]:
    return tuple(map(type, args))
