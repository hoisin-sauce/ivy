from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

class AccessMethod(Enum):
    GETATTR = auto()
    GETITEM = auto()

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
    left: Any
    right: Any
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
class Attribute:
    """
    Stores and allows for arbitrary __getitem__ and __getattr__ on an object to allow for database agnostic query creation
    Comparisons with an object of this type will return a condition rather than a boolean

    Attributes:
        accessed_by: The type of access that was used to create this attribute, e.g. a[thing] or a.thing
        accessed_with: The parameter passed to the access type, so "thing" in the above example
        parent: The parent object that this attribute belongs to
    """
    accessed_by: AccessMethod
    accessed_with: Any
    parent: "type | Attribute"


    def __getattr__(self, item: str) -> "Attribute":
        return Attribute(accessed_by=AccessMethod.GETATTR,
                         accessed_with=item,
                         parent=self)

    def __getitem__(self, item: Any) -> "Attribute":
            return Attribute(accessed_by=AccessMethod.GETITEM,
                             accessed_with=item,
                             parent=self)

    def __le__(self, other: Any) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.LE)

    def __ge__(self, other: Any) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.GE)

    def __lt__(self, other: Any) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.LT)

    def __gt__(self, other: Any) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.GT)

    # We want to store the calls here so its alright if eq isn't actually a bool for simplifying syntax
    # noinspection method-overriding
    def __eq__(self, other: Any) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.EQ)

    def __neq__(self, other: Any) -> Condition:
        return Condition(left=self, right=other,
                         operator=AttributeComparison.NEQ)

    def __contains__(self, item: Any) -> Condition:
        return Condition(left=self, right=item,
                         operator=AttributeComparison.CONTAINS)
