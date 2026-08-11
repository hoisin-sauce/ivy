from datalib import schema, sqlite_schema_translator
from datalib.database_constraint import StandardPrimaryKeyResolver
from datalib.naming import StandardTableNamer, StandardFieldNamer
import modeldata
from datalib.queries import Query, QueryBundle
from datalib.no_data import NoDatabaseManager, NoQueryBundleTranslator


def test_modeldata_graph_initialisation():
    db = schema.ClassDependencyGraph((modeldata,))
    build_order = db.get_build_order()
    assert(all(
        [all([dep in build_order[:i] for dep in db.datatype_map[obj].dependencies])
         for i, obj in enumerate(build_order)])), \
        "Build order is incorrect"
    assert(all(datatype in build_order
               for i in dir(modeldata)
               if type(datatype := getattr(modeldata, i)) == type and datatype.__module__ == modeldata.__name__)), \
        "Some classes were not initialised"

def test_optional_foreign():
    from test.datalib import test_data_foreign as test_data
    db = schema.ClassDependencyGraph((test_data,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver(), StandardFieldNamer())
    schema_translator.translate_schema(table_structure)

def test_enum():
    from test.datalib import test_data_enum as test_data
    db = schema.ClassDependencyGraph((test_data,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver(), StandardFieldNamer())
    schema_translator.translate_schema(table_structure)

def test_iter():
    from test.datalib import test_data_iter as test_data
    db = schema.ClassDependencyGraph((test_data,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver(), StandardFieldNamer())
    schema_translator.translate_schema(table_structure)

def test_modeldata_table_initialisation():
    db = schema.ClassDependencyGraph((modeldata,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver(), StandardFieldNamer())
    schema_translator.translate_schema(table_structure)

def test_query_combination():
    database_manager = NoDatabaseManager()
    query_1 = Query(int, database_manager.execute_query)
    query_2 = Query(str, database_manager.execute_query)
    combined_query: QueryBundle[int, str] = QueryBundle.create((query_1, query_2))
    query_3 = Query(bool, database_manager.execute_query)
    doubly_combined_query = QueryBundle.create((query_1, query_2, query_3))
    print(doubly_combined_query.expected_types)

if __name__ == "__main__":
    test_modeldata_graph_initialisation()
    test_modeldata_table_initialisation()
    test_enum()
    test_iter()
    test_optional_foreign()