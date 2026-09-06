from dataclasses import dataclass
from enum import Enum, auto
from types import ModuleType

from datalib.utils.type_processing import get_types_in_module

class AccessMethod(Enum):
    """
    Represents the method used to create an attribute object
    """
    GETATTR = auto()
    GETITEM = auto()
    CALL = auto()

class Comparison(Enum):
    """
    Represents arbitrary comparisons between conditions and attributes
    """

class AttributeComparison(Comparison):
    """
    Represents comparisons between attributes
    """
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    CONTAINS = auto()

class ConditionComparison(Comparison):
    """
    Represents comparisons between conditions
    """
    AND = auto()
    OR = auto()

@dataclass
class Condition:
    """
    Represents a condition. Comparisons using & and | with other conditions
    will return another condition object which is a combination of the two.

    Attributes:
        left: The left side of the condition
        right: The right side of the condition
        operator: The comparison being made between the two sides of the condition
    """
    left: object
    right: object
    operator: Comparison

    def __and__(self, other: "Condition") -> "Condition":
        if isinstance(other, Condition):
            return Condition(left=self, right=other,
                             operator=ConditionComparison.AND)

        raise TypeError("Conditions can only be compared with other conditions")

    def __or__(self, other: "Condition") -> "Condition":
        if isinstance(other, Condition):
            return Condition(left=self, right=other,
                             operator=ConditionComparison.OR)

        raise TypeError("Conditions can only be compared with other conditions")

@dataclass
class AttributeAccess:
    """
    Class describing how an attribute was access in a hashable format
    Attributes:
        method:
            AccessMethod enum indicating how the attribute was accessed
        ordered_params:
            Tuple containing the ordered arguments passed to the function
        kw_params:
            Tuple containing key-value pairs of the kwargs passed to the function
    """
    method: AccessMethod
    ordered_params: tuple[object, ...]
    kw_params: tuple[tuple[str, object]]

@dataclass
class Attribute:
    """
    Stores and allows for arbitrary __getitem__ and __getattr__ on an object to allow for database agnostic query creation
    Comparisons with an object of this type will return a condition rather than a boolean

    Attributes:
        access: The method used to access the attribute
        parent: The parent object that this attribute belongs to
    """
    access: AttributeAccess
    parent: "type | Attribute"


    def __getattr__(self, item: str) -> "Attribute":
        return Attribute(
            access=AttributeAccess(
                method=AccessMethod.GETATTR,
                ordered_params=(item,),
                kw_params=tuple()),
            parent=self)

    def __getitem__(self, item: object) -> "Attribute":
            return Attribute(
                access=AttributeAccess(
                    method=AccessMethod.GETITEM,
                    ordered_params=(item,),
                    kw_params=tuple()),
                parent=self)

    def __le__(self, other: object) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.LE)

    def __ge__(self, other: object) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.GE)

    def __lt__(self, other: object) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.LT)

    def __gt__(self, other: object) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.GT)

    # We want to store the calls here so its alright if eq isn't actually a bool for simplifying syntax
    # noinspection method-overriding
    def __eq__(self, other: object) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.EQ)

    def __neq__(self, other: object) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.NEQ)

    def __contains__(self, item: object) -> Condition:
        return Condition(left=self, right=item,
                         operator=AttributeComparison.CONTAINS)

    def __call__(self, *args, **kwargs):
        return Attribute(
            access=AttributeAccess(
                method=AccessMethod.CALL,
                ordered_params=args,
                kw_params=tuple(kwargs.items())),
            parent=self)


class QueryableTable:
    """
    Parent class for queryable classes, if that is the preferred method of implementation
    """
    def __class_getitem__(cls, item: str) -> Attribute:
        return Attribute(
            access=AttributeAccess(
                method=AccessMethod.GETITEM,
                ordered_params=(item,),
                kw_params=tuple()
            ),
            parent=cls)

def make_class_queryable(cls: type) -> None:
    """
    Makes the provided class subscriptable to produce queries
    Args:
        cls:
            The class to be changed
    """
    setattr(cls, '__class_getitem__', QueryableTable.__class_getitem__)

def make_module_queryable(module: ModuleType) -> None:
    for cls in get_types_in_module(module):
        make_class_queryable(cls)