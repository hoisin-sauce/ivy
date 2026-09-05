import itertools
import typing
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from collections.abc import Callable, Iterable
from types import UnionType, GenericAlias
from typing import ClassVar, Optional

from datalib.queries.speculative.condition_specifier import AccessMethod, Attribute
from datalib.utils.db_utils import flatten_to_list
from datalib.utils.type_processing import resolve_to_possible_types


class AbstractAttribute[T](metaclass=ABCMeta):
    """
    Base class for abstract attributes showing the structure required to
    be implemented to allow for an attribute to work with the surrounding
    validation structure
    Attributes:
        name: the name of the attribute
        attribute_type: the type of the attribute
        parent: the parent of the attribute, unless it is the top level class itself
        datatype_converter: the datatype converter responsible for resolving children to attributes

        supported_specialisations:
            (class attribute) a dictionary mapping each different supported
            specialisation's access method to the allowed parameter shapes
            of that method
        specialisation_functions:
            (class attribute) a dictionary mapping each specialisation and
            shape of access method to the function describing that specialisation
    """
    name: str
    attribute_type: type | UnionType | GenericAlias
    parent: "Optional[AbstractAttribute]"
    datatype_converter: "DatatypeConverter"

    supported_specialisations: \
        ClassVar[
            dict[
                AccessMethod,
                list[tuple[type, ...]]
            ]
        ]
    specialisation_functions: \
        ClassVar[
            dict[
                tuple[AccessMethod, tuple[object, ...]],
                Callable[..., list[type]]
            ]
        ]

    @classmethod
    def register_specialisation(cls: "AbstractAttribute[T]",
                                access_method: AccessMethod,
                                specialisation_function:
                                    Callable[[object], list[type]]):
        """
        Registers the provided specialisation method to be able to resolve
        a specialisation of the specify type.
        
        e.g. to use foo(str, int) to resolve class["hello", 2] we would need
        to register it with AccessMethod.GETITEM
        Args:
            access_method: 
                The type of access method to be registered to
            specialisation_function: 
                The function used to handle the specialisation
        """

        # TODO check for errors here

        function_hints = typing.get_type_hints(specialisation_function)
        function_raw_argument_shape: tuple[object] = tuple(function_hints.keys())

        possible_types_at_positions: tuple[tuple[type]] = \
            tuple(map(resolve_to_possible_types, function_raw_argument_shape))

        possible_shapes: Iterable[tuple[type]] = itertools.product(*possible_types_at_positions)

        for argument_shape in possible_shapes:
            if access_method not in cls.supported_specialisations:
                cls.supported_specialisations[access_method] = [argument_shape]
            else:
                cls.supported_specialisations[access_method].append(argument_shape)

            cls.specialisation_functions[(access_method, argument_shape)] = specialisation_function


    def supports_specialisation(self, access_method: AccessMethod, access_parameters: tuple[object, ...]) -> bool:
        """
        Returns whether the specific specialisation provided is supported by the object
        Args:
            access_method:
                method of access for the specialisation, e.g. getattr or calling
            access_parameters:
                parameters provided for the specialisation

        Returns:
            A boolean value indicating if the provided specification is supported
        """
        if access_method not in self.supported_specialisations:
            return False

        if tuple(map(type, access_parameters)) not in self.supported_specialisations[access_method]:
            return False

        return True

@dataclass
class AttributeCollection:
    attributes: list[AbstractAttribute]

    def get_next(self, access_method: AccessMethod, parameter: object) -> "AttributeCollection":
        for attribute in self.attributes:
            if attribute.supports_specialisation(access_method):
                ...

        raise NotImplementedError("Haven't done it yet innit")


class AbstractAttributeTypeManager[T](metaclass=ABCMeta):
    handled_type: type[T]

    @abstractmethod
    def can_handle(self, obj: object) -> bool:
        """
        Returns whether the type manager can convert the given object into attributes
        Args:
            obj:
                the object we are checking can be converted
        Returns:
            A boolean value indicating whether the object can be converted
        """

    @abstractmethod
    def convert_to_attributes(self, attribute_name: str, obj: T, parent: AbstractAttribute) -> AttributeCollection:
        ...

class DatatypeConverter:
    type_managers: list[AbstractAttributeTypeManager]

    # TODO figure out how we are finding appropriate attributes
    # e.g. order of list vs doing a topological sort on the sets handled by each attribute collection

    def register_type_manager(self, type_manager: AbstractAttributeTypeManager):
        """Allows the datatype converter to use the type manager"""
        self.type_managers.append(type_manager)

    def convert_to_attributes(self, attribute_name: str, attribute_obj: object, attribute_parent: AbstractAttribute) -> AttributeCollection:
        """
        Converts the provided object and metadata about it to a representation of the attribute
        Args:
            attribute_name: name of the attribute
            attribute_obj: object to be converted
            attribute_parent: parent object of the attribute

        Returns:
            An AttributeCollection object representing the attributes that could be represented by this object
        """
        for type_manager in self.type_managers:
            if type_manager.can_handle(attribute_obj):
                return type_manager.convert_to_attributes(attribute_name, attribute_obj, attribute_parent)

        return AttributeCollection(list())


class SchemaCondition:
    ...

class ConditionVerifier:
    ...