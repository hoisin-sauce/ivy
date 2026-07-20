import datalib
import modeldata

def test_modeldata_initialisation():
    db = datalib.Database((modeldata,))
    build_order = db.get_build_order()
    print(build_order)
    assert(all([all([dep in build_order[:i] for dep in db.datatype_map[obj].dependencies]) for i, obj in enumerate(build_order)])), "Build order is incorrect"
    assert(all(i in build_order for i in dir(modeldata))), "Some classes were not initialised"