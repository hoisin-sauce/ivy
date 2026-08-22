from dataclasses import dataclass
from typing import Optional

import typing
import types

@dataclass
class Attribute:
    name: str
    attribute_type: type
    parent: type

@dataclass
class ObjectAttribute:
    possible_attributes: list[Attribute]

def make_class_subscriptable(cls: type):
    def __class_getitem__(item) -> ObjectAttribute:
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

        # process arguements into desired type

        if item not in (hints := typing.get_type_hints(cls)):
            raise KeyError(f"{repr(item)} is not an attribute of {cls.__name__}")

        attribute_target = hints[item]

        if isinstance(attribute_target, type):
            attr = Attribute(name = item, attribute_type = attribute_target, parent = cls)

            return ObjectAttribute(possible_attributes = [attr,])

        if isinstance(attribute_target, types.UnionType):
            possible_attribute_types = typing.get_args(attribute_target)
            possible_attributes = list(map(
                lambda t: Attribute(name = item, attribute_type = t, parent = cls),
                possible_attribute_types
            ))

            return ObjectAttribute(possible_attributes = possible_attributes)

        raise KeyError(f"{repr(item)} could not be resolved to an attribute of {cls.__name__}")


    cls.__class_getitem__ = __class_getitem__