"""Standardised interface for naming tables

TODO approach should be more planned out
"""
from abc import abstractmethod, ABCMeta
from datalib.datatypes import Table


class Namer(metaclass=ABCMeta):
    @abstractmethod
    def name_table_with_module(self, datatype: type) -> str:
        ...
    @abstractmethod
    def name_table_without_module(self, datatype: type) -> str:
        ...

    @abstractmethod
    def name_union_alias(self, parent: Table, field_name: str) -> str:
        ...

    @abstractmethod
    def name_union_selector(self, parent: Table, field_name: str) -> str:
        ...

    @abstractmethod
    def name_union_member(self, parent: Table, field_name: str, datatype: type) -> str:
        ...

    @abstractmethod
    def name_enum_alias(self, field_name: str):
        ...

    @abstractmethod
    def name_iterator_inner(self, parent: Table, field_name: str) -> str:
        ...

    @abstractmethod
    def name_iterator_link_table(self, parent: Table, field_name: str, datatype:type) -> str:
        ...

class StandardTableNamer(Namer):
    def name_table_with_module(self, datatype: type) -> str:
        return datatype.__module__ + "__" + datatype.__name__

    def name_table_without_module(self, datatype: type) -> str:
        return datatype.__name__

    def name_union_alias(self, parent: Table, field_name: str) -> str:
        return parent.name + "_" + field_name

    def name_union_selector(self, parent: Table, field_name: str) -> str:
        return self.name_union_alias(parent, field_name) + "__union__selector__"

    def name_union_member(self, parent: Table, field_name: str, datatype: type) -> str:
        return self.name_union_alias(parent, field_name) + f"__union_member_{datatype.__name__}__"

    def name_enum_alias(self, field_name: str) -> str:
        return "__enum__" + field_name

    def name_iterator_inner(self, parent: Table, field_name: str) -> str:
        return parent.name + field_name + "__iter_inner__"

    def name_iterator_link_table(self, parent: Table, field_name: str, datatype: type) -> str:
        return f"{parent.name}_{field_name}__iter_link__{datatype.__module__}_{datatype.__name__}"
