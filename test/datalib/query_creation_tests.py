from datalib.no_data import NoDatabaseManager
from datalib.queries import *

blank_database_interface = NoDatabaseManager()

def test_basic_query():
    from test.datalib import test_data_query_tables as query_data

    q = Query(query_data.SampleChild, blank_database_interface.execute_query)

    assert q.expected_type == query_data.SampleChild
    assert not q.conditions

def test_query_from_interface():
    from test.datalib import test_data_query_tables as query_data

    q = blank_database_interface.select(query_data.SampleChild)

    assert q.expected_type == query_data.SampleChild
    assert not q.conditions

def test_query_basic_valid_condition():
    from test.datalib import test_data_query_tables as query_data
    make_module_subscriptable(query_data)

    q = blank_database_interface.select(query_data.SampleChild).where(
        query_data.SampleChild["a"] == 1 # TODO make it so that this is accepted by the linter, unsure as to how
    )

    assert q.expected_type == query_data.SampleChild
    assert len(q.conditions) == 1
    assert isinstance(q.conditions[0].left, ObjectAttribute)
    assert isinstance(q.conditions[0].right, int)

def test_query_subscripting_field():
    from test.datalib import test_data_query_tables as query_data
    make_module_subscriptable(query_data)

    q = blank_database_interface.select(query_data.SampleGrandparent).where(
        query_data.SampleGrandparent["parent"]["child"] == query_data.SampleGrandparent["child"]
    )

    assert q.expected_type == query_data.SampleGrandparent
    assert len(q.conditions) == 1
    assert isinstance(q.conditions[0].left, ObjectAttribute)
    assert isinstance(q.conditions[0].left.object_type, ObjectAttribute)
    assert isinstance(q.conditions[0].right, ObjectAttribute)

def test_query_combination():
    query_1 = Query(int, blank_database_interface.execute_query)
    query_2 = Query(str, blank_database_interface.execute_query)
    combined_query: QueryBundle[int, str] = QueryBundle.create((query_1, query_2))
    query_3 = Query(bool, blank_database_interface.execute_query)
    doubly_combined_query = QueryBundle.create((query_1, query_2, query_3))

    # TODO write assertion properties

if __name__ == "__main__":
    test_basic_query()
    test_query_from_interface()
    test_query_basic_valid_condition()
    test_query_subscripting_field()
    test_query_combination()