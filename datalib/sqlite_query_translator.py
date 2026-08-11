from datalib.abstract_database_components import QueryTranslator, QueryToBeResolved
from datalib.database_types import SQLiteString
from datalib.datatypes import Table
from datalib.naming import FieldNamer
from datalib.queries import Query
from datalib.schema import TableStructure


class SQLiteQueryTranslator(QueryTranslator[SQLiteString]):
    schema: TableStructure
    namer: FieldNamer
    # TODO query to be resolved needs to have a constructor for the output type
    # ORRRRR we could just use reflection to guarantee that it will exist
    def translate_query[T](self, query: Query[T]) -> QueryToBeResolved[T, SQLiteString]:
        table: Table = self.schema.table_lookups[query.expected_type]
        conditions = query.conditions

        # how do we approach instantiating a boilerplate class

"""
Thoughts

we want a query coming from

select(table).where(table[field] == ...)

okay so we probably want a way to process the table[field] part (both left and right of the condition)

adapting the select(table) shouldn't be that much of an issue


"""