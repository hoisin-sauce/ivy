"""Standardised interface for naming tables

TODO approach should be more planned out
"""
from abc import abstractmethod, ABCMeta
from datalib.datatypes import Table


class Namer(metaclass=ABCMeta):
    ...

class TableNamer(Namer, metaclass=ABCMeta):
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
    def name_union_member(self, parent: Table, field_name: str,
                          datatype: type) -> str:
        ...

    @abstractmethod
    def name_enum_alias(self, field_name: str):
        ...

    @abstractmethod
    def name_iterator_inner(self, parent: Table, field_name: str) -> str:
        ...

    @abstractmethod
    def name_iterator_link_table(self, parent: Table, field_name: str,
                                 datatype: type) -> str:
        ...

    @abstractmethod
    def name_iterator_field_to_parent(self) -> str:
        ...

    @abstractmethod
    def name_iterator_field_to_data(self) -> str:
        ...

    @abstractmethod
    def name_primary_key(self, table: Table) -> str:
        ...

class StandardTableNamer(TableNamer):
    def sanitise_module_name(self, module_name: str) -> str:
        del self
        return module_name.replace(".", "_")

    def name_table_with_module(self, datatype: type) -> str:
        return (self.sanitise_module_name(datatype.__module__) + "__" +
                datatype.__name__)

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
        return parent.name + "__" + field_name + "__iter_inner__"

    def name_iterator_link_table(self, parent: Table, field_name: str, datatype: type) -> str:
        return f"{parent.name}_{field_name}__iter_link__{datatype.__module__}_{datatype.__name__}"

    def name_iterator_field_to_parent(self) -> str:
        return "parent_field"

    def name_iterator_field_to_data(self) -> str:
        return "field_to_data"

    def name_primary_key(self, table: Table) -> str:
        return f"{table.name}id"
