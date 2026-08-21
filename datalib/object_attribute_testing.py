import typing

class Attribute:
    name: str
    attribute_type: type
    parent: type

class ObjectAttribute:
    possible_attributes: list[Attribute]

def make_class_subscriptable(cls: type):
    def __class_getitem__(item):
        if item not in typing.get_type_hints(cls).keys():
            raise KeyError(f"{repr(item)} is not an attribute of {cls.__name__}")
    cls.__class_getitem__ = __class_getitem__