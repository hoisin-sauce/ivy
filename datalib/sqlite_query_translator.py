from datalib.abstract_database_components import QueryTranslator, \
    QueryToBeResolved
from datalib.database_types import SQLiteString
from datalib.datatypes import Table
from datalib.queries import Query, Condition, ObjectAttribute, \
    ConditionCombination, ConditionOperator
from datalib.schema import TableStructure
from typing import Any


# text conversions

def select_all_from(table_name: str) -> str:
    return f"SELECT\n\t*\nFROM\n\t{table_name}\n"


def get_condition_opener() -> str:
    return "WHERE"


def end_select_statement() -> str:
    return f";"


def add_indent(string: str, indent_amount: int) -> str:
    lines = string.splitlines()
    line_prefix = "\n" + "\t" * indent_amount
    return line_prefix.join(lines)


class SQLiteQueryTranslator(QueryTranslator[SQLiteString]):
    schema: TableStructure

    # TODO query to be resolved needs to have a constructor for the output type
    # ORRRRR we could just use reflection to guarantee that it will exist
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[
        T, SQLiteString]:
        table: Table = self.schema.table_lookups[query.expected_type]
        conditions = query.conditions

        # how do we approach instantiating a boilerplate class
        raise NotImplementedError("Query format not yet supported")

    def resolve_condition(self, condition: Condition) -> str:
        return self.resolve_condition(condition)

    def resolve_condition_fragment(self, fragment: Any) -> str:
        # we want to implement conversion implementation here
        # this is for logic flow
        # We want explicitly isinstance checks rather than match because????
        # note: this code is definitely not backwards compatible
        # The whole framework requires typing to function as intended ideally
        if isinstance(fragment, Condition):
            if isinstance(fragment.operator, ConditionCombination):
                # indent sub block
                return add_indent(
                    f"(\n\t{self.resolve_condition_fragment(fragment.left)}\n{fragment.operator.value()}\n\t{self.resolve_condition_fragment(fragment.right)}\n)", 1)
                raise NotImplementedError("Combinations are not yet supported")
            elif isinstance(fragment.operator, ConditionOperator):
                # have inline
                # note that we will have to implement in here
                return f"({self.resolve_condition_fragment(fragment.left)} {fragment.operator.value()} {self.resolve_condition_fragment(fragment.right)})"
                raise NotImplementedError("Operators are not yet supported")
            else:
                # Note - should be unreachable
                raise NotImplementedError(
                    "Supplied condition type is not supported")

        if isinstance(fragment, ObjectAttribute):
            # resolve the table necessities
            ...
            raise NotImplementedError("ObjectAttributes are not yet supported")

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

        raise NotImplementedError("Data values are not yet supported")


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
