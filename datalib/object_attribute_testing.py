from dataclasses import dataclass
from typing import Optional

import typing
import types

from .db_utils import flatten_to_list

@dataclass
class Attribute:
    name: str
    attribute_type: type
    parent: "type | Attribute"

    def get_next_types(self, attribute_name: str) -> list["Attribute"]:
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

    def __getitem__(self, item):
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


def process_indexing_arguments(item: tuple[str, type] | tuple[str, None] | str):
    # unpack arguments if necessary
    if isinstance(item, tuple):
        if len(item) == 2:
            item, wanted_type = item

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

def make_class_subscriptable(cls: type):
    def __class_getitem__(item) -> ObjectAttribute:
        item, wanted_type = process_indexing_arguments(item)

        # process arguments into desired type

        if item not in (hints := typing.get_type_hints(cls)):
            raise KeyError(f"{repr(item)} is not an attribute of {cls.__name__}")

        attribute_target = hints[item]

        if isinstance(attribute_target, type):
            attr = Attribute(name = item, attribute_type = attribute_target, parent = cls)

            if wanted_type is not None:
                if wanted_type != attribute_target:
                    # cannot be none here
                    # noinspection unresolved-references
                    raise KeyError(f"Supplied attribute {item} does not match requested type {wanted_type.__name__}")

            return ObjectAttribute(possible_attributes = [attr,])

        if isinstance(attribute_target, types.UnionType):
            possible_attribute_types = typing.get_args(attribute_target)

            if wanted_type is not None:
                possible_attribute_types: filter[type] = filter(wanted_type.__eq__, possible_attribute_types)

            possible_attributes: list[Attribute] = list(map(
                lambda t: Attribute(name = item, attribute_type = t, parent = cls),
                possible_attribute_types
            ))

            return ObjectAttribute(possible_attributes = possible_attributes)

        raise KeyError(f"{repr(item)} could not be resolved to an attribute of {cls.__name__}")

    cls.__class_getitem__ = __class_getitem__
