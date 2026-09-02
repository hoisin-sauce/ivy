""" Holds the representation of attributes under the speculative query system
"""
from dataclasses import dataclass

import typing
import types

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
            # TODO how can we standardise this handling of isinstance chains
            # it is a repeated pattern that shows up everywhere

            next_type = hints[attribute_name]

            if isinstance(next_type, type):
                return [Attribute(name = attribute_name, attribute_type = next_type, parent = self)]

            if isinstance(next_type, types.UnionType):
                next_types = typing.get_args(next_type)
                return list(map(
                    lambda t: Attribute(name = attribute_name, attribute_type = t, parent = self),
                    next_types
                ))
        raise AttributeError(f"{attribute_name} is not an attribute of {self.attribute_type.__name__}")
