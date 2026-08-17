from datalib import schema, sqlite_schema_translator
from datalib.database_constraint import StandardPrimaryKeyResolver
from datalib.naming import StandardTableNamer
import modeldata


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
        StandardPrimaryKeyResolver())
    schema_translator.translate_schema(table_structure)

def test_enum():
    from test.datalib import test_data_enum as test_data
    db = schema.ClassDependencyGraph((test_data,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver())
    schema_translator.translate_schema(table_structure)

def test_iter():
    from test.datalib import test_data_iter as test_data
    db = schema.ClassDependencyGraph((test_data,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver())
    schema_translator.translate_schema(table_structure)

def test_union():
    from test.datalib import test_data_union as test_data
    db = schema.ClassDependencyGraph((test_data,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver()
    )
    translated = schema_translator.translate_schema(table_structure)
    print(translated.query_to_database.query_string)

def test_modeldata_table_initialisation():
    db = schema.ClassDependencyGraph((modeldata,))
    table_structure = schema.TableStructure(db, StandardTableNamer())
    schema_translator = sqlite_schema_translator.SQLiteSchemaTranslator(
        StandardPrimaryKeyResolver())
    schema_translator.translate_schema(table_structure)

if __name__ == "__main__":
    test_modeldata_graph_initialisation()
    test_modeldata_table_initialisation()
    test_enum()
    test_iter()
    test_optional_foreign()