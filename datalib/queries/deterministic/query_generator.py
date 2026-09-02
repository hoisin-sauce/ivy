"""Implementation of the QueryGenerator instance for a DeterministicQuery
"""
from typing import Callable, Generator

from datalib.database.abstract_database_components import QueryGenerator
from datalib.queries.deterministic import DeterministicQuery, queries

class DeterministicQueryGenerator(QueryGenerator[DeterministicQuery]):
    def get_query[T](self, datatype: type[T], executor: Callable[[queries.Query[T]], Generator[T, None, None]]) -> queries.Query[T]:
        return queries.Query(datatype, executor)
