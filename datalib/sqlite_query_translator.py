from dataclasses import dataclass
from typing import Any

from datalib.abstract_database_components import QueryTranslator, \
    QueryToBeResolved
from datalib.database_types import SQLiteString
from datalib.datatypes import Table
from datalib.queries import Query, Condition, ObjectAttribute, \
    ConditionCombination, ConditionOperator
from datalib.schema import TableStructure
from datalib import const
from lm_utils import object_to_dict


# text conversions

def select_all_from(table_name: str) -> str:
    return f"SELECT\n\t*\nFROM\n\t{table_name}"


def get_condition_opener() -> str:
    return "\nWHERE\n"


def end_select_statement() -> str:
    return f";"


def add_indent(string: str, indent_amount: int) -> str:
    lines = string.splitlines()
    line_prefix = "\n" + "\t" * indent_amount
    return line_prefix.join(lines)

@dataclass
class SQLiteQueryTranslator(QueryTranslator[SQLiteString]):
    schema: TableStructure

    # TODO query to be resolved needs to have a constructor for the output type
    # ORRRRR we could just use reflection to guarantee that it will exist
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[
        T, SQLiteString]:

        assert query.expected_type in self.schema.table_lookups

        table: Table = self.schema.table_lookups[query.expected_type]
        conditions = query.conditions


        query_string = select_all_from(table.name)
        if conditions:
            query_string += get_condition_opener()
            query_string += "\nAND\n".join(map(self.resolve_condition, conditions))

        query_string += end_select_statement()
        sqlite_query_string = SQLiteString(query_string)
        return QueryToBeResolved[T, SQLiteString](sqlite_query_string)

    def resolve_condition(self, condition: Condition) -> str:
        return self.resolve_condition_fragment(condition)

    def resolve_condition_fragment(self, fragment: Any) -> str:
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

    def translate_condition_combination_fragment(self, fragment: Condition) -> str:
        return add_indent(
            f"(\n\t{self.resolve_condition_fragment(fragment.left)}\n{fragment.operator.value()}\n\t{self.resolve_condition_fragment(fragment.right)}\n)",
            1)

    def translate_condition_operator_fragment(self, fragment: Condition) -> str:
        assert isinstance(fragment, Condition)

        resolved_left = self.resolve_condition_fragment(fragment.left)
        operation = fragment.operator.value
        resolved_right = self.resolve_condition_fragment(fragment.right)

        return f"({resolved_left} {operation} {resolved_right})"

    def translate_non_nested_field(self, fragment: ObjectAttribute) -> str:
        assert isinstance(fragment.object_type, type), "Non-nested fields require the parent of an attribute to be a type"
        table = self.schema.table_lookups[fragment.object_type]
        field_name = fragment.attribute_name

        return f"{table.name}.{field_name}"

    def translate_standard_constant(self, fragment: const.BASIC_TYPE_HINT) -> str:
        del self # To allow for a standard signature
        return str(fragment)

    def translate_nested_field(self, fragment: ObjectAttribute) -> str:
        # TODO verify functionality after database implementation

        assert isinstance(fragment.object_type, ObjectAttribute)
        assert fragment.attribute_type in self.schema.table_lookups

"""
Thoughts

we want a query coming from

select(table).where(table[field] == ...)

okay so we probably want a way to process the table[field] part (both left and right of the condition)

adapting the select(table) shouldn't be that much of an issue

all we need is
SELECT
    *
FROM
    table.name
as the general query string

how do we translate the condition

how do we get the corresponding fields???
does the table object need a field name mapper

the query contract should guarantee that an conditions contain valid fields
a condition however, does not validate that this comparison is valid?
or does it fully in the ObjectAttribute

i think it validates that the types are valid but not that it works properly

we can take a recursive approach to unpacking conditions

conditions have a structure like this:

conition LEFT OPERATOR RIGHT
where LEFT = CONDITION | FIELD
and 
RIGHT = CONDITION | FIELD
so we just give them something like
condition => (RESOLVE(LEFT) OPERATOR RESOLVE(RIGHT))

SELECT
    *
FROM
    table.name
WHERE
    (
        thing == otherthing
    )
WHERE
    (
        (
            thing == otherthing
        ) OR (
            thing == otherthing
        )
    )
and now resolve is the issue
"""
