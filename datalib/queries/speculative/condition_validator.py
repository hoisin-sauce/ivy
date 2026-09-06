from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from collections.abc import Callable
from types import UnionType, GenericAlias
from typing import ClassVar, Optional

from datalib.queries.speculative.condition_specifier import AccessMethod, Attribute, AttributeComparison, Comparison, AttributeAccess
from datalib.utils.type_processing import get_function_argument_shapes, type_map, FunctionParameterSignature


@dataclass
class AttributeDetails:
    """
    Stores possible details that a function could return to help build the
    next attribute.
    Attributes:
        attribute_name:
            Optional name for the next set of attributes
        possible_attribute_options:
            List of objects that can be used to set the types of the next
            attributes
    """
    attribute_name: Optional[str]
    possible_attribute_options: list

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
        supported_comparisons:
            (class attribute) a list containing all possible comparisons that this
            attribute supports#
    """
    name: str
    attribute_type: type | UnionType | GenericAlias
    parent: "Optional[AbstractAttribute]"
    datatype_converter: "DatatypeConverter"

    supported_specialisations: \
        ClassVar[
            dict[
                AccessMethod,
                list[FunctionParameterSignature]
            ]
        ]
    specialisation_functions: \
        ClassVar[
            dict[
                tuple[AccessMethod, FunctionParameterSignature],
                Callable[..., AttributeDetails]
            ]
        ]

    supported_comparisons: ClassVar[list[AttributeComparison]]

    @classmethod
    def register_specialisation(cls: "AbstractAttribute[T]",
                                access_method: AccessMethod,
                                specialisation_function: Callable[..., AttributeDetails]):
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

        possible_shapes = get_function_argument_shapes(specialisation_function)

        for argument_shape in possible_shapes:
            if access_method not in cls.supported_specialisations:
                cls.supported_specialisations[access_method] = [argument_shape]
            else:
                cls.supported_specialisations[access_method].append(argument_shape)

            cls.specialisation_functions[(access_method, argument_shape)] = specialisation_function


    @classmethod
    def supports_specialisation(cls, access_method: AttributeAccess) -> bool:
        """
        Returns whether the specific specialisation provided is supported by the object
        Args:
            access_method:
                AttributeAccess object holding the access method and
                supplied parameters

        Returns:
            A boolean value indicating if the provided specification is supported
        """
        if access_method.method not in cls.supported_specialisations:
            return False

        if type_map(access_method.ordered_params) not in cls.supported_specialisations[access_method.method]:
            return False

        return True

    def apply_specialisation(self, access_method: AttributeAccess) -> "AttributeCollection":
        """
        Applies the given specialisation to the attribute to give a collection
        of next possible attributes once the specialisation has been applied
        Args:
            access_method:
                AttributeAccess object holding the access method and
                supplied parameters
        Returns:
            A collection of next possible attributes
        """
        # Use assert so it will be skipped when optimised
        assert self.supports_specialisation(access_method, access_method.ordered_params)

        function_access_signature: tuple[AccessMethod, FunctionParameterSignature] = \
            (
                access_method.method,
                (access_method.ordered_params, access_method.kw_params)
            )

        kw_params_mapping = {k:v for k,v in access_method.kw_params}

        next_types = self.specialisation_functions[function_access_signature]\
                      (*access_method.ordered_params, **kw_params_mapping)

        name = next_types.attribute_name if next_types.attribute_name else self.name

        next_attributes = list(map(
            lambda attr_classification:
                self.datatype_converter.convert_to_attributes(
                    attribute_name=name,
                    attribute_obj=attr_classification,
                    attribute_parent=self
            ), next_types.possible_attribute_options
        ))

        return AttributeCollection(next_attributes)

    @classmethod
    def supports_comparison(cls, comparison: Comparison) -> bool:
        """
        Returns a boolean indicating if a particular comparison is supported
        Args:
            comparison:
                Comparison being checked
        Returns:
            Boolean indicator
        """
        return comparison in cls.supported_comparisons

@dataclass
class AttributeCollection:
    attributes: list[AbstractAttribute]

    def get_next(self, access_method: AttributeAccess) -> "AttributeCollection":
        """
        Get the next attribute collection returned from applying the provided
        access method and parameters
        Args:
            access_method:
                AttributeAccess object holding the access method and
                supplied parameters
        Returns:
            AttributeCollection object representing the next possible attributes
        """
        next_attributes = list()

        for attribute in self.attributes:
            if attribute.supports_specialisation(access_method):
                corresponding_next_attribute_collection = attribute.apply_specialisation(access_method)
                next_attributes.extend(corresponding_next_attribute_collection.attributes)

        return AttributeCollection(next_attributes)


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
    def convert_to_attributes(self,
                              attribute_name: str,
                              obj: T,
                              parent: AbstractAttribute) -> AttributeCollection:
        """
        Converts the provided object and metadata into a collection of simplified
        attributes that it could represent
        Args:
            attribute_name:
                name of the attributes
            obj:
                object being processed
            parent:
                parent attribute
        Returns:
            AttributeCollection object represnting possible attributes
        """

class DatatypeConverter:
    """
    Centralised class that manages converting objects and information about
    them into their validated attributes
    Attributes:
        type_managers:
            List of type managers that handle assigning different objects
            different attributes. Priority of handling is the same as the
            order of this list
    """
    type_managers: list[AbstractAttributeTypeManager]


    def register_type_manager(self, type_manager: AbstractAttributeTypeManager):
        """Allows the datatype converter to use the provided type manager"""
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

    def validate_attribute(self, attr: Attribute) -> AttributeCollection:
        """
        Validates attribute and turns it into a collection of concrete attributes
        that actually correlate with the datatypes and shape of the datastructures
        that are used to access it
        Args:
            attr:
                Attribute to be validated
        Returns:
            Possible attributes including parents and possible types that can
            be reached by applying the operations applied to the provided attribute
        """

        # Find parent and order of operations

        reverse_access_order: list[AttributeAccess] = list()
        while isinstance(attr, Attribute):
            reverse_access_order.append(attr.access)
            attr = attr.parent

        access_order: list[AttributeAccess] = list(reversed(reverse_access_order))
        root_type: type = attr

        # how do we assign the parent???
        # Step through operations applied, validating at each stage
        # Terminating early if the attribute collection is ever empty


class SchemaCondition:
    ...

class ConditionVerifier:
    ...