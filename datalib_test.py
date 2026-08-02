import datalib
import modeldata

def test_modeldata_graph_initialisation():
    db = datalib.ClassDependencyGraph((modeldata,))
    build_order = db.get_build_order()
    assert(all(
        [all([dep in build_order[:i] for dep in db.datatype_map[obj].dependencies])
         for i, obj in enumerate(build_order)])), \
        "Build order is incorrect"
    assert(all(datatype in build_order
               for i in dir(modeldata)
               if type(datatype := getattr(modeldata, i)) == type and datatype.__module__ == modeldata.__name__)), \
        "Some classes were not initialised"

def test_modeldata_table_initialisation():
    db = datalib.ClassDependencyGraph((modeldata,))
    table_structure = datalib.TableStructure(db)

if __name__ == "__main__":
    test_modeldata_graph_initialisation()
    test_modeldata_table_initialisation()