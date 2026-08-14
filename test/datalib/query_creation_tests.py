from types import ModuleType

from datalib.abstract_database_components import QueryToBeResolved
from datalib.database_constraint import PrimaryKeyResolver, \
    StandardPrimaryKeyResolver
from datalib.database_types import SQLiteString
from datalib.naming import StandardTableNamer
from datalib.no_data import NoDatabaseManager
from datalib.queries import *
from datalib.sqlite_query_translator import SQLiteQueryTranslator
from datalib.graph import ClassDependencyGraph
from datalib.schema import TableStructure
from datalib.sqlite_schema_translator import SQLiteSchemaTranslator

from lm_utils import remove_whitespace

blank_database_interface = NoDatabaseManager()

def test_basic_query():
    from test.datalib import test_data_query_tables as query_data

    q = Query(query_data.SampleChild, blank_database_interface.execute_query)

    assert q.expected_type == query_data.SampleChild
    assert not q.conditions

    translator = setup_translation_environment(query_data)
    translated_q = translator.translate_query(q)

    expected_query = ("SELECT"
                      "test_datalib_test_data_query_tables__SampleChild.*"
                      "FROM"
                      "test_datalib_test_data_query_tables__SampleChild;")

    assert remove_whitespace(translated_q.query_to_database) == remove_whitespace(expected_query)

def test_query_from_interface():
    from test.datalib import test_data_query_tables as query_data

    q = blank_database_interface.select(query_data.SampleChild)

    assert q.expected_type == query_data.SampleChild
    assert not q.conditions

    translator = setup_translation_environment(query_data)
    translated_q = translator.translate_query(q)

    expected_query = ("SELECT"
                      "test_datalib_test_data_query_tables__SampleChild.*"
                      "FROM"
                      "test_datalib_test_data_query_tables__SampleChild;")

    assert remove_whitespace(translated_q.query_to_database) == remove_whitespace(expected_query)

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

    translator = setup_translation_environment(query_data)
    translated_q = translator.translate_query(q)

    expected_query = ("SELECT"
                      "test_datalib_test_data_query_tables__SampleChild.*"
                      "FROM"
                      "test_datalib_test_data_query_tables__SampleChild"
                      "WHERE"
                      "(test_datalib_test_data_query_tables__SampleChild.a = 1);")

    assert remove_whitespace(translated_q.query_to_database) == remove_whitespace(expected_query)

def test_query_subscripting_field():
    from test.datalib import test_data_query_tables as query_data
    make_module_subscriptable(query_data)

    q = blank_database_interface.select(query_data.SampleGrandparent).where(
        query_data.SampleGrandparent["parent"]["child"] == query_data.SampleGrandparent["child"]
    )

    assert q.expected_type == query_data.SampleGrandparent
    assert len(q.conditions) == 1
    assert isinstance(q.conditions[0].left, ObjectAttribute)
    # noinspection unresolved-references
    assert isinstance(q.conditions[0].left.object_type, ObjectAttribute)
    assert isinstance(q.conditions[0].right, ObjectAttribute)

    translator = setup_translation_environment(query_data)
    translated_q = translator.translate_query(q)

    expected_q = (  "SELECT"
                    "test_datalib_test_data_query_tables__SampleGrandparent.*"
                    "FROM"
                    "	test_datalib_test_data_query_tables__SampleGrandparent"
                    "INNER JOIN test_datalib_test_data_query_tables__SampleParent ON test_datalib_test_data_query_tables__SampleParent.test_datalib_test_data_query_tables__SampleParentid = test_datalib_test_data_query_tables__SampleGrandparent.parent"
                    "WHERE"
                    "(test_datalib_test_data_query_tables__SampleParent.child = test_datalib_test_data_query_tables__SampleGrandparent.child);"
    )

    assert remove_whitespace(translated_q.query_to_database) == remove_whitespace(expected_q)

def test_multiple_subscripting_fields():
    from test.datalib import test_data_query_tables as query_data
    make_module_subscriptable(query_data)
    q = blank_database_interface.select(query_data.SampleGreatGrandparent).where(
        query_data.SampleGreatGrandparent["grandparent"]["parent"]["child"] == query_data.SampleGreatGrandparent["grandparent"]["child"]
    )

    assert q.expected_type == query_data.SampleGreatGrandparent
    assert len(q.conditions) == 1
    assert isinstance(q.conditions[0].left, ObjectAttribute)
    assert isinstance(q.conditions[0].right, ObjectAttribute)

    translator = setup_translation_environment(query_data)
    translated_q = translator.translate_query(q)

    expected_query = (  "SELECT"
	                    "test_datalib_test_data_query_tables__SampleGreatGrandparent.*"
                        "FROM"
                        "	test_datalib_test_data_query_tables__SampleGreatGrandparent"
                        "INNER JOIN test_datalib_test_data_query_tables__SampleGrandparent ON test_datalib_test_data_query_tables__SampleGrandparent.test_datalib_test_data_query_tables__SampleGrandparentid = test_datalib_test_data_query_tables__SampleGreatGrandparent.grandparent"
                        "INNER JOIN test_datalib_test_data_query_tables__SampleParent ON test_datalib_test_data_query_tables__SampleParent.test_datalib_test_data_query_tables__SampleParentid = test_datalib_test_data_query_tables__SampleGrandparent.parent"
                        "WHERE"
                        "(test_datalib_test_data_query_tables__SampleParent.child = test_datalib_test_data_query_tables__SampleGrandparent.child);"
    )

    assert remove_whitespace(translated_q.query_to_database) == remove_whitespace(expected_query)

def test_query_combination():
    query_1 = Query(int, blank_database_interface.execute_query)
    query_2 = Query(str, blank_database_interface.execute_query)
    combined_query: QueryBundle[int, str] = QueryBundle.create((query_1, query_2))

    assert combined_query.expected_types == (int, str)

    query_3 = Query(bool, blank_database_interface.execute_query)
    doubly_combined_query = QueryBundle.create((query_1, query_2, query_3))

    assert doubly_combined_query.expected_types == (int, str, bool)

    # TODO write assertion properties

def test_field_with_multiple_types():
    from test.datalib import test_data_query_tables as query_data
    make_module_subscriptable(query_data)

    print_schema(query_data)

    q = blank_database_interface.select(query_data.CouldHaveParentOrGrandparent).where(query_data.CouldHaveParentOrGrandparent["simpler_concept"] == 1)

def setup_translation_environment(module: ModuleType) -> SQLiteQueryTranslator:
    make_module_subscriptable(module)
    creation_graph = ClassDependencyGraph((module,))
    table_structure = TableStructure(creation_graph, StandardTableNamer())
    sqlite_query_translator = SQLiteQueryTranslator(table_structure)
    return sqlite_query_translator

def print_translated_query[T](translated_query: QueryToBeResolved[T, SQLiteString]):
    print("\n" + translated_query.query_to_database)

def print_schema(module: ModuleType):
    creation_graph = ClassDependencyGraph((module,))
    table_structure = TableStructure(creation_graph, StandardTableNamer())
    sqlite_schema_translator = SQLiteSchemaTranslator(StandardPrimaryKeyResolver())
    schema = sqlite_schema_translator.translate_schema(table_structure)
    print(schema.query_to_database)

if __name__ == "__main__":
    test_basic_query()
    test_query_from_interface()
    test_query_basic_valid_condition()
    test_query_subscripting_field()
    test_query_combination()
    test_multiple_subscripting_fields()