""" Representing data queries without requiring specific reference
"""
from dataclasses import dataclass
from typing import Optional

import typing
import types

from datalib.utils.db_utils import flatten_to_list

@dataclass
class Attribute:
    name: str
    attribute_type: type
    parent: "type | Attribute"

    def get_next_types(self, attribute_name: str) -> list["Attribute"]:
        """
        Get the possible types of an attribute of this attribute of the specified name.
        Args:
            attribute_name:
                Name of the attribute to be checked for types
        Returns:
            A list of the possible next types
        Raises:
            AttributeError: If the attribute is not an attribute of self.attribute_type
        """
        if attribute_name in (hints := typing.get_type_hints(self.attribute_type)):
            if isinstance((next_type := hints[attribute_name]), type):
                return [Attribute(name = attribute_name, attribute_type = next_type, parent = self)]

            if isinstance(next_type, types.UnionType):
                next_types = typing.get_args(next_type)
                return list(map(
                    lambda t: Attribute(name = attribute_name, attribute_type = t, parent = self),
                    next_types
                ))
        raise AttributeError(f"{attribute_name} is not an attribute of {self.attribute_type.__name__}")

@dataclass
class ObjectAttribute:
    possible_attributes: list[Attribute]

    def is_still_possible(self) -> bool:
        """
        Returns a boolean indicating whether there are any remaining possible attributes
        Returns:
            Boolean indicating representing if it still possible to access this type
        """
        return len(self.possible_attributes) != 0

    def __getitem__(self, item: type | str | tuple[str, type]) -> "ObjectAttribute":
        """
        Return another ObjectAttribute object referring to an attribute of the attribute this object represents, or
        specialise this object to only represent objects of a specific type.
        Args:
            item:
                The required modification to this object, any type of parameter which is a string will check for an
                attribute of the possible types this represents, any type of parameter which is a type will restrict
                the returned ObjectAttribute to be of that type.
        Returns:
            ObjectAttribute representing a modification of the types stored in the current object.
        Raises:
            TypeError: If an argument of the wrong type is provided
        """
        if isinstance(item, type):
            possible_next_attributes: list[Attribute] = list[Attribute](filter(
                lambda attr: attr.attribute_type == item,
                self.possible_attributes
            ))

        else:
            item, wanted_type = process_indexing_arguments(item)

            possible_next_attributes: list[Attribute] = flatten_to_list(map(
                lambda a: a.get_next_types(item),
                self.possible_attributes
            ))

            if wanted_type is not None:
                possible_next_attributes = list[Attribute](filter(
                    lambda attr: attr.attribute_type == wanted_type,
                    possible_next_attributes
                ))

        return ObjectAttribute(possible_next_attributes)

    def get_comparable_attributes(self, other: "ObjectAttribute") -> list[tuple[Attribute, Attribute]]:
        """
        Get all pairings of identical types that could be represented by this ObjectAttribute and the other
        ObjectAttribute
        Args:
            other:
                Other ObjectAttribute value that we are comparing against
        Returns:
            A list holding all possible pairings
        """
        return [(i, j)
                for i in self.possible_attributes for j in other.possible_attributes
                if i.attribute_type == j.attribute_type
        ]


def process_indexing_arguments(item: tuple[str, Optional[type]] | str) -> tuple[str, Optional[type]]:
    """
    Unpacks the arguments when subscripting a type to the name and possible specified type
    Args:
        item:
            The provided arguments
    Returns:
        A tuple containing the name of the wanted attribute and nullable type representing the wanted type
    Raises:
        TypeError: If the wanted type is not a type or None, or the wanted field is not a string
    """
    # unpack arguments if necessary
    if isinstance(item, tuple):

        if len(item) == 2:
            item, wanted_type = item

        else:
            raise KeyError(f"Tuple arguments of size {len(item)} are not supported.")
    else:
        wanted_type = None

    wanted_type: Optional[type]

    # validate type of arguments

    if not isinstance(wanted_type, (type, type(None))):
        raise TypeError(f"Wanted type must be a type or None.")

    if not isinstance(item, str):
        raise TypeError(f"Wanted field must be provided as a string.")

    return item, wanted_type

def make_class_subscriptable[T](cls: type[T]) -> type[T]:
    """
    Allows a class to be subscriptable to return an ObjectAttribute object to allow for easier query creation
    Args:
        cls:
            The class to be modified
    Returns:
        The modified class with __class_getitem__ implemented
    Raises:
        AttributeError: If the provided class already implements __class_getitem__
    """
    if hasattr(cls, "__class_getitem__"):
        raise AttributeError(f"{cls.__name__} already implements __class_getitem__ making subscriptable would create a conflict")

    def __class_getitem__(item_: str | tuple[str, Optional[type]]) -> ObjectAttribute:
        """
        Returns an object representing an attribute of this class, a name must be provided with an optional type
        Args:
            item_:
                A string or tuple containing a string and optional type specifying the name and optionally, the
                specific type of the attribute to be represented by the returning object.
        Returns:

        """
        item, wanted_type = process_indexing_arguments(item_)
        item: str
        wanted_type: Optional[type]

        # process arguments into desired type

        if item not in (hints := typing.get_type_hints(cls)):
            raise AttributeError(f"{repr(item)} is not an attribute of {cls.__name__}")

        attribute_target = hints[item]

        if isinstance(attribute_target, type):
            attr = Attribute(name = item, attribute_type = attribute_target, parent = cls)

            if wanted_type is not None:
                if wanted_type != attribute_target:
                    # cannot be none here
                    # noinspection unresolved-references
                    raise TypeError(f"Supplied attribute {item} does not match requested type {wanted_type.__name__}")

            return ObjectAttribute(possible_attributes = [attr,])

        if isinstance(attribute_target, types.UnionType):
            possible_attribute_types = typing.get_args(attribute_target)

            if wanted_type is not None:
                possible_attribute_types: list[type] = list(filter(
                    lambda t: t == wanted_type,
                    possible_attribute_types
                ))

            possible_attributes: list[Attribute] = list(
                map(
                    lambda t: Attribute(name = item, attribute_type = t, parent = cls),
                    possible_attribute_types
                ))

            return ObjectAttribute(possible_attributes = possible_attributes)

        if isinstance(attribute_target, types.GenericAlias):
            ...

        raise AttributeError(f"{repr(item)} could not be resolved to an attribute of {cls.__name__}")

    cls.__class_getitem__ = __class_getitem__
    return cls
