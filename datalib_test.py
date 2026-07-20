import datalib
import modeldata

def test_modeldata_initialisation():
    db = datalib.Database((modeldata,))
    build_order = db.get_build_order()
    assert(all(
        [all([dep in build_order[:i] for dep in db.datatype_map[obj].dependencies])
         for i, obj in enumerate(build_order)])), \
        "Build order is incorrect"
    assert(all(datatype in build_order
               for i in dir(modeldata)
               if type(datatype := getattr(modeldata, i)) == type)), \
        "Some classes were not initialised"

if __name__ == "__main__":
    test_modeldata_initialisation()