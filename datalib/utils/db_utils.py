"""Generic utility functions, may be refactored into multiple files later on.
"""
from itertools import chain
from typing import Any, Iterable
import typing

def safe_is_subclass(obj: Any, class_or_tuple: typing.Type|tuple[typing.Type]) -> bool:
    """
    Safe version of is_subclass for an unknown datatype, does not raise an
    exception if the object is not a type.
    Args:
        obj
            The object to be checked
        class_or_tuple
            A class or tuple of classes to be checked
    Returns:
        Boolean representing if the object is a subclass of the
        provided class or one of the classes in the provided tuple
    """
    return isinstance(obj, type) and issubclass(obj, class_or_tuple)

def flatten_to_list[T](two_d_iterable: Iterable[Iterable[T]]) -> list[T]:
    """
    Flattens 2-dimesional iterable into a list.
    Args:
        two_d_iterable:
            Second dimensional iterable to be flattened
    Returns:
        List containing the flattened iterable
    """
    return list(chain(*two_d_iterable))

def flatten_to_set[T](two_d_iterable: Iterable[Iterable[T]]) -> set[T]:
    """
        Flattens 2-dimesional iterable into a set.
        Args:
            two_d_iterable:
                Second dimensional iterable to be flattened
        Returns:
            Set containing the flattened iterable
        """
    return set(chain(*two_d_iterable))

def public_dir(obj: Any) -> list[str]:
    """
    Returns a list of the public attributes in the provided object.
    Args:
        obj
            Object to be processed
    Returns:
        List containing the public attributes in the provided object
    """
    return list(
        filter(
            lambda x: not x.startswith('_'),
            dir(obj)
        )
    )

def remove_duplicates_preserving_order[T](lst: list[T]) -> list[T]:
    """
    Remove all duplicate entries from a list whilst preserving order.
    Requires all elements in the list to be hashable.
    Args:
        lst:
            List of elements to be checked for duplication
    Returns:
        List of elements without any duplicate entries
    Raises:
        TypeError
            If a value is not hashable
    """

    seen = set()
    seen_add = seen.add

    # this allows for it to be called every iteration
    # noinspection none-function-assignment
    return [x for x in lst if not (x in seen or seen_add(x))]