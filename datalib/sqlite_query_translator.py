from dataclasses import dataclass
from secrets import token_urlsafe
from typing import Any, Optional, Iterable

from datalib.abstract_database_components import QueryTranslator, \
    QueryToBeResolved
from datalib.database_types import SQLiteString
from datalib.datatypes import Table
from datalib.queries import Query, Condition, ObjectAttribute, \
    ConditionCombination, ConditionOperator
from datalib.schema import TableStructure
from datalib import const
from lm_utils import object_to_dict, remove_duplicates_preserving_order


# text conversions

def select_all_from(table_name: str) -> str:
    return f"SELECT\n\t{table_name}.*\nFROM\n\t{table_name}"


def get_condition_opener() -> str:
    return "\nWHERE\n"


def end_select_statement() -> str:
    return f";"

def join_statement(new_table_name: str, new_table_join_on: str,
                   old_table_name: str, old_table_join_on: str) -> str:
    return (f"\nINNER JOIN {new_table_name} "
            f"ON {new_table_name}.{new_table_join_on} "
            f"= {old_table_name}.{old_table_join_on}")


def add_indent(string: str, indent_amount: int) -> str:
    lines = string.splitlines()
    line_prefix = "\n" + "\t" * indent_amount
    return line_prefix.join(lines)

@dataclass
class SQLiteConditionFragment:
    where_string: str
    join_strings: list[str] # order is necessary

    def get_tuple(self) -> tuple[str, list[str]]:
        return self.where_string, self.join_strings

# Note - only expose this
@dataclass
class SQLiteQueryTranslator(QueryTranslator[SQLiteString]):
    schema: TableStructure

    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[
        T, SQLiteString]:

        assert query.expected_type in self.schema.table_lookups

        table: Table = self.schema.table_lookups[query.expected_type]
        conditions = query.conditions


        query_string = select_all_from(table.name)

        if conditions:
            where_string, join_string = self.resolve_conditions(conditions)

            query_string += join_string
            query_string += where_string

        query_string += end_select_statement()
        sqlite_query_string = SQLiteString(query_string)
        return QueryToBeResolved[T, SQLiteString](sqlite_query_string, query.expected_type)

    def resolve_conditions(self, conditions: Iterable[Condition]) -> tuple[str, str]:
        """
        Resolves a container of conditions and returns the full join and where clauses
        Args:
            conditions:
                Container of conditions that need to be resolved
        Returns:
            A tuple in the form (where_string, join_string) where
            join_string is the string representing the entire text for the join
            statements needing to be processed and where_string represents the
            conditions applied to data
        """
        join_string = ""
        where_string = get_condition_opener()

        for condition in conditions:
            sub_where_string, sub_join_string = \
                self.resolve_condition(condition).get_tuple()

            join_string += "".join(sub_join_string)
            where_string += sub_where_string

        return where_string, join_string

    def resolve_condition(self, condition: Condition) -> SQLiteConditionFragment:
        """
        Resolves a condition to its string components
        Args:
            condition:
                The condition being resolved
        Returns:
            A tuple representing the where component and inner join components
            that need to be added to the overall query string
        """
        return self.resolve_condition_fragment(condition)

    def resolve_condition_fragment(self, fragment: Any) -> SQLiteConditionFragment:
        # we want to implement conversion implementation here
        # this is for logic flow # TODO refactor for this
        # We want explicitly isinstance checks rather than match because????
        # note: this code is definitely not backwards compatible
        # The whole framework requires typing to function as intended ideally

        if isinstance(fragment, Condition):
            if isinstance(fragment.operator, ConditionCombination):
                # indent sub block
                return self.translate_condition_combination_fragment(fragment)
            elif isinstance(fragment.operator, ConditionOperator):
                # have inline
                # note that we will have to implement in here
                return self.translate_condition_operator_fragment(fragment)
            else:
                # Note - should be unreachable
                raise NotImplementedError(
                    "Supplied condition type is not supported")

        if isinstance(fragment, ObjectAttribute):
            # resolve the table necessities
            ...
            if isinstance(fragment.object_type, ObjectAttribute):
                return self.translate_nested_field(fragment)

            if isinstance(fragment.object_type, type):
                return self.translate_non_nested_field(fragment)

            raise NotImplementedError(f"ObjectAttributes of parent type {type(fragment.object_type).__name__} are not yet supported")

        if isinstance(fragment, type):
            # resolve table reference and find primary key
            # ooooh this one might have some issues
            # we can't restructure schema for this one
            ...
            raise NotImplementedError(
                "References to classes as a whole are not yet supported")

        # We are now left with only a sepecific value to compare to not just a
        # Different part of the table
        # Should we verify functionality of the SQL?
        # I think that we have to resolve the issues
        # We are now approached with the idea of concurrency
        # What strategy is to be
        if isinstance(fragment, tuple(const.BASIC_TYPES)):
            return self.translate_standard_constant(fragment)

        raise NotImplementedError("Data values are not yet supported")

    def translate_condition_combination_fragment(self, fragment: Condition) -> SQLiteConditionFragment:
        assert isinstance(fragment, Condition)
        assert isinstance(fragment.operator, ConditionCombination)

        resolved_left, join_l = self.resolve_condition_fragment(fragment.left).get_tuple()
        resolved_operator = fragment.operator.value
        resolved_right, join_r = self.resolve_condition_fragment(fragment.right).get_tuple()

        where_string: str = add_indent(
            f"(\n\t{resolved_left}\n{resolved_operator}\n\t{resolved_right}\n)",
            1)

        join_strings: list[str] = remove_duplicates_preserving_order(join_l + join_r)

        return SQLiteConditionFragment(where_string, join_strings)

    def translate_condition_operator_fragment(self, fragment: Condition) -> SQLiteConditionFragment:
        assert isinstance(fragment, Condition)
        assert isinstance(fragment.operator, ConditionOperator)

        resolved_left, join_l = self.resolve_condition_fragment(fragment.left).get_tuple()
        operation = fragment.operator.value
        resolved_right, join_r = self.resolve_condition_fragment(fragment.right).get_tuple()

        where_string = f"({resolved_left} {operation} {resolved_right})"

        join_strings: list[str] = remove_duplicates_preserving_order(join_l + join_r)

        return SQLiteConditionFragment(where_string, join_strings)

    def translate_non_nested_field(self, fragment: ObjectAttribute) -> SQLiteConditionFragment:
        """
        Returns the resolved field name for an immediate attribute of an object,
        e.g. A.B -> table_name_for_A.B and an empty literal,
        representing no join statement necessary.
        Args:
            fragment:
                The ObjectAttribute which represents a non-nested field
        Returns:
            Tuple containing the resolved field name and its join
        """
        assert isinstance(fragment.object_type, type), "Non-nested fields require the parent of an attribute to be a type"

        table = self.schema.table_lookups[fragment.object_type]
        field_name = fragment.attribute_name

        return SQLiteConditionFragment(f"{table.name}.{field_name}", list())

    def translate_standard_constant(self, fragment: const.BASIC_TYPE_HINT) -> SQLiteConditionFragment:
        del self # To allow for a standard signature
        # TODO fix sql injection
        return SQLiteConditionFragment(str(fragment), list())

    def translate_nested_field(self, fragment: ObjectAttribute) -> SQLiteConditionFragment:

        assert isinstance(fragment.object_type, ObjectAttribute)
        assert fragment.attribute_type in self.schema.table_lookups

        parent = fragment.object_type
        parent_type = parent.attribute_type

        assert isinstance(parent_type, type), "GenericAlias fields are not yet supported"

        table = self.schema.table_lookups[parent_type]
        field_name = fragment.attribute_name

        where_string = f"{table.name}.{field_name}"

        required_joins = list()

        while isinstance(parent, ObjectAttribute):
            # TODO refactor, logic is a bit complex here
            # resolve what we are joining to
            parent_attribute = parent.attribute_type
            assert isinstance(parent_attribute, type), "Complex fields are not yet supported"

            parent_table = self.schema.table_lookups[parent_attribute]
            parent_primary_key = parent_table.get_primary_key()

            # resolve what we are joining from
            grandparent = parent.object_type
            if isinstance(grandparent, ObjectAttribute):
                join_from  = grandparent.attribute_type
                assert isinstance(join_from, type)
                grandparent_table = self.schema.table_lookups[join_from]
                grandparent_foreign_key = grandparent_table.get_field(
                    parent.attribute_name)

                if not grandparent_foreign_key:
                    raise KeyError(
                        f"{parent.attribute_name} is not a valid member of {grandparent_table.name}")

            elif isinstance(grandparent, type):
                grandparent_table = self.schema.table_lookups[grandparent]
                grandparent_foreign_key = grandparent_table.get_field(
                    parent.attribute_name)

                if not grandparent_foreign_key:
                    raise KeyError(
                        f"{parent.attribute_name} is not a valid member of {grandparent_table.name}")
            else:
                raise NotImplementedError(f"Object attribute parents of type {type(grandparent).__name__} are not yet supported")


            join_string = join_statement(parent_table.name, parent_primary_key.name, grandparent_table.name, grandparent_foreign_key.name)

            required_joins = [join_string] + required_joins

            parent = grandparent

        return SQLiteConditionFragment(where_string, required_joins)


# TODO refactor where statements into their own functions
# TODO allow for the resolving of union fields
# Note - my honest opinion is that this strategy of resolving the fields at present is a bit naive in approaching resolving union fields
